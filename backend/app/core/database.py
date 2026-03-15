"""
MongoDB database connection and session management.
"""

import logging
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ServerSelectionTimeoutError
from app.core.config import settings

logger = logging.getLogger(__name__)

client: MongoClient = None
db = None


async def connect_to_mongo():
    """Connect to MongoDB."""
    global client, db
    try:
        client = MongoClient(
            settings.MONGODB_URL,
            serverSelectionTimeoutMS=5000
        )
        db = client[settings.MONGODB_DB]
        # Verify connection
        client.admin.command('ping')
        logger.info("Connected to MongoDB: %s / %s", settings.MONGODB_URL, settings.MONGODB_DB)
    except ServerSelectionTimeoutError as e:
        logger.error("Failed to connect to MongoDB: %s", e)
        raise


async def close_mongo_connection():
    """Close MongoDB connection."""
    global client
    if client:
        client.close()
        logger.info("Disconnected from MongoDB")


def get_db():
    """Get database instance."""
    return db


def get_collection(collection_name: str):
    """
    Get a collection from the database.

    Args:
        collection_name: Name of the collection

    Returns:
        MongoDB collection
    """
    return db[collection_name]


def create_indexes() -> None:
    """
    Create all required MongoDB indexes for performance and uniqueness.
    Safe to call multiple times — MongoDB is idempotent for existing indexes.
    """
    try:
        # users — unique email
        users = db["users"]
        users.create_index([("email", ASCENDING)], unique=True, background=True)
        users.create_index([("created_at", DESCENDING)], background=True)

        # interviews
        interviews = db["interviews"]
        interviews.create_index([("user_id", ASCENDING)], background=True)
        interviews.create_index([("user_id", ASCENDING), ("status", ASCENDING)], background=True)
        interviews.create_index([("created_at", DESCENDING)], background=True)
        interviews.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)], background=True)

        # career_intelligence — one doc per user
        ci = db["career_intelligence"]
        ci.create_index([("user_id", ASCENDING)], unique=True, background=True)
        ci.create_index([("updated_at", DESCENDING)], background=True)

        # notifications
        notifications = db["notifications"]
        notifications.create_index([("user_id", ASCENDING)], background=True)
        notifications.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)], background=True)
        notifications.create_index([("is_read", ASCENDING)], background=True)

        # resumes
        resumes = db["resumes"]
        resumes.create_index([("user_id", ASCENDING)], background=True)
        resumes.create_index([("uploaded_at", DESCENDING)], background=True)

        logger.info("MongoDB indexes created / verified")
    except Exception as exc:
        logger.warning("Index creation warning (non-fatal): %s", exc)
