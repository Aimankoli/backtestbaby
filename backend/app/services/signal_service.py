from typing import Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId
from app.db.mongodb import get_db


async def create_signal(
    user_id: str,
    conversation_id: str,
    twitter_username: str,
    ticker: Optional[str] = None,
    check_interval: int = 60,
    description: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new signal for monitoring Twitter account

    Args:
        user_id: User who owns this signal
        conversation_id: Conversation to send updates to
        twitter_username: Twitter username to monitor (without @)
        ticker: Ticker to trade (None = model decides)
        check_interval: Seconds between checks
        description: Optional description

    Returns:
        Created signal document
    """
    db = get_db()

    signal_doc = {
        "user_id": user_id,
        "conversation_id": conversation_id,
        "twitter_username": twitter_username.lstrip("@"),  # Remove @ if present
        "ticker": ticker,
        "status": "active",
        "last_checked_at": None,
        "last_tweet_id": None,
        "signal_type": "twitter_sentiment",
        "parameters": {
            "check_interval": check_interval,
        },
        "description": description,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

    result = await db.signals.insert_one(signal_doc)
    signal_doc["_id"] = result.inserted_id

    return signal_doc


async def get_signal(signal_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    """Get signal by ID for a specific user"""
    db = get_db()

    signal = await db.signals.find_one({
        "_id": ObjectId(signal_id),
        "user_id": user_id
    })

    return signal


async def list_user_signals(
    user_id: str,
    status: Optional[str] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    List all signals for a user

    Args:
        user_id: User ID
        status: Filter by status (active, paused, stopped)
        limit: Maximum number of results

    Returns:
        List of signal documents
    """
    db = get_db()

    query = {"user_id": user_id}
    if status:
        query["status"] = status

    cursor = db.signals.find(query).sort("created_at", -1).limit(limit)
    signals = await cursor.to_list(length=limit)

    return signals


async def list_active_signals() -> List[Dict[str, Any]]:
    """
    Get all active signals across all users for background monitoring

    Returns:
        List of active signal documents
    """
    db = get_db()

    cursor = db.signals.find({"status": "active"})
    signals = await cursor.to_list(length=None)

    return signals


async def update_signal(
    signal_id: str,
    user_id: str,
    update_data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Update signal fields

    Args:
        signal_id: Signal ID
        user_id: User ID (for authorization)
        update_data: Fields to update

    Returns:
        Updated signal document or None
    """
    db = get_db()

    # Add updated_at timestamp
    update_data["updated_at"] = datetime.utcnow()

    result = await db.signals.find_one_and_update(
        {"_id": ObjectId(signal_id), "user_id": user_id},
        {"$set": update_data},
        return_document=True
    )

    return result


async def update_signal_check_time(signal_id: str, tweet_id: Optional[str] = None):
    """
    Update last_checked_at timestamp and optionally last_tweet_id
    Called by background monitor after each check
    """
    db = get_db()

    update_doc = {
        "last_checked_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

    if tweet_id:
        update_doc["last_tweet_id"] = tweet_id

    await db.signals.update_one(
        {"_id": ObjectId(signal_id)},
        {"$set": update_doc}
    )


async def pause_signal(signal_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    """Pause a signal"""
    return await update_signal(signal_id, user_id, {"status": "paused"})


async def resume_signal(signal_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    """Resume a paused signal"""
    return await update_signal(signal_id, user_id, {"status": "active"})


async def stop_signal(signal_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    """Stop a signal permanently"""
    return await update_signal(signal_id, user_id, {"status": "stopped"})


async def delete_signal(signal_id: str, user_id: str) -> bool:
    """Delete a signal"""
    db = get_db()

    result = await db.signals.delete_one({
        "_id": ObjectId(signal_id),
        "user_id": user_id
    })

    return result.deleted_count > 0


# ============================================================================
# Signal Event Operations
# ============================================================================

async def create_signal_event(
    signal_id: str,
    tweet_id: str,
    tweet_text: str,
    tweet_author: str,
    sentiment: str,
    confidence: float,
    ticker_mentioned: Optional[str] = None,
    action_taken: List[str] = None,
    backtest_results: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Record a signal event (tweet analysis result)

    Args:
        signal_id: Signal that triggered this event
        tweet_id: Twitter tweet ID
        tweet_text: Tweet content
        tweet_author: Twitter username
        sentiment: bullish, bearish, neutral
        confidence: 0-1 confidence score
        ticker_mentioned: Ticker extracted from tweet
        action_taken: List of actions like ["backtest_triggered", "message_sent"]
        backtest_results: Optional backtest result data

    Returns:
        Created event document
    """
    db = get_db()

    event_doc = {
        "signal_id": signal_id,
        "tweet_id": tweet_id,
        "tweet_text": tweet_text,
        "tweet_author": tweet_author,
        "sentiment": sentiment,
        "confidence": confidence,
        "ticker_mentioned": ticker_mentioned,
        "action_taken": action_taken or [],
        "backtest_results": backtest_results,
        "timestamp": datetime.utcnow()
    }

    result = await db.signal_events.insert_one(event_doc)
    event_doc["_id"] = result.inserted_id

    return event_doc


async def get_signal_events(
    signal_id: str,
    limit: int = 50,
    sentiment_filter: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get events for a signal

    Args:
        signal_id: Signal ID
        limit: Max number of events
        sentiment_filter: Filter by sentiment (bullish, bearish, neutral)

    Returns:
        List of event documents
    """
    db = get_db()

    query = {"signal_id": signal_id}
    if sentiment_filter:
        query["sentiment"] = sentiment_filter

    cursor = db.signal_events.find(query).sort("timestamp", -1).limit(limit)
    events = await cursor.to_list(length=limit)

    return events


async def get_recent_events(user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Get recent signal events for a user across all their signals

    Args:
        user_id: User ID
        limit: Max number of events

    Returns:
        List of event documents with signal info
    """
    db = get_db()

    # First get user's signal IDs
    user_signals = await list_user_signals(user_id, limit=1000)
    signal_ids = [str(s["_id"]) for s in user_signals]

    if not signal_ids:
        return []

    # Get events for those signals
    cursor = db.signal_events.find({
        "signal_id": {"$in": signal_ids}
    }).sort("timestamp", -1).limit(limit)

    events = await cursor.to_list(length=limit)

    return events
