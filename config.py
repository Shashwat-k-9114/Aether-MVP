"""
Aether — Application Configuration
------------------------------------------------
Centralised configuration objects for every environment the app can run
in (development, testing, production). Values are pulled from environment
variables so secrets never live in source control. See `.env.example`
for the full list of variables the app understands.
"""

import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class BaseConfig:
    """Shared configuration inherited by every environment."""

    # --- Core Flask ---------------------------------------------------
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
    JSON_SORT_KEYS = False

    # --- Database -------------------------------------------------------
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'aether.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Session ---------------------------------------------------------
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = timedelta(days=14)

    # --- AI Provider ------------------------------------------------------
    # The active AI backend. Defaults to "mock" so the product works fully
    # offline out of the box. Swap to "openai" / "anthropic" / "gemini" /
    # "grok" once real credentials are supplied — see services/ai.py.
    AI_PROVIDER = os.environ.get("AI_PROVIDER", "mock")
    AI_API_KEY = os.environ.get("AI_API_KEY", "")
    AI_MODEL = os.environ.get("AI_MODEL", "aether-mock-v1")

    # --- Misc ------------------------------------------------------------
    ITEMS_PER_PAGE = 10


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    ENV = "development"


class TestingConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False


class ProductionConfig(BaseConfig):
    DEBUG = False
    ENV = "production"
    SESSION_COOKIE_SECURE = True


CONFIG_MAP = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}


def get_config():
    """Return the config class matching FLASK_ENV (defaults to development)."""
    env = os.environ.get("FLASK_ENV", "development")
    return CONFIG_MAP.get(env, DevelopmentConfig)
