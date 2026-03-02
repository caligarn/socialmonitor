"""Hacker News front-page trend collector (no API key needed)."""

from __future__ import annotations

from socialmonitor.utils.http import fetch_json

TOP_STORIES_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{id}.json"
MAX_ITEMS = 30


async def fetch_trends() -> list[dict]:
    """Return the current top stories from Hacker News."""
    story_ids = await fetch_json(TOP_STORIES_URL)
    story_ids = story_ids[:MAX_ITEMS]

    results: list[dict] = []
    for sid in story_ids:
        try:
            item = await fetch_json(ITEM_URL.format(id=sid))
            if not item:
                continue
            results.append(
                {
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "score": item.get("score", 0),
                    "category": _categorise(item.get("title", "")),
                    "meta": {
                        "hn_id": sid,
                        "by": item.get("by", ""),
                        "comments": item.get("descendants", 0),
                    },
                }
            )
        except Exception:
            continue
    return results


AI_KEYWORDS = {
    "ai", "llm", "gpt", "claude", "openai", "anthropic", "gemini",
    "machine learning", "deep learning", "neural", "transformer",
    "diffusion", "stable diffusion", "midjourney", "chatgpt",
    "copilot", "langchain", "rag", "fine-tune", "fine-tuning",
    "embedding", "vector", "agent", "multimodal",
}


def _categorise(title: str) -> str:
    lower = title.lower()
    if any(kw in lower for kw in AI_KEYWORDS):
        return "ai"
    tech_keywords = {"python", "rust", "javascript", "linux", "open source", "github", "database", "api"}
    if any(kw in lower for kw in tech_keywords):
        return "tech"
    return "general"
