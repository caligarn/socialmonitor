"""Tests for the influencer tracker."""

from socialmonitor.influencers.tracker import InfluencerTracker


class TestInfluencerTracker:
    def test_seed_defaults(self, db_session):
        tracker = InfluencerTracker(db_session)
        count = tracker.seed_defaults()
        assert count > 0

        # Second call should not re-seed
        count2 = tracker.seed_defaults()
        assert count2 == 0

    def test_add_and_list(self, db_session):
        tracker = InfluencerTracker(db_session)
        tracker.add_influencer("Test Person", "@test", "twitter", category="creator")

        result = tracker.list_influencers()
        assert len(result) == 1
        assert result[0].name == "Test Person"

    def test_list_filter_by_platform(self, db_session):
        tracker = InfluencerTracker(db_session)
        tracker.add_influencer("Alice", "@alice", "twitter")
        tracker.add_influencer("Bob", "@bob", "youtube")

        twitter_only = tracker.list_influencers(platform="twitter")
        assert len(twitter_only) == 1
        assert twitter_only[0].name == "Alice"

    def test_remove_influencer(self, db_session):
        tracker = InfluencerTracker(db_session)
        inf = tracker.add_influencer("Remove Me", "@rm", "twitter")
        assert tracker.remove_influencer(inf.id) is True

        # Soft delete – should not appear in list
        result = tracker.list_influencers()
        assert len(result) == 0

    def test_record_activity(self, db_session):
        tracker = InfluencerTracker(db_session)
        inf = tracker.add_influencer("Active", "@active", "twitter")
        tracker.record_activity(inf.id, "post", "Big news!")

        activities = tracker.get_recent_activities(inf.id)
        assert len(activities) == 1
        assert activities[0].title == "Big news!"

    def test_leaderboard_without_metrics(self, db_session):
        tracker = InfluencerTracker(db_session)
        tracker.add_influencer("Person A", "@a", "twitter")
        tracker.add_influencer("Person B", "@b", "twitter")

        board = tracker.get_leaderboard()
        assert len(board) == 2
        # All followers should be None
        assert all(e["followers"] is None for e in board)

    def test_leaderboard_with_metrics(self, db_session):
        tracker = InfluencerTracker(db_session)
        a = tracker.add_influencer("Small", "@small", "twitter")
        b = tracker.add_influencer("Big", "@big", "twitter")

        tracker.record_metrics(a.id, followers=1000)
        tracker.record_metrics(b.id, followers=50000)

        board = tracker.get_leaderboard()
        assert board[0]["name"] == "Big"
        assert board[0]["followers"] == 50000
