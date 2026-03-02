"""Reddit AI-related subreddit trend collector.

Works without API keys using the public JSON endpoints.
"""

from __future__ import annotations

from socialmonitor.utils.http import fetch_json

AI_SUBREDDITS = [
    "artificial",
    "MachineLearning",
    "LocalLLaMA",
    "ChatGPT",
    "singularity",
    "StableDiffusion",
]

SUBREDDIT_URL = "https://www.reddit.com/r/{sub}/hot.json?limit=10"
MAX_ITEMS = 30


async def fetch_trends() -> list[dict]:
    """Return trending posts from AI-related subreddits."""
    results: list[dict] = []

    for sub in AI_SUBREDDITS:
        try:
            data = await fetch_json(
                SUBREDDIT_URL.format(sub=sub),
                headers={"User-Agent": "SocialMonitor/0.1"},
            )
            posts = data.get("data", {}).get("children", [])
            for post in posts:
                pd = post.get("data", {})
                if pd.get("stickied"):
                    continue
                results.append(
                    {
                        "title": pd.get("title", ""),
                        "url": f"https://reddit.com{pd.get('permalink', '')}",
                        "score": pd.get("score", 0),
                        "category": "ai",
                        "meta": {
                            "subreddit": sub,
                            "author": pd.get("author", ""),
                            "comments": pd.get("num_comments", 0),
                            "upvote_ratio": pd.get("upvote_ratio", 0),
                        },
                    }
                )
        except Exception:
            continue

    # Sort by score descending and trim
    results.sort(key=lambda x: x.get("score", 0), reverse=True)
    return results[:MAX_ITEMS]
