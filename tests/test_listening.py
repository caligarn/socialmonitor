"""Tests for the social listening service."""

from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from socialmonitor.db.models import Mention
from socialmonitor.listening.service import SocialListeningService


class TestSocialListeningService:
    def test_save_mention(self, db_session):
        svc = SocialListeningService(db_session)
        mention = svc._save_mention(
            {
                "platform": "tiktok",
                "author": "testuser",
                "author_followers": 50000,
                "content": "Check out this AI tool!",
                "url": "https://tiktok.com/@testuser/video/123",
                "keyword_matched": "AI",
                "likes": 1200,
                "comments": 45,
                "shares": 89,
                "views": 25000,
                "published_at": 1700000000,
                "meta": {"video_id": "123"},
            }
        )

        assert mention.id is not None
        assert mention.platform == "tiktok"
        assert mention.author == "testuser"
        assert mention.likes == 1200
        assert mention.views == 25000
        assert mention.keyword_matched == "AI"
        assert mention.published_at is not None

    def test_save_mention_iso_date(self, db_session):
        svc = SocialListeningService(db_session)
        mention = svc._save_mention(
            {
                "platform": "youtube_shorts",
                "author": "channel1",
                "content": "AI news",
                "url": "https://youtube.com/shorts/abc",
                "keyword_matched": "AI",
                "published_at": "2024-01-15T10:30:00Z",
            }
        )
        assert mention.published_at is not None

    def test_save_mention_no_date(self, db_session):
        svc = SocialListeningService(db_session)
        mention = svc._save_mention(
            {
                "platform": "instagram",
                "author": "iguser",
                "content": "ML post",
                "keyword_matched": "machine learning",
            }
        )
        assert mention.published_at is None
        assert mention.platform == "instagram"

    def test_get_mentions_empty(self, db_session):
        svc = SocialListeningService(db_session)
        assert svc.get_mentions() == []

    def test_get_mentions_filtered(self, db_session):
        svc = SocialListeningService(db_session)
        svc._save_mention({"platform": "tiktok", "author": "a", "keyword_matched": "AI"})
        svc._save_mention({"platform": "instagram", "author": "b", "keyword_matched": "LLM"})
        svc._save_mention({"platform": "tiktok", "author": "c", "keyword_matched": "GPT"})

        tiktok_only = svc.get_mentions(platform="tiktok")
        assert len(tiktok_only) == 2
        assert all(m.platform == "tiktok" for m in tiktok_only)

        ai_only = svc.get_mentions(keyword="AI")
        assert len(ai_only) == 1
        assert ai_only[0].author == "a"

    def test_get_top_mentions(self, db_session):
        svc = SocialListeningService(db_session)
        svc._save_mention({"platform": "tiktok", "author": "low", "views": 100, "likes": 5})
        svc._save_mention({"platform": "tiktok", "author": "high", "views": 100000, "likes": 5000})
        svc._save_mention({"platform": "instagram", "author": "mid", "views": 1000, "likes": 200})

        top = svc.get_top_mentions(limit=2)
        assert len(top) == 2
        assert top[0].author == "high"

    def test_get_platform_summary(self, db_session):
        svc = SocialListeningService(db_session)
        svc._save_mention({"platform": "tiktok", "likes": 100, "views": 5000})
        svc._save_mention({"platform": "tiktok", "likes": 200, "views": 3000})
        svc._save_mention({"platform": "instagram", "likes": 50, "views": 1000})

        summary = svc.get_platform_summary()
        assert len(summary) == 3  # instagram, tiktok, youtube_shorts

        tiktok_entry = next(s for s in summary if s["platform"] == "tiktok")
        assert tiktok_entry["mention_count"] == 2
        assert tiktok_entry["total_likes"] == 300
        assert tiktok_entry["total_views"] == 8000

        yt_entry = next(s for s in summary if s["platform"] == "youtube_shorts")
        assert yt_entry["mention_count"] == 0

    @pytest.mark.asyncio
    async def test_collect_all(self, db_session):
        svc = SocialListeningService(db_session)
        mock_data = [
            {"platform": "instagram", "author": "user1", "keyword_matched": "AI", "likes": 10},
        ]

        with (
            patch("socialmonitor.listening.service.instagram.fetch_mentions", new_callable=AsyncMock, return_value=mock_data),
            patch("socialmonitor.listening.service.tiktok.fetch_mentions", new_callable=AsyncMock, return_value=[]),
            patch("socialmonitor.listening.service.youtube_shorts.fetch_mentions", new_callable=AsyncMock, return_value=[]),
        ):
            saved = await svc.collect_all()

        assert len(saved) == 1
        assert saved[0].platform == "instagram"

    @pytest.mark.asyncio
    async def test_collect_platform(self, db_session):
        svc = SocialListeningService(db_session)
        mock_data = [
            {"platform": "tiktok", "author": "tiktoker", "keyword_matched": "LLM", "views": 999},
        ]

        with patch("socialmonitor.listening.service.tiktok.fetch_mentions", new_callable=AsyncMock, return_value=mock_data):
            saved = await svc.collect_platform("tiktok")

        assert len(saved) == 1
        assert saved[0].author == "tiktoker"

    @pytest.mark.asyncio
    async def test_collect_platform_unknown(self, db_session):
        svc = SocialListeningService(db_session)
        with pytest.raises(ValueError, match="Unknown listening platform"):
            await svc.collect_platform("facebook")

    @pytest.mark.asyncio
    async def test_collect_all_handles_failure(self, db_session):
        svc = SocialListeningService(db_session)

        with (
            patch("socialmonitor.listening.service.instagram.fetch_mentions", new_callable=AsyncMock, side_effect=Exception("API down")),
            patch("socialmonitor.listening.service.tiktok.fetch_mentions", new_callable=AsyncMock, return_value=[{"platform": "tiktok", "author": "ok"}]),
            patch("socialmonitor.listening.service.youtube_shorts.fetch_mentions", new_callable=AsyncMock, return_value=[]),
        ):
            saved = await svc.collect_all()

        assert len(saved) == 1
        assert saved[0].platform == "tiktok"
