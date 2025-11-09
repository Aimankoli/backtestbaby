from typing import Optional, AsyncIterator, Dict, Any
import json
import re
import asyncio
from datetime import datetime
from app.config import DEFAULT_MODEL
from app.services.dedalus_service import dedalus_service
from app.services.conversation_service import (
    get_conversation,
    add_message_to_conversation,
    link_strategy_to_conversation
)
from app.services.strategy_service import create_strategy, get_strategy_by_conversation
from app.services.agent import (
    fetch_stock_data,
    generate_backtest_script,
    execute_backtest,
    explain_metric
)


SYSTEM_PROMPT = """You are a trading strategy assistant with the ability to create backtesting strategies and set up Twitter sentiment signals.

When a user describes their strategy, start your response with:
STRATEGY_METADATA:
{"name": "Strategy Name", "description": "Brief description"}

When a user asks to monitor a Twitter account or create a signal, start your response with:
SIGNAL_METADATA:
{"twitter_username": "username", "ticker": "SYMBOL", "check_interval": 60, "description": "Brief description"}

Examples of signal requests:
- "Monitor @elonmusk for TSLA signals"
- "Track @cathiedwood tweets for ARKK sentiment"
- "Create a signal for @realDonaldTrump on SPY"
- "Watch @chamath for SPAC opportunities"

Then provide your analysis and explain what the signal will do."""


async def process_chat_message(
    conversation_id: str,
    user_id: str,
    user_message: str,
    model: str = None
) -> AsyncIterator[str]:
    """
    Process a chat message with conversation history and streaming response

    Yields:
        JSON-encoded chunks:
        - {"type": "content", "data": "text chunk"}
        - {"type": "tool_start", "data": "tool_name"}
        - {"type": "tool_end", "data": "tool_name"}
        - {"type": "strategy_created", "data": {"strategy_id": "...", "name": "..."}}
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
        full_message = f"{SYSTEM_PROMPT}\n\nUser: {user_message}"
    else:
        full_message = user_message

    # Get response from Dedalus - use non-streaming with manual chunks for reliability
    full_response = ""
    result_obj = None
    try:
        print(f"[DEBUG] Calling Dedalus with message: {full_message[:100]}...")

        # Collect tool events in a list
        tool_events_list = []

        def on_tool_event_callback(event: Dict[str, Any]):
            """Callback for tool execution events"""
            print(f"[TOOL_EVENT] {event}")
            tool_events_list.append(event)

        # Call Dedalus with backtest tools - NON-STREAMING for stability
        result = await dedalus_service.chat_with_history(
            user_message=full_message,
            conversation_history=conversation_history if not is_first_message else [],
            model=model,
            mcp_servers=[],
            tools=[fetch_stock_data, generate_backtest_script, execute_backtest, explain_metric],
            stream=False,  # Use non-streaming for now
            on_tool_event=on_tool_event_callback
        )

        print(f"[DEBUG] Got result from Dedalus")

        # Extract response
        full_response = result.final_output if hasattr(result, 'final_output') else str(result)
        print(f"[DEBUG] Full response: {len(full_response)} chars")
        print(f"[DEBUG] Tool events captured: {len(tool_events_list)}")

        # Stream tool events first
        for tool_event in tool_events_list:
            yield json.dumps({"type": "tool_event", "data": tool_event}) + "\n"
            await asyncio.sleep(0.05)  # Small delay for visual effect

        # Manually chunk the response for streaming effect
        CHUNK_SIZE = 50  # Characters per chunk
        for i in range(0, len(full_response), CHUNK_SIZE):
            chunk = full_response[i:i+CHUNK_SIZE]
            yield json.dumps({"type": "content", "data": chunk}) + "\n"
            await asyncio.sleep(0.03)  # Small delay for streaming effect

        # Store result object for backtest extraction
        result_obj = result

        # Check if backtest was executed and extract structured data
        backtest_data = await extract_backtest_data(result_obj) if result_obj else None

        # If backtest data exists, send it as structured data
        if backtest_data:
            yield json.dumps({"type": "backtest_result", "data": backtest_data}) + "\n"

        # Save assistant response to DB
        await add_message_to_conversation(conversation_id, user_id, "assistant", full_response)

        # If first message, parse strategy metadata and create strategy
        strategy_id = None
        if is_first_message:
            strategy_metadata = extract_strategy_metadata(full_response)
            if strategy_metadata:
                # Create strategy
                strategy = await create_strategy(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    name=strategy_metadata.get("name", "Untitled Strategy"),
                    description=strategy_metadata.get("description")
                )

                # Link strategy to conversation
                strategy_id = str(strategy["_id"])
                await link_strategy_to_conversation(conversation_id, user_id, strategy_id)

                # Notify client that strategy was created
                yield json.dumps({
                    "type": "strategy_created",
                    "data": {
                        "strategy_id": strategy_id,
                        "name": strategy_metadata.get("name"),
                        "description": strategy_metadata.get("description")
                    }
                }) + "\n"

        # Check for signal creation request (can happen in any message)
        signal_metadata = extract_signal_metadata(full_response)
        if signal_metadata:
            from app.services.signal_service import create_signal

            print(f"[DEBUG] Creating signal from chat: @{signal_metadata['twitter_username']}")

            # Create signal
            signal = await create_signal(
                user_id=user_id,
                conversation_id=conversation_id,
                twitter_username=signal_metadata["twitter_username"],
                ticker=signal_metadata.get("ticker"),
                check_interval=signal_metadata.get("check_interval", 60),
                description=signal_metadata.get("description") or f"Monitor @{signal_metadata['twitter_username']} via chat"
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
                    "check_interval": signal["parameters"].get("check_interval", 60),
                    "status": signal["status"]
                }
            }) + "\n"

        # Now save backtest results to the strategy (after it's been created)
        if backtest_data:
            strategy = await get_strategy_by_conversation(conversation_id, user_id)
            if strategy:
                from app.services.strategy_service import update_strategy, add_backtest_result
                # Save code to strategy
                if backtest_data.get("code"):
                    await update_strategy(
                        strategy_id=str(strategy["_id"]),
                        user_id=user_id,
                        update_data={"backtest_code": backtest_data["code"]}
                    )
                # Save backtest results with plot HTML and data CSV
                if backtest_data.get("metrics"):
                    await add_backtest_result(
                        strategy_id=str(strategy["_id"]),
                        user_id=user_id,
                        backtest_result={
                            "backtest_id": backtest_data.get("backtest_id", ""),
                            "metrics": backtest_data["metrics"],
                            "plot_path": backtest_data.get("plot_path"),
                            "plot_html": backtest_data.get("plot_html"),
                            "data_csv": backtest_data.get("data_csv"),
                            "ran_at": datetime.utcnow()
                        }
                    )

        # Signal completion
        yield json.dumps({"type": "done"}) + "\n"

    except Exception as e:
        yield json.dumps({"type": "error", "data": str(e)}) + "\n"


async def extract_backtest_data(result: Any) -> Optional[Dict[str, Any]]:
    """
    Extract structured backtest data from Dedalus result.

    Returns a dict with:
    - code: The generated Python code
    - description: Strategy description
    - metrics: Backtest metrics as a dict
    - plot_path: Path to the plot HTML file
    - plot_html: HTML content of the plot
    - data_csv: CSV data content
    - data_path: Path to the data CSV file
    - backtest_id: Unique ID for this backtest run
    """
    try:
        backtest_data = {
            "code": None,
            "description": None,
            "metrics": {},
            "plot_path": None,
            "plot_html": None,
            "data_csv": None,
            "data_path": None,
            "backtest_id": None,
            "script_path": None
        }

        # Extract from tool_results attribute (Dedalus structure)
        if hasattr(result, 'tool_results') and result.tool_results:
            for tool_result in result.tool_results:
                tool_name = tool_result.get('name', '')
                tool_output = tool_result.get('result', '')

                if tool_name == 'fetch_stock_data' and tool_output:
                    try:
                        data_result = json.loads(tool_output)
                        backtest_data["data_path"] = data_result.get("file_path")
                    except Exception as e:
                        print(f"[ERROR] Failed to parse data fetch result: {e}")

                if tool_name == 'generate_backtest_script' and tool_output:
                    try:
                        script_data = json.loads(tool_output)
                        backtest_data["script_path"] = script_data.get("script_path")
                    except Exception as e:
                        print(f"[ERROR] Failed to parse script data: {e}")

                if tool_name == 'execute_backtest' and tool_output:
                    try:
                        exec_data = json.loads(tool_output)
                        backtest_data["metrics"] = exec_data.get("metrics", {})
                        backtest_data["plot_path"] = exec_data.get("plot_path")
                        backtest_data["backtest_id"] = exec_data.get("script_path", "").split("/")[-1].replace(".py", "")
                    except Exception as e:
                        print(f"[ERROR] Failed to parse exec data: {e}")

        # If we have a script path, read the code
        if backtest_data.get("script_path"):
            try:
                from pathlib import Path
                script_path = Path(backtest_data["script_path"])
                if script_path.exists():
                    backtest_data["code"] = script_path.read_text()
                    print(f"[DEBUG] Read backtest code: {len(backtest_data['code'])} chars")
            except Exception as e:
                print(f"[ERROR] Failed to read script file: {e}")

        # Read plot HTML file
        if backtest_data.get("plot_path"):
            try:
                from pathlib import Path
                plot_path = Path(backtest_data["plot_path"])
                if plot_path.exists():
                    backtest_data["plot_html"] = plot_path.read_text()
                    print(f"[DEBUG] Read plot HTML: {len(backtest_data['plot_html'])} chars")
            except Exception as e:
                print(f"[ERROR] Failed to read plot HTML file: {e}")

        # Read data CSV file
        if backtest_data.get("data_path"):
            try:
                from pathlib import Path
                data_path = Path(backtest_data["data_path"])
                if data_path.exists():
                    backtest_data["data_csv"] = data_path.read_text()
                    print(f"[DEBUG] Read data CSV: {len(backtest_data['data_csv'])} chars")
            except Exception as e:
                print(f"[ERROR] Failed to read data CSV file: {e}")

        # Fallback: Try to parse metrics from the final_output text
        if not backtest_data.get("metrics") and hasattr(result, 'final_output'):
            backtest_data["metrics"] = parse_metrics_from_text(result.final_output)

        # Only return if we have actual backtest data (code or metrics)
        if backtest_data.get("code") or backtest_data.get("metrics"):
            return backtest_data

        return None
    except Exception as e:
        print(f"[ERROR] Error extracting backtest data: {e}")
        import traceback
        traceback.print_exc()
        return None


def parse_metrics_from_text(text: str) -> Dict[str, Any]:
    """
    Parse backtest metrics from text response
    
    Looks for patterns like:
    - Total Return: 7.32%
    - Buy & Hold Return: 43.60%
    - Max Drawdown: -7.07%
    - Sharpe Ratio: 0.42
    - Number of Trades: 1
    - Win Rate: 100%
    """
    metrics = {}
    
    try:
        # Total Return
        match = re.search(r'Total Return:\s*([-\d.]+)%', text)
        if match:
            metrics['total_return'] = float(match.group(1))
        
        # Buy & Hold Return
        match = re.search(r'Buy\s*&\s*Hold Return:\s*([-\d.]+)%', text)
        if match:
            metrics['buy_hold_return'] = float(match.group(1))
        
        # Max Drawdown
        match = re.search(r'Max(?:imum)?\s*Drawdown:\s*([-\d.]+)%', text)
        if match:
            metrics['max_drawdown'] = float(match.group(1))
        
        # Sharpe Ratio
        match = re.search(r'Sharpe Ratio:\s*([-\d.]+)', text)
        if match:
            metrics['sharpe_ratio'] = float(match.group(1))
        
        # Number of Trades
        match = re.search(r'(?:Number of Trades|# Trades):\s*(\d+)', text)
        if match:
            metrics['num_trades'] = int(match.group(1))
        
        # Win Rate
        match = re.search(r'Win Rate:\s*([-\d.]+)%', text)
        if match:
            metrics['win_rate'] = float(match.group(1))
    
    except Exception as e:
        print(f"[DEBUG] Error parsing metrics from text: {e}")
    
    return metrics


def extract_strategy_metadata(response: str) -> Optional[Dict[str, Any]]:
    """
    Extract strategy metadata from LLM response

    Looks for pattern:
    STRATEGY_METADATA:
    {
      "name": "...",
      "description": "..."
    }
    """
    # Look for STRATEGY_METADATA: followed by JSON
    pattern = r'STRATEGY_METADATA:\s*(\{[^}]+\})'
    match = re.search(pattern, response, re.DOTALL)

    if match:
        try:
            metadata_str = match.group(1)
            # Clean up the JSON string (handle newlines, extra spaces)
            metadata_str = re.sub(r'\s+', ' ', metadata_str)
            metadata = json.loads(metadata_str)
            return metadata
        except json.JSONDecodeError:
            # If JSON parsing fails, try to extract manually
            name_match = re.search(r'"name"\s*:\s*"([^"]+)"', response)
            desc_match = re.search(r'"description"\s*:\s*"([^"]+)"', response)

            if name_match:
                return {
                    "name": name_match.group(1),
                    "description": desc_match.group(1) if desc_match else None
                }

    return None


def extract_signal_metadata(response: str) -> Optional[Dict[str, Any]]:
    """
    Extract signal metadata from LLM response

    Looks for pattern:
    SIGNAL_METADATA:
    {
      "twitter_username": "...",
      "ticker": "...",
      "check_interval": 60,
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
                    metadata["check_interval"] = 60

                # ticker can be None
                if "ticker" not in metadata:
                    metadata["ticker"] = None

                return metadata
        except json.JSONDecodeError:
            # If JSON parsing fails, try to extract manually
            username_match = re.search(r'"twitter_username"\s*:\s*"@?([^"]+)"', response)
            ticker_match = re.search(r'"ticker"\s*:\s*"([^"]+)"', response)
            interval_match = re.search(r'"check_interval"\s*:\s*(\d+)', response)
            desc_match = re.search(r'"description"\s*:\s*"([^"]+)"', response)

            if username_match:
                return {
                    "twitter_username": username_match.group(1),
                    "ticker": ticker_match.group(1) if ticker_match else None,
                    "check_interval": int(interval_match.group(1)) if interval_match else 60,
                    "description": desc_match.group(1) if desc_match else None
                }

    return None


async def handle_tool_results(
    conversation_id: str,
    user_id: str,
    tool_name: str,
    tool_results: Dict[str, Any]
) -> bool:
    """
    Handle tool results and save them to both conversation and strategy

    Args:
        conversation_id: The conversation ID
        user_id: The user ID
        tool_name: Name of the tool that was executed
        tool_results: Results from the tool execution

    Returns:
        True if successful
    """
    # Format tool results as a message
    results_message = f"Tool '{tool_name}' completed:\n{json.dumps(tool_results, indent=2)}"

    # Add to conversation as assistant message
    await add_message_to_conversation(conversation_id, user_id, "assistant", results_message)

    # If it's a backtest result, also save to strategy
    if tool_name == "backtest" or "backtest" in tool_name.lower():
        strategy = await get_strategy_by_conversation(conversation_id, user_id)
        if strategy:
            from app.services.strategy_service import add_backtest_result
            await add_backtest_result(
                strategy_id=str(strategy["_id"]),
                user_id=user_id,
                backtest_result=tool_results
            )

    return True
