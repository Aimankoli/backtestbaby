from dedalus_labs import AsyncDedalus, DedalusRunner
from typing import Optional, List, Dict, Any, AsyncIterator
import os

class DedalusService:
    """Singleton service for Dedalus client"""
    _instance: Optional['DedalusService'] = None
    _client: Optional[AsyncDedalus] = None
    _runner: Optional[DedalusRunner] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._client is None:
            self._client = AsyncDedalus()
            self._runner = DedalusRunner(self._client)
            print("Dedalus client initialized")

    async def chat_with_history(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        model: str = "openai/gpt-4.1",
        mcp_servers: Optional[List[str]] = None,
        tools: Optional[List[Any]] = None,
        stream: bool = True
    ):
        """
        Send a chat message with conversation history

        Args:
            user_message: The new user message
            conversation_history: List of previous messages [{"role": "user/assistant", "content": "..."}]
            model: Model to use (default: openai/gpt-5)
            mcp_servers: List of MCP servers to use
            tools: Custom Python tools
            stream: Whether to stream the response
        """
        # Build full conversation with new message
        full_conversation = conversation_history + [{"role": "user", "content": user_message}]

        # Convert to Dedalus format
        input_text = self._format_conversation_for_dedalus(full_conversation)

        result = await self._runner.run(
            input=input_text,
            model=model,
            mcp_servers=mcp_servers or [],
            tools=tools or [],
            stream=stream
        )

        return result

    def _format_conversation_for_dedalus(self, messages: List[Dict[str, str]]) -> str:
        """
        Format conversation history for Dedalus input
        Dedalus accepts string input, so we format it as a conversation
        """
        if not messages:
            return ""

        # If only one message (first message), return it directly
        if len(messages) == 1:
            return messages[0]["content"]

        # For multiple messages, format as conversation context
        formatted = "Previous conversation:\n\n"
        for msg in messages[:-1]:  # All messages except the last
            role = "User" if msg["role"] == "user" else "Assistant"
            formatted += f"{role}: {msg['content']}\n\n"

        # Add the latest user message
        formatted += f"User: {messages[-1]['content']}"

        return formatted

    async def chat_with_streaming(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        model: str = "openai/gpt-4.1",
        mcp_servers: Optional[List[str]] = None,
        tools: Optional[List[Any]] = None
    ) -> AsyncIterator[str]:
        """
        Stream chat responses with progress updates

        Yields chunks of the response as they arrive
        """
        # Build full conversation
        full_conversation = conversation_history + [{"role": "user", "content": user_message}]
        input_text = self._format_conversation_for_dedalus(full_conversation)

        # For now, get non-streaming result and yield it as one chunk
        # TODO: Implement proper streaming once we figure out the Dedalus streaming API
        result = await self._runner.run(
            input=input_text,
            model=model,
            mcp_servers=mcp_servers or [],
            tools=tools or [],
            stream=False  # Disable streaming for now
        )

        # Yield the full response
        if hasattr(result, 'final_output'):
            yield result.final_output
        else:
            yield str(result)


# Create singleton instance
dedalus_service = DedalusService()
