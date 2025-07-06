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
