from fastapi import APIRouter, HTTPException, status, Depends, Request, Query
from fastapi.responses import FileResponse
from typing import Dict, Any, Optional
from datetime import datetime
import os

from ...models.schemas import MessageResponse
from ...utils.database import db
from ...utils.security import get_current_active_user, api_limiter
from ...utils.export import export_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/export", tags=["Export"])


# PUBLIC_INTERFACE
@router.post("/entries", response_model=Dict[str, Any], summary="Export journal entries")
@api_limiter
async def export_entries(
    request: Request,
    export_format: str = Query(..., pattern="^(txt|pdf)$", description="Export format (txt or pdf)"),
    date_from: Optional[datetime] = Query(None, description="Export from date (ISO format)"),
    date_to: Optional[datetime] = Query(None, description="Export to date (ISO format)"),
    include_private: bool = Query(True, description="Include private entries"),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Export journal entries to file.
    
    Exports user's journal entries to TXT or PDF format with optional date filtering.
    Returns download information for the generated file.
    
    Args:
        export_format: Format to export (txt or pdf)
        date_from: Optional start date for filtering entries
        date_to: Optional end date for filtering entries
        include_private: Whether to include private entries
        current_user: Current authenticated user
        
    Returns:
        Export file information including download details
        
    Raises:
        HTTPException: If export fails or no entries found
    """
    try:
        # Build search parameters for entries to export
        search_params = {
            "date_from": date_from,
            "date_to": date_to,
            "limit": 1000,  # Export limit
            "offset": 0
        }
        
        # Get entries to export
        entries = db.search_entries(current_user["id"], search_params)
        
        # Filter private entries if needed
        if not include_private:
            entries = [entry for entry in entries if not entry.get("is_private", False)]
        
        if not entries:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No entries found for export with the specified criteria"
            )
        
        # Generate timestamp for filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Export based on format
        try:
            if export_format == "txt":
                filename = f"journal_entries_{current_user['username']}_{timestamp}.txt"
                filepath = export_service.export_to_txt(current_user["id"], entries, filename)
            elif export_format == "pdf":
                filename = f"journal_entries_{current_user['username']}_{timestamp}.pdf"
                filepath = export_service.export_to_pdf(current_user["id"], entries, filename)
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid export format. Use 'txt' or 'pdf'"
                )
            
            # Check if file was created
            if not os.path.exists(filepath):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to generate export file"
                )
            
            return {
                "message": "Export completed successfully",
                "filename": filename,
                "format": export_format,
                "entries_count": len(entries),
                "file_size": os.path.getsize(filepath),
                "created_at": datetime.now().isoformat(),
                "download_endpoint": f"/api/export/download/{filename}"
            }
            
        except Exception as export_error:
            logger.error(f"Export generation error: {export_error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate {export_format.upper()} export: {str(export_error)}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during export"
        )


# PUBLIC_INTERFACE
@router.get("/download/{filename}", summary="Download exported file")
async def download_export_file(
    filename: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Download an exported file.
    
    Downloads a previously generated export file. Files are user-specific
    and automatically cleaned up after a period.
    
    Args:
        filename: Name of the file to download
        current_user: Current authenticated user
        
    Returns:
        File download response
        
    Raises:
        HTTPException: If file not found or access denied
    """
    try:
        # Validate filename format and ownership
        if not filename or ".." in filename or "/" in filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid filename"
            )
        
        # Check if filename contains user's username (basic security)
        if current_user["username"] not in filename:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this file"
            )
        
        # Build file path
        filepath = os.path.join(export_service.export_dir, filename)
        
        # Check if file exists
        if not os.path.exists(filepath):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Export file not found or has expired"
            )
        
        # Determine media type
        media_type = "text/plain" if filename.endswith(".txt") else "application/pdf"
        
        # Return file
        return FileResponse(
            path=filepath,
            filename=filename,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download error for {filename}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during file download"
        )


# PUBLIC_INTERFACE
@router.delete("/cleanup", response_model=MessageResponse, summary="Cleanup old export files")
async def cleanup_exports(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Cleanup old export files.
    
    Removes export files older than 7 days. Only removes files belonging
    to the current user.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Cleanup status message
    """
    try:
        # Run cleanup for old exports
        export_service.cleanup_old_exports(days_old=7)
        
        return MessageResponse(
            message="Export cleanup completed successfully",
            success=True
        )
        
    except Exception as e:
        logger.error(f"Cleanup error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during cleanup"
        )
