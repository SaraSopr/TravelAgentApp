from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = Field(default="TravelAgentApp", alias="APP_NAME")
    env: str = Field(default="dev", alias="ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")

    bus_backend: str = Field(default="inmemory", alias="BUS_BACKEND")
    nats_url: str = Field(default="nats://localhost:4222", alias="NATS_URL")
    nats_connect_retries: int = Field(default=20, alias="NATS_CONNECT_RETRIES")
    nats_connect_delay_ms: int = Field(default=500, alias="NATS_CONNECT_DELAY_MS")

    postgres_dsn: str = Field(default="postgresql+asyncpg://postgres:postgres@localhost:5432/travel_agent", alias="POSTGRES_DSN")
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    state_backend: str = Field(default="memory", alias="STATE_BACKEND")

    observer_poll_seconds: int = Field(default=30, alias="OBSERVER_POLL_SECONDS")
    observer_enabled: bool = Field(default=True, alias="OBSERVER_ENABLED")
    observer_max_events_per_cycle: int = Field(default=20, alias="OBSERVER_MAX_EVENTS_PER_CYCLE")
    news_api_url: str = Field(default="https://newsapi.org/v2/everything", alias="NEWS_API_URL")
    news_api_key: str = Field(default="", alias="NEWS_API_KEY")
    transit_alerts_url: str = Field(default="", alias="TRANSIT_ALERTS_URL")
    social_signals_url: str = Field(default="", alias="SOCIAL_SIGNALS_URL")
    threat_impact_threshold: float = Field(default=0.65, alias="THREAT_IMPACT_THRESHOLD")
    replan_cooldown_seconds: int = Field(default=180, alias="REPLAN_COOLDOWN_SECONDS")
    bus_max_retries: int = Field(default=2, alias="BUS_MAX_RETRIES")
    bus_retry_base_ms: int = Field(default=150, alias="BUS_RETRY_BASE_MS")
    otel_enabled: bool = Field(default=False, alias="OTEL_ENABLED")
    otel_service_name: str = Field(default="travel-agent-app", alias="OTEL_SERVICE_NAME")
    otel_exporter_endpoint: str = Field(default="", alias="OTEL_EXPORTER_ENDPOINT")
    auth_secret: str = Field(default="dev-secret-change-me", alias="AUTH_SECRET")
    auth_token_ttl_minutes: int = Field(default=120, alias="AUTH_TOKEN_TTL_MINUTES")
    auth_login_max_attempts: int = Field(default=8, alias="AUTH_LOGIN_MAX_ATTEMPTS")
    auth_login_window_seconds: int = Field(default=60, alias="AUTH_LOGIN_WINDOW_SECONDS")
    auth_login_lock_seconds: int = Field(default=120, alias="AUTH_LOGIN_LOCK_SECONDS")


@lru_cache
def get_settings() -> Settings:
    return Settings()
