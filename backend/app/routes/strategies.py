from fastapi import APIRouter, Depends, HTTPException, status
from app.models.strategy import StrategyCreate, StrategyResponse, StrategyUpdate, Signal, BacktestResult
from app.models.user import UserResponse
from app.dependencies.auth import get_current_user
from app.services import strategy_service
from typing import List

router = APIRouter(prefix="/strategies", tags=["Strategies"])


def convert_strategy_to_response(strategy: dict) -> StrategyResponse:
    """Convert MongoDB strategy document to StrategyResponse model"""
    return StrategyResponse(
        id=str(strategy["_id"]),
        conversation_id=strategy["conversation_id"],
        user_id=strategy["user_id"],
        name=strategy["name"],
        description=strategy.get("description"),
        signals=[Signal(**signal) for signal in strategy.get("signals", [])],
        backtest_code=strategy.get("backtest_code"),
        backtest_results=[BacktestResult(**result) for result in strategy.get("backtest_results", [])],
        parameters=strategy.get("parameters", {}),
        status=strategy["status"],
        created_at=strategy["created_at"],
        updated_at=strategy["updated_at"]
    )


@router.post("/", response_model=StrategyResponse, status_code=status.HTTP_201_CREATED)
async def create_strategy(
    strategy: StrategyCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """Create a new strategy (linked to a conversation)"""
    created = await strategy_service.create_strategy(
        user_id=current_user.id,
        conversation_id=strategy.conversation_id,
        name=strategy.name or "Untitled Strategy",
        description=strategy.description
    )
    return convert_strategy_to_response(created)


@router.get("/", response_model=List[StrategyResponse])
async def get_strategies(
    skip: int = 0,
    limit: int = 50,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get all strategies for the current user"""
    strategies = await strategy_service.get_user_strategies(
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )
    return [convert_strategy_to_response(s) for s in strategies]


@router.get("/{strategy_id}", response_model=StrategyResponse)
async def get_strategy(
    strategy_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get a specific strategy by ID"""
    strategy = await strategy_service.get_strategy(strategy_id, current_user.id)
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found"
        )
    return convert_strategy_to_response(strategy)


@router.get("/conversation/{conversation_id}", response_model=StrategyResponse)
async def get_strategy_by_conversation(
    conversation_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get the strategy associated with a conversation"""
    strategy = await strategy_service.get_strategy_by_conversation(conversation_id, current_user.id)
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found for this conversation"
        )
    return convert_strategy_to_response(strategy)


@router.patch("/{strategy_id}", response_model=StrategyResponse)
async def update_strategy_endpoint(
    strategy_id: str,
    strategy_update: StrategyUpdate,
    current_user: UserResponse = Depends(get_current_user)
):
    """Update a strategy"""
    update_data = strategy_update.dict(exclude_unset=True)
    updated = await strategy_service.update_strategy(
        strategy_id=strategy_id,
        user_id=current_user.id,
        update_data=update_data
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found"
        )
    return convert_strategy_to_response(updated)


@router.post("/{strategy_id}/signals", response_model=StrategyResponse)
async def add_signal(
    strategy_id: str,
    signal: Signal,
    current_user: UserResponse = Depends(get_current_user)
):
    """Add a signal to a strategy"""
    updated = await strategy_service.add_signal_to_strategy(
        strategy_id=strategy_id,
        user_id=current_user.id,
        signal=signal.dict()
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found"
        )
    return convert_strategy_to_response(updated)


@router.get("/{strategy_id}/code")
async def get_strategy_code(
    strategy_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get the generated Python backtest code for a strategy"""
    strategy = await strategy_service.get_strategy(strategy_id, current_user.id)
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found"
        )
    
    code = strategy.get("backtest_code")
    if not code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No backtest code generated for this strategy yet"
        )
    
    return {"strategy_id": strategy_id, "code": code}


@router.delete("/{strategy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_strategy_endpoint(
    strategy_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Delete a strategy"""
    deleted = await strategy_service.delete_strategy(strategy_id, current_user.id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found"
        )
    return None
