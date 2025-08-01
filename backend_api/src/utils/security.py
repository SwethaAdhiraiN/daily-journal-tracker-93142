from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from slowapi import Limiter
from slowapi.util import get_remote_address
import logging

from .auth import extract_token_data
from .database import db

logger = logging.getLogger(__name__)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

# Security scheme
security = HTTPBearer(auto_error=False)


class SecurityService:
    """Security service for authentication and authorization"""
    
    @staticmethod
    def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Dict[str, Any]:
        """Get current authenticated user"""
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        token_data = extract_token_data(credentials.credentials)
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user from database
        user = db.get_user_by_id(token_data["user_id"])
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is disabled",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
    
    @staticmethod
    def get_current_active_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        """Get current active user"""
        if not current_user.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User account is disabled"
            )
        return current_user
    
    @staticmethod
    def require_admin(current_user: Dict[str, Any] = Depends(get_current_active_user)) -> Dict[str, Any]:
        """Require admin role"""
        if current_user.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        return current_user
    
    @staticmethod
    def get_optional_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[Dict[str, Any]]:
        """Get current user if authenticated, otherwise None"""
        if not credentials:
            return None
        
        token_data = extract_token_data(credentials.credentials)
        if not token_data:
            return None
        
        user = db.get_user_by_id(token_data["user_id"])
        if not user or not user.get("is_active", True):
            return None
        
        return user


# Create dependency instances
get_current_user = SecurityService.get_current_user
get_current_active_user = SecurityService.get_current_active_user
require_admin = SecurityService.require_admin
get_optional_user = SecurityService.get_optional_user


def validate_entry_access(entry_id: str, user: Dict[str, Any]) -> Dict[str, Any]:
    """Validate user has access to entry"""
    entry = db.get_entry_by_id(entry_id)
    
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Journal entry not found"
        )
    
    # Check if user owns the entry or is admin
    if entry.get("user_id") != user["id"] and user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this journal entry"
        )
    
    if entry.get("deleted", False):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Journal entry not found"
        )
    
    return entry


def sanitize_input(text: str, max_length: int = 10000) -> str:
    """Sanitize text input"""
    if not text:
        return ""
    
    # Basic sanitization
    sanitized = text.strip()[:max_length]
    
    # Remove null bytes
    sanitized = sanitized.replace('\x00', '')
    
    return sanitized


def validate_file_upload(file_content: bytes, allowed_types: list = None) -> bool:
    """Validate uploaded file"""
    if not allowed_types:
        allowed_types = ['text/plain', 'application/pdf']
    
    # Check file size (max 10MB)
    if len(file_content) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large (max 10MB)"
        )
    
    return True


# Rate limiting decorators
auth_limiter = limiter.limit("10/minute")
api_limiter = limiter.limit("100/minute")
search_limiter = limiter.limit("30/minute")
