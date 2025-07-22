"""
Main routes module.
Contains the main application routes like home page, tours listing, etc.
"""

from flask import (
    Blueprint,
    render_template,
    request,
    flash,
    redirect,
    url_for,
    current_app,
)
from flask_login import login_required, current_user
from datetime import datetime
from app.models import Tour, Category, Booking, Review, BookingStatus, Inquiry, InquiryResponse, User
from app.forms import ContactForm, TourSearchForm
from app.utils import send_inquiry_notification_email, send_bot_response_email, send_admin_notification_email
from app.bot_service import inquiry_bot
from flask_mail import Message
from app import mail
from app.reporting import (
    generate_comprehensive_report,
    get_booking_statistics,
    get_popular_tours,
    export_bookings_to_csv,
)
from app import db
from app.decorators import admin_required

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
    Display information about the travel company.
    """
    return render_template("about.html")


@main_bp.route("/services")
def services():
    """
    Services page route - temporarily redirected to about page.
    The services page is commented out for performance optimization.
    """
    from flask import redirect, url_for
    return redirect(url_for('main.about'))


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
    Contact form route with automatic bot processing.
    Allows users to submit inquiries and get automated responses.
    """
    form = ContactForm()

    if form.validate_on_submit():
        # Create the inquiry with processing status initially
        inquiry = Inquiry(
            name=form.name.data,
            email=form.email.data,
            subject=form.subject.data,
            message=form.message.data,
            status='processing',  # Start with processing status to avoid showing in pending
            created_at=datetime.utcnow()
        )
        
        # Link to user if logged in
        if current_user.is_authenticated:
            inquiry.user_id = current_user.id
        
        db.session.add(inquiry)
        db.session.flush()  # Get the inquiry ID
        
        try:
            current_app.logger.info(f"Processing new inquiry {inquiry.id} with bot")
            
            # IMMEDIATE BOT PROCESSING - happens before saving as pending
            bot_response_data = inquiry_bot.generate_response(inquiry)
            current_app.logger.info(f"Bot response generated: {bool(bot_response_data)}")
            
            if bot_response_data:
                # Create bot response record
                bot_response = InquiryResponse(
                    inquiry_id=inquiry.id,
                    response_text=bot_response_data['text'],
                    is_bot_response=True,
                    bot_confidence=bot_response_data.get('confidence', 0.5),
                    requires_human_review=bot_response_data.get('requires_review', True),
                    created_at=datetime.utcnow()
                )
                db.session.add(bot_response)
                
                # Mark as bot processed immediately
                inquiry.bot_processed = True
                inquiry.last_bot_response_at = datetime.utcnow()
                
                # Analyze inquiry and determine final status
                analysis = inquiry_bot.analyze_inquiry(inquiry.message, inquiry.subject)
                should_escalate, reasons = inquiry_bot.should_escalate_to_human(inquiry, analysis)
                
                current_app.logger.info(f"Bot analysis: {analysis}")
                current_app.logger.info(f"Should escalate: {should_escalate}, reasons: {reasons}")
                
                if should_escalate:
                    # Only goes to pending if escalation is needed
                    inquiry.requires_human_attention = True
                    inquiry.status = 'needs_review'
                    current_app.logger.info(f"Inquiry {inquiry.id} escalated to human review")
                else:
                    # Bot successfully handled - mark as resolved, not pending
                    inquiry.requires_human_attention = False
                    inquiry.status = 'resolved'  # Bot resolved it successfully
                    current_app.logger.info(f"Inquiry {inquiry.id} successfully resolved by bot")
                
                # Set sentiment safely
                sentiment = analysis.get('sentiment', 'neutral') if isinstance(analysis, dict) else 'neutral'
                inquiry.sentiment = sentiment
                
                # Commit changes BEFORE sending emails
                db.session.commit()
                current_app.logger.info(f"Inquiry {inquiry.id} committed with status: {inquiry.status}")
                
                # Send automated response email to user
                try:
                    send_bot_response_email(inquiry, bot_response_data['text'])
                    current_app.logger.info(f"Bot response email sent for inquiry {inquiry.id}")
                except Exception as email_error:
                    current_app.logger.error(f"Failed to send bot response email: {email_error}")
                    # Don't fail the whole process if email fails
                
                # Send admin notification if escalated
                if should_escalate:
                    try:
                        send_admin_notification_email(inquiry)
                        current_app.logger.info(f"Admin notification sent for escalated inquiry {inquiry.id}")
                    except Exception as email_error:
                        current_app.logger.error(f"Failed to send admin notification: {email_error}")
                    
                    flash('Thank you for your message! You have received an immediate automated response. Our team has also been notified and will provide additional assistance.', 'success')
                else:
                    flash('Thank you for your message! You have received an immediate automated response that should address your inquiry. No further action is needed.', 'success')
                
            else:
                # Bot couldn't generate a response - escalate to human immediately
                current_app.logger.warning(f"Bot could not generate response for inquiry {inquiry.id}")
                inquiry.requires_human_attention = True
                inquiry.status = 'needs_review'
                inquiry.bot_processed = False  # Mark as not processed since bot failed
                
                db.session.commit()
                current_app.logger.info(f"Inquiry {inquiry.id} escalated to human - committed with status: {inquiry.status}")
                
                # Send admin notification for unprocessed inquiry
                try:
                    send_admin_notification_email(inquiry)
                    current_app.logger.info(f"Admin notification sent for unprocessed inquiry {inquiry.id}")
                except Exception as email_error:
                    current_app.logger.error(f"Failed to send admin notification: {email_error}")
                
                flash('Thank you for your message! Our team will review your inquiry personally and get back to you soon.', 'success')
            
        except Exception as e:
            current_app.logger.error(f"Error processing inquiry with bot: {str(e)}", exc_info=True)
            
            # If bot processing completely fails, mark for human review
            try:
                inquiry.requires_human_attention = True
                inquiry.status = 'needs_review'  # Changed from 'error' to 'needs_review'
                inquiry.bot_processed = False
                db.session.commit()
                current_app.logger.info(f"Inquiry {inquiry.id} marked for human review due to error")
                
                # Notify admin of the error
                try:
                    send_admin_notification_email(inquiry)
                    current_app.logger.info(f"Admin notification sent for error inquiry {inquiry.id}")
                except Exception as email_error:
                    current_app.logger.error(f"Failed to send admin notification for error: {email_error}")
                    
            except Exception as fallback_error:
                current_app.logger.error(f"Fallback error handling failed: {fallback_error}")
            
            flash('Thank you for your message! We have received it and will get back to you soon.', 'success')
        
        return redirect(url_for('main.contact'))

    return render_template("contact.html", form=form)


def send_bot_response_email(inquiry, bot_response_text):
    """Send bot response to user via email."""
    try:
        msg = Message(
            subject=f'Re: {inquiry.subject}',
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[inquiry.email]
        )
        
        msg.html = f'''
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #007bff 0%, #0056b3 100%); color: white; padding: 20px; text-align: center;">
                <h2>🤖 Affordable Escapes - Automated Response</h2>
            </div>
            <div style="padding: 20px; background: #f8f9fa;">
                <p>Dear {inquiry.name},</p>
                <p>Thank you for contacting us! Here's an immediate response to your inquiry:</p>
                <div style="background: white; padding: 20px; border-left: 4px solid #007bff; margin: 20px 0; border-radius: 5px;">
                    {bot_response_text.replace(chr(10), '<br>')}
                </div>
                <p>If you need further assistance, please don't hesitate to reply to this email or contact our support team.</p>
                <hr style="margin: 20px 0; border: none; border-top: 1px solid #ddd;">
                <p style="font-size: 12px; color: #666;">
                    This is an automated response. For immediate assistance, you can also:
                    <br>• Visit our website: <a href="{url_for('main.index', _external=True)}">Affordable Escapes</a>
                    <br>• Browse our tours: <a href="{url_for('tours.index', _external=True)}">View Tours</a>
                    <br>• Check your dashboard: <a href="{url_for('main.dashboard', _external=True)}">Dashboard</a>
                </p>
                <p>Best regards,<br><strong>Affordable Escapes Team</strong></p>
            </div>
        </div>
        '''
        
        mail.send(msg)
        current_app.logger.info(f"Bot response email sent to {inquiry.email}")
    except Exception as e:
        current_app.logger.error(f"Failed to send bot response email: {e}")


def send_admin_notification_email(inquiry):
    """Notify admin of inquiry requiring human attention."""
    try:
        admin_emails = [user.email for user in User.query.filter_by(role='admin').all()]
        if not admin_emails:
            admin_emails = [current_app.config.get('MAIL_DEFAULT_SENDER', 'admin@example.com')]
        
        msg = Message(
            subject=f'🚨 Inquiry Requires Attention: {inquiry.subject}',
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=admin_emails
        )
        
        sentiment_color = {
            'positive': '#28a745',
            'negative': '#dc3545', 
            'neutral': '#6c757d'
        }.get(inquiry.sentiment, '#6c757d')
        
        msg.html = f'''
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #dc3545; color: white; padding: 20px; text-align: center;">
                <h2>🚨 Inquiry Requires Human Attention</h2>
            </div>
            <div style="padding: 20px;">
                <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                    <h3 style="margin-top: 0;">Inquiry Details</h3>
                    <p><strong>From:</strong> {inquiry.name} (<a href="mailto:{inquiry.email}">{inquiry.email}</a>)</p>
                    <p><strong>Subject:</strong> {inquiry.subject}</p>
                    <p><strong>Status:</strong> <span style="background: #ffc107; padding: 2px 8px; border-radius: 3px; color: black;">{inquiry.status}</span></p>
                    <p><strong>Sentiment:</strong> <span style="background: {sentiment_color}; color: white; padding: 2px 8px; border-radius: 3px;">{inquiry.sentiment or 'Unknown'}</span></p>
                    <p><strong>Requires Human Attention:</strong> {'Yes' if inquiry.requires_human_attention else 'No'}</p>
                    <p><strong>Bot Processed:</strong> {'Yes' if inquiry.bot_processed else 'No'}</p>
                </div>
                
                <div style="background: #ffffff; padding: 20px; border-left: 4px solid #dc3545; margin: 20px 0; border-radius: 5px;">
                    <h4 style="margin-top: 0;">Message:</h4>
                    <p style="line-height: 1.6;">{inquiry.message.replace(chr(10), '<br>')}</p>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{url_for('admin_inquiry.inquiry_detail', id=inquiry.id, _external=True)}" 
                       style="background: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">
                       📋 View & Respond in Admin Panel
                    </a>
                </div>
                
                <hr style="margin: 20px 0; border: none; border-top: 1px solid #ddd;">
                <p style="font-size: 12px; color: #666;">
                    This notification was sent because the inquiry was flagged for human review by our automated system.
                </p>
            </div>
        </div>
        '''
        
        mail.send(msg)
        current_app.logger.info(f"Admin notification sent for inquiry {inquiry.id}")
    except Exception as e:
        current_app.logger.error(f"Failed to send admin notification: {e}")


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

        # Save inquiry to database
        try:
            from app.models import Inquiry
            inquiry = Inquiry(
                name=f"{first_name} {last_name}",
                email=email,
                phone=phone,
                subject=subject,
                message=message,
                inquiry_type='general',  # Default to general inquiry
                status='new',
                priority='medium',
                user_id=current_user.id if current_user.is_authenticated else None
            )
            db.session.add(inquiry)
            db.session.commit()
            current_app.logger.info(f"Inquiry saved successfully for {email}")
        except Exception as db_error:
            db.session.rollback()
            current_app.logger.error(f"Database error saving inquiry: {str(db_error)}")
            flash("Sorry, there was an error saving your message. Please try again.", "error")
            return redirect(url_for("main.index"))

        # Send notification email to admin
        try:
            send_inquiry_notification_email(
                {
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": email,
                    "phone": phone,
                    "subject": subject,
                    "message": message,
                }
            )
            flash(
                f"Thank you {first_name}! Your message has been sent. We'll get back to you soon.",
                "success",
            )
        except Exception as email_error:
            current_app.logger.error(f"Failed to send inquiry notification: {str(email_error)}")
            # Still show success message since the inquiry was saved
            flash(
                f"Thank you {first_name}! Your message has been received. We'll get back to you soon.",
                "success",
            )

    except Exception as e:
        current_app.logger.error(f"Unexpected error in send_message: {str(e)}")
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


@main_bp.route("/admin/reports")
@login_required
@admin_required
def admin_reports():
    """
    Admin reports and analytics page.
    """
    # Generate comprehensive report
    report_data = generate_comprehensive_report()

    if not report_data:
        flash("Error generating reports. Please try again.", "danger")
        return redirect(url_for("main.dashboard"))

    return render_template(
        "admin/reports.html", report=report_data, title="Reports & Analytics"
    )


@main_bp.route("/admin/reports/export")
@login_required
@admin_required
def export_bookings():
    """
    Export bookings data as CSV.
    """
    from flask import make_response
    from datetime import datetime, timedelta

    # Get date range from query parameters
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    if start_date:
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    if end_date:
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

    csv_content = export_bookings_to_csv(start_date, end_date)

    if not csv_content:
        flash("Error exporting data. Please try again.", "danger")
        return redirect(url_for("main.admin_reports"))

    # Create response with CSV content
    response = make_response(csv_content)
    response.headers["Content-Type"] = "text/csv"
    response.headers["Content-Disposition"] = (
        f'attachment; filename=bookings_export_{datetime.now().strftime("%Y%m%d")}.csv'
    )

    return response


@main_bp.route("/admin/reviews", methods=["GET", "POST"])
@admin_required
def admin_reviews():
    """
    Admin page to manage reviews, approve/delete, and view analytics.
    """
    # Approve or delete actions
    if request.method == "POST":
        review_id = request.form.get("review_id")
        action = request.form.get("action")
        review = Review.query.get(review_id)
        if review:
            if action == "approve":
                review.is_approved = True
                review.approved_at = datetime.utcnow()
                db.session.commit()
                flash("Review approved.", "success")
            elif action == "delete":
                db.session.delete(review)
                db.session.commit()
                flash("Review deleted.", "warning")
        return redirect(url_for("main.admin_reviews"))

    # Get all reviews (pending first)
    reviews = Review.query.order_by(
        Review.is_approved.asc(), Review.created_at.desc()
    ).all()
    # Revenue analytics
    total_revenue = (
        db.session.query(db.func.sum(Booking.total_amount))
        .filter(Booking.status == BookingStatus.CONFIRMED)
        .scalar()
        or 0
    )
    # Popular destinations
    popular_destinations = (
        db.session.query(Tour.destination, db.func.count(Booking.id))
        .join(Booking)
        .filter(Booking.status == BookingStatus.CONFIRMED)
        .group_by(Tour.destination)
        .order_by(db.func.count(Booking.id).desc())
        .limit(5)
        .all()
    )
    return render_template(
        "admin/reviews.html",
        reviews=reviews,
        total_revenue=total_revenue,
        popular_destinations=popular_destinations,
    )
