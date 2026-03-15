"""
Authentication API endpoints.
Register, login, and user profile management.
"""

import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.schemas.api import UserRegister, UserLogin, TokenResponse, UserResponse
from app.core.security import hash_password, verify_password, create_access_token
from app.core.database import get_collection
from app.core.config import settings
from app.api.dependencies import get_current_user
from bson import ObjectId

logger = logging.getLogger(__name__)

# Auth endpoints use a tighter rate limit than the global default
_auth_limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
@_auth_limiter.limit(f"{settings.AUTH_RATE_LIMIT_PER_MINUTE}/minute")
async def register(request: Request, user_data: UserRegister):
    """
    Register a new user.
    
    Args:
        user_data: User registration data
        
    Returns:
        Token and user info
    """
    
    users_collection = get_collection("users")
    normalized_email = user_data.email.strip().lower()
    normalized_name = user_data.name.strip()
    normalized_password = user_data.password.strip()

    if not normalized_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Name cannot be empty"
        )

    if len(normalized_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters"
        )
    
    # Check if user exists
    existing_user = users_collection.find_one({"email": normalized_email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    # Hash password
    hashed_password = hash_password(normalized_password)

    now = datetime.utcnow()
    # Create user with onboarding tracking
    user_doc = {
        "name": normalized_name,
        "full_name": normalized_name,
        "email": normalized_email,
        "password_hash": hashed_password,
        "primary_role": "",
        "experience_level": "",
        "profile_image_url": "",
        "onboarding_completed": False,
        "onboarding_step": 0,
        "created_at": now,
        "updated_at": now
    }
    logger.info("Registering new user: %s", normalized_email)
    
    result = users_collection.insert_one(user_doc)
    user_id = str(result.inserted_id)
    
    # Create token
    access_token = create_access_token({"sub": user_id, "email": normalized_email})
    
    return TokenResponse(
        access_token=access_token,
        user=UserResponse(
            _id=user_id,
            name=user_doc.get("full_name") or user_doc.get("name", ""),
            email=normalized_email,
            created_at=user_doc["created_at"],
            onboarding_completed=False,
            onboarding_step=0
        )
    )


@router.post("/login", response_model=TokenResponse)
@_auth_limiter.limit(f"{settings.AUTH_RATE_LIMIT_PER_MINUTE}/minute")
async def login(request: Request, credentials: UserLogin):
    """
    Login user.
    
    Args:
        credentials: Login credentials
        
    Returns:
        Token and user info
    """
    
    users_collection = get_collection("users")
    normalized_email = credentials.email.strip().lower()
    normalized_password = credentials.password.strip()
    
    # Find user
    user = users_collection.find_one({"email": normalized_email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Verify password
    if not verify_password(normalized_password, user.get("password_hash", "")):
        logger.warning("Failed login attempt for: %s", normalized_email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Create token
    user_id = str(user["_id"])
    access_token = create_access_token({"sub": user_id, "email": user["email"]})
    logger.info("User logged in: %s", normalized_email)
    
    return TokenResponse(
        access_token=access_token,
        user=UserResponse(
            _id=user_id,
            name=user.get("full_name") or user.get("name", ""),
            email=user.get("email", ""),
            created_at=user.get("created_at"),
            onboarding_completed=user.get("onboarding_completed", False),
            onboarding_step=user.get("onboarding_step", 0)
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
        created_at=user.get("created_at"),
        onboarding_completed=user.get("onboarding_completed", False),
        onboarding_step=user.get("onboarding_step", 0)
    )


@router.post("/refresh")
async def refresh_token(current_user_id: str = Depends(get_current_user)):
    """Refresh access token using the existing valid token."""
    users_collection = get_collection("users")
    user = users_collection.find_one({"_id": ObjectId(current_user_id)})
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    access_token = create_access_token({"sub": current_user_id, "email": user.get("email", "")})
    logger.info("Token refreshed for user: %s", current_user_id)
    return {"access_token": access_token, "token_type": "bearer"}


@router.patch("/onboarding")
async def update_onboarding(current_user_id: str = Depends(get_current_user)):
    """Mark onboarding as completed."""
    users_collection = get_collection("users")
    users_collection.update_one(
        {"_id": ObjectId(current_user_id)},
        {"$set": {"onboarding_completed": True, "onboarding_step": 3, "updated_at": datetime.utcnow()}}
    )
    logger.info("Onboarding completed for user: %s", current_user_id)
    return {"success": True, "message": "Onboarding complete"}


@router.get("/onboarding-status")
async def get_onboarding_status(current_user_id: str = Depends(get_current_user)):
    """Get user onboarding status."""
    users_collection = get_collection("users")
    user = users_collection.find_one({"_id": ObjectId(current_user_id)}, {"onboarding_completed": 1, "onboarding_step": 1})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "onboarding_completed": user.get("onboarding_completed", False),
        "onboarding_step": user.get("onboarding_step", 0)
    }
