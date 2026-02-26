"""
Utility functions for file handling, validation, and common operations.
"""

import os
import secrets
from pathlib import Path
from typing import Tuple
from app.core.config import settings


def validate_file_upload(filename: str, file_size: int) -> Tuple[bool, str]:
    """
    Validate uploaded file.
    
    Args:
        filename: Original filename
        file_size: File size in bytes
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    
    # Check file extension
    file_ext = Path(filename).suffix.lower().lstrip('.')
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        return False, f"File type .{file_ext} not allowed. Use PDF or DOCX."
    
    # Check file size
    if file_size > settings.MAX_FILE_SIZE:
        max_mb = settings.MAX_FILE_SIZE / (1024 * 1024)
        return False, f"File size exceeds {max_mb}MB limit"
    
    # Check file size minimum
    if file_size < 1024:  # 1 KB minimum
        return False, "File is too small"
    
    return True, ""


def generate_safe_filename(original_filename: str, user_id: str) -> str:
    """
    Generate a safe, unique filename for upload.
    
    Args:
        original_filename: Original filename from upload
        user_id: User ID for file organization
        
    Returns:
        Safe filename
    """
    
    # Get file extension
    ext = Path(original_filename).suffix.lower()
    
    # Generate random string
    random_str = secrets.token_hex(8)
    
    # Create safe filename
    safe_name = f"resume_{user_id}_{random_str}{ext}"
    
    return safe_name


def get_upload_path(filename: str) -> str:
    """
    Get full path for uploaded file.
    
    Args:
        filename: Filename
        
    Returns:
        Full file path
    """
    
    # Ensure upload directory exists
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    return str(upload_dir / filename)


def cleanup_file(file_path: str) -> bool:
    """
    Delete a file safely.
    
    Args:
        file_path: Path to file
        
    Returns:
        Success status
    """
    
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
    except Exception as e:
        print(f"Error deleting file {file_path}: {e}")
    
    return False


def format_error_response(error: str, code: str = "ERROR") -> dict:
    """
    Format standardized error response.
    
    Args:
        error: Error message
        code: Error code
        
    Returns:
        Error response dict
    """
    
    return {
        "error": error,
        "code": code,
        "status": "error"
    }


def format_success_response(data: dict, message: str = "Success") -> dict:
    """
    Format standardized success response.
    
    Args:
        data: Response data
        message: Success message
        
    Returns:
        Success response dict
    """
    
    return {
        "data": data,
        "message": message,
        "status": "success"
    }


async def truncate_text(text: str, max_length: int = 1000) -> str:
    """
    Truncate text to maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        
    Returns:
        Truncated text
    """
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length] + "..."


def extract_domain_from_role(job_role: str) -> str:
    """
    Extract technical domain from job role.
    
    Args:
        job_role: Job role/title
        
    Returns:
        Domain name
    """
    
    role_lower = job_role.lower()
    
    domains = {
        "backend": ["backend", "server", "api", "django", "flask", "fastapi"],
        "frontend": ["frontend", "react", "vue", "angular", "ui", "ux"],
        "fullstack": ["fullstack", "full-stack", "full stack"],
        "devops": ["devops", "infrastructure", "cloud", "aws", "azure"],
        "data": ["data", "engineer", "ml", "machine learning", "ai"],
        "mobile": ["mobile", "ios", "android", "flutter", "react native"],
    }
    
    for domain, keywords in domains.items():
        if any(keyword in role_lower for keyword in keywords):
            return domain.capitalize()
    
    return "General"
