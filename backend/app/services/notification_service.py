"""Notification service for in-app and optional email delivery."""

from __future__ import annotations

from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from typing import Dict, List, Optional

from bson import ObjectId
from bson.errors import InvalidId

from app.core.config import settings
from app.core.database import get_collection


NOTIFICATION_TYPES = {
    "INTERVIEW_REMINDER",
    "INTERVIEW_COMPLETED",
    "WEEKLY_REPORT",
    "SKILL_SUGGESTION",
    "RESUME_ANALYSIS",
    "SYSTEM",
}


def _to_object_id(value: str | ObjectId) -> ObjectId:
    return value if isinstance(value, ObjectId) else ObjectId(value)


def _to_iso_utc(value) -> str | None:
    if not value:
        return None
    if hasattr(value, "isoformat"):
        return f"{value.isoformat()}Z"
    return str(value)


def _serialize_notification(document: Dict) -> Dict:
    return {
        "id": str(document.get("_id")),
        "user_id": str(document.get("user_id")) if document.get("user_id") else "",
        "type": document.get("type", "SYSTEM"),
        "title": document.get("title", ""),
        "message": document.get("message", ""),
        "metadata": document.get("metadata") or {},
        "read": bool(document.get("read", False)),
        "created_at": _to_iso_utc(document.get("created_at")),
    }


def ensure_notifications_indexes() -> None:
    collection = get_collection("notifications")
    collection.create_index([("user_id", 1)])
    collection.create_index([("created_at", -1)])


def _get_preferences(user_id: str | ObjectId) -> Dict:
    collection = get_collection("user_notifications")
    existing = collection.find_one({"user_id": _to_object_id(user_id)})
    if existing:
        return {
            "email_notifications": bool(existing.get("email_notifications", True)),
            "interview_reminders": bool(existing.get("interview_reminders", True)),
            "weekly_summary": bool(existing.get("weekly_summary", True)),
            "skill_suggestions": bool(existing.get("skill_suggestions", True)),
        }
    return {
        "email_notifications": True,
        "interview_reminders": True,
        "weekly_summary": True,
        "skill_suggestions": True,
    }


def _is_enabled_for_type(notification_type: str, prefs: Dict) -> bool:
    if notification_type == "INTERVIEW_REMINDER":
        return bool(prefs.get("interview_reminders", True))
    if notification_type == "WEEKLY_REPORT":
        return bool(prefs.get("weekly_summary", True))
    if notification_type == "SKILL_SUGGESTION":
        return bool(prefs.get("skill_suggestions", True))
    return True


def _send_email(user_id: str | ObjectId, subject: str, message: str) -> None:
    if not settings.SMTP_HOST or not settings.SMTP_PORT or not settings.SMTP_FROM_EMAIL:
        return

    users_collection = get_collection("users")
    user = users_collection.find_one({"_id": _to_object_id(user_id)})
    if not user or not user.get("email"):
        return

    mime = MIMEText(message, "plain", "utf-8")
    mime["Subject"] = subject
    mime["From"] = settings.SMTP_FROM_EMAIL
    mime["To"] = user["email"]

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
        if settings.SMTP_USE_TLS:
            server.starttls()
        if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        server.send_message(mime)


def _should_send_email(notification_type: str) -> bool:
    return notification_type in {"WEEKLY_REPORT", "INTERVIEW_REMINDER", "RESUME_ANALYSIS"}


def _is_duplicate(notification_type: str, user_id: str | ObjectId, title: str, metadata: Dict) -> bool:
    collection = get_collection("notifications")
    now = datetime.utcnow()

    if notification_type == "INTERVIEW_REMINDER":
        window_start = now - timedelta(hours=20)
        duplicate = collection.find_one(
            {
                "user_id": _to_object_id(user_id),
                "type": notification_type,
                "created_at": {"$gte": window_start},
            }
        )
        return duplicate is not None

    if notification_type == "WEEKLY_REPORT":
        week_start = now - timedelta(days=6)
        duplicate = collection.find_one(
            {
                "user_id": _to_object_id(user_id),
                "type": notification_type,
                "created_at": {"$gte": week_start},
            }
        )
        return duplicate is not None

    if notification_type == "SKILL_SUGGESTION":
        weakest = (metadata or {}).get("weakest_skill")
        if not weakest:
            return False
        duplicate = collection.find_one(
            {
                "user_id": _to_object_id(user_id),
                "type": notification_type,
                "metadata.weakest_skill": weakest,
                "created_at": {"$gte": now - timedelta(days=2)},
            }
        )
        return duplicate is not None

    if notification_type == "RESUME_ANALYSIS":
        resume_id = (metadata or {}).get("resume_id")
        if not resume_id:
            return False
        duplicate = collection.find_one(
            {
                "user_id": _to_object_id(user_id),
                "type": notification_type,
                "metadata.resume_id": resume_id,
            }
        )
        return duplicate is not None

    if notification_type == "INTERVIEW_COMPLETED":
        interview_id = (metadata or {}).get("interview_id")
        if not interview_id:
            return False
        duplicate = collection.find_one(
            {
                "user_id": _to_object_id(user_id),
                "type": notification_type,
                "metadata.interview_id": interview_id,
            }
        )
        return duplicate is not None

    return False


def create_notification(
    user_id: str | ObjectId,
    notification_type: str,
    title: str,
    message: str,
    metadata: Optional[Dict] = None,
) -> Optional[Dict]:
    ensure_notifications_indexes()

    if notification_type not in NOTIFICATION_TYPES:
        raise ValueError(f"Unsupported notification type: {notification_type}")

    prefs = _get_preferences(user_id)
    if not _is_enabled_for_type(notification_type, prefs):
        return None

    metadata = metadata or {}
    if _is_duplicate(notification_type, user_id, title, metadata):
        return None

    document = {
        "user_id": _to_object_id(user_id),
        "type": notification_type,
        "title": title,
        "message": message,
        "metadata": metadata,
        "read": False,
        "created_at": datetime.utcnow(),
    }

    collection = get_collection("notifications")
    inserted = collection.insert_one(document)
    document["_id"] = inserted.inserted_id

    if prefs.get("email_notifications", True) and _should_send_email(notification_type):
        try:
            _send_email(user_id, title, message)
        except Exception:
            # Notification creation should not fail due to email provider issues.
            pass

    return _serialize_notification(document)


def get_user_notifications(user_id: str | ObjectId) -> List[Dict]:
    ensure_notifications_indexes()
    collection = get_collection("notifications")
    documents = list(
        collection.find({"user_id": _to_object_id(user_id)}).sort([
            ("read", 1),
            ("created_at", -1),
        ])
    )
    return [_serialize_notification(item) for item in documents]


def mark_notification_read(notification_id: str, user_id: str | ObjectId) -> bool:
    collection = get_collection("notifications")
    try:
        object_id = ObjectId(notification_id)
    except (InvalidId, TypeError):
        return False
    result = collection.update_one(
        {"_id": object_id, "user_id": _to_object_id(user_id)},
        {"$set": {"read": True}}
    )
    return result.modified_count > 0


def mark_all_notifications_read(user_id: str | ObjectId) -> int:
    collection = get_collection("notifications")
    result = collection.update_many(
        {"user_id": _to_object_id(user_id), "read": False},
        {"$set": {"read": True}}
    )
    return int(result.modified_count)


def get_unread_count(user_id: str | ObjectId) -> int:
    collection = get_collection("notifications")
    return int(collection.count_documents({"user_id": _to_object_id(user_id), "read": False}))


def delete_notification(notification_id: str, user_id: str | ObjectId) -> bool:
    collection = get_collection("notifications")
    try:
        object_id = ObjectId(notification_id)
    except (InvalidId, TypeError):
        return False
    result = collection.delete_one({"_id": object_id, "user_id": _to_object_id(user_id)})
    return result.deleted_count > 0
