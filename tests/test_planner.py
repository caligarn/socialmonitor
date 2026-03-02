"""Tests for the content planner."""

from datetime import datetime, timedelta

from socialmonitor.content.planner import ContentPlanner


class TestContentPlanner:
    def test_create_and_list_plans(self, db_session):
        planner = ContentPlanner(db_session)
        planner.create_plan("Post about AI", platform="twitter")
        planner.create_plan("Video script", platform="youtube", content_type="video_script")

        plans = planner.list_plans()
        assert len(plans) == 2

    def test_filter_by_status(self, db_session):
        planner = ContentPlanner(db_session)
        plan = planner.create_plan("Draft one")
        planner.update_plan(plan.id, status="scheduled")
        planner.create_plan("Still draft")

        drafts = planner.list_plans(status="draft")
        assert len(drafts) == 1
        assert drafts[0].title == "Still draft"

    def test_update_plan(self, db_session):
        planner = ContentPlanner(db_session)
        plan = planner.create_plan("Original Title")

        updated = planner.update_plan(plan.id, title="New Title", status="scheduled")
        assert updated is not None
        assert updated.title == "New Title"
        assert updated.status == "scheduled"

    def test_delete_plan(self, db_session):
        planner = ContentPlanner(db_session)
        plan = planner.create_plan("Delete me")
        assert planner.delete_plan(plan.id) is True
        assert planner.get_plan(plan.id) is None

    def test_get_upcoming(self, db_session):
        planner = ContentPlanner(db_session)

        future = datetime.utcnow() + timedelta(days=1)
        past = datetime.utcnow() - timedelta(days=1)

        planner.create_plan("Future plan", scheduled_for=future)
        planner.create_plan("Past plan", scheduled_for=past)

        upcoming = planner.get_upcoming()
        assert len(upcoming) == 1
        assert upcoming[0].title == "Future plan"
