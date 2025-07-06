"""
Decorators for the Travel App.
This module contains custom decorators for access control and other functionality.
"""

from functools import wraps
from flask import abort, flash, redirect, url_for, request
from flask_login import current_user


def admin_required(f):
    """
    Decorator to require admin access.
    Redirects non-admin users to access denied page.

    Usage:
        @admin_required
        def admin_only_view():
            pass
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login", next=request.url))

        if not current_user.is_admin():
            flash("You do not have permission to access this page.", "danger")
            return abort(403)

        return f(*args, **kwargs)

    return decorated_function


def user_required(f):
    """
    Decorator to require user authentication.
    Alternative to @login_required with custom message.

    Usage:
        @user_required
        def user_only_view():
            pass
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login", next=request.url))

        return f(*args, **kwargs)

    return decorated_function


def active_user_required(f):
    """
    Decorator to require active user account.
    Blocks deactivated users.

    Usage:
        @active_user_required
        def active_user_only_view():
            pass
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login", next=request.url))

        if not current_user.is_active:
            flash(
                "Your account has been deactivated. Please contact support.", "danger"
            )
            return redirect(url_for("auth.logout"))

        return f(*args, **kwargs)

    return decorated_function


def anonymous_required(f):
    """
    Decorator to require anonymous access (not logged in).
    Redirects authenticated users to dashboard.

    Usage:
        @anonymous_required
        def login_view():
            pass
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated:
            if current_user.is_admin():
                return redirect(url_for("admin.dashboard"))
            else:
                return redirect(url_for("main.dashboard"))

        return f(*args, **kwargs)

    return decorated_function


def verified_user_required(f):
    """
    Decorator to require verified user account.
    (For future email verification feature)

    Usage:
        @verified_user_required
        def verified_user_only_view():
            pass
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login", next=request.url))

        # Note: Add email_verified field to User model if implementing email verification
        # if not current_user.email_verified:
        #     flash('Please verify your email address to access this page.', 'warning')
        #     return redirect(url_for('auth.verify_email'))

        return f(*args, **kwargs)

    return decorated_function


def check_booking_ownership(f):
    """
    Decorator to check if user owns the booking.
    For protecting booking-related routes.

    Usage:
        @check_booking_ownership
        def view_booking(booking_id):
            pass
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login", next=request.url))

        # Get booking_id from kwargs
        booking_id = kwargs.get("booking_id")
        if not booking_id:
            return abort(400)

        from app.models import Booking

        booking = Booking.query.get_or_404(booking_id)

        # Check if user owns the booking or is admin
        if booking.user_id != current_user.id and not current_user.is_admin():
            flash("You do not have permission to access this booking.", "danger")
            return abort(403)

        return f(*args, **kwargs)

    return decorated_function


def check_review_ownership(f):
    """
    Decorator to check if user owns the review.
    For protecting review-related routes.

    Usage:
        @check_review_ownership
        def edit_review(review_id):
            pass
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login", next=request.url))

        # Get review_id from kwargs
        review_id = kwargs.get("review_id")
        if not review_id:
            return abort(400)

        from app.models import Review

        review = Review.query.get_or_404(review_id)

        # Check if user owns the review or is admin
        if review.user_id != current_user.id and not current_user.is_admin():
            flash("You do not have permission to access this review.", "danger")
            return abort(403)

        return f(*args, **kwargs)

    return decorated_function


def rate_limit(max_per_minute=60):
    """
    Simple rate limiting decorator.
    (For production, use Flask-Limiter instead)

    Usage:
        @rate_limit(max_per_minute=10)
        def limited_view():
            pass
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Simple rate limiting implementation
            # In production, use Redis or Flask-Limiter

            # For now, just pass through
            # TODO: Implement proper rate limiting

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def validate_json(f):
    """
    Decorator to validate JSON request data.
    For API endpoints.

    Usage:
        @validate_json
        def api_endpoint():
            pass
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json:
            return {"error": "Request must be JSON"}, 400

        return f(*args, **kwargs)

    return decorated_function


def log_activity(activity_type):
    """
    Decorator to log user activities.
    (For future activity logging feature)

    Usage:
        @log_activity('booking_created')
        def create_booking():
            pass
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Execute the function first
            result = f(*args, **kwargs)

            # Log the activity
            try:
                if current_user.is_authenticated:
                    # TODO: Implement activity logging
                    # ActivityLog.create(
                    #     user_id=current_user.id,
                    #     activity_type=activity_type,
                    #     details=f"Function: {f.__name__}, Args: {args}, Kwargs: {kwargs}"
                    # )
                    pass
            except Exception as e:
                # Don't fail the main function if logging fails
                from flask import current_app

                current_app.logger.error(f"Activity logging failed: {str(e)}")

            return result

        return decorated_function

    return decorator


def cache_result(timeout=300):
    """
    Simple result caching decorator.
    (For production, use Flask-Cache or Redis)

    Usage:
        @cache_result(timeout=600)
        def expensive_function():
            pass
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Simple caching implementation
            # In production, use proper caching solution

            # For now, just pass through
            # TODO: Implement proper caching

            return f(*args, **kwargs)

        return decorated_function

    return decorator
