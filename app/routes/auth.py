"""
Authentication routes module.
Contains all authentication-related routes: login, logout, register, password reset, etc.
"""

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    current_app,
    abort,
)
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User, UserRole
from app.forms import (
    LoginForm,
    RegistrationForm,
    ForgotPasswordForm,
    ResetPasswordForm,
    ChangePasswordForm,
    EditProfileForm,
)
from app.utils import send_email, generate_reset_token, verify_reset_token
from datetime import datetime
import secrets

# Create authentication blueprint
auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """
    User registration route.
    Handles new user account creation.
    """

    # Redirect if user is already logged in
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = RegistrationForm()

    if form.validate_on_submit():
        try:
            # Create new user instance
            user = User(
                username=form.username.data,
                email=form.email.data.lower(),
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                phone=form.phone.data,
                role=UserRole.USER,  # Default role
            )

            # Set password (automatically hashed)
            user.set_password(form.password.data)

            # Save to database
            db.session.add(user)
            db.session.commit()

            flash("Registration successful! You can now log in.", "success")

            # Send welcome email (optional)
            try:
                send_welcome_email(user)
            except Exception as e:
                # Log error but don't fail registration
                current_app.logger.error(f"Failed to send welcome email: {str(e)}")

            return redirect(url_for("auth.login"))

        except Exception as e:
            db.session.rollback()
            flash("Registration failed. Please try again.", "danger")
            current_app.logger.error(f"Registration error: {str(e)}")
    else:
        # Show validation errors for debugging
        if form.errors:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"{field}: {error}", "danger")

    return render_template("auth/register.html", title="Register", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """
    User login route.
    Handles user authentication and session management.
    """

    # Redirect if user is already logged in
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = LoginForm()

    if form.validate_on_submit():
        # Check if input is email or username
        user_input = form.username_or_email.data

        if "@" in user_input:
            # Input is email
            user = User.query.filter_by(email=user_input.lower()).first()
        else:
            # Input is username
            user = User.query.filter_by(username=user_input).first()

        # Validate user and password
        if user and user.check_password(form.password.data):
            if user.is_active:
                # Log in the user
                login_user(user, remember=form.remember_me.data)

                # Update last login timestamp (you can add this field to User model)
                # user.last_login = datetime.utcnow()
                # db.session.commit()

                flash(f"Welcome back, {user.first_name}!", "success")

                # Redirect to next page or homepage
                next_page = request.args.get("next")
                if next_page:
                    return redirect(next_page)
                else:
                    # Redirect all users to homepage after login
                    return redirect(url_for("main.index"))
            else:
                flash(
                    "Your account has been deactivated. Please contact support.",
                    "warning",
                )
        else:
            flash("Invalid username/email or password.", "danger")

    return render_template("auth/login.html", title="Login", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    """
    User logout route.
    Handles user session termination.
    """

    user_name = current_user.first_name
    logout_user()
    flash(f"You have been logged out successfully, {user_name}.", "info")
    return redirect(url_for("main.index"))


@auth_bp.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    """
    Forgot password route.
    Handles password reset requests.
    """

    # Redirect if user is already logged in
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = ForgotPasswordForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()

        if user:
            # Generate reset token
            token = generate_reset_token(user)

            # Send reset email
            try:
                send_password_reset_email(user, token)
                flash(
                    "Password reset instructions have been sent to your email.", "info"
                )
            except Exception as e:
                flash("Failed to send reset email. Please try again later.", "danger")
                current_app.logger.error(f"Failed to send reset email: {str(e)}")
        else:
            # Don't reveal if email exists or not (security)
            flash("Password reset instructions have been sent to your email.", "info")

        return redirect(url_for("auth.login"))

    return render_template(
        "auth/forgot_password.html", title="Forgot Password", form=form
    )


@auth_bp.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    """
    Password reset route.
    Handles password reset with token validation.
    """

    # Redirect if user is already logged in
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    # Verify token
    user = verify_reset_token(token)
    if not user:
        flash("Invalid or expired reset token.", "danger")
        return redirect(url_for("auth.forgot_password"))

    form = ResetPasswordForm()

    if form.validate_on_submit():
        # Update password
        user.set_password(form.password.data)
        db.session.commit()

        flash(
            "Your password has been reset successfully. You can now log in.", "success"
        )
        return redirect(url_for("auth.login"))

    return render_template(
        "auth/reset_password.html", title="Reset Password", form=form
    )


@auth_bp.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    """
    Change password route for logged-in users.
    Handles password updates.
    """

    form = ChangePasswordForm()

    if form.validate_on_submit():
        # Verify current password
        if not current_user.check_password(form.current_password.data):
            flash("Current password is incorrect.", "danger")
            return render_template(
                "auth/change_password.html", title="Change Password", form=form
            )

        # Update password
        current_user.set_password(form.new_password.data)
        db.session.commit()

        flash("Your password has been updated successfully.", "success")
        return redirect(url_for("main.dashboard"))

    return render_template(
        "auth/change_password.html", title="Change Password", form=form
    )


@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    """
    User profile route.
    Handles profile viewing and updating.
    """

    form = EditProfileForm(current_user.username, current_user.email)

    if form.validate_on_submit():
        # Update user information
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.username = form.username.data
        current_user.email = form.email.data.lower()
        current_user.phone = form.phone.data
        current_user.bio = form.bio.data
        current_user.updated_at = datetime.utcnow()

        db.session.commit()
        flash("Your profile has been updated successfully.", "success")
        return redirect(url_for("auth.profile"))

    elif request.method == "GET":
        # Pre-populate form with current user data
        form.first_name.data = current_user.first_name
        form.last_name.data = current_user.last_name
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.phone.data = current_user.phone
        form.bio.data = current_user.bio

    return render_template("auth/edit_profile.html", title="Edit Profile", form=form)


@auth_bp.route("/dashboard")
@login_required
def dashboard():
    """
    User dashboard route.
    Shows user's bookings, reviews, and account information.
    """

    # Get user's recent bookings
    recent_bookings = (
        current_user.bookings.order_by(
            db.desc(current_user.bookings.property.mapper.class_.created_at)
        )
        .limit(5)
        .all()
    )

    # Get user's reviews
    user_reviews = (
        current_user.reviews.order_by(
            db.desc(current_user.reviews.property.mapper.class_.created_at)
        )
        .limit(5)
        .all()
    )

    # Calculate statistics
    total_bookings = len(current_user.bookings)
    completed_bookings = len(
        [b for b in current_user.bookings if b.status == "completed"]
    )

    return render_template(
        "auth/dashboard.html",
        title="Dashboard",
        recent_bookings=recent_bookings,
        user_reviews=user_reviews,
        total_bookings=total_bookings,
        completed_bookings=completed_bookings,
    )


@auth_bp.route("/test_reset_email")
def test_reset_email():
    """
    Development route to test password reset emails.
    Only works in development mode.
    """

    if not current_app.debug:
        abort(404)

    # Find a test user
    user = User.query.first()
    if not user:
        return "No users found. Create a user first."

    # Generate reset token
    token = generate_reset_token(user)

    # Create reset link
    reset_link = url_for("auth.reset_password", token=token, _external=True)

    return f"""
    <h2>Password Reset Test</h2>
    <p><strong>User:</strong> {user.email}</p>
    <p><strong>Reset Link:</strong></p>
    <p><a href="{reset_link}" target="_blank">{reset_link}</a></p>
    <p><em>This link is valid for 1 hour.</em></p>
    <hr>
    <a href="{url_for('auth.login')}">Back to Login</a>
    """


# Helper functions for email sending
def send_welcome_email(user):
    """Send welcome email to new user"""
    subject = "Welcome to Travel App!"
    body = f"""
    Dear {user.first_name},
    
    Welcome to Travel App! We're excited to have you join our community of travel enthusiasts.
    
    Your account has been created successfully. You can now:
    - Browse our amazing tour packages
    - Make bookings for your dream destinations
    - Leave reviews and share your experiences
    
    If you have any questions, feel free to contact our support team.
    
    Happy travels!
    The Travel App Team
    """

    send_email(subject, [user.email], body)


def send_password_reset_email(user, token):
    """Send password reset email"""
    subject = "Password Reset - Travel App"

    reset_url = url_for("auth.reset_password", token=token, _external=True)

    body = f"""
    Dear {user.first_name},
    
    You have requested to reset your password for your Travel App account.
    
    Please click the link below to reset your password:
    {reset_url}
    
    This link will expire in 1 hour for security reasons.
    
    If you did not request this password reset, please ignore this email.
    
    Best regards,
    The Travel App Team
    """

    send_email(subject, [user.email], body)


# Error handlers specific to authentication
@auth_bp.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors in auth blueprint"""
    return render_template("errors/404.html"), 404


@auth_bp.errorhandler(500)
def internal_error(error):
    """Handle 500 errors in auth blueprint"""
    db.session.rollback()
    return render_template("errors/500.html"), 500
