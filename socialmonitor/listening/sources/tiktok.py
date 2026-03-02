"""TikTok social listening via RapidAPI.

Uses the ``tiktok-scraper7`` endpoint on RapidAPI to search for videos
matching configured keywords.  Falls back gracefully when no API key is
available.
"""

from __future__ import annotations

from socialmonitor.config import settings
from socialmonitor.utils.http import fetch_json

SEARCH_URL = "https://tiktok-scraper7.p.rapidapi.com/feed/search"
MAX_ITEMS = 30


async def fetch_mentions(keywords: list[str] | None = None) -> list[dict]:
    """Return recent TikTok videos matching *keywords*."""
    if not settings.has_rapidapi:
        return []

    keywords = keywords or settings.listening_keyword_list
    headers = {
        "x-rapidapi-key": settings.rapidapi_key,
        "x-rapidapi-host": "tiktok-scraper7.p.rapidapi.com",
    }

    results: list[dict] = []
    for kw in keywords:
        try:
            data = await fetch_json(
                SEARCH_URL,
                params={"keywords": kw, "region": "us", "count": "20"},
                headers=headers,
            )
            videos = data.get("data", {}).get("videos", [])
            for video in videos:
                author_info = video.get("author", {})
                stats = video.get("stats", {})
                results.append(
                    {
                        "platform": "tiktok",
                        "author": author_info.get("uniqueId", ""),
                        "author_followers": author_info.get("followerCount"),
                        "content": video.get("desc", ""),
                        "url": f"https://www.tiktok.com/@{author_info.get('uniqueId', '')}/video/{video.get('id', '')}",
                        "keyword_matched": kw,
                        "likes": stats.get("diggCount", 0),
                        "comments": stats.get("commentCount", 0),
                        "shares": stats.get("shareCount", 0),
                        "views": stats.get("playCount", 0),
                        "published_at": video.get("createTime"),
                        "meta": {
                            "video_id": video.get("id", ""),
                            "duration": video.get("duration"),
                            "music": video.get("music", {}).get("title", ""),
                        },
                    }
                )
        except Exception:
            continue

    results.sort(key=lambda x: x.get("views", 0), reverse=True)
    return results[:MAX_ITEMS]
