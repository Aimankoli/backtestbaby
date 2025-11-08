from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class Signal(BaseModel):
    """Trading signal configuration"""
    type: str  # "moving_average", "webhook", "rsi", etc.
    parameters: Dict[str, Any]  # Signal-specific parameters
    description: Optional[str] = None


class BacktestResult(BaseModel):
    """Results from a backtest run"""
    backtest_id: Optional[str] = None
    total_return: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    win_rate: Optional[float] = None
    total_trades: Optional[int] = None
    plot_path: Optional[str] = None
    metrics: Dict[str, Any] = {}  # Additional metrics
    ran_at: datetime = Field(default_factory=datetime.utcnow)


class StrategyCreate(BaseModel):
    conversation_id: str
    name: Optional[str] = "Untitled Strategy"
    description: Optional[str] = None


class StrategyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    signals: Optional[List[Signal]] = None
    backtest_code: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    status: Optional[str] = None


class StrategyResponse(BaseModel):
    id: str  # strategy_id
    conversation_id: str
    user_id: str
    name: str
    description: Optional[str] = None
    signals: List[Signal] = []
    backtest_code: Optional[str] = None  # Generated Python code
    backtest_results: List[BacktestResult] = []
    parameters: Dict[str, Any] = {}  # Strategy parameters
    status: str = "draft"  # draft, ready, backtested, live
    created_at: datetime
    updated_at: datetime
