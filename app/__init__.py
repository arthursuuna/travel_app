"""
Application factory module.
This module creates and configures the Flask application instance.
"""

from flask import Flask
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from config import Config
import os

# Import db from models
from app.models import db

# Initialize other extensions
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()
csrf = CSRFProtect()


def create_app(config_class=Config):
    """
    Application factory function.
    Creates and configures a Flask application instance.

    Args:
        config_class: Configuration class to use (default: Config)

    Returns:
        Flask application instance
    """

    # Create Flask application instance
    app = Flask(__name__)

    # Load configuration from config class
    app.config.from_object(config_class)

    # Initialize extensions with the app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)  # Re-enabled CSRF protection

    # Configure Flask-Login
    login_manager.login_view = "auth.login"  # Redirect unauthorized users to login
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "info"

    @login_manager.user_loader
    def load_user(user_id):
        """
        Load user by ID for Flask-Login.
        This callback is used to reload the user object from the user ID stored in the session.
        """
        from app.models import User

        return User.query.get(int(user_id))

    # Create upload directories if they don't exist
    upload_path = os.path.join(app.instance_path, "static", "images", "uploads")
    os.makedirs(upload_path, exist_ok=True)

    # Register blueprints (URL routing modules)
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.tours import tours_bp
    from app.routes.bookings import bookings_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(tours_bp, url_prefix="/tours")
    app.register_blueprint(bookings_bp, url_prefix="/bookings")

    # Basic error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return (
            "<h1>404 - Page Not Found</h1><p>The page you're looking for doesn't exist.</p>",
            404,
        )

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return (
            "<h1>500 - Internal Server Error</h1><p>Something went wrong on our end.</p>",
            500,
        )

    return app
