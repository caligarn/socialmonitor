"""Instagram social listening via RapidAPI.

Uses the ``instagram-scraper-api2`` endpoint on RapidAPI to search for
posts matching configured keywords.  Falls back gracefully when no API
key is available.
"""

from __future__ import annotations

from socialmonitor.config import settings
from socialmonitor.utils.http import fetch_json

SEARCH_URL = "https://instagram-scraper-api2.p.rapidapi.com/v1/hashtag"
MAX_ITEMS = 30


async def fetch_mentions(keywords: list[str] | None = None) -> list[dict]:
    """Return recent Instagram posts matching *keywords*."""
    if not settings.has_rapidapi:
        return []

    keywords = keywords or settings.listening_keyword_list
    headers = {
        "x-rapidapi-key": settings.rapidapi_key,
        "x-rapidapi-host": "instagram-scraper-api2.p.rapidapi.com",
    }

    results: list[dict] = []
    for kw in keywords:
        tag = kw.strip().replace(" ", "").lower()
        try:
            data = await fetch_json(
                SEARCH_URL,
                params={"hashtag": tag},
                headers=headers,
            )
            items = data.get("data", {}).get("items", [])
            for item in items:
                caption = item.get("caption", {})
                user = item.get("user", {})
                results.append(
                    {
                        "platform": "instagram",
                        "author": user.get("username", ""),
                        "author_followers": user.get("follower_count"),
                        "content": caption.get("text", "") if isinstance(caption, dict) else str(caption),
                        "url": f"https://www.instagram.com/p/{item.get('code', '')}/",
                        "keyword_matched": kw,
                        "likes": item.get("like_count", 0),
                        "comments": item.get("comment_count", 0),
                        "views": item.get("view_count"),
                        "published_at": item.get("taken_at"),
                        "meta": {
                            "media_type": item.get("media_type"),
                            "shortcode": item.get("code", ""),
                        },
                    }
                )
        except Exception:
            continue

    results.sort(key=lambda x: x.get("likes", 0), reverse=True)
    return results[:MAX_ITEMS]
