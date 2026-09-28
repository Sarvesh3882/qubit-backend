from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    SECRET_KEY: str = "qubit-dev-secret-key-change-in-production-32chars!!"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days
    DATABASE_URL: str = "sqlite+aiosqlite:///./qubit.db"

    # Comma-separated list of allowed CORS origins.
    # In production set this to your Vercel URL, e.g.:
    #   "https://qubit-app.vercel.app"
    # Multiple origins: "https://qubit-app.vercel.app,https://staging.qubit-app.vercel.app"
    # All *.vercel.app preview URLs are also allowed automatically via regex.
    FRONTEND_ORIGIN: str = "http://localhost:3000"

    # ── Origin Quantum / QPanda3 Runtime ─────────────────────────────────────
    # API key for QPanda3 Runtime SDK.
    # Source: github.com/OriginQ/qpanda3-runtime-mcp-server
    # Obtain key at: https://qcloud.originqc.com
    QPANDA3_API_KEY: Optional[str] = None

    # Runtime server URL. Defaults to the official Origin Quantum endpoint.
    # Default is hardcoded in qpanda3_runtime itself; we mirror it here so
    # operators can override without changing code.
    # Official default: https://qpanda3-runtime.qpanda.cn
    QPANDA3_SERVER_URL: str = "https://qpanda3-runtime.qpanda.cn"

    # Channel — "qcloud" is the only documented public channel.
    QPANDA3_CHANNEL: str = "qcloud"

    # Optional path to a config.yml file (alternative auth method).
    QPANDA3_CONFIG_PATH: Optional[str] = None

    # ── Research Intelligence ─────────────────────────────────────────────────
    # GNews API key — required for news feed.
    # Get a free key at: https://gnews.io
    GNEWS_API_KEY: Optional[str] = None

    # OpenAlex email — strongly recommended to get higher rate limits (polite pool).
    # Register at: https://openalex.org
    OPENALEX_EMAIL: Optional[str] = None

    # Semantic Scholar API key — optional, raises rate limits significantly.
    # Unauthenticated free tier: 100 req / 5 min. With key: 1 req/s + higher quotas.
    # Get a free key at: https://www.semanticscholar.org/product/api
    SEMANTIC_SCHOLAR_API_KEY: Optional[str] = None

    # Research cache TTL in seconds (default 30 minutes)
    RESEARCH_CACHE_TTL_SECONDS: int = 1800

    # ── Mistral AI ────────────────────────────────────────────────────────────
    # API key for Mistral AI — required for the AI tutor assistant.
    # Obtain at: https://console.mistral.ai/api-keys
    MISTRAL_API_KEY: Optional[str] = None

    # Agent ID for a pre-configured Mistral Agent (from Mistral Studio).
    # When set, the agent's own instructions + tools are used, and QUBIT
    # injects learner context as a prefix on the user message.
    # Format: "ag:xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
    MISTRAL_AGENT_ID: Optional[str] = None

    # Fallback model when no Agent ID is set (Chat Completions path).
    # Options: mistral-small-latest, mistral-medium-latest, mistral-large-latest
    MISTRAL_MODEL: str = "mistral-small-latest"

    model_config = {"env_file": ".env"}


settings = Settings()
