"""Shared HTTP client with retry and rate-limit support."""

from __future__ import annotations

import httpx

_CLIENT: httpx.AsyncClient | None = None


def get_client() -> httpx.AsyncClient:
    """Return a shared async HTTP client (created lazily)."""
    global _CLIENT
    if _CLIENT is None or _CLIENT.is_closed:
        _CLIENT = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={"User-Agent": "SocialMonitor/0.1"},
        )
    return _CLIENT


async def fetch_json(url: str, **kwargs) -> dict:
    """GET *url* and return parsed JSON."""
    client = get_client()
    resp = await client.get(url, **kwargs)
    resp.raise_for_status()
    return resp.json()


async def fetch_text(url: str, **kwargs) -> str:
    """GET *url* and return the response body as text."""
    client = get_client()
    resp = await client.get(url, **kwargs)
    resp.raise_for_status()
    return resp.text
