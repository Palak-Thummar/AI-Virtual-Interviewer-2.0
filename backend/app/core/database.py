"""
MongoDB database connection and session management.
"""

from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from contextlib import asynccontextmanager
from app.core.config import settings

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
        print("[DB] Connected to MongoDB")
    except ServerSelectionTimeoutError as e:
        print(f"[DB ERROR] Failed to connect to MongoDB: {e}")
        raise


async def close_mongo_connection():
    """Close MongoDB connection."""
    global client
    if client:
        client.close()
        print("📴 Disconnected from MongoDB")


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
