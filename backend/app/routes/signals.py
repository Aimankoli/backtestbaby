from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from app.models.signal import (
    SignalCreate,
    SignalUpdate,
    SignalResponse,
    SignalEventResponse
)
from app.models.user import UserResponse
from app.dependencies.auth import get_current_user
from app.services.signal_service import (
    create_signal,
    get_signal,
    list_user_signals,
    update_signal,
    pause_signal,
    resume_signal,
    stop_signal,
    delete_signal,
    get_signal_events,
    get_recent_events
)


router = APIRouter(prefix="/signals", tags=["signals"])


@router.post("/", response_model=SignalResponse, status_code=status.HTTP_201_CREATED)
async def create_new_signal(
    signal_data: SignalCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Create a new Twitter signal

    Creates a signal to monitor a Twitter account and trigger trading actions
    based on tweet sentiment analysis.

    The signal will be active immediately and checked every `check_interval` seconds.
    """
    # For now, we'll use a default conversation
    # TODO: Allow user to specify conversation_id or create a default "signals" conversation
    from app.services.conversation_service import create_conversation

    # Create a conversation for this signal if needed
    # Or user can specify conversation_id in request
    conversation = await create_conversation(
        user_id=current_user.id,
        title=f"Signal: @{signal_data.twitter_username}"
    )

    signal = await create_signal(
        user_id=current_user.id,
        conversation_id=str(conversation["_id"]),
        twitter_username=signal_data.twitter_username,
        ticker=signal_data.ticker,
        check_interval=signal_data.check_interval,
        description=signal_data.description
    )

    return SignalResponse(
        id=str(signal["_id"]),
        user_id=signal["user_id"],
        conversation_id=signal["conversation_id"],
        twitter_username=signal["twitter_username"],
        ticker=signal.get("ticker"),
        status=signal["status"],
        last_checked_at=signal.get("last_checked_at"),
        last_tweet_id=signal.get("last_tweet_id"),
        signal_type=signal["signal_type"],
        parameters=signal.get("parameters", {}),
        description=signal.get("description"),
        created_at=signal["created_at"],
        updated_at=signal["updated_at"]
    )


@router.get("/", response_model=List[SignalResponse])
async def list_signals(
    status_filter: Optional[str] = None,
    limit: int = 50,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    List all signals for the current user

    Parameters:
    - status: Filter by status (active, paused, stopped)
    - limit: Maximum number of results (default: 50)
    """
    signals = await list_user_signals(
        user_id=current_user.id,
        status=status_filter,
        limit=limit
    )

    return [
        SignalResponse(
            id=str(s["_id"]),
            user_id=s["user_id"],
            conversation_id=s["conversation_id"],
            twitter_username=s["twitter_username"],
            ticker=s.get("ticker"),
            status=s["status"],
            last_checked_at=s.get("last_checked_at"),
            last_tweet_id=s.get("last_tweet_id"),
            signal_type=s["signal_type"],
            parameters=s.get("parameters", {}),
            description=s.get("description"),
            created_at=s["created_at"],
            updated_at=s["updated_at"]
        )
        for s in signals
    ]


@router.get("/{signal_id}", response_model=SignalResponse)
async def get_signal_details(
    signal_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get details of a specific signal"""
    signal = await get_signal(signal_id, current_user.id)

    if not signal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Signal not found"
        )

    return SignalResponse(
        id=str(signal["_id"]),
        user_id=signal["user_id"],
        conversation_id=signal["conversation_id"],
        twitter_username=signal["twitter_username"],
        ticker=signal.get("ticker"),
        status=signal["status"],
        last_checked_at=signal.get("last_checked_at"),
        last_tweet_id=signal.get("last_tweet_id"),
        signal_type=signal["signal_type"],
        parameters=signal.get("parameters", {}),
        description=signal.get("description"),
        created_at=signal["created_at"],
        updated_at=signal["updated_at"]
    )


@router.patch("/{signal_id}", response_model=SignalResponse)
async def update_signal_details(
    signal_id: str,
    signal_update: SignalUpdate,
    current_user: UserResponse = Depends(get_current_user)
):
    """Update signal configuration"""
    update_data = signal_update.model_dump(exclude_unset=True)

    signal = await update_signal(signal_id, current_user.id, update_data)

    if not signal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Signal not found"
        )

    return SignalResponse(
        id=str(signal["_id"]),
        user_id=signal["user_id"],
        conversation_id=signal["conversation_id"],
        twitter_username=signal["twitter_username"],
        ticker=signal.get("ticker"),
        status=signal["status"],
        last_checked_at=signal.get("last_checked_at"),
        last_tweet_id=signal.get("last_tweet_id"),
        signal_type=signal["signal_type"],
        parameters=signal.get("parameters", {}),
        description=signal.get("description"),
        created_at=signal["created_at"],
        updated_at=signal["updated_at"]
    )


@router.post("/{signal_id}/pause", response_model=SignalResponse)
async def pause_signal_endpoint(
    signal_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Pause an active signal"""
    signal = await pause_signal(signal_id, current_user.id)

    if not signal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Signal not found"
        )

    return SignalResponse(
        id=str(signal["_id"]),
        user_id=signal["user_id"],
        conversation_id=signal["conversation_id"],
        twitter_username=signal["twitter_username"],
        ticker=signal.get("ticker"),
        status=signal["status"],
        last_checked_at=signal.get("last_checked_at"),
        last_tweet_id=signal.get("last_tweet_id"),
        signal_type=signal["signal_type"],
        parameters=signal.get("parameters", {}),
        description=signal.get("description"),
        created_at=signal["created_at"],
        updated_at=signal["updated_at"]
    )


@router.post("/{signal_id}/resume", response_model=SignalResponse)
async def resume_signal_endpoint(
    signal_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Resume a paused signal"""
    signal = await resume_signal(signal_id, current_user.id)

    if not signal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Signal not found"
        )

    return SignalResponse(
        id=str(signal["_id"]),
        user_id=signal["user_id"],
        conversation_id=signal["conversation_id"],
        twitter_username=signal["twitter_username"],
        ticker=signal.get("ticker"),
        status=signal["status"],
        last_checked_at=signal.get("last_checked_at"),
        last_tweet_id=signal.get("last_tweet_id"),
        signal_type=signal["signal_type"],
        parameters=signal.get("parameters", {}),
        description=signal.get("description"),
        created_at=signal["created_at"],
        updated_at=signal["updated_at"]
    )


@router.post("/{signal_id}/stop", response_model=SignalResponse)
async def stop_signal_endpoint(
    signal_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Stop a signal permanently"""
    signal = await stop_signal(signal_id, current_user.id)

    if not signal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Signal not found"
        )

    return SignalResponse(
        id=str(signal["_id"]),
        user_id=signal["user_id"],
        conversation_id=signal["conversation_id"],
        twitter_username=signal["twitter_username"],
        ticker=signal.get("ticker"),
        status=signal["status"],
        last_checked_at=signal.get("last_checked_at"),
        last_tweet_id=signal.get("last_tweet_id"),
        signal_type=signal["signal_type"],
        parameters=signal.get("parameters", {}),
        description=signal.get("description"),
        created_at=signal["created_at"],
        updated_at=signal["updated_at"]
    )


@router.delete("/{signal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_signal_endpoint(
    signal_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Delete a signal"""
    deleted = await delete_signal(signal_id, current_user.id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Signal not found"
        )

    return None


@router.get("/{signal_id}/events", response_model=List[SignalEventResponse])
async def get_signal_events_endpoint(
    signal_id: str,
    sentiment: Optional[str] = None,
    limit: int = 50,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get signal events (detected signals) for a specific signal

    Parameters:
    - sentiment: Filter by sentiment (bullish, bearish, neutral)
    - limit: Maximum number of events (default: 50)
    """
    # Verify user owns this signal
    signal = await get_signal(signal_id, current_user.id)
    if not signal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Signal not found"
        )

    events = await get_signal_events(
        signal_id=signal_id,
        limit=limit,
        sentiment_filter=sentiment
    )

    return [
        SignalEventResponse(
            id=str(e["_id"]),
            signal_id=e["signal_id"],
            tweet_id=e["tweet_id"],
            tweet_text=e["tweet_text"],
            tweet_author=e["tweet_author"],
            sentiment=e["sentiment"],
            confidence=e["confidence"],
            ticker_mentioned=e.get("ticker_mentioned"),
            action_taken=e.get("action_taken", []),
            backtest_results=e.get("backtest_results"),
            timestamp=e["timestamp"]
        )
        for e in events
    ]


@router.get("/events/recent", response_model=List[SignalEventResponse])
async def get_recent_signal_events(
    limit: int = 20,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get recent signal events across all user's signals"""
    events = await get_recent_events(user_id=current_user.id, limit=limit)

    return [
        SignalEventResponse(
            id=str(e["_id"]),
            signal_id=e["signal_id"],
            tweet_id=e["tweet_id"],
            tweet_text=e["tweet_text"],
            tweet_author=e["tweet_author"],
            sentiment=e["sentiment"],
            confidence=e["confidence"],
            ticker_mentioned=e.get("ticker_mentioned"),
            action_taken=e.get("action_taken", []),
            backtest_results=e.get("backtest_results"),
            timestamp=e["timestamp"]
        )
        for e in events
    ]
