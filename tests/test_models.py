"""Tests for database models and basic operations."""

from datetime import datetime

from socialmonitor.db.models import (
    ContentPlan,
    GeneratedContent,
    Influencer,
    InfluencerActivity,
    SocialAccount,
    AccountMetric,
    TrendItem,
    TrendSnapshot,
)


class TestTrendModels:
    def test_create_snapshot_with_items(self, db_session):
        snapshot = TrendSnapshot(platform="hackernews", captured_at=datetime.utcnow())
        db_session.add(snapshot)
        db_session.flush()

        item = TrendItem(
            snapshot_id=snapshot.id,
            rank=1,
            title="Test Trend",
            url="https://example.com",
            score=42.0,
            category="ai",
        )
        db_session.add(item)
        db_session.commit()

        assert snapshot.id is not None
        assert len(snapshot.items) == 1
        assert snapshot.items[0].title == "Test Trend"

    def test_cascade_delete(self, db_session):
        snapshot = TrendSnapshot(platform="reddit_ai")
        db_session.add(snapshot)
        db_session.flush()

        db_session.add(TrendItem(snapshot_id=snapshot.id, rank=1, title="Item 1"))
        db_session.add(TrendItem(snapshot_id=snapshot.id, rank=2, title="Item 2"))
        db_session.commit()

        db_session.delete(snapshot)
        db_session.commit()

        assert db_session.query(TrendItem).count() == 0


class TestSocialAccountModels:
    def test_create_account_with_metrics(self, db_session):
        account = SocialAccount(platform="twitter", handle="@testuser")
        db_session.add(account)
        db_session.flush()

        metric = AccountMetric(
            account_id=account.id,
            followers=1000,
            engagement_rate=3.5,
        )
        db_session.add(metric)
        db_session.commit()

        assert account.id is not None
        assert len(account.metrics) == 1
        assert account.metrics[0].followers == 1000


class TestInfluencerModels:
    def test_create_influencer_with_activity(self, db_session):
        inf = Influencer(
            name="Test Person",
            handle="@test",
            platform="twitter",
            category="researcher",
        )
        db_session.add(inf)
        db_session.flush()

        activity = InfluencerActivity(
            influencer_id=inf.id,
            content_type="post",
            title="Big announcement",
        )
        db_session.add(activity)
        db_session.commit()

        assert inf.id is not None
        assert len(inf.activities) == 1

    def test_influencer_defaults(self, db_session):
        inf = Influencer(name="New Person", handle="@new", platform="youtube")
        db_session.add(inf)
        db_session.commit()

        assert inf.is_active is True
        assert inf.added_at is not None


class TestContentModels:
    def test_create_plan_with_generated_content(self, db_session):
        plan = ContentPlan(
            title="AI Trends Recap",
            platform="twitter",
            content_type="thread",
            topic="Weekly AI trends",
        )
        db_session.add(plan)
        db_session.flush()

        gen = GeneratedContent(
            plan_id=plan.id,
            version=1,
            body="Here are this week's top AI developments...",
            model_used="claude-sonnet-4-6",
        )
        db_session.add(gen)
        db_session.commit()

        assert plan.id is not None
        assert len(plan.generated_contents) == 1
        assert plan.generated_contents[0].is_selected is False

    def test_plan_defaults(self, db_session):
        plan = ContentPlan(title="Draft Post")
        db_session.add(plan)
        db_session.commit()

        assert plan.status == "draft"
        assert plan.created_at is not None
