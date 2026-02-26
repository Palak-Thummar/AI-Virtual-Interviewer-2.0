"""
Authentication API endpoints.
Register, login, and user profile management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from datetime import timedelta
from app.schemas.api import UserRegister, UserLogin, TokenResponse, UserResponse
from app.core.security import hash_password, verify_password, create_access_token
from app.core.database import get_collection
from app.core.config import settings
from app.api.dependencies import get_current_user
from bson import ObjectId

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
async def register(user_data: UserRegister):
    """
    Register a new user.
    
    Args:
        user_data: User registration data
        
    Returns:
        Token and user info
    """
    
    users_collection = get_collection("users")
    
    # Check if user exists
    existing_user = users_collection.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    # Hash password
    hashed_password = hash_password(user_data.password)
    
    # Create user
    user_doc = {
        "name": user_data.name,
        "full_name": user_data.name,
        "email": user_data.email,
        "password_hash": hashed_password,
        "primary_role": "",
        "experience_level": "",
        "profile_image_url": "",
        "created_at": __import__("datetime").datetime.utcnow(),
        "updated_at": __import__("datetime").datetime.utcnow()
    }
    
    result = users_collection.insert_one(user_doc)
    user_id = str(result.inserted_id)
    
    # Create token
    access_token = create_access_token({"sub": user_id, "email": user_data.email})
    
    return TokenResponse(
        access_token=access_token,
        user=UserResponse(
            _id=user_id,
            name=user_doc.get("full_name") or user_doc.get("name", ""),
            email=user_data.email,
            created_at=user_doc["created_at"]
        )
    )


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    """
    Login user.
    
    Args:
        credentials: Login credentials
        
    Returns:
        Token and user info
    """
    
    users_collection = get_collection("users")
    
    # Find user
    user = users_collection.find_one({"email": credentials.email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Verify password
    if not verify_password(credentials.password, user.get("password_hash", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Create token
    user_id = str(user["_id"])
    access_token = create_access_token({"sub": user_id, "email": user["email"]})
    
    return TokenResponse(
        access_token=access_token,
        user=UserResponse(
            _id=user_id,
            name=user.get("full_name") or user.get("name", ""),
            email=user.get("email", ""),
            created_at=user.get("created_at")
        )
    )


@router.get("/me", response_model=UserResponse)
async def get_profile(current_user_id: str = Depends(get_current_user)):
    """
    Get current user profile.
    
    Args:
        current_user_id: Current user ID from token
        
    Returns:
        User profile data
    """
    
    users_collection = get_collection("users")
    user = users_collection.find_one({"_id": ObjectId(current_user_id)})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        _id=str(user["_id"]),
        name=user.get("full_name") or user.get("name", ""),
        email=user.get("email", ""),
        created_at=user.get("created_at")
    )


@router.post("/refresh")
async def refresh_token(current_user_id: str = None):
    """
    Refresh access token.
    
    Args:
        current_user_id: Current user ID
        
    Returns:
        New token
    """
    
    if not current_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    # Create new token
    access_token = create_access_token({"sub": current_user_id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
