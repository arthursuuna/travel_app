import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """
    Configuration class for the Flask application.
    This centralizes all configuration settings and loads them from environment variables.
    """

    # SECURITY SETTINGS
    # Secret key used for session management and CSRF protection
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key-change-in-production"

    # DATABASE SETTINGS
    # Database URL - SQLite for development, can be changed to PostgreSQL for production
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DATABASE_URL") or "sqlite:///travel_app.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Disable event system to save memory

    # EMAIL SETTINGS
    # Configuration for sending emails (booking confirmations, notifications, etc.)
    MAIL_SERVER = os.environ.get("MAIL_SERVER") or "smtp.gmail.com"
    MAIL_PORT = int(os.environ.get("MAIL_PORT") or 587)
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() in ["true", "on", "1"]
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER")

    # FILE UPLOAD SETTINGS
    # Configuration for file uploads (tour images)
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB max file size
    UPLOAD_FOLDER = 'app/static/images/tours'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    # PAYMENT SETTINGS
    # Stripe payment gateway configuration
    STRIPE_PUBLIC_KEY = os.environ.get("STRIPE_PUBLIC_KEY")
    STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY")

    # PAGINATION SETTINGS
    # Number of items to display per page
    TOURS_PER_PAGE = 12
    BOOKINGS_PER_PAGE = 10
    REVIEWS_PER_PAGE = 5

    # SECURITY SETTINGS
    # CSRF protection configuration
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour token expiry

    # SESSION SETTINGS
    # Session timeout configuration
    PERMANENT_SESSION_LIFETIME = 1800  # 30 minutes in seconds
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access to session cookie
    SESSION_COOKIE_SAMESITE = "Lax"  # CSRF protection
