import os
from pathlib import Path
from flask import Flask
from hackerservice.extensions import db, migrate

# Ensure project root is on path for imports
project_root = Path(__file__).parent.parent
import sys
sys.path.insert(0, str(project_root))

# Configuration classes
from config.settings import BaseConfig, DevConfig, TestConfig

def create_app():
    """
    Application factory: creates and configures the Flask app.
    Chooses configuration based on FLASK_CONFIG env var.
    Registers extensions and blueprints.
    """
    # Select config
    config_name = os.getenv("FLASK_CONFIG", "DevConfig")
    config_module = __import__("config.settings", fromlist=[config_name])
    config_obj = getattr(config_module, config_name)

    # Instantiate app with correct template/static folders
    app = Flask(
        __name__,
        template_folder=str(project_root / "templates"),
        static_folder=str(project_root / "static"),
    )
    app.config.from_object(config_obj)

    # Initialize Flask extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints
    from hackerservice.blueprints import register_blueprints
    register_blueprints(app)

    # Future blueprints:
    # from app.routes.payments import bp as payments_bp
    # app.register_blueprint(payments_bp, url_prefix='/payments')
    #
    # from app.routes.admin import bp as admin_bp
    # app.register_blueprint(admin_bp, url_prefix='/admin')

    return app

