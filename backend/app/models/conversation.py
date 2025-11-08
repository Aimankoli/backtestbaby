from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ConversationCreate(BaseModel):
    title: Optional[str] = "New Conversation"


class ConversationUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None


class ConversationResponse(BaseModel):
    id: str  # conversation_id
    user_id: str
    strategy_id: Optional[str] = None  # Will be set when strategy is created
    title: str
    messages: List[Message] = []
    status: str = "active"  # active, completed, archived
    created_at: datetime
    updated_at: datetime


class MessageCreate(BaseModel):
    content: str  # User message content only (role is always "user")


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    conversation_id: str
    strategy_id: Optional[str] = None
    message: Message  # The assistant's response
    strategy_created: bool = False
