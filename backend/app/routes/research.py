"""
Research Chatbot Endpoint
=========================
This endpoint provides a research chatbot with Brave Search capabilities and Twitter signal monitoring.

Features:
- Web search using Brave Search MCP
- Financial research and analysis
- Twitter sentiment signal creation
- Conversation history management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from app.models.conversation import (
    ConversationCreate,
    ConversationResponse,
    MessageCreate,
    ChatRequest,
    Message
)
from app.models.user import UserResponse
from app.dependencies.auth import get_current_user
from app.services.conversation_service import (
    create_conversation,
    get_conversation as get_conversation_service,
    get_user_conversations,
    delete_conversation as delete_conversation_service
)
from app.services.research_chat_service import process_research_message
from typing import List
from bson import ObjectId

router = APIRouter(prefix="/research", tags=["Research"])


@router.post("/", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_new_research_conversation(
    conversation: ConversationCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """Create a new research conversation"""
    conv = await create_conversation(
        user_id=current_user.id,
        title=conversation.title or "New Research Chat"
    )

    return ConversationResponse(
        id=str(conv["_id"]),
        user_id=conv["user_id"],
        strategy_id=conv.get("strategy_id"),
        title=conv["title"],
        messages=[
            Message(
                role=msg["role"],
                content=msg["content"],
                timestamp=msg["timestamp"]
            ) for msg in conv.get("messages", [])
        ],
        status=conv["status"],
        created_at=conv["created_at"],
        updated_at=conv["updated_at"]
    )


@router.get("/", response_model=List[ConversationResponse])
async def list_research_conversations(
    skip: int = 0,
    limit: int = 50,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get all research conversations for the current user"""
    conversations = await get_user_conversations(
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )

    return [
        ConversationResponse(
            id=str(conv["_id"]),
            user_id=conv["user_id"],
            strategy_id=conv.get("strategy_id"),
            title=conv["title"],
            messages=[
                Message(
                    role=msg["role"],
                    content=msg["content"],
                    timestamp=msg["timestamp"]
                ) for msg in conv.get("messages", [])
            ],
            status=conv["status"],
            created_at=conv["created_at"],
            updated_at=conv["updated_at"]
        )
        for conv in conversations
    ]


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_research_conversation(
    conversation_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get a specific research conversation by ID"""
    conv = await get_conversation_service(conversation_id, current_user.id)

    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research conversation not found"
        )

    return ConversationResponse(
        id=str(conv["_id"]),
        user_id=conv["user_id"],
        strategy_id=conv.get("strategy_id"),
        title=conv["title"],
        messages=[
            Message(
                role=msg["role"],
                content=msg["content"],
                timestamp=msg["timestamp"]
            ) for msg in conv.get("messages", [])
        ],
        status=conv["status"],
        created_at=conv["created_at"],
        updated_at=conv["updated_at"]
    )


@router.post("/{conversation_id}/chat")
async def research_chat(
    conversation_id: str,
    request: ChatRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Send a research chat message and get streaming response

    Returns a stream of JSON objects:
    - {"type": "content", "data": "text chunk"}
    - {"type": "signal_created", "data": {"signal_id": "...", "twitter_username": "..."}}
    - {"type": "done"}
    - {"type": "error", "data": "error message"}
    """
    # Verify conversation exists and belongs to user
    conv = await get_conversation_service(conversation_id, current_user.id)
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research conversation not found"
        )

    # Stream the research chat response
    return StreamingResponse(
        process_research_message(
            conversation_id=conversation_id,
            user_id=current_user.id,
            user_message=request.message
        ),
        media_type="application/x-ndjson"
    )


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_research_conversation(
    conversation_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Delete a research conversation"""
    deleted = await delete_conversation_service(conversation_id, current_user.id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research conversation not found"
        )

    return None