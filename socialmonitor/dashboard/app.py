"""Textual TUI dashboard for SocialMonitor."""

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Footer, Header, Static, DataTable, TabbedContent, TabPane

from socialmonitor.db import get_session, init_db
from socialmonitor.trends import TrendCollector
from socialmonitor.analytics import AnalyticsTracker
from socialmonitor.influencers import InfluencerTracker
from socialmonitor.content import ContentPlanner
from socialmonitor.listening import SocialListeningService


class DashboardApp(App):
    """Social Monitor Dashboard – a TUI for viewing all modules."""

    CSS = """
    Screen {
        layout: vertical;
    }
    #main {
        height: 1fr;
    }
    .panel-title {
        text-style: bold;
        color: $accent;
        padding: 0 1;
    }
    DataTable {
        height: 1fr;
    }
    """

    TITLE = "SocialMonitor Dashboard"
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent(id="main"):
            with TabPane("Trends", id="tab-trends"):
                yield DataTable(id="trends-table")
            with TabPane("My Accounts", id="tab-accounts"):
                yield DataTable(id="accounts-table")
            with TabPane("AI Influencers", id="tab-influencers"):
                yield DataTable(id="influencers-table")
            with TabPane("Content Plans", id="tab-plans"):
                yield DataTable(id="plans-table")
            with TabPane("Social Listening", id="tab-listening"):
                yield DataTable(id="listening-table")
        yield Footer()

    def on_mount(self) -> None:
        init_db()
        self._load_all()

    def action_refresh(self) -> None:
        self._load_all()

    def _load_all(self) -> None:
        session = get_session()
        try:
            self._load_trends(session)
            self._load_accounts(session)
            self._load_influencers(session)
            self._load_plans(session)
            self._load_listening(session)
        finally:
            session.close()

    def _load_trends(self, session) -> None:
        table = self.query_one("#trends-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Rank", "Platform", "Title", "Score", "Category")

        collector = TrendCollector(session)
        items = collector.get_latest(limit=50)
        for item in items:
            table.add_row(
                str(item.rank or ""),
                item.snapshot.platform if item.snapshot else "",
                (item.title or "")[:80],
                f"{item.score:.0f}" if item.score else "-",
                item.category or "",
            )

    def _load_accounts(self, session) -> None:
        table = self.query_one("#accounts-table", DataTable)
        table.clear(columns=True)
        table.add_columns("ID", "Platform", "Handle", "Followers", "Engagement")

        tracker = AnalyticsTracker(session)
        for acct in tracker.list_accounts():
            summary = tracker.get_growth_summary(acct.id)
            table.add_row(
                str(acct.id),
                acct.platform,
                acct.handle,
                str(summary.get("current_followers", "-")),
                f"{summary.get('avg_engagement_rate', 0):.1f}%",
            )

    def _load_influencers(self, session) -> None:
        table = self.query_one("#influencers-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Name", "Handle", "Platform", "Category", "Followers")

        tracker = InfluencerTracker(session)
        for entry in tracker.get_leaderboard(limit=30):
            table.add_row(
                entry["name"],
                entry["handle"] or "",
                entry["platform"],
                entry["category"] or "",
                str(entry["followers"]) if entry["followers"] else "-",
            )

    def _load_plans(self, session) -> None:
        table = self.query_one("#plans-table", DataTable)
        table.clear(columns=True)
        table.add_columns("ID", "Title", "Platform", "Type", "Status", "Scheduled")

        planner = ContentPlanner(session)
        for plan in planner.list_plans(limit=30):
            table.add_row(
                str(plan.id),
                (plan.title or "")[:60],
                plan.platform or "",
                plan.content_type or "",
                plan.status or "",
                plan.scheduled_for.strftime("%Y-%m-%d %H:%M") if plan.scheduled_for else "-",
            )

    def _load_listening(self, session) -> None:
        table = self.query_one("#listening-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Platform", "Author", "Content", "Likes", "Views", "Keyword")

        svc = SocialListeningService(session)
        for m in svc.get_top_mentions(limit=50):
            table.add_row(
                m.platform or "",
                m.author or "",
                (m.content or "")[:60],
                f"{m.likes:,}" if m.likes else "-",
                f"{m.views:,}" if m.views else "-",
                m.keyword_matched or "",
            )
