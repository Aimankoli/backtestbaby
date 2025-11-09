"""
Signal Monitor Background Service

This service runs in the background and monitors active signals.
For each signal, it:
1. Checks for new tweets from the monitored Twitter account
2. Uses Dedalus + Twitter MCP tools to analyze sentiment
3. If signal detected, triggers backtest and sends message to conversation
4. Stores signal events in database
"""

import asyncio
import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from app.services.signal_service import (
    list_active_signals,
    update_signal_check_time,
    create_signal_event
)
from app.services.dedalus_service import dedalus_service
from app.services.conversation_service import add_message_to_conversation
from app.config import DEFAULT_MODEL

# Desktop notifications
try:
    from plyer import notification
    NOTIFICATIONS_AVAILABLE = True
except ImportError:
    NOTIFICATIONS_AVAILABLE = False
    print("[SignalMonitor] plyer not available - desktop notifications disabled")


class SignalMonitor:
    """Background service to monitor Twitter signals"""

    def __init__(self):
        self.running = False
        self.task = None

    async def start(self):
        """Start the background monitoring loop"""
        if self.running:
            print("[SignalMonitor] Already running")
            return

        self.running = True
        self.task = asyncio.create_task(self._monitor_loop())
        print("[SignalMonitor] Started monitoring signals")

    async def stop(self):
        """Stop the background monitoring loop"""
        if not self.running:
            return

        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

        print("[SignalMonitor] Stopped monitoring signals")

    async def _monitor_loop(self):
        """Main monitoring loop - runs continuously"""
        while self.running:
            try:
                await self._check_all_signals()
            except Exception as e:
                print(f"[SignalMonitor] Error in monitor loop: {e}")
                import traceback
                traceback.print_exc()

            # Wait 60 seconds before next check
            await asyncio.sleep(60)

    async def _check_all_signals(self):
        """Check all active signals"""
        try:
            # Get all active signals
            signals = await list_active_signals()

            if not signals:
                return

            print(f"[SignalMonitor] Checking {len(signals)} active signals")

            # Process each signal
            for signal in signals:
                try:
                    await self._process_signal(signal)
                except Exception as e:
                    print(f"[SignalMonitor] Error processing signal {signal['_id']}: {e}")

        except Exception as e:
            print(f"[SignalMonitor] Error fetching active signals: {e}")

    async def _process_signal(self, signal: Dict[str, Any]):
        """
        Process a single signal

        Steps:
        1. Check if enough time has passed since last check
        2. Call Dedalus with Twitter MCP tools to get latest tweets + analyze sentiment
        3. If signal detected (bullish/bearish), trigger actions
        4. Update signal metadata
        """
        signal_id = str(signal["_id"])
        twitter_username = signal["twitter_username"]
        conversation_id = signal["conversation_id"]
        user_id = signal["user_id"]
        check_interval = signal.get("parameters", {}).get("check_interval", 1.0)

        # Check if we should skip this check based on interval
        last_checked = signal.get("last_checked_at")
        if last_checked:
            time_since_check = (datetime.utcnow() - last_checked).total_seconds()
            if time_since_check < check_interval:
                return  # Too soon to check again

        print(f"[SignalMonitor] Processing signal for @{twitter_username}")

        try:
            # Call Dedalus with Twitter MCP to analyze recent tweets
            # Your friend's Twitter MCP will provide tools for this
            analysis_result = await self._analyze_twitter_account(
                twitter_username,
                signal.get("ticker"),
                signal.get("last_tweet_id")
            )

            # Update last checked time
            latest_tweet_id = analysis_result.get("latest_tweet_id")
            await update_signal_check_time(signal_id, latest_tweet_id)

            # Check if signal was detected
            if analysis_result.get("signal_detected"):
                await self._handle_signal_detected(
                    signal,
                    analysis_result,
                    conversation_id,
                    user_id
                )

        except Exception as e:
            print(f"[SignalMonitor] Error analyzing @{twitter_username}: {e}")
            import traceback
            traceback.print_exc()

    async def _analyze_twitter_account(
        self,
        twitter_username: str,
        ticker: Optional[str],
        last_tweet_id: Optional[str]
    ) -> Dict[str, Any]:
        """
        Use REAL Twitter API + Dedalus to analyze recent tweets

        Steps:
        1. Fetch tweets using real Twitter API
        2. Check created_at timestamps for new tweets
        3. Use Dedalus + your friend's Twitter MCP for sentiment analysis (or fallback for now)
        """
        from app.services.twitter_service import twitter_service

        # Check if Twitter API is available
        if not twitter_service.is_available():
            print(f"[SignalMonitor] Twitter API not available - check X_BEARER_TOKEN")
            return {
                "signal_detected": False,
                "sentiment": "neutral",
                "confidence": 0.0,
                "ticker": None,
                "latest_tweet_id": last_tweet_id,
                "error": "Twitter API not initialized"
            }

        try:
            # Get recent tweets using REAL Twitter API
            tweets = await twitter_service.get_recent_tweets(
                username=twitter_username,
                since_id=last_tweet_id,
                max_results=5
            )

            if not tweets:
                print(f"[SignalMonitor] No new tweets from @{twitter_username}")
                return {
                    "signal_detected": False,
                    "sentiment": "neutral",
                    "confidence": 0.0,
                    "ticker": None,
                    "latest_tweet_id": last_tweet_id
                }

            # Get the most recent tweet
            latest_tweet = tweets[0]
            tweet_text = latest_tweet["text"]
            tweet_id = latest_tweet["id"]

            print(f"[SignalMonitor] Analyzing tweet {tweet_id}: \"{tweet_text[:60]}...\"")

            # TODO: Use your friend's Twitter MCP for sentiment analysis
            # For now, use Dedalus with a simple prompt
            ticker_instruction = f"Focus on {ticker}" if ticker else "Identify which ticker to trade"

            prompt = f"""Analyze this tweet from @{twitter_username} for trading signals:

Tweet: "{tweet_text}"

{ticker_instruction}

Determine:
1. Sentiment: bullish, bearish, or neutral
2. Confidence level (0.0-1.0)
3. Which ticker symbol to trade (look for $ mentions or infer from context)
4. Brief reasoning

Return ONLY valid JSON:
{{
    "sentiment": "bullish|bearish|neutral",
    "confidence": 0.0-1.0,
    "ticker": "SYMBOL" or null,
    "reasoning": "brief explanation"
}}
"""

            # Call Dedalus for sentiment analysis
            result = await dedalus_service.chat_with_history(
                user_message=prompt,
                conversation_history=[],
                model=DEFAULT_MODEL,
                mcp_servers=[],  # Will use your friend's MCP here when ready
                tools=[],
                stream=False
            )

            response_text = result.final_output if hasattr(result, 'final_output') else str(result)

            # Parse sentiment analysis
            analysis = self._parse_analysis_response(response_text)

            # Determine if signal is strong enough
            sentiment = analysis.get("sentiment", "neutral")
            confidence = analysis.get("confidence", 0.0)
            signal_detected = sentiment in ["bullish", "bearish"] and confidence >= 0.6

            # Use ticker from analysis or fallback
            detected_ticker = analysis.get("ticker") or ticker

            return {
                "signal_detected": signal_detected,
                "sentiment": sentiment,
                "confidence": confidence,
                "ticker": detected_ticker,
                "latest_tweet_id": tweet_id,
                "tweet_text": tweet_text,
                "reasoning": analysis.get("reasoning", "")
            }

        except Exception as e:
            print(f"[SignalMonitor] Error analyzing @{twitter_username}: {e}")
            import traceback
            traceback.print_exc()
            return {
                "signal_detected": False,
                "sentiment": "neutral",
                "confidence": 0.0,
                "ticker": None,
                "latest_tweet_id": last_tweet_id,
                "error": str(e)
            }

    async def _analyze_with_mock_tools(
        self,
        twitter_username: str,
        ticker: Optional[str],
        last_tweet_id: Optional[str]
    ) -> Dict[str, Any]:
        """
        Analyze tweets using mock tools for testing

        This simulates what the Twitter MCP will do
        """
        from app.services.twitter_mock_tools import get_user_tweets_mock, analyze_tweet_sentiment_mock
        import json

        print(f"[SignalMonitor] Using MOCK tools for @{twitter_username}")

        # Get tweets (mock)
        tweets_result = get_user_tweets_mock(twitter_username, last_tweet_id)
        tweets_data = json.loads(tweets_result)

        if not tweets_data.get("has_new_tweets") or not tweets_data.get("tweets"):
            print(f"[SignalMonitor] No new tweets from @{twitter_username}")
            return {
                "signal_detected": False,
                "sentiment": "neutral",
                "confidence": 0.0,
                "ticker": None,
                "latest_tweet_id": last_tweet_id
            }

        # Analyze the most recent tweet
        latest_tweet = tweets_data["tweets"][0]
        tweet_text = latest_tweet["text"]
        tweet_id = latest_tweet["id"]

        # Analyze sentiment (mock)
        sentiment_result = analyze_tweet_sentiment_mock(tweet_text)
        sentiment_data = json.loads(sentiment_result)

        # Determine if signal is strong enough
        confidence = sentiment_data["confidence"]
        sentiment = sentiment_data["sentiment"]
        signal_detected = sentiment in ["bullish", "bearish"] and confidence >= 0.6

        # Use ticker from tweet analysis or fallback to signal config
        detected_ticker = sentiment_data.get("ticker") or ticker

        return {
            "signal_detected": signal_detected,
            "sentiment": sentiment,
            "confidence": confidence,
            "ticker": detected_ticker,
            "latest_tweet_id": tweet_id,
            "tweet_text": tweet_text,
            "reasoning": sentiment_data.get("reasoning", "")
        }

    def _parse_analysis_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse AI response to extract signal analysis

        Tries to find JSON in the response text
        """
        try:
            # Try to find JSON in the response
            import re

            # Look for JSON object in response
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                json_str = json_match.group(0)
                analysis = json.loads(json_str)

                # Ensure required fields exist
                if "signal_detected" not in analysis:
                    analysis["signal_detected"] = False
                if "sentiment" not in analysis:
                    analysis["sentiment"] = "neutral"
                if "confidence" not in analysis:
                    analysis["confidence"] = 0.0

                # Rename tweet_id to latest_tweet_id if present
                if "tweet_id" in analysis:
                    analysis["latest_tweet_id"] = analysis["tweet_id"]

                return analysis

        except Exception as e:
            print(f"[SignalMonitor] Error parsing analysis response: {e}")

        # Return default no-signal response
        return {
            "signal_detected": False,
            "sentiment": "neutral",
            "confidence": 0.0,
            "ticker": None,
            "latest_tweet_id": None
        }

    async def _handle_signal_detected(
        self,
        signal: Dict[str, Any],
        analysis: Dict[str, Any],
        conversation_id: str,
        user_id: str
    ):
        """
        Handle when a trading signal is detected

        Actions:
        1. Create signal event record
        2. Trigger backtest (if ticker available)
        3. Send message to user's conversation
        """
        signal_id = str(signal["_id"])
        twitter_username = signal["twitter_username"]
        sentiment = analysis.get("sentiment", "neutral")
        confidence = analysis.get("confidence", 0.0)
        ticker = analysis.get("ticker") or signal.get("ticker")
        tweet_text = analysis.get("tweet_text", "")
        tweet_id = analysis.get("latest_tweet_id", "")
        reasoning = analysis.get("reasoning", "")

        print(f"[SignalMonitor] 🚨 Signal detected for @{twitter_username}: {sentiment} {ticker} (confidence: {confidence})")

        actions_taken = []

        # Create signal event
        event = await create_signal_event(
            signal_id=signal_id,
            tweet_id=tweet_id,
            tweet_text=tweet_text,
            tweet_author=twitter_username,
            sentiment=sentiment,
            confidence=confidence,
            ticker_mentioned=ticker,
            action_taken=[],  # Will update after actions
            backtest_results=None
        )

        # TODO: Trigger backtest
        # This will be implemented when we integrate with your backtest system
        backtest_result = await self._trigger_backtest(ticker, sentiment)
        if backtest_result:
            actions_taken.append("backtest_triggered")

        # Send message to user's conversation
        message_sent = await self._send_signal_message(
            conversation_id=conversation_id,
            user_id=user_id,
            twitter_username=twitter_username,
            sentiment=sentiment,
            confidence=confidence,
            ticker=ticker,
            tweet_text=tweet_text,
            reasoning=reasoning,
            backtest_result=backtest_result
        )

        if message_sent:
            actions_taken.append("message_sent")

        # Update event with actions taken
        from app.db.mongodb import get_db
        db = get_db()
        await db.signal_events.update_one(
            {"_id": event["_id"]},
            {"$set": {
                "action_taken": actions_taken,
                "backtest_results": backtest_result
            }}
        )

        # Send desktop notification
        if NOTIFICATIONS_AVAILABLE:
            try:
                emoji = "📈" if sentiment == "bullish" else "📉" if sentiment == "bearish" else "➡️"
                notification.notify(
                    title=f"{emoji} Signal Detected: @{twitter_username}",
                    message=f"{sentiment.upper()} on {ticker or 'Unknown'} ({confidence:.0%} confidence)\n{tweet_text[:100]}...",
                    app_name="BacktestMCP",
                    timeout=10
                )
                print(f"[SignalMonitor] 🔔 Desktop notification sent")
            except Exception as e:
                print(f"[SignalMonitor] ⚠️ Notification failed (non-critical): {e}")

    async def _trigger_backtest(
        self,
        ticker: Optional[str],
        sentiment: str
    ) -> Optional[Dict[str, Any]]:
        """
        Trigger a backtest for the signal using the backtest tools

        Runs a simple backtest based on the signal sentiment
        """
        if not ticker:
            print(f"[SignalMonitor] No ticker specified, skipping backtest")
            return None

        from app.services.agent import fetch_stock_data, generate_backtest_script, execute_backtest
        from datetime import datetime, timedelta
        import json

        print(f"[SignalMonitor] 🔄 Triggering backtest for {ticker} ({sentiment} signal)")

        try:
            # Define date range - last 1 year
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

            # Step 1: Fetch stock data
            print(f"[SignalMonitor] Fetching {ticker} data from {start_date} to {end_date}")
            data_result = fetch_stock_data(ticker, start_date, end_date)
            data_json = json.loads(data_result)

            if not data_json.get("success"):
                print(f"[SignalMonitor] ✗ Failed to fetch data: {data_json.get('error')}")
                return None

            data_file = data_json["file_path"]
            print(f"[SignalMonitor] ✓ Data fetched: {data_file}")

            # Step 2: Generate backtest script
            strategy_desc = f"Simple moving average crossover strategy based on {sentiment} signal from Twitter"
            print(f"[SignalMonitor] Generating backtest script...")
            script_result = generate_backtest_script(strategy_desc, data_file, ticker)
            script_json = json.loads(script_result)

            if not script_json.get("success"):
                print(f"[SignalMonitor] ✗ Failed to generate script")
                return None

            script_file = script_json["script_path"]
            print(f"[SignalMonitor] ✓ Script generated: {script_file}")

            # Step 3: Execute backtest
            print(f"[SignalMonitor] Executing backtest...")
            exec_result = execute_backtest(script_file)
            exec_json = json.loads(exec_result)

            if not exec_json.get("success"):
                print(f"[SignalMonitor] ✗ Backtest execution failed")
                return None

            metrics = exec_json.get("metrics", {})
            plot_path = exec_json.get("plot_path")

            print(f"[SignalMonitor] ✓ Backtest complete!")
            print(f"[SignalMonitor]   Total Return: {metrics.get('total_return', 'N/A')}%")
            print(f"[SignalMonitor]   Sharpe Ratio: {metrics.get('sharpe_ratio', 'N/A')}")
            print(f"[SignalMonitor]   Max Drawdown: {metrics.get('max_drawdown', 'N/A')}%")

            # Read plot HTML and data CSV files
            plot_html = None
            data_csv = None

            if plot_path:
                try:
                    from pathlib import Path
                    plot_file = Path(plot_path)
                    if plot_file.exists():
                        plot_html = plot_file.read_text()
                        print(f"[SignalMonitor] ✓ Read plot HTML: {len(plot_html)} chars")
                except Exception as e:
                    print(f"[SignalMonitor] ✗ Failed to read plot HTML: {e}")

            if data_file:
                try:
                    from pathlib import Path
                    data_file_path = Path(data_file)
                    if data_file_path.exists():
                        data_csv = data_file_path.read_text()
                        print(f"[SignalMonitor] ✓ Read data CSV: {len(data_csv)} chars")
                except Exception as e:
                    print(f"[SignalMonitor] ✗ Failed to read data CSV: {e}")

            # Return backtest results with file contents
            return {
                "ticker": ticker,
                "strategy": strategy_desc,
                "date_range": f"{start_date} to {end_date}",
                "metrics": metrics,
                "plot_path": plot_path,
                "plot_html": plot_html,
                "data_csv": data_csv,
                "script_path": script_file
            }

        except Exception as e:
            print(f"[SignalMonitor] ✗ Error running backtest: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def _send_signal_message(
        self,
        conversation_id: str,
        user_id: str,
        twitter_username: str,
        sentiment: str,
        confidence: float,
        ticker: Optional[str],
        tweet_text: str,
        reasoning: str,
        backtest_result: Optional[Dict[str, Any]]
    ) -> bool:
        """
        Send a message to the user's conversation about the signal

        Returns True if message was sent successfully
        """
        try:
            # Format the message
            emoji = "📈" if sentiment == "bullish" else "📉" if sentiment == "bearish" else "➡️"

            message = f"""{emoji} **Signal Detected from @{twitter_username}**

**Sentiment**: {sentiment.upper()} (Confidence: {confidence:.1%})
**Ticker**: {ticker or "TBD"}

**Tweet**: "{tweet_text}"

**Analysis**: {reasoning}
"""

            if backtest_result:
                metrics = backtest_result.get("metrics", {})
                message += f"""

**📊 Backtest Results** ({backtest_result.get('date_range', 'N/A')}):
- Total Return: {metrics.get('total_return', 'N/A')}%
- Buy & Hold: {metrics.get('buy_hold_return', 'N/A')}%
- Sharpe Ratio: {metrics.get('sharpe_ratio', 'N/A')}
- Max Drawdown: {metrics.get('max_drawdown', 'N/A')}%
- Win Rate: {metrics.get('win_rate', 'N/A')}%
- # Trades: {metrics.get('num_trades', 'N/A')}
"""
                if backtest_result.get('plot_path'):
                    message += f"\n📈 Chart: {backtest_result['plot_path']}"

            # Add message to conversation
            await add_message_to_conversation(
                conversation_id=conversation_id,
                user_id=user_id,
                role="assistant",
                content=message
            )

            print(f"[SignalMonitor] ✓ Sent signal message to conversation {conversation_id}")
            return True

        except Exception as e:
            print(f"[SignalMonitor] Error sending signal message: {e}")
            return False


# Global signal monitor instance
signal_monitor = SignalMonitor()
