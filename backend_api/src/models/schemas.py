from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, validator
from enum import Enum


class UserRole(str, Enum):
    """User role enumeration"""
    REGULAR_USER = "regular_user"
    ADMIN = "admin"


class MoodType(str, Enum):
    """Mood type enumeration"""
    VERY_HAPPY = "very_happy"
    HAPPY = "happy" 
    NEUTRAL = "neutral"
    SAD = "sad"
    VERY_SAD = "very_sad"
    ANXIOUS = "anxious"
    EXCITED = "excited"
    CALM = "calm"
    ANGRY = "angry"
    GRATEFUL = "grateful"


# User Models
class UserRegister(BaseModel):
    """User registration request model"""
    username: str = Field(..., min_length=3, max_length=50, description="Username (3-50 characters)")
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(..., min_length=8, max_length=128, description="Password (8-128 characters)")
    full_name: Optional[str] = Field(None, max_length=100, description="Full name (optional)")
    
    @validator('username')
    def validate_username(cls, v):
        if not v.isalnum() and '_' not in v:
            raise ValueError('Username must contain only alphanumeric characters and underscores')
        return v.lower()


class UserLogin(BaseModel):
    """User login request model"""
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="Password")


class UserResponse(BaseModel):
    """User response model"""
    id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    full_name: Optional[str] = Field(None, description="Full name")
    role: UserRole = Field(..., description="User role")
    created_at: datetime = Field(..., description="Account creation timestamp")
    is_active: bool = Field(True, description="Account active status")


class UserUpdate(BaseModel):
    """User update request model"""
    full_name: Optional[str] = Field(None, max_length=100, description="Full name")
    email: Optional[EmailStr] = Field(None, description="Email address")


# Journal Entry Models
class JournalEntryCreate(BaseModel):
    """Journal entry creation request model"""
    title: str = Field(..., min_length=1, max_length=200, description="Entry title")
    content: str = Field(..., min_length=1, max_length=10000, description="Entry content")
    mood: Optional[MoodType] = Field(None, description="Mood associated with entry")
    tags: Optional[List[str]] = Field(default_factory=list, description="Entry tags")
    is_private: bool = Field(False, description="Whether entry is private")
    
    @validator('tags')
    def validate_tags(cls, v):
        if v:
            # Clean and validate tags
            clean_tags = []
            for tag in v:
                if isinstance(tag, str) and tag.strip():
                    clean_tag = tag.strip().lower()[:50]  # Max 50 chars per tag
                    if clean_tag not in clean_tags:
                        clean_tags.append(clean_tag)
            return clean_tags[:10]  # Max 10 tags
        return []


class JournalEntryUpdate(BaseModel):
    """Journal entry update request model"""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="Entry title")
    content: Optional[str] = Field(None, min_length=1, max_length=10000, description="Entry content")
    mood: Optional[MoodType] = Field(None, description="Mood associated with entry")
    tags: Optional[List[str]] = Field(None, description="Entry tags")
    is_private: Optional[bool] = Field(None, description="Whether entry is private")
    
    @validator('tags')
    def validate_tags(cls, v):
        if v is not None:
            clean_tags = []
            for tag in v:
                if isinstance(tag, str) and tag.strip():
                    clean_tag = tag.strip().lower()[:50]
                    if clean_tag not in clean_tags:
                        clean_tags.append(clean_tag)
            return clean_tags[:10]
        return v


class JournalEntryResponse(BaseModel):
    """Journal entry response model"""
    id: str = Field(..., description="Entry ID")
    title: str = Field(..., description="Entry title")
    content: str = Field(..., description="Entry content")
    mood: Optional[MoodType] = Field(None, description="Entry mood")
    tags: List[str] = Field(default_factory=list, description="Entry tags")
    is_private: bool = Field(False, description="Privacy status")
    user_id: str = Field(..., description="Owner user ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


# Search and Filter Models
class EntrySearchParams(BaseModel):
    """Entry search parameters"""
    query: Optional[str] = Field(None, max_length=200, description="Search query")
    mood: Optional[MoodType] = Field(None, description="Filter by mood")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    date_from: Optional[datetime] = Field(None, description="Filter from date")
    date_to: Optional[datetime] = Field(None, description="Filter to date")
    limit: int = Field(20, ge=1, le=100, description="Results limit")
    offset: int = Field(0, ge=0, description="Results offset")


# Authentication Models
class Token(BaseModel):
    """JWT token response model"""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")


class TokenData(BaseModel):
    """Token data model for JWT validation"""
    username: Optional[str] = None
    user_id: Optional[str] = None
    role: Optional[str] = None


# Response Models
class MessageResponse(BaseModel):
    """Generic message response model"""
    message: str = Field(..., description="Response message")
    success: bool = Field(True, description="Operation success status")


class EntryListResponse(BaseModel):
    """Journal entries list response model"""
    entries: List[JournalEntryResponse] = Field(..., description="List of entries")
    total: int = Field(..., description="Total number of entries")
    limit: int = Field(..., description="Results limit")
    offset: int = Field(..., description="Results offset")


# Export Models
class ExportRequest(BaseModel):
    """Export request model"""
    format: str = Field(..., pattern="^(txt|pdf)$", description="Export format (txt or pdf)")
    date_from: Optional[datetime] = Field(None, description="Export from date")
    date_to: Optional[datetime] = Field(None, description="Export to date")
    include_private: bool = Field(True, description="Include private entries")


class ExportResponse(BaseModel):
    """Export response model"""
    download_url: str = Field(..., description="Download URL for exported file")
    filename: str = Field(..., description="Generated filename")
    expires_at: datetime = Field(..., description="Download link expiration")
