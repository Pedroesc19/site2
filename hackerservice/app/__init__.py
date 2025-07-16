"""
hackerservice.app
~~~~~~~~~~~~~~~
Flask application-factory + early dotenv loader.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask

from hackerservice.extensions import db, migrate, login   # ← login manager added

# --------------------------------------------------------------------------- #
# ❶  Paths
# --------------------------------------------------------------------------- #
app_dir   = Path(__file__).resolve().parent           # …/hackerservice/hackerservice/app
pkg_root  = app_dir.parent                            # …/hackerservice/hackerservice
proj_root = pkg_root.parent                           # …/hackerservice  (outer project)

# --------------------------------------------------------------------------- #
# ❷  Load .env (outer root) BEFORE anything reads os.getenv
# --------------------------------------------------------------------------- #
load_dotenv(proj_root / ".env")                       # silently ignored if file absent

# --------------------------------------------------------------------------- #
# ❸  Ensure outer root on import path (so `config`, etc. resolve cleanly)
# --------------------------------------------------------------------------- #
sys.path.insert(0, str(proj_root))

# Import config AFTER .env has been processed
from config.settings import BaseConfig, DevConfig, TestConfig  # noqa: E402

# --------------------------------------------------------------------------- #
# ❹  Factory
# --------------------------------------------------------------------------- #
def create_app() -> Flask:
    """
    Application-factory.

    • Picks settings via ``FLASK_CONFIG`` env-var (default: ``DevConfig``).
    • Initialises extensions (SQLAlchemy, Alembic, LoginManager).
    • Registers core, admin, auth & affiliate blueprints.
    """
    cfg_name   = os.getenv("FLASK_CONFIG", "DevConfig")
    cfg_module = __import__("config.settings", fromlist=[cfg_name])
    cfg_obj    = getattr(cfg_module, cfg_name)

    app = Flask(
        __name__,
        template_folder=str(pkg_root / "templates"),  # ← inner templates/
        static_folder=str(pkg_root / "static"),       # ← inner static/
    )
    app.config.from_object(cfg_obj)

    # ── Extensions ────────────────────────────────────────────────────────
    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)                 # <— NEW: login manager

    # ── Core blueprints (services + payments) ─────────────────────────────
    from hackerservice.blueprints import register_blueprints  # noqa: WPS433,E402
    register_blueprints(app)

    # ── Auth / Affiliate / Admin portals ─────────────────────────────────
    from hackerservice.blueprints.auth      import bp as auth_bp          # noqa: E402
    from hackerservice.blueprints.affiliate import bp as affiliate_bp     # noqa: E402
    app.register_blueprint(auth_bp)
    app.register_blueprint(affiliate_bp)

    # Flask-Admin init (secured inside)
    from hackerservice.blueprints.admin import init_admin                 # noqa: E402
    init_admin(app)

    return app


# gunicorn entry-point:  ``gunicorn 'hackerservice.app:create_app()'``
app = create_app()

