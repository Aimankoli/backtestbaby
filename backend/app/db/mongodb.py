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


async def close_mongo_connection():
    """Close MongoDB connection on application shutdown"""
    if db_conn.client:
        db_conn.client.close()
        print("MongoDB connection closed")


def get_db():
    """Get database instance"""
    return db_conn.db
