"""Notification API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_current_user
from app.services.notification_service import (
    delete_notification,
    get_unread_count,
    get_user_notifications,
    mark_all_notifications_read,
    mark_notification_read,
)


router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("")
async def list_notifications(current_user_id: str = Depends(get_current_user)):
    return {"notifications": get_user_notifications(current_user_id)}


@router.get("/unread-count")
async def unread_notifications_count(current_user_id: str = Depends(get_current_user)):
    return {"unread_count": get_unread_count(current_user_id)}


@router.put("/{notification_id}/read")
async def read_notification(notification_id: str, current_user_id: str = Depends(get_current_user)):
    updated = mark_notification_read(notification_id, current_user_id)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return {"message": "Notification marked as read"}


@router.put("/read-all")
async def read_all_notifications(current_user_id: str = Depends(get_current_user)):
    modified = mark_all_notifications_read(current_user_id)
    return {"updated": modified}


@router.delete("/{notification_id}")
async def remove_notification(notification_id: str, current_user_id: str = Depends(get_current_user)):
    deleted = delete_notification(notification_id, current_user_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return {"message": "Notification deleted"}
