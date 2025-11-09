"""
Mock Twitter Tools for Testing

These are placeholder tools that simulate what your friend's Twitter MCP will provide.
Once the real MCP is ready, we'll switch to using that instead.

These tools will be removed when the real Twitter MCP is integrated.
"""

import random
from typing import Optional


def get_user_tweets_mock(username: str, since_id: Optional[str] = None) -> str:
    """
    Mock tool that simulates getting tweets from a user

    This simulates what the Twitter MCP tool will do.
    The real tool from your friend's MCP will replace this.

    Args:
        username: Twitter username to fetch tweets from
        since_id: Only return tweets after this ID

    Returns:
        JSON string with tweet data
    """
    import json

    # Simulate different tweet scenarios
    scenarios = [
        {
            "has_new_tweets": True,
            "tweets": [
                {
                    "id": f"tweet_{random.randint(1000000, 9999999)}",
                    "text": "Just announced major partnership with $TSLA! This is huge for the future. 🚀",
                    "created_at": "2025-11-08T18:00:00Z"
                }
            ]
        },
        {
            "has_new_tweets": True,
            "tweets": [
                {
                    "id": f"tweet_{random.randint(1000000, 9999999)}",
                    "text": "Concerned about the market conditions. Selling my $SPY positions today.",
                    "created_at": "2025-11-08T19:00:00Z"
                }
            ]
        },
        {
            "has_new_tweets": False,
            "tweets": []
        }
    ]

    # Pick a random scenario
    result = random.choice(scenarios)

    print(f"[MOCK] get_user_tweets_mock(@{username}, since_id={since_id})")
    print(f"[MOCK] Returning: {len(result.get('tweets', []))} tweets")

    return json.dumps(result)


def analyze_tweet_sentiment_mock(tweet_text: str) -> str:
    """
    Mock tool that simulates sentiment analysis on a tweet

    This simulates what the Twitter MCP sentiment analysis tool will do.
    The real tool from your friend's MCP will replace this.

    Args:
        tweet_text: The tweet text to analyze

    Returns:
        JSON string with sentiment analysis
    """
    import json
    import re

    # Simple keyword-based mock sentiment
    bullish_keywords = ["partnership", "huge", "great", "buying", "rocket", "moon", "bullish", "growth"]
    bearish_keywords = ["concerned", "selling", "crash", "worried", "bearish", "down", "loss"]

    text_lower = tweet_text.lower()

    # Extract ticker mentions (e.g., $TSLA, $SPY)
    ticker_pattern = r'\$([A-Z]{1,5})'
    tickers = re.findall(ticker_pattern, tweet_text)

    bullish_count = sum(1 for word in bullish_keywords if word in text_lower)
    bearish_count = sum(1 for word in bearish_keywords if word in text_lower)

    if bullish_count > bearish_count:
        sentiment = "bullish"
        confidence = min(0.6 + (bullish_count * 0.1), 0.95)
    elif bearish_count > bullish_count:
        sentiment = "bearish"
        confidence = min(0.6 + (bearish_count * 0.1), 0.95)
    else:
        sentiment = "neutral"
        confidence = 0.5

    result = {
        "sentiment": sentiment,
        "confidence": confidence,
        "ticker": tickers[0] if tickers else None,
        "reasoning": f"Detected {bullish_count} bullish and {bearish_count} bearish keywords"
    }

    print(f"[MOCK] analyze_tweet_sentiment_mock('{tweet_text[:50]}...')")
    print(f"[MOCK] Result: {sentiment} ({confidence:.0%} confidence)")

    return json.dumps(result)
