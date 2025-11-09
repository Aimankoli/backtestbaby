from bson import ObjectId
from datetime import datetime
from typing import Optional, List
from app.db.mongodb import get_db


async def create_conversation(user_id: str, title: str = "New Conversation", conversation_type: str = "strategy") -> dict:
    """Create a new conversation"""
    db = get_db()
    conversation = {
        "user_id": user_id,
        "strategy_id": None,  # Will be set when strategy is created
        "title": title,
        "messages": [],
        "status": "active",
        "conversation_type": conversation_type,  # "strategy" or "research"
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    result = await db.conversations.insert_one(conversation)
    conversation["_id"] = result.inserted_id
    return conversation


async def get_conversation(conversation_id: str, user_id: str) -> Optional[dict]:
    """Get a conversation by ID"""
    db = get_db()
    return await db.conversations.find_one({
        "_id": ObjectId(conversation_id),
        "user_id": user_id
    })


async def get_user_conversations(user_id: str, skip: int = 0, limit: int = 50) -> List[dict]:
    """Get all conversations for a user"""
    db = get_db()
    cursor = db.conversations.find({"user_id": user_id}).sort("updated_at", -1).skip(skip).limit(limit)
    return await cursor.to_list(length=limit)


async def update_conversation(conversation_id: str, user_id: str, update_data: dict) -> Optional[dict]:
    """Update a conversation"""
    db = get_db()
    update_data["updated_at"] = datetime.utcnow()

    result = await db.conversations.update_one(
        {"_id": ObjectId(conversation_id), "user_id": user_id},
        {"$set": update_data}
    )

    if result.modified_count > 0:
        return await get_conversation(conversation_id, user_id)
    return None


async def add_message_to_conversation(conversation_id: str, user_id: str, role: str, content: str) -> Optional[dict]:
    """Add a message to a conversation"""
    db = get_db()
    message = {
        "role": role,
        "content": content,
        "timestamp": datetime.utcnow()
    }

    result = await db.conversations.update_one(
        {"_id": ObjectId(conversation_id), "user_id": user_id},
        {
            "$push": {"messages": message},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )

    if result.modified_count > 0:
        return await get_conversation(conversation_id, user_id)
    return None


async def link_strategy_to_conversation(conversation_id: str, user_id: str, strategy_id: str) -> bool:
    """Link a strategy to a conversation"""
    db = get_db()
    result = await db.conversations.update_one(
        {"_id": ObjectId(conversation_id), "user_id": user_id},
        {"$set": {"strategy_id": strategy_id, "updated_at": datetime.utcnow()}}
    )
    return result.modified_count > 0


async def delete_conversation(conversation_id: str, user_id: str) -> bool:
    """Delete a conversation"""
    db = get_db()
    result = await db.conversations.delete_one({
        "_id": ObjectId(conversation_id),
        "user_id": user_id
    })
    return result.deleted_count > 0
