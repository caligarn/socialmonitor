"""Track top AI influencers and their activities."""

from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy.orm import Session

from socialmonitor.db.models import Influencer, InfluencerActivity, InfluencerMetric


# Pre-seeded list of well-known AI influencers
DEFAULT_INFLUENCERS = [
    {"name": "Andrej Karpathy", "handle": "@karpathy", "platform": "twitter", "category": "researcher", "bio": "Former Tesla AI Director, OpenAI founding member, AI educator"},
    {"name": "Jim Fan", "handle": "@DrJimFan", "platform": "twitter", "category": "researcher", "bio": "NVIDIA Senior Research Manager, AI agent researcher"},
    {"name": "Yann LeCun", "handle": "@ylecun", "platform": "twitter", "category": "researcher", "bio": "Meta Chief AI Scientist, Turing Award winner"},
    {"name": "Demis Hassabis", "handle": "@demaborsa", "platform": "twitter", "category": "founder", "bio": "Google DeepMind CEO, Nobel Prize winner"},
    {"name": "Sam Altman", "handle": "@sama", "platform": "twitter", "category": "founder", "bio": "OpenAI CEO"},
    {"name": "Dario Amodei", "handle": "@DarioAmodei", "platform": "twitter", "category": "founder", "bio": "Anthropic CEO"},
    {"name": "Emad Mostaque", "handle": "@EMostaque", "platform": "twitter", "category": "founder", "bio": "Former Stability AI CEO"},
    {"name": "Harrison Chase", "handle": "@hwchase17", "platform": "twitter", "category": "founder", "bio": "LangChain creator and CEO"},
    {"name": "Simon Willison", "handle": "@simonw", "platform": "twitter", "category": "creator", "bio": "AI tools builder, Datasette creator, prolific AI blogger"},
    {"name": "Swyx", "handle": "@swyx", "platform": "twitter", "category": "creator", "bio": "AI engineer, Latent Space podcast host"},
    {"name": "Elvis Saravia", "handle": "@oaboromelvis", "platform": "twitter", "category": "creator", "bio": "Prompt Engineering Guide creator, AI researcher"},
    {"name": "Matt Shumer", "handle": "@mattshumer_", "platform": "twitter", "category": "founder", "bio": "HyperWrite CEO, AI agent builder"},
    {"name": "Matt Wolfe", "handle": "@maborattaborwolfe", "platform": "youtube", "category": "creator", "bio": "AI news YouTuber, FutureTools.io curator"},
    {"name": "Yannic Kilcher", "handle": "@yaborkilcher", "platform": "youtube", "category": "creator", "bio": "AI paper explainer, ML educator"},
    {"name": "Fireship", "handle": "@Fireship", "platform": "youtube", "category": "creator", "bio": "Fast-paced tech and AI explainer"},
]


class InfluencerTracker:
    """Manage and track AI influencers."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def seed_defaults(self) -> int:
        """Add default influencers if the table is empty. Returns count added."""
        existing = self.session.query(Influencer).count()
        if existing > 0:
            return 0

        added = 0
        for inf in DEFAULT_INFLUENCERS:
            self.session.add(
                Influencer(
                    name=inf["name"],
                    handle=inf["handle"],
                    platform=inf["platform"],
                    category=inf["category"],
                    bio=inf["bio"],
                )
            )
            added += 1
        self.session.commit()
        return added

    # ---- CRUD ----------------------------------------------------------------

    def add_influencer(
        self,
        name: str,
        handle: str,
        platform: str,
        category: str = "creator",
        bio: str = "",
        profile_url: str = "",
    ) -> Influencer:
        inf = Influencer(
            name=name,
            handle=handle,
            platform=platform,
            category=category,
            bio=bio,
            profile_url=profile_url,
        )
        self.session.add(inf)
        self.session.commit()
        return inf

    def list_influencers(
        self, platform: str | None = None, category: str | None = None
    ) -> list[Influencer]:
        q = self.session.query(Influencer).filter(Influencer.is_active.is_(True))
        if platform:
            q = q.filter(Influencer.platform == platform)
        if category:
            q = q.filter(Influencer.category == category)
        return q.order_by(Influencer.name).all()

    def remove_influencer(self, influencer_id: int) -> bool:
        inf = self.session.get(Influencer, influencer_id)
        if inf:
            inf.is_active = False
            self.session.commit()
            return True
        return False

    # ---- Activity tracking ---------------------------------------------------

    def record_activity(
        self,
        influencer_id: int,
        content_type: str,
        title: str,
        url: str = "",
        summary: str = "",
        published_at: datetime | None = None,
        engagement_score: float | None = None,
        meta: dict | None = None,
    ) -> InfluencerActivity:
        activity = InfluencerActivity(
            influencer_id=influencer_id,
            content_type=content_type,
            title=title,
            url=url,
            summary=summary,
            published_at=published_at or datetime.utcnow(),
            engagement_score=engagement_score,
            meta_json=json.dumps(meta or {}),
        )
        self.session.add(activity)
        self.session.commit()
        return activity

    def get_recent_activities(
        self,
        influencer_id: int | None = None,
        limit: int = 50,
    ) -> list[InfluencerActivity]:
        q = self.session.query(InfluencerActivity).order_by(
            InfluencerActivity.captured_at.desc()
        )
        if influencer_id is not None:
            q = q.filter(InfluencerActivity.influencer_id == influencer_id)
        return q.limit(limit).all()

    # ---- Metrics -------------------------------------------------------------

    def record_metrics(
        self,
        influencer_id: int,
        followers: int | None = None,
        engagement_rate: float | None = None,
        meta: dict | None = None,
    ) -> InfluencerMetric:
        metric = InfluencerMetric(
            influencer_id=influencer_id,
            followers=followers,
            engagement_rate=engagement_rate,
            meta_json=json.dumps(meta or {}),
        )
        self.session.add(metric)
        self.session.commit()
        return metric

    def get_leaderboard(self, limit: int = 20) -> list[dict]:
        """Return influencers ranked by latest follower count."""
        influencers = (
            self.session.query(Influencer)
            .filter(Influencer.is_active.is_(True))
            .all()
        )
        ranked = []
        for inf in influencers:
            latest_metric = (
                self.session.query(InfluencerMetric)
                .filter(InfluencerMetric.influencer_id == inf.id)
                .order_by(InfluencerMetric.captured_at.desc())
                .first()
            )
            ranked.append(
                {
                    "id": inf.id,
                    "name": inf.name,
                    "handle": inf.handle,
                    "platform": inf.platform,
                    "category": inf.category,
                    "followers": latest_metric.followers if latest_metric else None,
                    "engagement_rate": latest_metric.engagement_rate if latest_metric else None,
                }
            )
        # Sort: those with follower data first, then by follower count
        ranked.sort(key=lambda x: (x["followers"] is not None, x["followers"] or 0), reverse=True)
        return ranked[:limit]
