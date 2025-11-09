from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class SignalCreate(BaseModel):
    """Request model for creating a new signal"""
    twitter_username: str = Field(..., description="Twitter username to monitor (without @)")
    ticker: Optional[str] = Field(None, description="Ticker to trade, or None for model to decide")
    check_interval: float = Field(1.0, description="Check interval in seconds", ge=0.5, le=1.5)
    description: Optional[str] = Field(None, description="User description of what this signal does")


class SignalUpdate(BaseModel):
    """Request model for updating a signal"""
    status: Optional[str] = Field(None, description="Signal status: active, paused, stopped")
    check_interval: Optional[float] = Field(None, description="Check interval in seconds", ge=0.5, le=1.5)
    description: Optional[str] = Field(None, description="User description")


class SignalResponse(BaseModel):
    """Response model for signal data"""
    id: str
    user_id: str
    conversation_id: str
    twitter_username: str
    ticker: Optional[str] = None
    status: str  # active, paused, stopped
    last_checked_at: Optional[datetime] = None
    last_tweet_id: Optional[str] = None
    signal_type: str = "twitter_sentiment"
    parameters: Dict[str, Any] = {}
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class SignalEventCreate(BaseModel):
    """Internal model for creating signal events"""
    signal_id: str
    tweet_id: str
    tweet_text: str
    tweet_author: str
    sentiment: str  # bullish, bearish, neutral
    confidence: float = Field(..., ge=0.0, le=1.0)
    ticker_mentioned: Optional[str] = None
    action_taken: List[str] = []  # ["backtest_triggered", "message_sent"]
    backtest_results: Optional[Dict[str, Any]] = None


class SignalEventResponse(BaseModel):
    """Response model for signal event data"""
    id: str
    signal_id: str
    tweet_id: str
    tweet_text: str
    tweet_author: str
    sentiment: str
    confidence: float
    ticker_mentioned: Optional[str] = None
    action_taken: List[str] = []
    backtest_results: Optional[Dict[str, Any]] = None
    timestamp: datetime
