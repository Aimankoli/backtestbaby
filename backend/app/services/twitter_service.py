"""
Twitter/X Service

Real Twitter API integration using python-twitter library
Uses Bearer Token for read-only access to tweets
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pytwitter import Api
from app.config import X_BEARER_TOKEN


class TwitterService:
    """Service for interacting with Twitter/X API"""

    def __init__(self):
        """Initialize Twitter API client with bearer token"""
        self.api = None
        if X_BEARER_TOKEN:
            try:
                self.api = Api(bearer_token=X_BEARER_TOKEN)
                print("[TwitterService] ✓ Initialized with bearer token")
            except Exception as e:
                print(f"[TwitterService] ✗ Error initializing API: {e}")
        else:
            print("[TwitterService] ✗ WARNING: X_BEARER_TOKEN not set in .env")

    def is_available(self) -> bool:
        """Check if Twitter API is available"""
        return self.api is not None

    async def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get Twitter user info by username

        Args:
            username: Twitter username (without @)

        Returns:
            Dict with user_id, name, username or None
        """
        if not self.api:
            print("[TwitterService] API not initialized")
            return None

        try:
            username = username.lstrip("@")
            print(f"[TwitterService] Looking up user: @{username}")

            response = self.api.get_user(username=username)

            if response and response.data:
                user_data = {
                    "user_id": response.data.id,
                    "name": response.data.name,
                    "username": response.data.username
                }
                print(f"[TwitterService] ✓ Found @{username} (ID: {user_data['user_id']})")
                return user_data
            else:
                print(f"[TwitterService] ✗ User @{username} not found")
                return None

        except Exception as e:
            print(f"[TwitterService] ✗ Error getting user @{username}: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def get_recent_tweets(
        self,
        username: str,
        since_id: Optional[str] = None,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get recent tweets from a user using their timeline

        Args:
            username: Twitter username (without @)
            since_id: Only return tweets after this tweet ID
            max_results: Maximum number of tweets (5-100)

        Returns:
            List of tweet dictionaries with id, text, created_at
        """
        if not self.api:
            print("[TwitterService] API not initialized")
            return []

        try:
            # First get user info to get user_id
            user_data = await self.get_user_by_username(username)
            if not user_data:
                return []

            user_id = user_data["user_id"]
            print(f"[TwitterService] Fetching tweets for @{username} (ID: {user_id})")

            # Build parameters for get_timelines
            params = {
                "user_id": user_id,
                "max_results": min(max(max_results, 5), 100),
                "tweet_fields": ["id", "text", "created_at", "author_id"],
                "exclude": ["retweets", "replies"]  # Only original tweets
            }

            if since_id:
                params["since_id"] = since_id
                print(f"[TwitterService] Getting tweets since ID: {since_id}")

            # Get user timeline
            response = self.api.get_timelines(**params)

            tweets = []
            if response and response.data:
                for tweet in response.data:
                    tweet_dict = {
                        "id": tweet.id,
                        "text": tweet.text,
                        "created_at": tweet.created_at if hasattr(tweet, 'created_at') else None,
                        "author_id": tweet.author_id if hasattr(tweet, 'author_id') else user_id
                    }
                    tweets.append(tweet_dict)

                print(f"[TwitterService] ✓ Found {len(tweets)} tweets from @{username}")
            else:
                print(f"[TwitterService] No tweets found for @{username}")

            return tweets

        except Exception as e:
            print(f"[TwitterService] ✗ Error fetching tweets for @{username}: {e}")
            import traceback
            traceback.print_exc()
            return []

    async def get_latest_tweet(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get the most recent tweet from a user

        Args:
            username: Twitter username (without @)

        Returns:
            Tweet dictionary or None
        """
        tweets = await self.get_recent_tweets(username, max_results=1)
        return tweets[0] if tweets else None

    async def check_for_new_tweets(
        self,
        username: str,
        last_checked_at: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Check for new tweets since last check using created_at timestamp

        Args:
            username: Twitter username (without @)
            last_checked_at: DateTime of last check

        Returns:
            List of new tweets (empty if none)
        """
        tweets = await self.get_recent_tweets(username, max_results=10)

        if not tweets or not last_checked_at:
            return tweets

        # Filter tweets created after last check
        new_tweets = []
        for tweet in tweets:
            if tweet.get("created_at"):
                # Parse created_at (Twitter returns ISO format string)
                try:
                    tweet_time = datetime.fromisoformat(tweet["created_at"].replace("Z", "+00:00"))
                    if tweet_time > last_checked_at:
                        new_tweets.append(tweet)
                except Exception as e:
                    print(f"[TwitterService] Error parsing created_at: {e}")
                    continue

        if new_tweets:
            print(f"[TwitterService] ✓ Found {len(new_tweets)} new tweets from @{username}")
        else:
            print(f"[TwitterService] No new tweets from @{username} since {last_checked_at}")

        return new_tweets


# Global Twitter service instance
twitter_service = TwitterService()
