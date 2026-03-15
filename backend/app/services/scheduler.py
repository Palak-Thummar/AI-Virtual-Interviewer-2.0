"""Background scheduler for reminder and weekly report notifications."""

from __future__ import annotations

from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from bson import ObjectId

from app.core.database import get_collection
from app.services.career_intelligence_service import get_or_create_user_intelligence
from app.services.notification_service import create_notification


_scheduler: AsyncIOScheduler | None = None


def _format_score(value) -> float:
    try:
        return round(float(value or 0), 2)
    except (TypeError, ValueError):
        return 0.0


def run_interview_reminder_job() -> None:
    interviews = get_collection("interviews")
    users = get_collection("users")

    pending_users = interviews.distinct("user_id", {"status": "pending"})
    for user_id in pending_users:
        pending_count = interviews.count_documents({"user_id": user_id, "status": "pending"})
        user_doc = users.find_one({"_id": user_id}) or {}
        first_name = (user_doc.get("name") or user_doc.get("full_name") or "there").split(" ")[0]
        create_notification(
            user_id=str(user_id),
            notification_type="INTERVIEW_REMINDER",
            title="Interview Reminder",
            message=(
                f"Hi {first_name}, you have {pending_count} pending interview session"
                f"{'s' if pending_count != 1 else ''}. Continue now to stay consistent."
            ),
            metadata={"pending_count": pending_count},
        )


def run_weekly_report_job() -> None:
    users = get_collection("users")
    interviews = get_collection("interviews")

    for user in users.find({}, {"_id": 1}):
        user_id: ObjectId = user["_id"]
        completed_count = interviews.count_documents({"user_id": user_id, "status": "completed"})
        avg_score = 0.0
        weakest_skill = "-"

        intelligence = get_or_create_user_intelligence(str(user_id))
        avg_score = _format_score(intelligence.get("average_score", 0))
        weakest_skill = intelligence.get("weakest_skill", "-") or "-"

        message = (
            "Weekly Performance Report\n"
            f"Interviews completed: {completed_count}\n"
            f"Average score: {avg_score}\n"
            f"Weakest skill: {weakest_skill}"
        )

        create_notification(
            user_id=str(user_id),
            notification_type="WEEKLY_REPORT",
            title="Weekly Performance Report",
            message=message,
            metadata={
                "completed_interviews": completed_count,
                "average_score": avg_score,
                "weakest_skill": weakest_skill,
                "generated_at": datetime.utcnow().isoformat(),
            },
        )


def start_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        return

    _scheduler = AsyncIOScheduler(timezone="UTC")
    _scheduler.add_job(run_interview_reminder_job, "cron", hour=9, minute=0, id="interview-reminders", replace_existing=True)
    _scheduler.add_job(run_weekly_report_job, "cron", day_of_week="sun", hour=10, minute=0, id="weekly-reports", replace_existing=True)
    _scheduler.start()


def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
    _scheduler = None
