def register_blueprints(app):
    """Attach every blueprint to the Flask app."""
    from .services import bp as services_bp
    from .payments import bp as payments_bp

    app.register_blueprint(services_bp)
    app.register_blueprint(payments_bp, url_prefix="/payments")
