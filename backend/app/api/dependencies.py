"""
Dependency injection for current user authentication.
"""

from fastapi import Depends, HTTPException, status, Header
from typing import Optional
from app.core.security import decode_token


async def get_current_user(authorization: Optional[str] = Header(None)) -> str:
    """
    Get current user ID from JWT token in Authorization header.
    
    Args:
        authorization: Authorization header value (Bearer <token>)
        
    Returns:
        User ID
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Extract token from "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = parts[1]
    payload = decode_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    user_id = payload.get("sub")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing user ID",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return user_id
