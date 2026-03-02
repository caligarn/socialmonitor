"""YouTube AI-video trend collector.

Uses the YouTube Data API v3 when a key is configured; otherwise falls back
to parsing the RSS feeds of popular AI channels with xml.etree.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

from socialmonitor.config import settings
from socialmonitor.utils.http import fetch_json, fetch_text

# Popular AI YouTube channel IDs for RSS fallback
AI_CHANNEL_IDS = [
    "UCWN3xxRkmTPphYht914IwCw",  # Two Minute Papers
    "UCZHmQk67mSJgfCCTn7xBfew",  # Bycloud
    "UCXUPKJO5MZQN11PqgIvyuvQ",  # AI Explained
    "UCbfYPyITQ-7l4upoX8nvctg",  # Two Minute Papers
    "UCLXo7UDZvByw2ixzpQCufnA",  # Matt Wolfe
]

YOUTUBE_RSS = "https://www.youtube.com/feeds/videos.xml?channel_id={cid}"
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"

MAX_ITEMS = 30

# Atom namespace used by YouTube feeds
_NS = {"atom": "http://www.w3.org/2005/Atom", "media": "http://search.yahoo.com/mrss/"}


async def fetch_trends() -> list[dict]:
    """Return trending AI videos."""
    if settings.has_youtube:
        return await _fetch_via_api()
    return await _fetch_via_rss()


async def _fetch_via_api() -> list[dict]:
    params = {
        "part": "snippet",
        "q": "artificial intelligence OR LLM OR GPT OR AI news",
        "type": "video",
        "order": "viewCount",
        "publishedAfter": "",  # could add date filter
        "maxResults": MAX_ITEMS,
        "key": settings.youtube_api_key,
    }
    data = await fetch_json(YOUTUBE_SEARCH_URL, params=params)
    results: list[dict] = []
    for item in data.get("items", []):
        snippet = item.get("snippet", {})
        vid = item.get("id", {}).get("videoId", "")
        results.append(
            {
                "title": snippet.get("title", ""),
                "url": f"https://www.youtube.com/watch?v={vid}",
                "score": 0,
                "category": "ai",
                "meta": {
                    "channel": snippet.get("channelTitle", ""),
                    "published": snippet.get("publishedAt", ""),
                    "video_id": vid,
                },
            }
        )
    return results


async def _fetch_via_rss() -> list[dict]:
    """Parse Atom/RSS feeds using stdlib xml – no extra dependency required."""
    results: list[dict] = []
    for cid in AI_CHANNEL_IDS:
        try:
            xml_text = await fetch_text(YOUTUBE_RSS.format(cid=cid))
            root = ET.fromstring(xml_text)

            channel_title = ""
            title_el = root.find("atom:title", _NS)
            if title_el is not None and title_el.text:
                channel_title = title_el.text

            entries = root.findall("atom:entry", _NS)
            for entry in entries[:5]:
                title_el = entry.find("atom:title", _NS)
                link_el = entry.find("atom:link", _NS)
                pub_el = entry.find("atom:published", _NS)
                results.append(
                    {
                        "title": title_el.text if title_el is not None and title_el.text else "",
                        "url": link_el.get("href", "") if link_el is not None else "",
                        "score": 0,
                        "category": "ai",
                        "meta": {
                            "channel": channel_title,
                            "published": pub_el.text if pub_el is not None and pub_el.text else "",
                        },
                    }
                )
        except Exception:
            continue
    return results[:MAX_ITEMS]
