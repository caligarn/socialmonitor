"""SQLAlchemy ORM models for the entire application."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# Trend monitoring
# ---------------------------------------------------------------------------

class TrendSnapshot(Base):
    """A point-in-time capture of trending topics from a platform."""

    __tablename__ = "trend_snapshots"

    id = Column(Integer, primary_key=True)
    platform = Column(String(50), nullable=False, index=True)  # twitter, reddit, youtube, hackernews
    captured_at = Column(DateTime, default=datetime.utcnow, index=True)

    items = relationship("TrendItem", back_populates="snapshot", cascade="all, delete-orphan")


class TrendItem(Base):
    """A single trending topic or post within a snapshot."""

    __tablename__ = "trend_items"

    id = Column(Integer, primary_key=True)
    snapshot_id = Column(Integer, ForeignKey("trend_snapshots.id"), nullable=False)
    rank = Column(Integer)
    title = Column(String(500), nullable=False)
    url = Column(String(1000))
    score = Column(Float)  # normalised popularity score 0-100
    category = Column(String(100))  # ai, tech, general, etc.
    meta_json = Column(Text)  # extra platform-specific data as JSON

    snapshot = relationship("TrendSnapshot", back_populates="items")


# ---------------------------------------------------------------------------
# Personal social accounts & analytics
# ---------------------------------------------------------------------------

class SocialAccount(Base):
    """A social media account belonging to the user."""

    __tablename__ = "social_accounts"

    id = Column(Integer, primary_key=True)
    platform = Column(String(50), nullable=False)
    handle = Column(String(200), nullable=False)
    display_name = Column(String(300))
    profile_url = Column(String(1000))
    added_at = Column(DateTime, default=datetime.utcnow)

    metrics = relationship("AccountMetric", back_populates="account", cascade="all, delete-orphan")


class AccountMetric(Base):
    """Time-series metrics for a social account (followers, engagement, etc.)."""

    __tablename__ = "account_metrics"

    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("social_accounts.id"), nullable=False)
    captured_at = Column(DateTime, default=datetime.utcnow, index=True)
    followers = Column(Integer)
    following = Column(Integer)
    posts_count = Column(Integer)
    engagement_rate = Column(Float)  # percentage
    likes_recent = Column(Integer)
    comments_recent = Column(Integer)
    shares_recent = Column(Integer)
    impressions_recent = Column(Integer)
    meta_json = Column(Text)

    account = relationship("SocialAccount", back_populates="metrics")


# ---------------------------------------------------------------------------
# AI influencer tracking
# ---------------------------------------------------------------------------

class Influencer(Base):
    """A notable person / account in the AI space."""

    __tablename__ = "influencers"

    id = Column(Integer, primary_key=True)
    name = Column(String(300), nullable=False)
    handle = Column(String(200))
    platform = Column(String(50), nullable=False)
    profile_url = Column(String(1000))
    category = Column(String(100))  # researcher, founder, creator, journalist
    bio = Column(Text)
    is_active = Column(Boolean, default=True)
    added_at = Column(DateTime, default=datetime.utcnow)

    activities = relationship("InfluencerActivity", back_populates="influencer", cascade="all, delete-orphan")
    metrics = relationship("InfluencerMetric", back_populates="influencer", cascade="all, delete-orphan")


class InfluencerActivity(Base):
    """A tracked piece of content from an influencer (post, video, article)."""

    __tablename__ = "influencer_activities"

    id = Column(Integer, primary_key=True)
    influencer_id = Column(Integer, ForeignKey("influencers.id"), nullable=False)
    content_type = Column(String(50))  # post, video, article, paper
    title = Column(String(500))
    summary = Column(Text)
    url = Column(String(1000))
    published_at = Column(DateTime)
    engagement_score = Column(Float)
    captured_at = Column(DateTime, default=datetime.utcnow)
    meta_json = Column(Text)

    influencer = relationship("Influencer", back_populates="activities")


class InfluencerMetric(Base):
    """Point-in-time follower / engagement snapshot for an influencer."""

    __tablename__ = "influencer_metrics"

    id = Column(Integer, primary_key=True)
    influencer_id = Column(Integer, ForeignKey("influencers.id"), nullable=False)
    captured_at = Column(DateTime, default=datetime.utcnow, index=True)
    followers = Column(Integer)
    engagement_rate = Column(Float)
    meta_json = Column(Text)

    influencer = relationship("Influencer", back_populates="metrics")


# ---------------------------------------------------------------------------
# Social listening
# ---------------------------------------------------------------------------

class Mention(Base):
    """A mention or post discovered by the social listening service."""

    __tablename__ = "mentions"

    id = Column(Integer, primary_key=True)
    platform = Column(String(50), nullable=False, index=True)  # instagram, tiktok, youtube_shorts
    author = Column(String(300))
    author_followers = Column(Integer)
    content = Column(Text)
    url = Column(String(1000))
    keyword_matched = Column(String(200))
    likes = Column(Integer)
    comments = Column(Integer)
    shares = Column(Integer)
    views = Column(Integer)
    sentiment = Column(String(20))  # positive, negative, neutral
    published_at = Column(DateTime)
    captured_at = Column(DateTime, default=datetime.utcnow, index=True)
    meta_json = Column(Text)


# ---------------------------------------------------------------------------
# Content planning & generation
# ---------------------------------------------------------------------------

class ContentPlan(Base):
    """A content plan / calendar entry."""

    __tablename__ = "content_plans"

    id = Column(Integer, primary_key=True)
    title = Column(String(500), nullable=False)
    platform = Column(String(50))
    content_type = Column(String(50))  # post, thread, video_script, article
    status = Column(String(50), default="draft")  # draft, scheduled, published
    scheduled_for = Column(DateTime)
    topic = Column(String(500))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    generated_contents = relationship("GeneratedContent", back_populates="plan", cascade="all, delete-orphan")


class GeneratedContent(Base):
    """AI-generated content linked to a plan."""

    __tablename__ = "generated_contents"

    id = Column(Integer, primary_key=True)
    plan_id = Column(Integer, ForeignKey("content_plans.id"), nullable=False)
    version = Column(Integer, default=1)
    body = Column(Text, nullable=False)
    model_used = Column(String(100))
    prompt_used = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_selected = Column(Boolean, default=False)

    plan = relationship("ContentPlan", back_populates="generated_contents")
