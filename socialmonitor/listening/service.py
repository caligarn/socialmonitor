"""Orchestrates social listening across Instagram, TikTok, and YouTube Shorts."""

from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy.orm import Session

from socialmonitor.db.models import Mention
from socialmonitor.listening.sources import instagram, tiktok, youtube_shorts


class SocialListeningService:
    """Collect and query social mentions from short-form video platforms."""

    def __init__(self, session: Session) -> None:
        self.session = session

    async def collect_all(self, keywords: list[str] | None = None) -> list[Mention]:
        """Fetch mentions from all platforms and persist them."""
        saved: list[Mention] = []

        collectors = [
            ("instagram", instagram.fetch_mentions),
            ("tiktok", tiktok.fetch_mentions),
            ("youtube_shorts", youtube_shorts.fetch_mentions),
        ]

        for platform, fetch_fn in collectors:
            try:
                raw_items = await fetch_fn(keywords)
                for item in raw_items:
                    mention = self._save_mention(item)
                    saved.append(mention)
            except Exception as exc:
                print(f"[listening] {platform} collection failed: {exc}")

        return saved

    async def collect_platform(
        self, platform: str, keywords: list[str] | None = None
    ) -> list[Mention]:
        """Collect mentions from a single platform."""
        fetch_map = {
            "instagram": instagram.fetch_mentions,
            "tiktok": tiktok.fetch_mentions,
            "youtube_shorts": youtube_shorts.fetch_mentions,
        }
        fetch_fn = fetch_map.get(platform)
        if not fetch_fn:
            raise ValueError(f"Unknown listening platform: {platform}")

        raw_items = await fetch_fn(keywords)
        saved = [self._save_mention(item) for item in raw_items]
        return saved

    def _save_mention(self, item: dict) -> Mention:
        published_at = item.get("published_at")
        if isinstance(published_at, (int, float)):
            published_at = datetime.utcfromtimestamp(published_at)
        elif isinstance(published_at, str):
            try:
                published_at = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
            except ValueError:
                published_at = None

        mention = Mention(
            platform=item.get("platform", ""),
            author=item.get("author", ""),
            author_followers=item.get("author_followers"),
            content=item.get("content", ""),
            url=item.get("url", ""),
            keyword_matched=item.get("keyword_matched", ""),
            likes=item.get("likes"),
            comments=item.get("comments"),
            shares=item.get("shares"),
            views=item.get("views"),
            published_at=published_at,
            meta_json=json.dumps(item.get("meta", {})),
        )
        self.session.add(mention)
        self.session.commit()
        return mention

    def get_mentions(
        self,
        platform: str | None = None,
        keyword: str | None = None,
        limit: int = 50,
    ) -> list[Mention]:
        """Query stored mentions with optional filters."""
        q = self.session.query(Mention).order_by(Mention.captured_at.desc())
        if platform:
            q = q.filter(Mention.platform == platform)
        if keyword:
            q = q.filter(Mention.keyword_matched == keyword)
        return q.limit(limit).all()

    def get_top_mentions(self, limit: int = 20) -> list[Mention]:
        """Return mentions ranked by engagement (likes + comments + views)."""
        mentions = (
            self.session.query(Mention)
            .order_by(Mention.captured_at.desc())
            .limit(200)
            .all()
        )
        mentions.sort(
            key=lambda m: (m.views or 0) + (m.likes or 0) * 10 + (m.comments or 0) * 20,
            reverse=True,
        )
        return mentions[:limit]

    def get_platform_summary(self) -> list[dict]:
        """Return a count and engagement summary grouped by platform."""
        platforms = ["instagram", "tiktok", "youtube_shorts"]
        summary = []
        for plat in platforms:
            mentions = (
                self.session.query(Mention)
                .filter(Mention.platform == plat)
                .order_by(Mention.captured_at.desc())
                .limit(100)
                .all()
            )
            total_likes = sum(m.likes or 0 for m in mentions)
            total_views = sum(m.views or 0 for m in mentions)
            summary.append(
                {
                    "platform": plat,
                    "mention_count": len(mentions),
                    "total_likes": total_likes,
                    "total_views": total_views,
                }
            )
        return summary
