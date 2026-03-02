"""FastAPI application – serves as the web API for SocialMonitor.

Deployed on Vercel as a Python serverless function.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from socialmonitor.db import init_db
from socialmonitor.db.session import SessionLocal

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(title="SocialMonitor API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    """FastAPI dependency that yields a DB session."""
    init_db()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class AccountCreate(BaseModel):
    platform: str
    handle: str
    display_name: str = ""

class MetricsRecord(BaseModel):
    followers: int | None = None
    engagement_rate: float | None = None
    likes_recent: int | None = None
    comments_recent: int | None = None

class InfluencerCreate(BaseModel):
    name: str
    handle: str
    platform: str
    category: str = "creator"
    bio: str = ""

class PlanCreate(BaseModel):
    title: str
    platform: str = "twitter"
    content_type: str = "post"
    topic: str = ""
    notes: str = ""
    scheduled_for: str | None = None  # ISO date string

class PlanUpdate(BaseModel):
    title: str | None = None
    platform: str | None = None
    content_type: str | None = None
    topic: str | None = None
    notes: str | None = None
    status: str | None = None
    scheduled_for: str | None = None

class GenerateRequest(BaseModel):
    extra_context: str = ""

class AutoGenerateRequest(BaseModel):
    platform: str = "twitter"
    content_type: str = "post"


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/api/health")
def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Trends
# ---------------------------------------------------------------------------

@app.post("/api/trends/collect")
async def trends_collect(platform: str | None = None, db: Session = Depends(get_db)):
    from socialmonitor.trends import TrendCollector

    collector = TrendCollector(db)
    if platform:
        snap = await collector.collect_platform(platform)
        return {"platform": platform, "items_count": len(snap.items)}
    else:
        snaps = await collector.collect_all()
        return {
            "platforms_collected": len(snaps),
            "total_items": sum(len(s.items) for s in snaps),
        }


@app.get("/api/trends")
def trends_list(
    platform: str | None = None,
    category: str | None = None,
    limit: int = 30,
    db: Session = Depends(get_db),
):
    from socialmonitor.trends import TrendCollector

    collector = TrendCollector(db)
    items = collector.get_latest(platform=platform, limit=limit)
    if category:
        items = [i for i in items if i.category == category]

    return [
        {
            "id": item.id,
            "rank": item.rank,
            "title": item.title,
            "url": item.url,
            "score": item.score,
            "category": item.category,
            "platform": item.snapshot.platform if item.snapshot else None,
            "captured_at": item.snapshot.captured_at.isoformat() if item.snapshot else None,
        }
        for item in items
    ]


# ---------------------------------------------------------------------------
# Accounts
# ---------------------------------------------------------------------------

@app.get("/api/accounts")
def accounts_list(db: Session = Depends(get_db)):
    from socialmonitor.analytics import AnalyticsTracker

    tracker = AnalyticsTracker(db)
    accounts = tracker.list_accounts()
    result = []
    for acct in accounts:
        summary = tracker.get_growth_summary(acct.id)
        result.append({
            "id": acct.id,
            "platform": acct.platform,
            "handle": acct.handle,
            "display_name": acct.display_name,
            "added_at": acct.added_at.isoformat() if acct.added_at else None,
            "current_followers": summary.get("current_followers"),
            "follower_growth": summary.get("follower_growth"),
            "avg_engagement_rate": summary.get("avg_engagement_rate"),
            "data_points": summary.get("data_points", 0),
        })
    return result


@app.post("/api/accounts")
def accounts_add(body: AccountCreate, db: Session = Depends(get_db)):
    from socialmonitor.analytics import AnalyticsTracker

    tracker = AnalyticsTracker(db)
    acct = tracker.add_account(
        platform=body.platform,
        handle=body.handle,
        display_name=body.display_name,
    )
    return {"id": acct.id, "platform": acct.platform, "handle": acct.handle}


@app.delete("/api/accounts/{account_id}")
def accounts_remove(account_id: int, db: Session = Depends(get_db)):
    from socialmonitor.analytics import AnalyticsTracker

    tracker = AnalyticsTracker(db)
    if not tracker.remove_account(account_id):
        raise HTTPException(404, "Account not found")
    return {"deleted": True}


@app.post("/api/accounts/{account_id}/metrics")
def accounts_record_metrics(account_id: int, body: MetricsRecord, db: Session = Depends(get_db)):
    from socialmonitor.analytics import AnalyticsTracker

    tracker = AnalyticsTracker(db)
    metric = tracker.record_metrics(
        account_id,
        followers=body.followers,
        engagement_rate=body.engagement_rate,
        likes_recent=body.likes_recent,
        comments_recent=body.comments_recent,
    )
    return {"id": metric.id, "captured_at": metric.captured_at.isoformat()}


@app.get("/api/accounts/{account_id}/metrics")
def accounts_get_metrics(account_id: int, limit: int = 30, db: Session = Depends(get_db)):
    from socialmonitor.analytics import AnalyticsTracker

    tracker = AnalyticsTracker(db)
    metrics = tracker.get_metrics_history(account_id, limit=limit)
    return [
        {
            "id": m.id,
            "captured_at": m.captured_at.isoformat() if m.captured_at else None,
            "followers": m.followers,
            "engagement_rate": m.engagement_rate,
            "likes_recent": m.likes_recent,
            "comments_recent": m.comments_recent,
        }
        for m in metrics
    ]


# ---------------------------------------------------------------------------
# Influencers
# ---------------------------------------------------------------------------

@app.get("/api/influencers")
def influencers_list(
    platform: str | None = None,
    category: str | None = None,
    db: Session = Depends(get_db),
):
    from socialmonitor.influencers import InfluencerTracker

    tracker = InfluencerTracker(db)
    influencers = tracker.list_influencers(platform=platform, category=category)
    return [
        {
            "id": inf.id,
            "name": inf.name,
            "handle": inf.handle,
            "platform": inf.platform,
            "category": inf.category,
            "bio": inf.bio,
        }
        for inf in influencers
    ]


@app.post("/api/influencers")
def influencers_add(body: InfluencerCreate, db: Session = Depends(get_db)):
    from socialmonitor.influencers import InfluencerTracker

    tracker = InfluencerTracker(db)
    inf = tracker.add_influencer(
        name=body.name,
        handle=body.handle,
        platform=body.platform,
        category=body.category,
        bio=body.bio,
    )
    return {"id": inf.id, "name": inf.name}


@app.post("/api/influencers/seed")
def influencers_seed(db: Session = Depends(get_db)):
    from socialmonitor.influencers import InfluencerTracker

    tracker = InfluencerTracker(db)
    count = tracker.seed_defaults()
    return {"seeded": count}


@app.delete("/api/influencers/{influencer_id}")
def influencers_remove(influencer_id: int, db: Session = Depends(get_db)):
    from socialmonitor.influencers import InfluencerTracker

    tracker = InfluencerTracker(db)
    if not tracker.remove_influencer(influencer_id):
        raise HTTPException(404, "Influencer not found")
    return {"deactivated": True}


@app.get("/api/influencers/leaderboard")
def influencers_leaderboard(limit: int = 20, db: Session = Depends(get_db)):
    from socialmonitor.influencers import InfluencerTracker

    tracker = InfluencerTracker(db)
    return tracker.get_leaderboard(limit=limit)


@app.get("/api/influencers/{influencer_id}/activities")
def influencers_activities(influencer_id: int, limit: int = 20, db: Session = Depends(get_db)):
    from socialmonitor.influencers import InfluencerTracker

    tracker = InfluencerTracker(db)
    activities = tracker.get_recent_activities(influencer_id=influencer_id, limit=limit)
    return [
        {
            "id": a.id,
            "content_type": a.content_type,
            "title": a.title,
            "url": a.url,
            "summary": a.summary,
            "published_at": a.published_at.isoformat() if a.published_at else None,
            "engagement_score": a.engagement_score,
        }
        for a in activities
    ]


# ---------------------------------------------------------------------------
# Content plans & generation
# ---------------------------------------------------------------------------

@app.get("/api/content/plans")
def content_list_plans(
    status: str | None = None,
    platform: str | None = None,
    db: Session = Depends(get_db),
):
    from socialmonitor.content import ContentPlanner

    planner = ContentPlanner(db)
    plans = planner.list_plans(status=status, platform=platform)
    return [
        {
            "id": p.id,
            "title": p.title,
            "platform": p.platform,
            "content_type": p.content_type,
            "status": p.status,
            "topic": p.topic,
            "notes": p.notes,
            "scheduled_for": p.scheduled_for.isoformat() if p.scheduled_for else None,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "generated_count": len(p.generated_contents),
        }
        for p in plans
    ]


@app.post("/api/content/plans")
def content_create_plan(body: PlanCreate, db: Session = Depends(get_db)):
    from socialmonitor.content import ContentPlanner

    planner = ContentPlanner(db)
    scheduled = None
    if body.scheduled_for:
        scheduled = datetime.fromisoformat(body.scheduled_for)
    plan = planner.create_plan(
        title=body.title,
        platform=body.platform,
        content_type=body.content_type,
        topic=body.topic or body.title,
        notes=body.notes,
        scheduled_for=scheduled,
    )
    return {"id": plan.id, "title": plan.title, "status": plan.status}


@app.put("/api/content/plans/{plan_id}")
def content_update_plan(plan_id: int, body: PlanUpdate, db: Session = Depends(get_db)):
    from socialmonitor.content import ContentPlanner

    planner = ContentPlanner(db)
    updates = body.model_dump(exclude_none=True)
    if "scheduled_for" in updates and updates["scheduled_for"]:
        updates["scheduled_for"] = datetime.fromisoformat(updates["scheduled_for"])
    plan = planner.update_plan(plan_id, **updates)
    if not plan:
        raise HTTPException(404, "Plan not found")
    return {"id": plan.id, "title": plan.title, "status": plan.status}


@app.delete("/api/content/plans/{plan_id}")
def content_delete_plan(plan_id: int, db: Session = Depends(get_db)):
    from socialmonitor.content import ContentPlanner

    planner = ContentPlanner(db)
    if not planner.delete_plan(plan_id):
        raise HTTPException(404, "Plan not found")
    return {"deleted": True}


@app.post("/api/content/generate/{plan_id}")
async def content_generate(plan_id: int, body: GenerateRequest = GenerateRequest(), db: Session = Depends(get_db)):
    from socialmonitor.content import ContentGenerator

    gen = ContentGenerator(db)
    result = await gen.generate_for_plan(plan_id, extra_context=body.extra_context)
    return {
        "id": result.id,
        "version": result.version,
        "body": result.body,
        "model_used": result.model_used,
    }


@app.get("/api/content/plans/{plan_id}/generated")
def content_get_generated(plan_id: int, db: Session = Depends(get_db)):
    from socialmonitor.content import ContentGenerator

    gen = ContentGenerator(db)
    items = gen.get_generated_content(plan_id)
    return [
        {
            "id": c.id,
            "version": c.version,
            "body": c.body,
            "model_used": c.model_used,
            "is_selected": c.is_selected,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in items
    ]


@app.post("/api/content/auto-generate")
async def content_auto_generate(body: AutoGenerateRequest = AutoGenerateRequest(), db: Session = Depends(get_db)):
    from socialmonitor.content import ContentGenerator

    gen = ContentGenerator(db)
    plan, result = await gen.generate_from_trends(
        platform=body.platform, content_type=body.content_type
    )
    return {
        "plan": {"id": plan.id, "title": plan.title},
        "content": {
            "id": result.id,
            "body": result.body,
            "model_used": result.model_used,
        },
    }


@app.post("/api/content/suggest")
async def content_suggest(count: int = 5, db: Session = Depends(get_db)):
    from socialmonitor.content import ContentGenerator

    gen = ContentGenerator(db)
    topics = await gen.suggest_topics(count=count)
    return {"topics": topics}


# ---------------------------------------------------------------------------
# Social listening
# ---------------------------------------------------------------------------

class ListeningCollectRequest(BaseModel):
    keywords: list[str] | None = None

@app.post("/api/listening/collect")
async def listening_collect(
    platform: str | None = None,
    body: ListeningCollectRequest = ListeningCollectRequest(),
    db: Session = Depends(get_db),
):
    from socialmonitor.listening import SocialListeningService

    svc = SocialListeningService(db)
    if platform:
        mentions = await svc.collect_platform(platform, keywords=body.keywords)
    else:
        mentions = await svc.collect_all(keywords=body.keywords)
    return {"mentions_collected": len(mentions)}


@app.get("/api/listening/mentions")
def listening_mentions(
    platform: str | None = None,
    keyword: str | None = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    from socialmonitor.listening import SocialListeningService

    svc = SocialListeningService(db)
    mentions = svc.get_mentions(platform=platform, keyword=keyword, limit=limit)
    return [
        {
            "id": m.id,
            "platform": m.platform,
            "author": m.author,
            "author_followers": m.author_followers,
            "content": m.content,
            "url": m.url,
            "keyword_matched": m.keyword_matched,
            "likes": m.likes,
            "comments": m.comments,
            "shares": m.shares,
            "views": m.views,
            "sentiment": m.sentiment,
            "published_at": m.published_at.isoformat() if m.published_at else None,
            "captured_at": m.captured_at.isoformat() if m.captured_at else None,
        }
        for m in mentions
    ]


@app.get("/api/listening/top")
def listening_top(limit: int = 20, db: Session = Depends(get_db)):
    from socialmonitor.listening import SocialListeningService

    svc = SocialListeningService(db)
    mentions = svc.get_top_mentions(limit=limit)
    return [
        {
            "id": m.id,
            "platform": m.platform,
            "author": m.author,
            "content": m.content,
            "url": m.url,
            "likes": m.likes,
            "comments": m.comments,
            "views": m.views,
        }
        for m in mentions
    ]


@app.get("/api/listening/summary")
def listening_summary(db: Session = Depends(get_db)):
    from socialmonitor.listening import SocialListeningService

    svc = SocialListeningService(db)
    return svc.get_platform_summary()
