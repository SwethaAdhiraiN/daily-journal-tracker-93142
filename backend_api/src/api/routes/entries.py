from fastapi import APIRouter, HTTPException, status, Depends, Request, Query
from typing import Dict, Any, Optional
from datetime import datetime

from ...models.schemas import (
    JournalEntryCreate, JournalEntryUpdate, JournalEntryResponse,
    EntryListResponse, MessageResponse, MoodType
)
from ...utils.database import db
from ...utils.security import (
    get_current_active_user, validate_entry_access, 
    api_limiter, search_limiter, sanitize_input
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/entries", tags=["Journal Entries"])


# PUBLIC_INTERFACE
@router.post("", response_model=JournalEntryResponse, summary="Create new journal entry")
@api_limiter
async def create_entry(
    request: Request,
    entry_data: JournalEntryCreate,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Create a new journal entry.
    
    Creates a new journal entry for the authenticated user with title, content,
    mood, and tags. All text content is sanitized for security.
    
    Args:
        entry_data: Journal entry creation data
        current_user: Current authenticated user
        
    Returns:
        Created journal entry
        
    Raises:
        HTTPException: If creation fails
    """
    try:
        # Sanitize input data
        sanitized_data = {
            "title": sanitize_input(entry_data.title, 200),
            "content": sanitize_input(entry_data.content, 10000),
            "mood": entry_data.mood.value if entry_data.mood else None,
            "tags": entry_data.tags or [],
            "is_private": entry_data.is_private,
            "user_id": current_user["id"]
        }
        
        # Create entry in database
        entry_id = db.create_entry(sanitized_data)
        if not entry_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create journal entry"
            )
        
        # Get created entry
        created_entry = db.get_entry_by_id(entry_id)
        if not created_entry:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve created entry"
            )
        
        return JournalEntryResponse(
            id=created_entry["id"],
            title=created_entry["title"],
            content=created_entry["content"],
            mood=created_entry.get("mood"),
            tags=created_entry.get("tags", []),
            is_private=created_entry.get("is_private", False),
            user_id=created_entry["user_id"],
            created_at=created_entry["created_at"],
            updated_at=created_entry["updated_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Entry creation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during entry creation"
        )


# PUBLIC_INTERFACE
@router.get("", response_model=EntryListResponse, summary="Get user's journal entries")
@api_limiter
async def get_entries(
    request: Request,
    limit: int = Query(20, ge=1, le=100, description="Number of entries to return"),
    offset: int = Query(0, ge=0, description="Number of entries to skip"),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Get journal entries for the current user.
    
    Retrieves a paginated list of journal entries belonging to the authenticated user,
    ordered by creation date (newest first).
    
    Args:
        limit: Maximum number of entries to return (1-100)
        offset: Number of entries to skip for pagination
        current_user: Current authenticated user
        
    Returns:
        Paginated list of journal entries
    """
    try:
        # Get entries from database
        entries = db.get_entries_by_user(current_user["id"], limit, offset)
        total_count = db.get_user_entry_count(current_user["id"])
        
        # Convert to response format
        entry_responses = []
        for entry in entries:
            entry_responses.append(JournalEntryResponse(
                id=entry["id"],
                title=entry["title"],
                content=entry["content"],
                mood=entry.get("mood"),
                tags=entry.get("tags", []),
                is_private=entry.get("is_private", False),
                user_id=entry["user_id"],
                created_at=entry["created_at"],
                updated_at=entry["updated_at"]
            ))
        
        return EntryListResponse(
            entries=entry_responses,
            total=total_count,
            limit=limit,
            offset=offset
        )
        
    except Exception as e:
        logger.error(f"Error fetching entries: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while fetching entries"
        )


# PUBLIC_INTERFACE
@router.get("/{entry_id}", response_model=JournalEntryResponse, summary="Get specific journal entry")
@api_limiter
async def get_entry(
    request: Request,
    entry_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Get a specific journal entry by ID.
    
    Retrieves a journal entry by its ID. User must own the entry or be an admin.
    
    Args:
        entry_id: ID of the journal entry to retrieve
        current_user: Current authenticated user
        
    Returns:
        Journal entry details
        
    Raises:
        HTTPException: If entry not found or access denied
    """
    try:
        # Validate access and get entry
        entry = validate_entry_access(entry_id, current_user)
        
        return JournalEntryResponse(
            id=entry["id"],
            title=entry["title"],
            content=entry["content"],
            mood=entry.get("mood"),
            tags=entry.get("tags", []),
            is_private=entry.get("is_private", False),
            user_id=entry["user_id"],
            created_at=entry["created_at"],
            updated_at=entry["updated_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching entry {entry_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while fetching entry"
        )


# PUBLIC_INTERFACE
@router.put("/{entry_id}", response_model=JournalEntryResponse, summary="Update journal entry")
@api_limiter
async def update_entry(
    request: Request,
    entry_id: str,
    entry_update: JournalEntryUpdate,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Update a journal entry.
    
    Updates an existing journal entry. User must own the entry or be an admin.
    Only provided fields will be updated.
    
    Args:
        entry_id: ID of the journal entry to update
        entry_update: Updated entry data
        current_user: Current authenticated user
        
    Returns:
        Updated journal entry
        
    Raises:
        HTTPException: If entry not found, access denied, or update fails
    """
    try:
        # Validate access
        validate_entry_access(entry_id, current_user)
        
        # Prepare update data
        update_data = {}
        if entry_update.title is not None:
            update_data["title"] = sanitize_input(entry_update.title, 200)
        if entry_update.content is not None:
            update_data["content"] = sanitize_input(entry_update.content, 10000)
        if entry_update.mood is not None:
            update_data["mood"] = entry_update.mood.value if entry_update.mood else None
        if entry_update.tags is not None:
            update_data["tags"] = entry_update.tags
        if entry_update.is_private is not None:
            update_data["is_private"] = entry_update.is_private
        
        # Update entry in database
        success = db.update_entry(entry_id, current_user["id"], update_data)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update journal entry"
            )
        
        # Get updated entry
        updated_entry = db.get_entry_by_id(entry_id)
        if not updated_entry:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve updated entry"
            )
        
        return JournalEntryResponse(
            id=updated_entry["id"],
            title=updated_entry["title"],
            content=updated_entry["content"],
            mood=updated_entry.get("mood"),
            tags=updated_entry.get("tags", []),
            is_private=updated_entry.get("is_private", False),
            user_id=updated_entry["user_id"],
            created_at=updated_entry["created_at"],
            updated_at=updated_entry["updated_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating entry {entry_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while updating entry"
        )


# PUBLIC_INTERFACE
@router.delete("/{entry_id}", response_model=MessageResponse, summary="Delete journal entry")
@api_limiter
async def delete_entry(
    request: Request,
    entry_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Delete a journal entry.
    
    Deletes (soft delete) a journal entry. User must own the entry or be an admin.
    
    Args:
        entry_id: ID of the journal entry to delete
        current_user: Current authenticated user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If entry not found, access denied, or deletion fails
    """
    try:
        # Validate access
        validate_entry_access(entry_id, current_user)
        
        # Delete entry
        success = db.delete_entry(entry_id, current_user["id"])
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete journal entry"
            )
        
        return MessageResponse(
            message="Journal entry deleted successfully",
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting entry {entry_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while deleting entry"
        )


# PUBLIC_INTERFACE
@router.get("/search/query", response_model=EntryListResponse, summary="Search journal entries")
@search_limiter
async def search_entries(
    request: Request,
    query: Optional[str] = Query(None, max_length=200, description="Search query"),
    mood: Optional[MoodType] = Query(None, description="Filter by mood"),
    tags: Optional[str] = Query(None, description="Comma-separated tags to filter by"),
    date_from: Optional[datetime] = Query(None, description="Filter from date (ISO format)"),
    date_to: Optional[datetime] = Query(None, description="Filter to date (ISO format)"),
    limit: int = Query(20, ge=1, le=100, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Search journal entries with filters.
    
    Search through user's journal entries using text query and various filters
    including mood, tags, and date range.
    
    Args:
        query: Text search query (searches title and content)
        mood: Filter by specific mood
        tags: Comma-separated list of tags to filter by
        date_from: Filter entries from this date onwards
        date_to: Filter entries up to this date
        limit: Maximum number of results to return
        offset: Number of results to skip for pagination
        current_user: Current authenticated user
        
    Returns:
        Paginated search results
    """
    try:
        # Parse tags
        tags_list = []
        if tags:
            tags_list = [tag.strip().lower() for tag in tags.split(",") if tag.strip()]
        
        # Build search parameters
        search_params = {
            "query": query,
            "mood": mood.value if mood else None,
            "tags": tags_list,
            "date_from": date_from,
            "date_to": date_to,
            "limit": limit,
            "offset": offset
        }
        
        # Search entries
        entries = db.search_entries(current_user["id"], search_params)
        
        # Convert to response format
        entry_responses = []
        for entry in entries:
            entry_responses.append(JournalEntryResponse(
                id=entry["id"],
                title=entry["title"],
                content=entry["content"],
                mood=entry.get("mood"),
                tags=entry.get("tags", []),
                is_private=entry.get("is_private", False),
                user_id=entry["user_id"],
                created_at=entry["created_at"],
                updated_at=entry["updated_at"]
            ))
        
        # Get total count for search (simplified - just return length)
        total_count = len(entry_responses)
        
        return EntryListResponse(
            entries=entry_responses,
            total=total_count,
            limit=limit,
            offset=offset
        )
        
    except Exception as e:
        logger.error(f"Error searching entries: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while searching entries"
        )
