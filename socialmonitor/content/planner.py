"""Content planning – create and manage a content calendar."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from socialmonitor.db.models import ContentPlan


class ContentPlanner:
    """CRUD + query operations for the content calendar."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create_plan(
        self,
        title: str,
        platform: str = "",
        content_type: str = "post",
        topic: str = "",
        notes: str = "",
        scheduled_for: datetime | None = None,
    ) -> ContentPlan:
        plan = ContentPlan(
            title=title,
            platform=platform,
            content_type=content_type,
            topic=topic,
            notes=notes,
            scheduled_for=scheduled_for,
            status="draft",
        )
        self.session.add(plan)
        self.session.commit()
        return plan

    def list_plans(
        self,
        status: str | None = None,
        platform: str | None = None,
        limit: int = 50,
    ) -> list[ContentPlan]:
        q = self.session.query(ContentPlan).order_by(ContentPlan.created_at.desc())
        if status:
            q = q.filter(ContentPlan.status == status)
        if platform:
            q = q.filter(ContentPlan.platform == platform)
        return q.limit(limit).all()

    def get_plan(self, plan_id: int) -> ContentPlan | None:
        return self.session.get(ContentPlan, plan_id)

    def update_plan(self, plan_id: int, **kwargs) -> ContentPlan | None:
        plan = self.get_plan(plan_id)
        if not plan:
            return None
        for key, value in kwargs.items():
            if hasattr(plan, key):
                setattr(plan, key, value)
        plan.updated_at = datetime.utcnow()
        self.session.commit()
        return plan

    def delete_plan(self, plan_id: int) -> bool:
        plan = self.get_plan(plan_id)
        if plan:
            self.session.delete(plan)
            self.session.commit()
            return True
        return False

    def get_upcoming(self, limit: int = 10) -> list[ContentPlan]:
        """Return plans scheduled in the future, soonest first."""
        now = datetime.utcnow()
        return (
            self.session.query(ContentPlan)
            .filter(ContentPlan.scheduled_for > now)
            .filter(ContentPlan.status.in_(["draft", "scheduled"]))
            .order_by(ContentPlan.scheduled_for)
            .limit(limit)
            .all()
        )
