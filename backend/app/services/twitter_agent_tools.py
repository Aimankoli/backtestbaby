"""
Twitter/X Agent Tools
=====================
Advanced Twitter API tools for the research agent.

All tools use Twitter API v2 with bearer token authentication for read-only operations.
Tools focus on: trend discovery, sentiment analysis, competitive intelligence,
account monitoring, and viral content identification.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Optional, Literal
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# X API configuration
X_API_BASE = "https://api.x.com/2"
X_BEARER_TOKEN = os.getenv("X_BEARER_TOKEN")

if not X_BEARER_TOKEN:
    print("[WARNING] X_BEARER_TOKEN not found in environment variables. Twitter tools will not work.")


# ==============================================================================
# Helper Functions
# ==============================================================================

async def make_x_api_request(
    endpoint: str,
    params: dict | None = None,
) -> dict:
    """Make authenticated request to X API v2."""
    headers = {
        "Authorization": f"Bearer {X_BEARER_TOKEN}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{X_API_BASE}{endpoint}",
                headers=headers,
                params=params,
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return {
                "error": f"API Error: {e.response.status_code}",
                "message": e.response.text,
            }
        except Exception as e:
            return {"error": "Request failed", "message": str(e)}


def build_search_query(
    keywords: str,
    require_all: bool = False,
    exclude: str | None = None,
    hashtags: str | None = None,
    from_users: str | None = None,
    is_verified: bool = False,
    has_media: bool = False,
    language: str | None = None,
) -> str:
    """Build advanced search query with operators for X API."""
    query_parts = []

    # Keywords
    if require_all:
        terms = keywords.split()
        query_parts.append(" ".join(terms))
    else:
        terms = keywords.split()
        query_parts.append(f"({' OR '.join(terms)})")

    # Exclude terms
    if exclude:
        exclude_terms = exclude.split()
        for term in exclude_terms:
            query_parts.append(f"-{term}")

    # Hashtags
    if hashtags:
        tags = hashtags.split()
        query_parts.extend([f"#{tag.lstrip('#')}" for tag in tags])

    # From specific users
    if from_users:
        users = from_users.split(",")
        user_query = " OR ".join([f"from:{user.strip()}" for user in users])
        query_parts.append(f"({user_query})")

    # Verified accounts only
    if is_verified:
        query_parts.append("is:verified")

    # Media presence
    if has_media:
        query_parts.append("has:media")

    # Language
    if language:
        query_parts.append(f"lang:{language}")

    return " ".join(query_parts)


def calculate_engagement_rate(tweet_data: dict) -> float:
    """Calculate engagement rate for a tweet."""
    if "public_metrics" not in tweet_data:
        return 0.0

    metrics = tweet_data["public_metrics"]
    likes = metrics.get("like_count", 0)
    retweets = metrics.get("retweet_count", 0)
    replies = metrics.get("reply_count", 0)
    impressions = metrics.get("impression_count", 1)

    if impressions > 0:
        return ((likes + retweets + replies) / impressions) * 100
    return 0.0


def format_tweet_data(tweet: dict, include_metrics: bool = True) -> dict:
    """Format tweet data for readable output."""
    formatted = {
        "id": tweet.get("id"),
        "text": tweet.get("text"),
        "created_at": tweet.get("created_at"),
        "author_id": tweet.get("author_id"),
        "url": f"https://twitter.com/i/web/status/{tweet.get('id')}" if tweet.get("id") else None,
    }

    if include_metrics and "public_metrics" in tweet:
        metrics = tweet["public_metrics"]
        formatted["engagement"] = {
            "likes": metrics.get("like_count", 0),
            "retweets": metrics.get("retweet_count", 0),
            "replies": metrics.get("reply_count", 0),
            "quotes": metrics.get("quote_count", 0),
            "impressions": metrics.get("impression_count", 0),
            "engagement_rate": round(calculate_engagement_rate(tweet), 2),
        }

    return formatted


def format_user_data(user: dict) -> dict:
    """Format user data for readable output."""
    formatted = {
        "id": user.get("id"),
        "username": user.get("username"),
        "name": user.get("name"),
        "verified": user.get("verified", False),
        "description": user.get("description"),
        "url": f"https://twitter.com/{user.get('username')}" if user.get("username") else None,
    }

    if "public_metrics" in user:
        metrics = user["public_metrics"]
        formatted["metrics"] = {
            "followers": metrics.get("followers_count", 0),
            "following": metrics.get("following_count", 0),
            "tweets": metrics.get("tweet_count", 0),
            "listed": metrics.get("listed_count", 0),
        }

    if "created_at" in user:
        formatted["created_at"] = user["created_at"]

    return formatted


# ==============================================================================
# Twitter Agent Tools
# ==============================================================================

async def search_trending_tweets(
    query: str,
    min_likes: int = 100,
    min_retweets: int = 20,
    hours_ago: int = 24,
    max_results: int = 20,
    only_verified: bool = False,
    language: str = "en",
) -> str:
    """
    Find high-engagement tweets on any topic - perfect for discovering viral content,
    trending discussions, or monitoring market sentiment.

    Use cases:
    - Track breaking news in crypto/finance
    - Discover trending YC companies or startup discussions
    - Monitor sentiment around specific stocks/tokens
    - Find viral content in your niche

    Args:
        query: Search keywords (e.g., "YC companies", "bitcoin crash", "AI startups")
        min_likes: Minimum likes threshold (default: 100)
        min_retweets: Minimum retweets threshold (default: 20)
        hours_ago: How many hours back to search (default: 24, max: 168 for 7 days)
        max_results: Number of results to return (10-100, default: 20)
        only_verified: Only search tweets from verified accounts
        language: Language code (default: "en")

    Returns:
        JSON string with viral tweets, engagement metrics, and insights
    """
    try:
        # Build search query
        search_query = build_search_query(
            keywords=query,
            is_verified=only_verified,
            language=language,
        )

        # Calculate time window
        end_time = datetime.utcnow() - timedelta(seconds=30)
        start_time = end_time - timedelta(hours=min(hours_ago, 168))

        # API parameters
        params = {
            "query": search_query,
            "max_results": 100,
            "start_time": start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "end_time": end_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "tweet.fields": "created_at,public_metrics,author_id,lang,entities",
            "expansions": "author_id",
            "user.fields": "username,name,verified,public_metrics",
            "sort_order": "relevancy",
        }

        response = await make_x_api_request("/tweets/search/recent", params)

        if "error" in response:
            return json.dumps(response)

        tweets = response.get("data", [])
        users = {user["id"]: user for user in response.get("includes", {}).get("users", [])}

        # Format and filter tweets by engagement
        formatted_tweets = []
        total_engagement = 0

        for tweet in tweets:
            metrics = tweet.get("public_metrics", {})
            likes = metrics.get("like_count", 0)
            retweets = metrics.get("retweet_count", 0)

            if likes < min_likes or retweets < min_retweets:
                continue

            formatted_tweet = format_tweet_data(tweet)

            author_id = tweet.get("author_id")
            if author_id and author_id in users:
                formatted_tweet["author"] = {
                    "username": users[author_id].get("username"),
                    "name": users[author_id].get("name"),
                    "verified": users[author_id].get("verified", False),
                }

            formatted_tweets.append(formatted_tweet)

            if "engagement" in formatted_tweet:
                eng = formatted_tweet["engagement"]
                total_engagement += eng["likes"] + eng["retweets"] + eng["replies"]

        result = {
            "query": query,
            "time_range": f"Last {hours_ago} hours",
            "total_results": len(formatted_tweets),
            "total_engagement": total_engagement,
            "avg_engagement_per_tweet": round(total_engagement / len(formatted_tweets), 2) if formatted_tweets else 0,
            "tweets": formatted_tweets[:max_results],
            "filters_applied": {
                "min_likes": min_likes,
                "min_retweets": min_retweets,
                "verified_only": only_verified,
                "language": language,
            },
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e), "tool": "search_trending_tweets"})


async def analyze_user_profile(
    username: str,
    include_recent_tweets: bool = True,
    tweet_count: int = 10,
) -> str:
    """
    Deep dive into a Twitter user's profile - perfect for due diligence,
    competitive research, or understanding key voices in your industry.

    Use cases:
    - Research potential partners or influencers
    - Competitive intelligence on rival companies
    - Due diligence on startup founders
    - Track thought leaders in your space

    Args:
        username: Twitter username (without @)
        include_recent_tweets: Include recent tweets in analysis
        tweet_count: Number of recent tweets to analyze (max: 100)

    Returns:
        JSON string with comprehensive profile analysis with metrics, bio, and recent activity
    """
    try:
        user_params = {
            "user.fields": "created_at,description,public_metrics,verified,url,location",
        }

        user_response = await make_x_api_request(f"/users/by/username/{username}", user_params)

        if "error" in user_response:
            return json.dumps(user_response)

        user_data = user_response.get("data", {})
        formatted_user = format_user_data(user_data)

        result = {
            "profile": formatted_user,
            "analysis": {},
        }

        if include_recent_tweets and user_data.get("id"):
            tweet_params = {
                "max_results": min(tweet_count, 100),
                "tweet.fields": "created_at,public_metrics",
                "exclude": "retweets,replies",
            }

            tweets_response = await make_x_api_request(
                f"/users/{user_data['id']}/tweets",
                tweet_params,
            )

            if "data" in tweets_response:
                tweets = tweets_response["data"]
                formatted_tweets = [format_tweet_data(t) for t in tweets]

                total_engagement = sum(
                    t.get("engagement", {}).get("likes", 0) +
                    t.get("engagement", {}).get("retweets", 0) +
                    t.get("engagement", {}).get("replies", 0)
                    for t in formatted_tweets
                )

                avg_engagement = total_engagement / len(tweets) if tweets else 0

                result["recent_tweets"] = formatted_tweets
                result["analysis"] = {
                    "recent_tweet_count": len(tweets),
                    "total_recent_engagement": total_engagement,
                    "avg_engagement_per_tweet": round(avg_engagement, 2),
                    "most_engaging_tweet": max(formatted_tweets, key=lambda t: t.get("engagement", {}).get("likes", 0)) if formatted_tweets else None,
                }

        return json.dumps(result, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e), "tool": "analyze_user_profile"})


async def monitor_keywords(
    keywords: str,
    require_all_keywords: bool = False,
    exclude_terms: Optional[str] = None,
    hashtags: Optional[str] = None,
    from_accounts: Optional[str] = None,
    hours_ago: int = 24,
    max_results: int = 50,
    has_media: bool = False,
    language: str = "en",
) -> str:
    """
    Advanced keyword monitoring with complex query building - perfect for tracking
    market sentiment, news, or specific discussions across Twitter.

    Use cases:
    - Monitor mentions of your product or competitors
    - Track breaking news in specific sectors
    - Sentiment analysis on stocks/crypto
    - Research customer pain points

    Args:
        keywords: Keywords to monitor (space-separated)
        require_all_keywords: If True, all keywords must be present (AND). If False, any keyword matches (OR)
        exclude_terms: Terms to exclude from results (space-separated)
        hashtags: Specific hashtags to include (space-separated, without #)
        from_accounts: Only show tweets from these accounts (comma-separated usernames)
        hours_ago: How far back to search (max: 168 hours = 7 days)
        max_results: Number of results (10-100)
        has_media: Only show tweets with media (images/videos)
        language: Language code (default: "en")

    Returns:
        JSON string with tweets matching the monitoring criteria with metadata
    """
    try:
        search_query = build_search_query(
            keywords=keywords,
            require_all=require_all_keywords,
            exclude=exclude_terms,
            hashtags=hashtags,
            from_users=from_accounts,
            has_media=has_media,
            language=language,
        )

        end_time = datetime.utcnow() - timedelta(seconds=30)
        start_time = end_time - timedelta(hours=min(hours_ago, 168))

        params = {
            "query": search_query,
            "max_results": min(max_results, 100),
            "start_time": start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "end_time": end_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "tweet.fields": "created_at,public_metrics,author_id,entities",
            "expansions": "author_id",
            "user.fields": "username,name,verified",
        }

        response = await make_x_api_request("/tweets/search/recent", params)

        if "error" in response:
            return json.dumps(response)

        tweets = response.get("data", [])
        users = {user["id"]: user for user in response.get("includes", {}).get("users", [])}

        formatted_tweets = []
        for tweet in tweets:
            formatted_tweet = format_tweet_data(tweet)

            author_id = tweet.get("author_id")
            if author_id and author_id in users:
                formatted_tweet["author"] = {
                    "username": users[author_id].get("username"),
                    "name": users[author_id].get("name"),
                    "verified": users[author_id].get("verified", False),
                }

            formatted_tweets.append(formatted_tweet)

        result = {
            "query_built": search_query,
            "monitoring_config": {
                "keywords": keywords,
                "require_all": require_all_keywords,
                "exclude": exclude_terms,
                "hashtags": hashtags,
                "from_accounts": from_accounts,
                "time_range_hours": hours_ago,
            },
            "total_results": len(formatted_tweets),
            "tweets": formatted_tweets,
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e), "tool": "monitor_keywords"})


async def find_influential_accounts(
    topic: str,
    min_followers: int = 10000,
    max_results: int = 20,
    language: str = "en",
) -> str:
    """
    Find key voices and influencers in any niche - perfect for building networks,
    finding experts, or competitive intelligence.

    Use cases:
    - Discover crypto/trading influencers
    - Find startup ecosystem thought leaders
    - Identify potential partners or collaborators
    - Competitive intelligence on key players

    Args:
        topic: Topic or niche to search (e.g., "AI startups", "DeFi", "SaaS")
        min_followers: Minimum follower count threshold
        max_results: Number of influential accounts to return
        language: Language code (default: "en")

    Returns:
        JSON string with list of influential accounts with metrics and recent activity
    """
    try:
        search_query = build_search_query(
            keywords=topic,
            is_verified=True,
            language=language,
        )

        params = {
            "query": search_query,
            "max_results": 100,
            "tweet.fields": "author_id,created_at",
            "expansions": "author_id",
            "user.fields": "username,name,verified,public_metrics,description,created_at",
        }

        response = await make_x_api_request("/tweets/search/recent", params)

        if "error" in response:
            return json.dumps(response)

        users = response.get("includes", {}).get("users", [])

        influential_users = []
        for user in users:
            metrics = user.get("public_metrics", {})
            follower_count = metrics.get("followers_count", 0)

            if follower_count >= min_followers:
                formatted_user = format_user_data(user)
                formatted_user["relevance_score"] = follower_count
                influential_users.append(formatted_user)

        influential_users.sort(key=lambda u: u.get("metrics", {}).get("followers", 0), reverse=True)

        result = {
            "topic": topic,
            "filters": {
                "min_followers": min_followers,
                "language": language,
            },
            "total_found": len(influential_users),
            "influential_accounts": influential_users[:max_results],
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e), "tool": "find_influential_accounts"})


async def track_account_activity(
    username: str,
    tweet_count: int = 20,
    include_replies: bool = False,
    include_retweets: bool = False,
) -> str:
    """
    Monitor specific accounts' recent posts - perfect for following thought leaders,
    competitors, or staying updated on key voices.

    Use cases:
    - Track competitor announcements
    - Monitor thought leaders in your space
    - Follow breaking news from key accounts
    - Analyze posting patterns

    Args:
        username: Twitter username to track (without @)
        tweet_count: Number of recent tweets to fetch (max: 100)
        include_replies: Include replies in results
        include_retweets: Include retweets in results

    Returns:
        JSON string with recent tweets with engagement metrics and activity analysis
    """
    try:
        user_response = await make_x_api_request(f"/users/by/username/{username}")

        if "error" in user_response:
            return json.dumps(user_response)

        user_id = user_response.get("data", {}).get("id")
        if not user_id:
            return json.dumps({"error": "User not found"})

        exclude = []
        if not include_replies:
            exclude.append("replies")
        if not include_retweets:
            exclude.append("retweets")

        params = {
            "max_results": min(tweet_count, 100),
            "tweet.fields": "created_at,public_metrics,entities",
        }

        if exclude:
            params["exclude"] = ",".join(exclude)

        tweets_response = await make_x_api_request(f"/users/{user_id}/tweets", params)

        if "error" in tweets_response:
            return json.dumps(tweets_response)

        tweets = tweets_response.get("data", [])
        formatted_tweets = [format_tweet_data(t) for t in tweets]

        if formatted_tweets:
            total_engagement = sum(
                t.get("engagement", {}).get("likes", 0) +
                t.get("engagement", {}).get("retweets", 0)
                for t in formatted_tweets
            )

            avg_engagement = total_engagement / len(formatted_tweets)
            most_engaging = max(formatted_tweets, key=lambda t: t.get("engagement", {}).get("likes", 0))
        else:
            total_engagement = 0
            avg_engagement = 0
            most_engaging = None

        result = {
            "username": username,
            "tracking_config": {
                "tweet_count": tweet_count,
                "includes_replies": include_replies,
                "includes_retweets": include_retweets,
            },
            "total_tweets": len(formatted_tweets),
            "activity_analysis": {
                "total_engagement": total_engagement,
                "avg_engagement_per_tweet": round(avg_engagement, 2),
                "most_engaging_tweet": most_engaging,
            },
            "recent_tweets": formatted_tweets,
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e), "tool": "track_account_activity"})


async def research_hashtag(
    hashtag: str,
    hours_ago: int = 24,
    max_results: int = 50,
    min_engagement: int = 10,
    language: str = "en",
) -> str:
    """
    Deep dive on hashtag performance - perfect for marketing research,
    trend analysis, or discovering popular content.

    Use cases:
    - Analyze campaign hashtag performance
    - Discover trending topics in your niche
    - Research hashtag strategy
    - Find top content using specific hashtags

    Args:
        hashtag: Hashtag to research (with or without #)
        hours_ago: Time range to analyze (max: 168 hours)
        max_results: Number of top tweets to return
        min_engagement: Minimum total engagement (likes + retweets)
        language: Language code (default: "en")

    Returns:
        JSON string with hashtag analysis with top tweets and usage metrics
    """
    try:
        clean_hashtag = hashtag.lstrip("#")
        search_query = f"#{clean_hashtag} lang:{language}"

        end_time = datetime.utcnow() - timedelta(seconds=30)
        start_time = end_time - timedelta(hours=min(hours_ago, 168))

        params = {
            "query": search_query,
            "max_results": 100,
            "start_time": start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "end_time": end_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "tweet.fields": "created_at,public_metrics,author_id,entities",
            "expansions": "author_id",
            "user.fields": "username,name,verified,public_metrics",
        }

        response = await make_x_api_request("/tweets/search/recent", params)

        if "error" in response:
            return json.dumps(response)

        tweets = response.get("data", [])
        users = {user["id"]: user for user in response.get("includes", {}).get("users", [])}

        formatted_tweets = []
        total_usage = 0
        total_reach = 0

        for tweet in tweets:
            metrics = tweet.get("public_metrics", {})
            engagement = metrics.get("like_count", 0) + metrics.get("retweet_count", 0)

            if engagement >= min_engagement:
                formatted_tweet = format_tweet_data(tweet)

                author_id = tweet.get("author_id")
                if author_id and author_id in users:
                    user = users[author_id]
                    formatted_tweet["author"] = {
                        "username": user.get("username"),
                        "name": user.get("name"),
                        "verified": user.get("verified", False),
                        "followers": user.get("public_metrics", {}).get("followers_count", 0),
                    }
                    total_reach += user.get("public_metrics", {}).get("followers_count", 0)

                formatted_tweets.append(formatted_tweet)
                total_usage += 1

        formatted_tweets.sort(
            key=lambda t: t.get("engagement", {}).get("likes", 0) + t.get("engagement", {}).get("retweets", 0),
            reverse=True,
        )

        result = {
            "hashtag": f"#{clean_hashtag}",
            "time_range_hours": hours_ago,
            "analysis": {
                "total_tweets_found": total_usage,
                "potential_reach": total_reach,
                "top_tweet": formatted_tweets[0] if formatted_tweets else None,
            },
            "filters": {
                "min_engagement": min_engagement,
                "language": language,
            },
            "top_tweets": formatted_tweets[:max_results],
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e), "tool": "research_hashtag"})


async def compare_accounts(
    username1: str,
    username2: str,
    include_recent_performance: bool = True,
) -> str:
    """
    Side-by-side comparison of two Twitter accounts - perfect for competitive
    analysis, benchmarking, or choosing between influencers/partners.

    Use cases:
    - Compare your account vs competitors
    - Benchmark against industry leaders
    - Choose between potential partners
    - Analyze competitive positioning

    Args:
        username1: First Twitter username (without @)
        username2: Second Twitter username (without @)
        include_recent_performance: Include recent tweet performance analysis

    Returns:
        JSON string with detailed comparison of both accounts with metrics and insights
    """
    try:
        usernames = f"{username1},{username2}"

        params = {
            "user.fields": "created_at,description,public_metrics,verified,url",
        }

        users_response = await make_x_api_request(f"/users/by?usernames={usernames}", params)

        if "error" in users_response:
            return json.dumps(users_response)

        users_data = users_response.get("data", [])

        if len(users_data) < 2:
            return json.dumps({"error": "Could not find both users"})

        user1_data = next((u for u in users_data if u.get("username") == username1), None)
        user2_data = next((u for u in users_data if u.get("username") == username2), None)

        comparison = {
            "account1": format_user_data(user1_data) if user1_data else {},
            "account2": format_user_data(user2_data) if user2_data else {},
            "comparison_metrics": {},
        }

        if user1_data and user2_data:
            m1 = user1_data.get("public_metrics", {})
            m2 = user2_data.get("public_metrics", {})

            comparison["comparison_metrics"] = {
                "followers_difference": m1.get("followers_count", 0) - m2.get("followers_count", 0),
                "followers_leader": username1 if m1.get("followers_count", 0) > m2.get("followers_count", 0) else username2,
                "tweets_difference": m1.get("tweet_count", 0) - m2.get("tweet_count", 0),
                "engagement_potential_ratio": round(
                    m1.get("followers_count", 1) / m2.get("followers_count", 1), 2
                ),
            }

        if include_recent_performance and user1_data and user2_data:
            recent_perf = {}

            for user_data, username in [(user1_data, username1), (user2_data, username2)]:
                tweet_params = {
                    "max_results": 10,
                    "tweet.fields": "public_metrics",
                    "exclude": "retweets,replies",
                }

                tweets_resp = await make_x_api_request(
                    f"/users/{user_data['id']}/tweets",
                    tweet_params,
                )

                if "data" in tweets_resp:
                    tweets = tweets_resp["data"]
                    avg_likes = sum(t.get("public_metrics", {}).get("like_count", 0) for t in tweets) / len(tweets) if tweets else 0
                    avg_retweets = sum(t.get("public_metrics", {}).get("retweet_count", 0) for t in tweets) / len(tweets) if tweets else 0

                    recent_perf[username] = {
                        "avg_likes_per_tweet": round(avg_likes, 2),
                        "avg_retweets_per_tweet": round(avg_retweets, 2),
                    }

            comparison["recent_performance"] = recent_perf

        return json.dumps(comparison, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e), "tool": "compare_accounts"})


async def find_viral_content(
    category: Literal["crypto", "startups", "tech", "finance", "news", "general"] = "general",
    hours_ago: int = 24,
    min_likes: int = 1000,
    min_retweets: int = 200,
    max_results: int = 25,
    language: str = "en",
) -> str:
    """
    Discover breakout viral content - perfect for trend spotting, content strategy,
    or staying on top of what's happening in your industry.

    Use cases:
    - Identify trending topics before they peak
    - Content strategy inspiration
    - Market sentiment tracking
    - Competitive intelligence

    Args:
        category: Content category to focus on (crypto, startups, tech, finance, news, general)
        hours_ago: How far back to search (max: 168 hours)
        min_likes: Minimum likes threshold (higher = more viral)
        min_retweets: Minimum retweets threshold
        max_results: Number of viral posts to return
        language: Language code (default: "en")

    Returns:
        JSON string with viral content with engagement metrics and trend insights
    """
    try:
        category_keywords = {
            "crypto": "bitcoin OR ethereum OR crypto OR DeFi OR NFT",
            "startups": "startup OR founder OR YC OR venture OR funding",
            "tech": "AI OR tech OR software OR SaaS OR developer",
            "finance": "stocks OR trading OR market OR investing OR portfolio",
            "news": "breaking OR news OR alert OR update",
            "general": "",
        }

        query_base = category_keywords.get(category, "")

        if query_base:
            search_query = f"({query_base}) lang:{language}"
        else:
            search_query = f"lang:{language}"

        end_time = datetime.utcnow() - timedelta(seconds=30)
        start_time = end_time - timedelta(hours=min(hours_ago, 168))

        params = {
            "query": search_query,
            "max_results": 100,
            "start_time": start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "end_time": end_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "tweet.fields": "created_at,public_metrics,author_id",
            "expansions": "author_id",
            "user.fields": "username,name,verified,public_metrics",
            "sort_order": "relevancy",
        }

        response = await make_x_api_request("/tweets/search/recent", params)

        if "error" in response:
            return json.dumps(response)

        tweets = response.get("data", [])
        users = {user["id"]: user for user in response.get("includes", {}).get("users", [])}

        formatted_tweets = []
        for tweet in tweets:
            metrics = tweet.get("public_metrics", {})
            likes = metrics.get("like_count", 0)
            retweets = metrics.get("retweet_count", 0)

            if likes < min_likes or retweets < min_retweets:
                continue

            formatted_tweet = format_tweet_data(tweet)

            author_id = tweet.get("author_id")
            if author_id and author_id in users:
                user = users[author_id]
                formatted_tweet["author"] = {
                    "username": user.get("username"),
                    "name": user.get("name"),
                    "verified": user.get("verified", False),
                }

            formatted_tweets.append(formatted_tweet)

        result = {
            "category": category,
            "time_range_hours": hours_ago,
            "virality_thresholds": {
                "min_likes": min_likes,
                "min_retweets": min_retweets,
            },
            "total_viral_posts": len(formatted_tweets),
            "viral_content": formatted_tweets[:max_results],
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e), "tool": "find_viral_content"})


async def get_conversation_context(
    tweet_id: str,
) -> str:
    """
    Get full context of a tweet including the conversation thread - perfect
    for understanding discussions, debates, or news threads.

    Use cases:
    - Understand full context of viral tweets
    - Research discussions and debates
    - Analyze conversation threads
    - Get complete information from thread

    Args:
        tweet_id: The ID of the tweet to get context for

    Returns:
        JSON string with tweet with full context and conversation information
    """
    try:
        params = {
            "tweet.fields": "created_at,public_metrics,author_id,conversation_id,in_reply_to_user_id,referenced_tweets",
            "expansions": "author_id,in_reply_to_user_id,referenced_tweets.id",
            "user.fields": "username,name,verified",
        }

        response = await make_x_api_request(f"/tweets/{tweet_id}", params)

        if "error" in response:
            return json.dumps(response)

        tweet = response.get("data", {})
        includes = response.get("includes", {})

        formatted_tweet = format_tweet_data(tweet)

        users = {user["id"]: user for user in includes.get("users", [])}
        author_id = tweet.get("author_id")
        if author_id and author_id in users:
            formatted_tweet["author"] = format_user_data(users[author_id])

        referenced_tweets = includes.get("tweets", [])
        formatted_referenced = [format_tweet_data(t) for t in referenced_tweets]

        result = {
            "main_tweet": formatted_tweet,
            "conversation_id": tweet.get("conversation_id"),
            "referenced_tweets": formatted_referenced,
            "context": {
                "is_reply": "in_reply_to_user_id" in tweet,
                "reply_to": tweet.get("in_reply_to_user_id"),
                "reference_count": len(formatted_referenced),
            },
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e), "tool": "get_conversation_context"})
