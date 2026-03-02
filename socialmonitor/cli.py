"""Command-line interface for SocialMonitor."""

from __future__ import annotations

import asyncio
from datetime import datetime

import click
from rich.console import Console
from rich.table import Table

from socialmonitor.db import get_session, init_db

console = Console()


@click.group()
def main():
    """SocialMonitor – monitor trends, track influencers, plan AI content."""
    init_db()


# ---------------------------------------------------------------------------
# Trends
# ---------------------------------------------------------------------------

@main.group()
def trends():
    """Collect and view trending topics."""


@trends.command("collect")
@click.option("--platform", "-p", default=None, help="Collect from a specific platform only")
def trends_collect(platform):
    """Fetch latest trends from all (or one) platform."""
    from socialmonitor.trends import TrendCollector

    session = get_session()
    collector = TrendCollector(session)

    async def _run():
        if platform:
            snap = await collector.collect_platform(platform)
            console.print(f"[green]Collected {len(snap.items)} items from {platform}[/]")
        else:
            snaps = await collector.collect_all()
            total = sum(len(s.items) for s in snaps)
            console.print(f"[green]Collected {total} items from {len(snaps)} platforms[/]")

    asyncio.run(_run())
    session.close()


@trends.command("show")
@click.option("--platform", "-p", default=None)
@click.option("--limit", "-n", default=30)
@click.option("--category", "-c", default=None, help="Filter by category (ai, tech, general)")
def trends_show(platform, limit, category):
    """Display latest trends."""
    from socialmonitor.trends import TrendCollector

    session = get_session()
    collector = TrendCollector(session)
    items = collector.get_latest(platform=platform, limit=limit)

    if category:
        items = [i for i in items if i.category == category]

    table = Table(title="Trending Topics")
    table.add_column("#", style="dim", width=4)
    table.add_column("Platform", width=12)
    table.add_column("Title", min_width=30)
    table.add_column("Score", justify="right", width=8)
    table.add_column("Category", width=10)

    for item in items:
        table.add_row(
            str(item.rank or ""),
            item.snapshot.platform if item.snapshot else "",
            item.title or "",
            f"{item.score:.0f}" if item.score else "-",
            item.category or "",
        )

    console.print(table)
    session.close()


# ---------------------------------------------------------------------------
# Accounts (personal analytics)
# ---------------------------------------------------------------------------

@main.group()
def accounts():
    """Manage your social media accounts."""


@accounts.command("add")
@click.argument("platform")
@click.argument("handle")
@click.option("--name", "-n", default="")
def accounts_add(platform, handle, name):
    """Add a social account to track."""
    from socialmonitor.analytics import AnalyticsTracker

    session = get_session()
    tracker = AnalyticsTracker(session)
    acct = tracker.add_account(platform=platform, handle=handle, display_name=name)
    console.print(f"[green]Added account #{acct.id}: {platform}/{handle}[/]")
    session.close()


@accounts.command("list")
def accounts_list():
    """List tracked accounts."""
    from socialmonitor.analytics import AnalyticsTracker

    session = get_session()
    tracker = AnalyticsTracker(session)

    table = Table(title="Your Social Accounts")
    table.add_column("ID", width=4)
    table.add_column("Platform", width=12)
    table.add_column("Handle")
    table.add_column("Followers", justify="right")
    table.add_column("Growth", justify="right")
    table.add_column("Engagement", justify="right")

    for acct in tracker.list_accounts():
        summary = tracker.get_growth_summary(acct.id)
        table.add_row(
            str(acct.id),
            acct.platform,
            acct.handle,
            str(summary.get("current_followers", "-")),
            str(summary.get("follower_growth", "-")),
            f"{summary.get('avg_engagement_rate', 0):.1f}%",
        )

    console.print(table)
    session.close()


@accounts.command("record")
@click.argument("account_id", type=int)
@click.option("--followers", "-f", type=int, default=None)
@click.option("--engagement", "-e", type=float, default=None)
@click.option("--likes", type=int, default=None)
@click.option("--comments", type=int, default=None)
def accounts_record(account_id, followers, engagement, likes, comments):
    """Record metrics for an account."""
    from socialmonitor.analytics import AnalyticsTracker

    session = get_session()
    tracker = AnalyticsTracker(session)
    tracker.record_metrics(
        account_id,
        followers=followers,
        engagement_rate=engagement,
        likes_recent=likes,
        comments_recent=comments,
    )
    console.print(f"[green]Recorded metrics for account #{account_id}[/]")
    session.close()


# ---------------------------------------------------------------------------
# Influencers
# ---------------------------------------------------------------------------

@main.group()
def influencers():
    """Track AI influencers."""


@influencers.command("seed")
def influencers_seed():
    """Populate default list of AI influencers."""
    from socialmonitor.influencers import InfluencerTracker

    session = get_session()
    tracker = InfluencerTracker(session)
    count = tracker.seed_defaults()
    if count:
        console.print(f"[green]Added {count} default influencers[/]")
    else:
        console.print("[yellow]Influencers already seeded[/]")
    session.close()


@influencers.command("list")
@click.option("--platform", "-p", default=None)
@click.option("--category", "-c", default=None)
def influencers_list(platform, category):
    """List tracked AI influencers."""
    from socialmonitor.influencers import InfluencerTracker

    session = get_session()
    tracker = InfluencerTracker(session)

    table = Table(title="AI Influencers")
    table.add_column("ID", width=4)
    table.add_column("Name", min_width=20)
    table.add_column("Handle", width=18)
    table.add_column("Platform", width=10)
    table.add_column("Category", width=12)

    for inf in tracker.list_influencers(platform=platform, category=category):
        table.add_row(str(inf.id), inf.name, inf.handle or "", inf.platform, inf.category or "")

    console.print(table)
    session.close()


@influencers.command("add")
@click.argument("name")
@click.argument("handle")
@click.argument("platform")
@click.option("--category", "-c", default="creator")
@click.option("--bio", "-b", default="")
def influencers_add(name, handle, platform, category, bio):
    """Add an influencer to track."""
    from socialmonitor.influencers import InfluencerTracker

    session = get_session()
    tracker = InfluencerTracker(session)
    inf = tracker.add_influencer(name=name, handle=handle, platform=platform, category=category, bio=bio)
    console.print(f"[green]Added influencer #{inf.id}: {name}[/]")
    session.close()


@influencers.command("leaderboard")
def influencers_leaderboard():
    """Show influencer rankings."""
    from socialmonitor.influencers import InfluencerTracker

    session = get_session()
    tracker = InfluencerTracker(session)

    table = Table(title="AI Influencer Leaderboard")
    table.add_column("Rank", width=4)
    table.add_column("Name", min_width=20)
    table.add_column("Handle", width=18)
    table.add_column("Platform", width=10)
    table.add_column("Followers", justify="right")

    for idx, entry in enumerate(tracker.get_leaderboard(), 1):
        table.add_row(
            str(idx),
            entry["name"],
            entry["handle"] or "",
            entry["platform"],
            f"{entry['followers']:,}" if entry["followers"] else "-",
        )

    console.print(table)
    session.close()


# ---------------------------------------------------------------------------
# Content planning & generation
# ---------------------------------------------------------------------------

@main.group()
def content():
    """Plan and generate AI-powered content."""


@content.command("plan")
@click.argument("title")
@click.option("--platform", "-p", default="twitter")
@click.option("--type", "content_type", default="post")
@click.option("--topic", "-t", default="")
@click.option("--notes", "-n", default="")
@click.option("--schedule", "-s", default=None, help="Schedule date (YYYY-MM-DD HH:MM)")
def content_plan(title, platform, content_type, topic, notes, schedule):
    """Create a new content plan."""
    from socialmonitor.content import ContentPlanner

    session = get_session()
    planner = ContentPlanner(session)
    scheduled_for = datetime.strptime(schedule, "%Y-%m-%d %H:%M") if schedule else None
    plan = planner.create_plan(
        title=title,
        platform=platform,
        content_type=content_type,
        topic=topic or title,
        notes=notes,
        scheduled_for=scheduled_for,
    )
    console.print(f"[green]Created plan #{plan.id}: {title}[/]")
    session.close()


@content.command("list")
@click.option("--status", "-s", default=None)
@click.option("--platform", "-p", default=None)
def content_list(status, platform):
    """List content plans."""
    from socialmonitor.content import ContentPlanner

    session = get_session()
    planner = ContentPlanner(session)

    table = Table(title="Content Plans")
    table.add_column("ID", width=4)
    table.add_column("Title", min_width=30)
    table.add_column("Platform", width=10)
    table.add_column("Type", width=10)
    table.add_column("Status", width=10)
    table.add_column("Scheduled", width=16)

    for plan in planner.list_plans(status=status, platform=platform):
        table.add_row(
            str(plan.id),
            plan.title or "",
            plan.platform or "",
            plan.content_type or "",
            plan.status or "",
            plan.scheduled_for.strftime("%Y-%m-%d %H:%M") if plan.scheduled_for else "-",
        )

    console.print(table)
    session.close()


@content.command("generate")
@click.argument("plan_id", type=int)
def content_generate(plan_id):
    """Generate AI content for a plan."""
    from socialmonitor.content import ContentGenerator

    session = get_session()
    gen = ContentGenerator(session)

    async def _run():
        result = await gen.generate_for_plan(plan_id)
        console.print(f"\n[bold green]Generated content v{result.version} (model: {result.model_used}):[/]\n")
        console.print(result.body)

    asyncio.run(_run())
    session.close()


@content.command("auto")
@click.option("--platform", "-p", default="twitter")
@click.option("--type", "content_type", default="post")
def content_auto(platform, content_type):
    """Auto-generate content from current trends."""
    from socialmonitor.content import ContentGenerator

    session = get_session()
    gen = ContentGenerator(session)

    async def _run():
        plan, result = await gen.generate_from_trends(platform=platform, content_type=content_type)
        console.print(f"[green]Created plan #{plan.id} and generated content:[/]\n")
        console.print(result.body)

    asyncio.run(_run())
    session.close()


@content.command("suggest")
@click.option("--count", "-n", default=5, type=int)
def content_suggest(count):
    """Get AI-suggested content topics based on trends."""
    from socialmonitor.content import ContentGenerator

    session = get_session()
    gen = ContentGenerator(session)

    async def _run():
        topics = await gen.suggest_topics(count=count)
        console.print("[bold]Suggested Topics:[/]\n")
        for line in topics:
            console.print(f"  {line}")

    asyncio.run(_run())
    session.close()


# ---------------------------------------------------------------------------
# Social listening
# ---------------------------------------------------------------------------

@main.group()
def listening():
    """Monitor mentions across Instagram, TikTok & YouTube Shorts."""


@listening.command("collect")
@click.option("--platform", "-p", default=None, help="instagram, tiktok, or youtube_shorts")
@click.option("--keywords", "-k", default=None, help="Comma-separated keywords to search")
def listening_collect(platform, keywords):
    """Fetch mentions from social platforms."""
    from socialmonitor.listening import SocialListeningService

    session = get_session()
    svc = SocialListeningService(session)
    kw_list = [k.strip() for k in keywords.split(",")] if keywords else None

    async def _run():
        if platform:
            mentions = await svc.collect_platform(platform, keywords=kw_list)
            console.print(f"[green]Collected {len(mentions)} mentions from {platform}[/]")
        else:
            mentions = await svc.collect_all(keywords=kw_list)
            console.print(f"[green]Collected {len(mentions)} mentions across all platforms[/]")

    asyncio.run(_run())
    session.close()


@listening.command("show")
@click.option("--platform", "-p", default=None)
@click.option("--keyword", "-k", default=None)
@click.option("--limit", "-n", default=30)
def listening_show(platform, keyword, limit):
    """Display recent mentions."""
    from socialmonitor.listening import SocialListeningService

    session = get_session()
    svc = SocialListeningService(session)
    mentions = svc.get_mentions(platform=platform, keyword=keyword, limit=limit)

    table = Table(title="Social Mentions")
    table.add_column("Platform", width=14)
    table.add_column("Author", width=18)
    table.add_column("Content", min_width=30)
    table.add_column("Likes", justify="right", width=8)
    table.add_column("Views", justify="right", width=10)
    table.add_column("Keyword", width=12)

    for m in mentions:
        table.add_row(
            m.platform or "",
            m.author or "",
            (m.content or "")[:60],
            f"{m.likes:,}" if m.likes else "-",
            f"{m.views:,}" if m.views else "-",
            m.keyword_matched or "",
        )

    console.print(table)
    session.close()


@listening.command("top")
@click.option("--limit", "-n", default=20)
def listening_top(limit):
    """Show top mentions by engagement."""
    from socialmonitor.listening import SocialListeningService

    session = get_session()
    svc = SocialListeningService(session)
    mentions = svc.get_top_mentions(limit=limit)

    table = Table(title="Top Mentions by Engagement")
    table.add_column("Platform", width=14)
    table.add_column("Author", width=18)
    table.add_column("Content", min_width=30)
    table.add_column("Likes", justify="right", width=8)
    table.add_column("Comments", justify="right", width=8)
    table.add_column("Views", justify="right", width=10)

    for m in mentions:
        table.add_row(
            m.platform or "",
            m.author or "",
            (m.content or "")[:60],
            f"{m.likes:,}" if m.likes else "-",
            f"{m.comments:,}" if m.comments else "-",
            f"{m.views:,}" if m.views else "-",
        )

    console.print(table)
    session.close()


@listening.command("summary")
def listening_summary():
    """Show per-platform summary of collected mentions."""
    from socialmonitor.listening import SocialListeningService

    session = get_session()
    svc = SocialListeningService(session)

    table = Table(title="Social Listening Summary")
    table.add_column("Platform", width=16)
    table.add_column("Mentions", justify="right", width=10)
    table.add_column("Total Likes", justify="right", width=12)
    table.add_column("Total Views", justify="right", width=14)

    for entry in svc.get_platform_summary():
        table.add_row(
            entry["platform"],
            str(entry["mention_count"]),
            f"{entry['total_likes']:,}",
            f"{entry['total_views']:,}",
        )

    console.print(table)
    session.close()


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@main.command()
def dashboard():
    """Launch the interactive TUI dashboard."""
    from socialmonitor.dashboard import DashboardApp

    app = DashboardApp()
    app.run()


if __name__ == "__main__":
    main()
