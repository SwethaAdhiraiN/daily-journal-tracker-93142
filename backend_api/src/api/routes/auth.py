from fastapi import APIRouter, HTTPException, status, Depends, Request
from typing import Dict, Any

from ...models.schemas import UserRegister, UserLogin, UserResponse, MessageResponse
from ...utils.database import db
from ...utils.auth import verify_password, get_password_hash, create_user_token, validate_password_strength
from ...utils.security import auth_limiter, get_current_active_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


# PUBLIC_INTERFACE
@router.post("/register", response_model=Dict[str, Any], summary="Register new user")
@auth_limiter
async def register_user(request: Request, user_data: UserRegister):
    """
    Register a new user account.
    
    Creates a new user with hashed password and returns user info with access token.
    Validates password strength and checks for existing username/email.
    
    Args:
        user_data: User registration data including username, email, password
        
    Returns:
        Dict containing user info and access token
        
    Raises:
        HTTPException: If username/email exists or validation fails
    """
    try:
        # Validate password strength
        if not validate_password_strength(user_data.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters with uppercase, lowercase, and digit"
            )
        
        # Check if user already exists
        existing_user = db.get_user_by_username(user_data.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        existing_email = db.get_user_by_email(user_data.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Hash password
        hashed_password = get_password_hash(user_data.password)
        
        # Create user data
        user_dict = {
            "username": user_data.username,
            "email": user_data.email,
            "password": hashed_password,
            "full_name": user_data.full_name,
            "role": "regular_user"
        }
        
        # Create user in database
        user_id = db.create_user(user_dict)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user account"
            )
        
        # Get created user
        created_user = db.get_user_by_id(user_id)
        if not created_user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve created user"
            )
        
        # Create access token
        access_token = create_user_token(created_user)
        
        # Return user info and token
        user_response = UserResponse(
            id=created_user["id"],
            username=created_user["username"],
            email=created_user["email"],
            full_name=created_user.get("full_name"),
            role=created_user["role"],
            created_at=created_user["created_at"],
            is_active=created_user["is_active"]
        )
        
        return {
            "message": "User registered successfully",
            "user": user_response.dict(),
            "access_token": access_token,
            "token_type": "bearer"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during registration"
        )


# PUBLIC_INTERFACE
@router.post("/login", response_model=Dict[str, Any], summary="User login")
@auth_limiter
async def login_user(request: Request, credentials: UserLogin):
    """
    Authenticate user and return access token.
    
    Validates user credentials and returns user info with JWT access token.
    Supports login with username or email.
    
    Args:
        credentials: Login credentials (username/email and password)
        
    Returns:
        Dict containing user info and access token
        
    Raises:
        HTTPException: If credentials are invalid or account is disabled
    """
    try:
        # Find user by username or email
        user = db.get_user_by_username(credentials.username)
        if not user:
            user = db.get_user_by_email(credentials.username)
        
        # Verify user exists and password is correct
        if not user or not verify_password(credentials.password, user["password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username/email or password",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Check if account is active
        if not user.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is disabled",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Create access token
        access_token = create_user_token(user)
        
        # Return user info and token
        user_response = UserResponse(
            id=user["id"],
            username=user["username"],
            email=user["email"],
            full_name=user.get("full_name"),
            role=user["role"],
            created_at=user["created_at"],
            is_active=user["is_active"]
        )
        
        return {
            "message": "Login successful",
            "user": user_response.dict(),
            "access_token": access_token,
            "token_type": "bearer"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during login"
        )


# PUBLIC_INTERFACE
@router.post("/logout", response_model=MessageResponse, summary="User logout")
async def logout_user(current_user: Dict[str, Any] = Depends(get_current_active_user)):
    """
    Logout current user.
    
    Currently just returns success message. In production, could implement
    token blacklisting or other logout mechanisms.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Success message
    """
    return MessageResponse(
        message="Logout successful",
        success=True
    )


# PUBLIC_INTERFACE
@router.get("/me", response_model=UserResponse, summary="Get current user info")
async def get_current_user_info(current_user: Dict[str, Any] = Depends(get_current_active_user)):
    """
    Get current authenticated user information.
    
    Returns detailed information about the currently authenticated user.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Current user information
    """
    return UserResponse(
        id=current_user["id"],
        username=current_user["username"],
        email=current_user["email"],
        full_name=current_user.get("full_name"),
        role=current_user["role"],
        created_at=current_user["created_at"],
        is_active=current_user["is_active"]
    )


# PUBLIC_INTERFACE
@router.get("/verify", response_model=Dict[str, Any], summary="Verify token")
async def verify_token(current_user: Dict[str, Any] = Depends(get_current_active_user)):
    """
    Verify if the current token is valid.
    
    Endpoint to check if the provided JWT token is still valid and active.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Token verification status and user info
    """
    return {
        "valid": True,
        "user": UserResponse(
            id=current_user["id"],
            username=current_user["username"],
            email=current_user["email"],
            full_name=current_user.get("full_name"),
            role=current_user["role"],
            created_at=current_user["created_at"],
            is_active=current_user["is_active"]
        ).dict()
    }
