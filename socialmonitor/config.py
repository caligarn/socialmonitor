"""Application configuration loaded from environment variables."""

from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central configuration sourced from env vars / .env file."""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    # Database
    database_url: str = "sqlite:///socialmonitor.db"

    # LLM providers (at least one needed for content generation)
    openai_api_key: str = ""
    anthropic_api_key: str = ""

    # Social platform credentials (optional – enables richer data)
    twitter_bearer_token: str = ""
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    youtube_api_key: str = ""

    # Scheduling
    trend_refresh_interval: int = 60  # minutes
    influencer_refresh_interval: int = 360  # minutes

    @property
    def has_openai(self) -> bool:
        return bool(self.openai_api_key)

    @property
    def has_anthropic(self) -> bool:
        return bool(self.anthropic_api_key)

    @property
    def has_twitter(self) -> bool:
        return bool(self.twitter_bearer_token)

    @property
    def has_reddit(self) -> bool:
        return bool(self.reddit_client_id and self.reddit_client_secret)

    @property
    def has_youtube(self) -> bool:
        return bool(self.youtube_api_key)


settings = Settings()
