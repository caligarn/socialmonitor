"""Orchestrates trend collection across all configured platforms."""

from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy.orm import Session

from socialmonitor.db.models import TrendItem, TrendSnapshot
from socialmonitor.trends.sources import hackernews, reddit, youtube


class TrendCollector:
    """Collect and store trending topics from multiple platforms."""

    def __init__(self, session: Session) -> None:
        self.session = session

    async def collect_all(self) -> list[TrendSnapshot]:
        """Run all available collectors and persist results."""
        snapshots: list[TrendSnapshot] = []

        collectors = [
            ("hackernews", hackernews.fetch_trends),
            ("reddit_ai", reddit.fetch_trends),
            ("youtube", youtube.fetch_trends),
        ]

        for platform, fetch_fn in collectors:
            try:
                items = await fetch_fn()
                snapshot = self._save(platform, items)
                snapshots.append(snapshot)
            except Exception as exc:
                # Log but don't crash – other sources may still work
                print(f"[trends] {platform} collection failed: {exc}")

        return snapshots

    async def collect_platform(self, platform: str) -> TrendSnapshot | None:
        """Collect trends for a single platform."""
        fetch_map = {
            "hackernews": hackernews.fetch_trends,
            "reddit_ai": reddit.fetch_trends,
            "youtube": youtube.fetch_trends,
        }
        fetch_fn = fetch_map.get(platform)
        if not fetch_fn:
            raise ValueError(f"Unknown platform: {platform}")
        items = await fetch_fn()
        return self._save(platform, items)

    def _save(self, platform: str, raw_items: list[dict]) -> TrendSnapshot:
        snapshot = TrendSnapshot(platform=platform, captured_at=datetime.utcnow())
        self.session.add(snapshot)
        self.session.flush()  # get snapshot.id

        for idx, item in enumerate(raw_items, 1):
            trend = TrendItem(
                snapshot_id=snapshot.id,
                rank=idx,
                title=item.get("title", ""),
                url=item.get("url", ""),
                score=item.get("score"),
                category=item.get("category", "general"),
                meta_json=json.dumps(item.get("meta", {})),
            )
            self.session.add(trend)

        self.session.commit()
        return snapshot

    def get_latest(self, platform: str | None = None, limit: int = 30) -> list[TrendItem]:
        """Return the most recent trend items, optionally filtered by platform."""
        query = (
            self.session.query(TrendItem)
            .join(TrendSnapshot)
            .order_by(TrendSnapshot.captured_at.desc(), TrendItem.rank)
        )
        if platform:
            query = query.filter(TrendSnapshot.platform == platform)
        return query.limit(limit).all()
