"""Tests for the trend collector."""

from socialmonitor.trends.collector import TrendCollector
from socialmonitor.trends.sources.hackernews import _categorise


class TestTrendCollector:
    def test_save_and_get_latest(self, db_session):
        collector = TrendCollector(db_session)
        raw_items = [
            {"title": "GPT-5 Released", "url": "https://example.com/1", "score": 100, "category": "ai"},
            {"title": "New Python Release", "url": "https://example.com/2", "score": 80, "category": "tech"},
        ]
        snapshot = collector._save("hackernews", raw_items)

        assert snapshot.id is not None
        assert len(snapshot.items) == 2

        latest = collector.get_latest(platform="hackernews")
        assert len(latest) == 2
        assert latest[0].rank == 1

    def test_get_latest_no_data(self, db_session):
        collector = TrendCollector(db_session)
        assert collector.get_latest() == []

    def test_get_latest_filter_platform(self, db_session):
        collector = TrendCollector(db_session)
        collector._save("hackernews", [{"title": "HN Story", "score": 50}])
        collector._save("reddit_ai", [{"title": "Reddit Post", "score": 30}])

        hn = collector.get_latest(platform="hackernews")
        assert len(hn) == 1
        assert hn[0].title == "HN Story"


class TestCategorise:
    def test_ai_keywords(self):
        assert _categorise("New GPT-5 model released") == "ai"
        assert _categorise("Claude 4 is amazing") == "ai"
        assert _categorise("LLM fine-tuning guide") == "ai"

    def test_tech_keywords(self):
        assert _categorise("Python 3.14 released") == "tech"
        assert _categorise("New Linux kernel features") == "tech"

    def test_general(self):
        assert _categorise("Weather today is great") == "general"
