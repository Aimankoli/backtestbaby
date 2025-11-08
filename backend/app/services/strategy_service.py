from bson import ObjectId
from datetime import datetime
from typing import Optional, List, Dict, Any
from app.db.mongodb import get_db


async def create_strategy(user_id: str, conversation_id: str, name: str = "Untitled Strategy", description: Optional[str] = None) -> dict:
    """Create a new strategy"""
    db = get_db()
    strategy = {
        "conversation_id": conversation_id,
        "user_id": user_id,
        "name": name,
        "description": description,
        "signals": [],
        "backtest_code": None,
        "backtest_results": [],
        "parameters": {},
        "status": "draft",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    result = await db.strategies.insert_one(strategy)
    strategy["_id"] = result.inserted_id
    return strategy


async def get_strategy(strategy_id: str, user_id: str) -> Optional[dict]:
    """Get a strategy by ID"""
    db = get_db()
    return await db.strategies.find_one({
        "_id": ObjectId(strategy_id),
        "user_id": user_id
    })


async def get_strategy_by_conversation(conversation_id: str, user_id: str) -> Optional[dict]:
    """Get strategy associated with a conversation"""
    db = get_db()
    return await db.strategies.find_one({
        "conversation_id": conversation_id,
        "user_id": user_id
    })


async def get_user_strategies(user_id: str, skip: int = 0, limit: int = 50) -> List[dict]:
    """Get all strategies for a user"""
    db = get_db()
    cursor = db.strategies.find({"user_id": user_id}).sort("updated_at", -1).skip(skip).limit(limit)
    return await cursor.to_list(length=limit)


async def update_strategy(strategy_id: str, user_id: str, update_data: dict) -> Optional[dict]:
    """Update a strategy"""
    db = get_db()
    update_data["updated_at"] = datetime.utcnow()

    result = await db.strategies.update_one(
        {"_id": ObjectId(strategy_id), "user_id": user_id},
        {"$set": update_data}
    )

    if result.modified_count > 0:
        return await get_strategy(strategy_id, user_id)
    return None


async def add_signal_to_strategy(strategy_id: str, user_id: str, signal: Dict[str, Any]) -> Optional[dict]:
    """Add a signal to a strategy"""
    db = get_db()
    result = await db.strategies.update_one(
        {"_id": ObjectId(strategy_id), "user_id": user_id},
        {
            "$push": {"signals": signal},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )

    if result.modified_count > 0:
        return await get_strategy(strategy_id, user_id)
    return None


async def add_backtest_result(strategy_id: str, user_id: str, backtest_result: Dict[str, Any]) -> Optional[dict]:
    """Add a backtest result to a strategy"""
    db = get_db()
    backtest_result["ran_at"] = datetime.utcnow()

    result = await db.strategies.update_one(
        {"_id": ObjectId(strategy_id), "user_id": user_id},
        {
            "$push": {"backtest_results": backtest_result},
            "$set": {"updated_at": datetime.utcnow(), "status": "backtested"}
        }
    )

    if result.modified_count > 0:
        return await get_strategy(strategy_id, user_id)
    return None


async def update_strategy_code(strategy_id: str, user_id: str, code: str) -> Optional[dict]:
    """Update the backtest code for a strategy"""
    db = get_db()
    result = await db.strategies.update_one(
        {"_id": ObjectId(strategy_id), "user_id": user_id},
        {"$set": {"backtest_code": code, "updated_at": datetime.utcnow()}}
    )

    if result.modified_count > 0:
        return await get_strategy(strategy_id, user_id)
    return None


async def delete_strategy(strategy_id: str, user_id: str) -> bool:
    """Delete a strategy"""
    db = get_db()
    result = await db.strategies.delete_one({
        "_id": ObjectId(strategy_id),
        "user_id": user_id
    })
    return result.deleted_count > 0
