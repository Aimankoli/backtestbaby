from typing import Optional, AsyncIterator, Dict, Any
import json
import re
from datetime import datetime
from app.config import DEFAULT_MODEL
from app.services.dedalus_service import dedalus_service
from app.services.conversation_service import (
    get_conversation,
    add_message_to_conversation
)
from app.services.research_agent_tools import create_twitter_signal
from app.services.twitter_agent_tools import (
    search_trending_tweets,
    analyze_user_profile,
    monitor_keywords,
    find_influential_accounts,
    track_account_activity,
    research_hashtag,
    compare_accounts,
    find_viral_content,
    get_conversation_context,
)


RESEARCH_SYSTEM_PROMPT = """You are an elite financial research assistant with access to web search (Brave Search) and advanced Twitter/X intelligence tools.

OUTPUT FORMAT REQUIREMENTS:
Always structure your responses with clear sections using markdown headers and bullet points. Use **bold** formatting for important information:

## Executive Summary
- Provide 2-3 key takeaways at the top
- Use **bold** for key metrics and numbers

## Research Findings
- Use bullet points and sub-bullets for clarity
- Include specific data points, numbers, and metrics
- Use **bold** for important figures, percentages, and key findings
- Cite sources when using web search results with links in parentheses

## Key Metrics & Data
- Present quantitative data in a clear format
- Use **bold** for all metrics, numbers, and percentages
- Include all important numbers in **bold**

## Analysis & Insights
- Provide actionable insights
- Connect findings to trading/investment implications
- Use **bold** for key conclusions and recommendations
- Use clear, concise language

## Risk Factors (if applicable)
- Identify potential concerns or red flags
- Use **bold** for risk severity levels and key concerns
- Use bullet points for each risk

## Recommendations (if applicable)
- Provide clear, actionable next steps
- Use **bold** for action items and key recommendations
- Use numbered lists for sequential actions

---

TWITTER/X RESEARCH TOOLS:

1. create_twitter_signal - Set up automated monitoring
   Use for: "Monitor @elonmusk for TSLA", "Track @cathiedwood"

2. search_trending_tweets - Find viral content
   Use for: "What's trending about Bitcoin?", "Viral AI tweets"

3. analyze_user_profile - Deep account analysis
   Use for: "Analyze @balajis profile", "Research @elonmusk"

4. monitor_keywords - Track keywords/phrases
   Use for: "Monitor NVDA mentions", "Track recession talk"

5. find_influential_accounts - Discover thought leaders
   Use for: "Find crypto influencers", "Top AI founders"

6. track_account_activity - Recent posts monitoring
   Use for: "Show @pmarca's tweets", "@chamath recent activity"

7. research_hashtag - Hashtag deep dive
   Use for: "Analyze #AI", "Research #Bitcoin performance"

8. compare_accounts - Side-by-side comparison
   Use for: "Compare @elonmusk vs @BillGates"

9. find_viral_content - Discover trending content
   Use for: "Viral crypto content", "Trending in tech"

10. get_conversation_context - Full thread context
    Use for: "Get tweet 123456789 context", "Show thread"

RESPONSE STYLE:
- Be concise but comprehensive
- Use bullet points and sub-bullets extensively
- Structure everything with clear markdown headers (## Header)
- Make it scannable and easy to read
- STRICT RULE: DO NOT use emojis in your responses. Keep all text professional and emoji-free.
- Use **bold** formatting for all important numbers, metrics, ticker symbols, and key findings
- Numbers and metrics should be in **bold** for emphasis"""


async def process_research_message(
    conversation_id: str,
    user_id: str,
    user_message: str,
    model: str = None
) -> AsyncIterator[str]:
    """
    Process a research chat message with conversation history and streaming response

    Yields:
        JSON-encoded chunks:
        - {"type": "content", "data": "text chunk"}
        - {"type": "tool_start", "data": "tool_name"}
        - {"type": "tool_end", "data": "tool_name"}
        - {"type": "signal_created", "data": {"signal_id": "...", "twitter_username": "..."}}
        - {"type": "done"}
    """
    # Use default model if not specified
    if model is None:
        model = DEFAULT_MODEL

    # Get conversation from DB
    conversation = await get_conversation(conversation_id, user_id)
    if not conversation:
        yield json.dumps({"type": "error", "data": "Conversation not found"}) + "\n"
        return

    # Check if this is the first message
    is_first_message = len(conversation.get("messages", [])) == 0

    # Add user message to conversation
    await add_message_to_conversation(conversation_id, user_id, "user", user_message)

    # Prepare conversation history for Dedalus
    messages = conversation.get("messages", [])
    conversation_history = [
        {"role": msg["role"], "content": msg["content"]}
        for msg in messages
    ]

    # Add system prompt for first message
    if is_first_message:
        full_message = f"{RESEARCH_SYSTEM_PROMPT}\n\nUser: {user_message}"
    else:
        full_message = user_message

    # Get response from Dedalus
    full_response = ""
    try:
        print(f"[DEBUG] Calling Dedalus for research with message: {full_message[:100]}...")

        # Call Dedalus with Brave Search MCP and all research tools
        result = await dedalus_service.chat_with_history(
            user_message=full_message,
            conversation_history=conversation_history if not is_first_message else [],
            model=model,
            mcp_servers=["aimankoli/brave-search-mcp"],  # Use Brave Search MCP
            tools=[
                # Signal creation tool
                create_twitter_signal,
                # Twitter research and monitoring tools
                search_trending_tweets,
                analyze_user_profile,
                monitor_keywords,
                find_influential_accounts,
                track_account_activity,
                research_hashtag,
                compare_accounts,
                find_viral_content,
                get_conversation_context,
            ],
            stream=False
        )

        print(f"[DEBUG] Got result from Dedalus for research")
        full_response = result.final_output if hasattr(result, 'final_output') else str(result)
        print(f"[DEBUG] Full response: {len(full_response)} chars")

        # Check if the create_twitter_signal tool was called
        signal_metadata = None
        if hasattr(result, 'tool_results') and result.tool_results:
            print(f"[DEBUG] Tool results found: {len(result.tool_results)} tools called")
            for tool_result in result.tool_results:
                tool_name = tool_result.get('name', '')
                tool_output = tool_result.get('result', '')

                print(f"[DEBUG] Tool called: {tool_name}")

                if tool_name == 'create_twitter_signal' and tool_output:
                    try:
                        signal_data = json.loads(tool_output)
                        if signal_data.get("success"):
                            signal_metadata = {
                                "twitter_username": signal_data.get("twitter_username"),
                                "ticker": signal_data.get("ticker"),
                                "check_interval": signal_data.get("check_interval", 1.0),
                                "description": signal_data.get("description")
                            }
                            print(f"[DEBUG] Signal tool called successfully: @{signal_metadata['twitter_username']}")
                    except json.JSONDecodeError as e:
                        print(f"[ERROR] Failed to parse signal tool output: {e}")

        # Yield the response
        yield json.dumps({"type": "content", "data": full_response}) + "\n"

        # Save assistant response to DB
        await add_message_to_conversation(conversation_id, user_id, "assistant", full_response)

        # Create signal in DB if tool was called
        if not signal_metadata:
            # Fallback: Check for signal metadata in response text (old method)
            signal_metadata = extract_signal_metadata(full_response)
        if signal_metadata:
            from app.services.signal_service import create_signal

            print(f"[DEBUG] Creating signal from research chat: @{signal_metadata['twitter_username']}")

            # Create signal
            signal = await create_signal(
                user_id=user_id,
                conversation_id=conversation_id,
                twitter_username=signal_metadata["twitter_username"],
                ticker=signal_metadata.get("ticker"),
                check_interval=signal_metadata.get("check_interval", 1.0),
                description=signal_metadata.get("description") or f"Monitor @{signal_metadata['twitter_username']} via research chat"
            )

            signal_id = str(signal["_id"])
            print(f"[DEBUG] Signal created: {signal_id}")

            # Notify client that signal was created
            yield json.dumps({
                "type": "signal_created",
                "data": {
                    "signal_id": signal_id,
                    "twitter_username": signal["twitter_username"],
                    "ticker": signal.get("ticker"),
                    "check_interval": signal["parameters"].get("check_interval", 1.0),
                    "status": signal["status"]
                }
            }) + "\n"

        # Signal completion
        yield json.dumps({"type": "done"}) + "\n"

    except Exception as e:
        print(f"[ERROR] Error in research chat: {e}")
        import traceback
        traceback.print_exc()
        yield json.dumps({"type": "error", "data": str(e)}) + "\n"


def extract_signal_metadata(response: str) -> Optional[Dict[str, Any]]:
    """
    Extract signal metadata from LLM response

    Looks for pattern:
    SIGNAL_METADATA:
    {
      "twitter_username": "...",
      "ticker": "...",
      "check_interval": 1,
      "description": "..."
    }
    """
    # Look for SIGNAL_METADATA: followed by JSON
    pattern = r'SIGNAL_METADATA:\s*(\{[^}]+\})'
    match = re.search(pattern, response, re.DOTALL)

    if match:
        try:
            metadata_str = match.group(1)
            # Clean up the JSON string (handle newlines, extra spaces)
            metadata_str = re.sub(r'\s+', ' ', metadata_str)
            metadata = json.loads(metadata_str)

            # Validate required fields
            if "twitter_username" in metadata:
                # Remove @ if present
                metadata["twitter_username"] = metadata["twitter_username"].lstrip("@")

                # Set defaults
                if "check_interval" not in metadata:
                    metadata["check_interval"] = 1.0

                # ticker can be None
                if "ticker" not in metadata:
                    metadata["ticker"] = None

                return metadata
        except json.JSONDecodeError:
            # If JSON parsing fails, try to extract manually
            username_match = re.search(r'"twitter_username"\s*:\s*"@?([^"]+)"', response)
            ticker_match = re.search(r'"ticker"\s*:\s*"([^"]+)"', response)
            interval_match = re.search(r'"check_interval"\s*:\s*([\d.]+)', response)
            desc_match = re.search(r'"description"\s*:\s*"([^"]+)"', response)

            if username_match:
                return {
                    "twitter_username": username_match.group(1),
                    "ticker": ticker_match.group(1) if ticker_match else None,
                    "check_interval": float(interval_match.group(1)) if interval_match else 1.0,
                    "description": desc_match.group(1) if desc_match else None
                }

    return None
