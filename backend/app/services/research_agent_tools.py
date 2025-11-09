"""
Research Agent Tools
====================
Custom tools for the research agent including signal creation
"""

import json
from typing import Optional
from datetime import datetime


def create_twitter_signal(
    twitter_username: str,
    ticker: Optional[str] = None,
    check_interval: float = 1.0,
    description: Optional[str] = None
) -> str:
    """
    Create a Twitter sentiment signal to monitor a specific account for trading signals.

    Use this when the user asks to:
    - Monitor a Twitter account
    - Set up a signal for a specific user
    - Track tweets for a stock

    Args:
        twitter_username: Twitter username to monitor (with or without @)
        ticker: Stock ticker symbol to associate with this signal (e.g., 'TSLA', 'SPY')
        check_interval: How often to check for new tweets in seconds (default: 1.0, range: 0.5-1.5)
        description: Optional description of what this signal monitors

    Returns:
        JSON string containing signal creation details and next steps
    """
    try:
        # Clean username
        username = twitter_username.lstrip("@")

        print(f"[TOOL: create_twitter_signal] Creating signal for @{username} (ticker: {ticker})...")

        # Return metadata that will be processed by the chat service
        # The chat service will handle the async DB creation
        result = {
            "success": True,
            "twitter_username": username,
            "ticker": ticker,
            "check_interval": check_interval,
            "description": description or f"Monitor @{username} tweets for {ticker or 'trading signals'}",
            "message": f"Signal created successfully! Monitoring @{username}" + (f" for {ticker}" if ticker else ""),
            "tool": "create_twitter_signal"
        }

        print(f"[TOOL: create_twitter_signal] ✓ Signal metadata prepared")
        return json.dumps(result, indent=2)

    except Exception as e:
        error_result = {
            "success": False,
            "error": str(e),
            "tool": "create_twitter_signal"
        }
        print(f"[TOOL: create_twitter_signal] ✗ Error: {e}")
        return json.dumps(error_result)
