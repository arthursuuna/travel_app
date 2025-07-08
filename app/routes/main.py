"""
Main routes module.
Contains the main application routes like home page, tours listing, etc.
"""

from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime
from app.models import Tour, Category, Booking, Review, BookingStatus
from app.forms import ContactForm, TourSearchForm
from app.utils import send_inquiry_notification_email
from app import db

# Create a Blueprint for main routes
# Blueprints help organize routes into logical modules
main_bp = Blueprint("main", __name__)


@main_bp.route("/")
@main_bp.route("/index")
def index():
    """
    Home page route.
    This is the main landing page of the travel application.
    """

    # Get featured tours (when we have tours)
    featured_tours = Tour.query.filter_by(featured=True, is_active=True).limit(6).all()

    return render_template("index.html", featured_tours=featured_tours)


@main_bp.route("/test")
def test():
    """
    Test route to verify the application is working.
    """
    return "<h1>🚀 Test Route Working!</h1><p>Flask app is configured correctly.</p><p><a href='/'>← Back to Home</a></p>"


@main_bp.route("/about")
def about():
    """
    About page route.
    """
    return render_template("about.html")


@main_bp.route("/dashboard")
@login_required
def dashboard():
    """
    User dashboard route.
    Shows user's bookings, reviews, and account information.
    """

    # Get user's recent bookings
    recent_bookings = (
        Booking.query.filter_by(user_id=current_user.id)
        .order_by(Booking.created_at.desc())
        .limit(5)
        .all()
    )

    # Get user's recent reviews
    user_reviews = (
        Review.query.filter_by(user_id=current_user.id)
        .order_by(Review.created_at.desc())
        .limit(5)
        .all()
    )

    # Calculate statistics
    total_bookings = Booking.query.filter_by(user_id=current_user.id).count()
    completed_bookings = Booking.query.filter_by(
        user_id=current_user.id, status=BookingStatus.COMPLETED
    ).count()

    return render_template(
        "dashboard.html",
        recent_bookings=recent_bookings,
        user_reviews=user_reviews,
        total_bookings=total_bookings,
        completed_bookings=completed_bookings,
    )


@main_bp.route("/contact", methods=["GET", "POST"])
def contact():
    """
    Contact form route.
    Allows users to submit inquiries.
    """
    form = ContactForm()

    if form.validate_on_submit():
        # Create inquiry (implementation will come later)
        flash("Thank you for your message! We'll get back to you soon.", "success")
        return redirect(url_for("main.contact"))

    return render_template("contact.html", form=form)


@main_bp.route("/send-message", methods=["POST"])
def send_message():
    """
    Handle contact form submission from homepage.
    Processes the message and sends notifications.
    """
    try:
        # Get form data
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        subject = request.form.get("subject")
        message = request.form.get("message")

        # Basic validation
        if not all([first_name, last_name, email, subject, message]):
            flash("Please fill in all required fields.", "error")
            return redirect(url_for("main.index"))

        # Here you could save to database or send email
        # For now, just show success message
        flash(
            f"Thank you {first_name}! Your message has been sent. We'll get back to you soon.",
            "success",
        )

        # Optional: Send notification email (if configured)
        # send_inquiry_notification_email(first_name, last_name, email, subject, message)

    except Exception as e:
        flash(
            "Sorry, there was an error sending your message. Please try again.", "error"
        )

    return redirect(url_for("main.index"))


@main_bp.route("/manage-users")
@login_required
def manage_users():
    """
    Admin dashboard for managing users.
    """
    from app.decorators import admin_required

    # Check if user is admin
    if not current_user.is_admin():
        flash("Access denied. Admin privileges required.", "danger")
        return redirect(url_for("main.dashboard"))

    # Get query parameters
    search = request.args.get("search", "")
    status = request.args.get("status", "")
    page = request.args.get("page", 1, type=int)

    # Start with base query
    from app.models import User

    query = User.query

    # Apply search filter
    if search:
        from sqlalchemy import or_

        query = query.filter(
            or_(
                User.first_name.contains(search),
                User.last_name.contains(search),
                User.email.contains(search),
            )
        )

    # Apply status filter
    if status == "admin":
        from app.models import UserRole

        query = query.filter(User.role == UserRole.ADMIN)
    elif status == "regular":
        from app.models import UserRole

        query = query.filter(User.role == UserRole.USER)

    # Order by created date (newest first)
    query = query.order_by(User.created_at.desc())

    # Paginate results
    users = query.paginate(page=page, per_page=15, error_out=False)  # 15 users per page

    # Get counts for statistics
    total_users = User.query.count()
    from app.models import UserRole

    admin_users = User.query.filter(User.role == UserRole.ADMIN).count()
    regular_users = User.query.filter(User.role == UserRole.USER).count()

    return render_template(
        "admin/manage_users.html",
        users=users,
        total_users=total_users,
        admin_users=admin_users,
        regular_users=regular_users,
        title="Manage Users",
    )


@main_bp.route("/users/<int:id>/toggle-admin", methods=["POST"])
@login_required
def toggle_user_admin(id):
    """
    Toggle user admin status (admin only).
    """
    if not current_user.is_admin():
        flash("Access denied. Admin privileges required.", "danger")
        return redirect(url_for("main.dashboard"))

    from app.models import User

    user = User.query.get_or_404(id)

    # Prevent admin from removing their own admin status
    if user.id == current_user.id:
        flash("You cannot modify your own admin status.", "warning")
        return redirect(url_for("main.manage_users"))

    try:
        from app.models import UserRole

        if user.role == UserRole.ADMIN:
            user.role = UserRole.USER
        else:
            user.role = UserRole.ADMIN
        db.session.commit()

        status = "admin" if user.role == UserRole.ADMIN else "regular user"
        flash(
            f'User "{user.first_name} {user.last_name}" is now a {status}.', "success"
        )

    except Exception as e:
        db.session.rollback()
        flash("An error occurred while updating the user.", "danger")

    return redirect(url_for("main.manage_users"))


@main_bp.route("/users/<int:id>/delete", methods=["POST"])
@login_required
def delete_user(id):
    """
    Delete a user (admin only).
    """
    if not current_user.is_admin():
        flash("Access denied. Admin privileges required.", "danger")
        return redirect(url_for("main.dashboard"))

    from app.models import User

    user = User.query.get_or_404(id)

    # Prevent admin from deleting themselves
    if user.id == current_user.id:
        flash("You cannot delete your own account.", "warning")
        return redirect(url_for("main.manage_users"))

    try:
        user_name = f"{user.first_name} {user.last_name}"

        # Check if user has bookings
        user_bookings = Booking.query.filter_by(user_id=user.id).count()
        if user_bookings > 0:
            flash(
                f'Cannot delete user "{user_name}" because they have {user_bookings} booking(s).',
                "danger",
            )
            return redirect(url_for("main.manage_users"))

        db.session.delete(user)
        db.session.commit()

        flash(f'User "{user_name}" deleted successfully!', "success")

    except Exception as e:
        db.session.rollback()
        flash("An error occurred while deleting the user.", "danger")

    return redirect(url_for("main.manage_users"))
