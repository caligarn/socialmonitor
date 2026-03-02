"""Tests for the analytics tracker."""

from socialmonitor.analytics.tracker import AnalyticsTracker


class TestAnalyticsTracker:
    def test_add_and_list_accounts(self, db_session):
        tracker = AnalyticsTracker(db_session)
        tracker.add_account("twitter", "@me", display_name="Me")
        tracker.add_account("youtube", "MyChannel")

        accounts = tracker.list_accounts()
        assert len(accounts) == 2

    def test_remove_account(self, db_session):
        tracker = AnalyticsTracker(db_session)
        acct = tracker.add_account("twitter", "@remove_me")
        assert tracker.remove_account(acct.id) is True
        assert len(tracker.list_accounts()) == 0

    def test_record_and_get_metrics(self, db_session):
        tracker = AnalyticsTracker(db_session)
        acct = tracker.add_account("twitter", "@metrics_test")

        tracker.record_metrics(acct.id, followers=100, engagement_rate=5.0)
        tracker.record_metrics(acct.id, followers=120, engagement_rate=4.5)

        history = tracker.get_metrics_history(acct.id)
        assert len(history) == 2
        # Most recent first
        assert history[0].followers == 120

    def test_growth_summary_no_data(self, db_session):
        tracker = AnalyticsTracker(db_session)
        acct = tracker.add_account("twitter", "@empty")
        summary = tracker.get_growth_summary(acct.id)
        assert summary["status"] == "no_data"

    def test_growth_summary_with_data(self, db_session):
        tracker = AnalyticsTracker(db_session)
        acct = tracker.add_account("twitter", "@growing")

        tracker.record_metrics(acct.id, followers=100, engagement_rate=5.0)
        tracker.record_metrics(acct.id, followers=150, engagement_rate=6.0)

        summary = tracker.get_growth_summary(acct.id)
        assert summary["status"] == "ok"
        assert summary["follower_growth"] == 50
        assert summary["avg_engagement_rate"] == 5.5
