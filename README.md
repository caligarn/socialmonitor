# SocialMonitor

Social media monitoring, AI influencer tracking, and AI-powered content planning system.

## Features

### 1. Trend Monitoring
Track what's popular across multiple platforms:
- **Hacker News** – top stories with AI/tech categorisation
- **Reddit** – hot posts from AI subreddits (r/MachineLearning, r/LocalLLaMA, r/ChatGPT, etc.)
- **YouTube** – trending AI videos via RSS or YouTube Data API

### 2. Personal Social Analytics
Monitor how your own accounts are performing:
- Track followers, engagement rate, likes, comments, shares
- View growth over time
- Compare performance across platforms

### 3. AI Influencer Tracking
Monitor who's leading the AI space:
- Pre-seeded list of top AI researchers, founders, and creators
- Track their activities (posts, videos, papers)
- Follower leaderboard and engagement metrics
- Add your own influencers to watch

### 4. AI Content Planner & Generator
Plan and create content with AI assistance:
- Content calendar with scheduling
- AI-generated posts, threads, video scripts, and articles
- Auto-generate content based on current trends
- Topic suggestions powered by LLMs
- Platform-specific formatting (Twitter, LinkedIn, YouTube, blog, Instagram)

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your API keys

# Seed the influencer database
socialmonitor influencers seed

# Collect trends
socialmonitor trends collect

# View trending topics
socialmonitor trends show --category ai

# Add your social accounts
socialmonitor accounts add twitter @yourhandle --name "Your Name"

# Plan content
socialmonitor content plan "Weekly AI Roundup" -p twitter -t "AI news"

# Auto-generate content from trends
socialmonitor content auto -p twitter

# Get AI topic suggestions
socialmonitor content suggest

# Launch the interactive dashboard
socialmonitor dashboard
```

## CLI Commands

| Command | Description |
|---|---|
| `trends collect` | Fetch trends from all platforms |
| `trends show` | Display latest trends |
| `accounts add` | Add a social account to track |
| `accounts list` | List your tracked accounts |
| `accounts record` | Record metrics for an account |
| `influencers seed` | Load default AI influencers |
| `influencers list` | List tracked influencers |
| `influencers add` | Add a new influencer |
| `influencers leaderboard` | Show ranking by followers |
| `content plan` | Create a content plan |
| `content list` | List content plans |
| `content generate` | Generate AI content for a plan |
| `content auto` | Auto-generate from trends |
| `content suggest` | Get AI topic suggestions |
| `dashboard` | Launch interactive TUI |

## Architecture

```
socialmonitor/
├── config.py              # Settings from env vars
├── cli.py                 # Click CLI entry point
├── db/
│   ├── models.py          # SQLAlchemy ORM models
│   └── session.py         # Database engine & sessions
├── trends/
│   ├── collector.py       # Trend orchestrator
│   └── sources/           # Platform-specific collectors
│       ├── hackernews.py
│       ├── reddit.py
│       └── youtube.py
├── analytics/
│   └── tracker.py         # Personal account metrics
├── influencers/
│   └── tracker.py         # AI influencer monitoring
├── content/
│   ├── planner.py         # Content calendar CRUD
│   └── generator.py       # LLM-powered generation
├── dashboard/
│   └── app.py             # Textual TUI dashboard
└── utils/
    ├── http.py            # Shared async HTTP client
    └── llm.py             # LLM provider abstraction
```

## Running Tests

```bash
pytest tests/ -v
```
