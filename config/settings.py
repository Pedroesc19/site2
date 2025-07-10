import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration hierarchy:
#   BaseConfig : production defaults (expects tmpfs secrets)
#   DevConfig  : overrides for local development (uses env or defaults)
#   TestConfig : testing flags on top of DevConfig
# ---------------------------------------------------------------------------

class BaseConfig:
    """Production / onion-service settings."""

    # --- Secret key --------------------------------------------------------
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY")
    if not SECRET_KEY:
        try:
            SECRET_KEY = Path("/run/secretcfg/SECRET_KEY").read_text().strip()
        except FileNotFoundError:
            SECRET_KEY = None  # DevConfig will supply fallback "password"

    # --- Database credentials ---------------------------------------------
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    if not DB_PASSWORD:
        try:
            DB_PASSWORD = Path("/run/secretcfg/DB_PASSWORD").read_text().strip()
        except FileNotFoundError:
            DB_PASSWORD = None  # DevConfig will supply fallback "password"

    SQLALCHEMY_DATABASE_URI = (
        f"postgresql://hackerservice_user:{DB_PASSWORD}@127.0.0.1/"
        "hackerservice_db"
    ) if DB_PASSWORD else None

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_SAMESITE = "Strict"
    SESSION_COOKIE_SECURE   = True    # Only over HTTPS / Onion
    PREFERRED_URL_SCHEME    = "http"


class DevConfig(BaseConfig):
    """Local development — uses literal 'password' fallbacks."""

    SESSION_COOKIE_SECURE = False  # allow http:// during dev

    # Provide literal "password" defaults when files/envs aren’t set
    SECRET_KEY  = BaseConfig.SECRET_KEY  or "password"
    DB_PASSWORD = BaseConfig.DB_PASSWORD or "password"

    SQLALCHEMY_DATABASE_URI = (
        f"postgresql://hackerservice_user:{DB_PASSWORD}@127.0.0.1/"
        "hackerservice_db"
    )


class TestConfig(DevConfig):
    """Pytest / CI settings."""
    TESTING = True

