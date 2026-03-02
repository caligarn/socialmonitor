"""Track and analyse the user's own social media accounts."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from socialmonitor.db.models import AccountMetric, SocialAccount


class AnalyticsTracker:
    """Manage social accounts and their metrics."""

    def __init__(self, session: Session) -> None:
        self.session = session

    # ---- Account management --------------------------------------------------

    def add_account(
        self,
        platform: str,
        handle: str,
        display_name: str = "",
        profile_url: str = "",
    ) -> SocialAccount:
        """Register a social account for tracking."""
        account = SocialAccount(
            platform=platform,
            handle=handle,
            display_name=display_name,
            profile_url=profile_url,
        )
        self.session.add(account)
        self.session.commit()
        return account

    def list_accounts(self) -> list[SocialAccount]:
        return self.session.query(SocialAccount).order_by(SocialAccount.platform).all()

    def remove_account(self, account_id: int) -> bool:
        account = self.session.get(SocialAccount, account_id)
        if account:
            self.session.delete(account)
            self.session.commit()
            return True
        return False

    # ---- Metrics recording ---------------------------------------------------

    def record_metrics(
        self,
        account_id: int,
        *,
        followers: int | None = None,
        following: int | None = None,
        posts_count: int | None = None,
        engagement_rate: float | None = None,
        likes_recent: int | None = None,
        comments_recent: int | None = None,
        shares_recent: int | None = None,
        impressions_recent: int | None = None,
    ) -> AccountMetric:
        """Record a metrics snapshot for an account."""
        metric = AccountMetric(
            account_id=account_id,
            captured_at=datetime.utcnow(),
            followers=followers,
            following=following,
            posts_count=posts_count,
            engagement_rate=engagement_rate,
            likes_recent=likes_recent,
            comments_recent=comments_recent,
            shares_recent=shares_recent,
            impressions_recent=impressions_recent,
        )
        self.session.add(metric)
        self.session.commit()
        return metric

    def get_metrics_history(
        self, account_id: int, limit: int = 50
    ) -> list[AccountMetric]:
        """Return metrics for an account ordered by most recent first."""
        return (
            self.session.query(AccountMetric)
            .filter(AccountMetric.account_id == account_id)
            .order_by(AccountMetric.captured_at.desc())
            .limit(limit)
            .all()
        )

    def get_growth_summary(self, account_id: int) -> dict:
        """Compute follower growth and engagement trends."""
        metrics = self.get_metrics_history(account_id, limit=30)
        if not metrics:
            return {"status": "no_data"}

        latest = metrics[0]
        oldest = metrics[-1]

        follower_growth = 0
        if latest.followers is not None and oldest.followers is not None:
            follower_growth = latest.followers - oldest.followers

        avg_engagement = 0.0
        engagement_values = [m.engagement_rate for m in metrics if m.engagement_rate is not None]
        if engagement_values:
            avg_engagement = sum(engagement_values) / len(engagement_values)

        return {
            "status": "ok",
            "current_followers": latest.followers,
            "follower_growth": follower_growth,
            "data_points": len(metrics),
            "avg_engagement_rate": round(avg_engagement, 2),
            "latest_captured": latest.captured_at.isoformat() if latest.captured_at else None,
        }
