from pymongo import AsyncMongoClient
from app.config import MONGODB_URL, MONGODB_DB_NAME

class DatabaseConnection:
    client: AsyncMongoClient = None
    db = None

db_conn = DatabaseConnection()


async def connect_to_mongo():
    """Connect to MongoDB on application startup"""
    db_conn.client = AsyncMongoClient(MONGODB_URL)
    db_conn.db = db_conn.client[MONGODB_DB_NAME]
    print(f"Connected to MongoDB database: {MONGODB_DB_NAME}")

    # Create indexes for better query performance
    await create_indexes()


async def close_mongo_connection():
    """Close MongoDB connection on application shutdown"""
    if db_conn.client:
        db_conn.client.close()
        print("MongoDB connection closed")


def get_db():
    """Get database instance"""
    return db_conn.db


async def create_indexes():
    """Create database indexes for better query performance"""
    db = db_conn.db

    # Users collection indexes
    await db.users.create_index("email", unique=True)
    await db.users.create_index("username", unique=True)

    # Conversations collection indexes
    await db.conversations.create_index("user_id")
    await db.conversations.create_index([("user_id", 1), ("updated_at", -1)])
    await db.conversations.create_index("strategy_id")

    # Strategies collection indexes
    await db.strategies.create_index("user_id")
    await db.strategies.create_index("conversation_id")
    await db.strategies.create_index([("user_id", 1), ("updated_at", -1)])
    await db.strategies.create_index("status")

    print("Database indexes created successfully")
