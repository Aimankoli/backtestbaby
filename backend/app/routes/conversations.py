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
from app.services.chat_service import process_chat_message
from typing import List
from bson import ObjectId

router = APIRouter(prefix="/conversations", tags=["Conversations"])


@router.post("/", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_new_conversation(
    conversation: ConversationCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """Create a new conversation"""
    conv = await create_conversation(
        user_id=current_user.id,
        title=conversation.title or "New Conversation",
        conversation_type=conversation.conversation_type or "strategy"
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
        conversation_type=conv.get("conversation_type", "strategy"),
        created_at=conv["created_at"],
        updated_at=conv["updated_at"]
    )


@router.get("/", response_model=List[ConversationResponse])
async def list_conversations(
    skip: int = 0,
    limit: int = 50,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get all conversations for the current user"""
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
            conversation_type=conv.get("conversation_type", "strategy"),
            created_at=conv["created_at"],
            updated_at=conv["updated_at"]
        )
        for conv in conversations
    ]


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get a specific conversation by ID"""
    conv = await get_conversation_service(conversation_id, current_user.id)

    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
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
        conversation_type=conv.get("conversation_type", "strategy"),
        created_at=conv["created_at"],
        updated_at=conv["updated_at"]
    )


@router.post("/{conversation_id}/chat")
async def chat(
    conversation_id: str,
    request: ChatRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Send a chat message and get streaming response

    Returns a stream of JSON objects:
    - {"type": "content", "data": "text chunk"}
    - {"type": "strategy_created", "data": {"strategy_id": "...", "name": "..."}}
    - {"type": "done"}
    - {"type": "error", "data": "error message"}
    """
    # Verify conversation exists and belongs to user
    conv = await get_conversation_service(conversation_id, current_user.id)
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    # Stream the chat response
    return StreamingResponse(
        process_chat_message(
            conversation_id=conversation_id,
            user_id=current_user.id,
            user_message=request.message
        ),
        media_type="application/x-ndjson"
    )


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Delete a conversation"""
    deleted = await delete_conversation_service(conversation_id, current_user.id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    return None
