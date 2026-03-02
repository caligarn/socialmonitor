"""YouTube Shorts social listening.

When a YouTube Data API key is configured, searches for short-form videos
(``videoDuration=short``) via the official API.  Otherwise falls back to
a RapidAPI scraper endpoint.
"""

from __future__ import annotations

from socialmonitor.config import settings
from socialmonitor.utils.http import fetch_json

YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
RAPIDAPI_SEARCH_URL = "https://youtube-scraper2.p.rapidapi.com/search"
MAX_ITEMS = 30


async def fetch_mentions(keywords: list[str] | None = None) -> list[dict]:
    """Return recent YouTube Shorts matching *keywords*."""
    keywords = keywords or settings.listening_keyword_list

    if settings.has_youtube:
        return await _fetch_via_api(keywords)
    if settings.has_rapidapi:
        return await _fetch_via_rapidapi(keywords)
    return []


async def _fetch_via_api(keywords: list[str]) -> list[dict]:
    """Use the official YouTube Data API v3 with short-duration filter."""
    results: list[dict] = []
    for kw in keywords:
        try:
            data = await fetch_json(
                YOUTUBE_SEARCH_URL,
                params={
                    "part": "snippet",
                    "q": kw,
                    "type": "video",
                    "videoDuration": "short",
                    "order": "viewCount",
                    "maxResults": 10,
                    "key": settings.youtube_api_key,
                },
            )
            for item in data.get("items", []):
                snippet = item.get("snippet", {})
                vid = item.get("id", {}).get("videoId", "")
                results.append(
                    {
                        "platform": "youtube_shorts",
                        "author": snippet.get("channelTitle", ""),
                        "content": snippet.get("title", ""),
                        "url": f"https://www.youtube.com/shorts/{vid}",
                        "keyword_matched": kw,
                        "likes": 0,
                        "comments": 0,
                        "views": 0,
                        "published_at": snippet.get("publishedAt"),
                        "meta": {
                            "video_id": vid,
                            "channel_id": snippet.get("channelId", ""),
                            "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
                        },
                    }
                )
        except Exception:
            continue
    return results[:MAX_ITEMS]


async def _fetch_via_rapidapi(keywords: list[str]) -> list[dict]:
    """Fallback: use a RapidAPI YouTube scraper."""
    headers = {
        "x-rapidapi-key": settings.rapidapi_key,
        "x-rapidapi-host": "youtube-scraper2.p.rapidapi.com",
    }
    results: list[dict] = []
    for kw in keywords:
        try:
            data = await fetch_json(
                RAPIDAPI_SEARCH_URL,
                params={"query": f"{kw} #shorts", "type": "video"},
                headers=headers,
            )
            for item in data.get("videos", []):
                results.append(
                    {
                        "platform": "youtube_shorts",
                        "author": item.get("channel", {}).get("name", ""),
                        "content": item.get("title", ""),
                        "url": item.get("link", ""),
                        "keyword_matched": kw,
                        "likes": 0,
                        "comments": 0,
                        "views": item.get("viewCount", 0),
                        "published_at": item.get("publishedAt"),
                        "meta": {
                            "video_id": item.get("videoId", ""),
                            "duration": item.get("duration"),
                        },
                    }
                )
        except Exception:
            continue
    return results[:MAX_ITEMS]
