"""
Utility functions for the Travel App.
This module contains helper functions for email, security, and other utilities.
"""

from flask import current_app
from flask_mail import Message
from app import mail, db
from app.models import User
import secrets
import jwt  # Helper library for encoding and decoding JSON Web Tokens (JWT).for  security and password reset functionality.
from datetime import datetime, timedelta
import os
from PIL import (
    Image,
)  # PIL (Python Imaging Library) is used for image processing tasks.
import uuid  # uuid is used to generate unique identifiers for files.
from werkzeug.utils import secure_filename


def send_email(subject, recipients, body, html_body=None):
    """
    Send email using Flask-Mail

    Args:
        subject (str): Email subject
        recipients (list): List of recipient email addresses
        body (str): Plain text email body
        html_body (str, optional): HTML email body
    """

    try:
        # For development - if email is not configured, just log the email
        if (
            not current_app.config.get("MAIL_USERNAME")
            or current_app.config.get("MAIL_USERNAME") == "your-email@gmail.com"
            or current_app.config.get("MAIL_PASSWORD") == "your-gmail-app-password-here"
        ):
            current_app.logger.info(f"=== EMAIL SIMULATION ===")
            current_app.logger.info(f"To: {recipients}")
            current_app.logger.info(f"Subject: {subject}")
            current_app.logger.info(f"Body: {body}")
            current_app.logger.info("=== END EMAIL ===")
            return

        msg = Message(
            subject=subject,
            recipients=recipients,
            body=body,
            html=html_body,
            sender=current_app.config["MAIL_DEFAULT_SENDER"],
        )

        mail.send(msg)
        current_app.logger.info(f"Email sent successfully to {recipients}")

    except Exception as e:
        current_app.logger.error(f"Failed to send email: {str(e)}")
        raise


def generate_reset_token(user):
    """
    Generate a password reset token for a user.

    Args:
        user (User): User object

    Returns:
        str: JWT token for password reset
    """

    try:
        payload = {
            "user_id": user.id,
            "exp": datetime.utcnow() + timedelta(hours=1),  # Token expires in 1 hour
        }

        token = jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")

        return token

    except Exception as e:
        current_app.logger.error(f"Failed to generate reset token: {str(e)}")
        raise


def verify_reset_token(token):
    """
    Verify and decode a password reset token.

    Args:
        token (str): JWT token

    Returns:
        User or None: User object if token is valid, None otherwise
    """

    try:
        payload = jwt.decode(
            token, current_app.config["SECRET_KEY"], algorithms=["HS256"]
        )

        user_id = payload["user_id"]
        user = User.query.get(user_id)

        return user

    except jwt.ExpiredSignatureError:
        current_app.logger.warning("Reset token has expired")
        return None
    except jwt.InvalidTokenError:
        current_app.logger.warning("Invalid reset token")
        return None
    except Exception as e:
        current_app.logger.error(f"Failed to verify reset token: {str(e)}")
        return None


def generate_secure_filename(filename):
    """
    Generate a secure filename for uploaded files.

    Args:
        filename (str): Original filename

    Returns:
        str: Secure filename
    """

    # Get file extension
    if "." in filename:
        extension = filename.rsplit(".", 1)[1].lower()
    else:
        extension = ""

    # Generate unique filename
    unique_filename = str(uuid.uuid4())

    if extension:
        return f"{unique_filename}.{extension}"
    else:
        return unique_filename


def allowed_file(filename):
    """
    Check if the uploaded file has an allowed extension.

    Args:
        filename (str): The name of the uploaded file

    Returns:
        bool: True if file extension is allowed, False otherwise
    """
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_image(image_file, folder, max_size=(800, 600)):
    """
    Save and resize an uploaded image.

    Args:
        image_file: FileStorage object from form
        folder (str): Folder to save image in
        max_size (tuple): Maximum dimensions (width, height)

    Returns:
        str: Saved filename
    """

    try:
        # Generate secure filename
        filename = generate_secure_filename(image_file.filename)

        # Create full path
        upload_path = os.path.join(current_app.root_path, "static", "images", folder)
        os.makedirs(upload_path, exist_ok=True)

        file_path = os.path.join(upload_path, filename)

        # Open and resize image
        img = Image.open(image_file)

        # Convert to RGB if necessary (for PNG with transparency)
        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGB")

        # Resize image while maintaining aspect ratio
        img.thumbnail(max_size, Image.Resampling.LANCZOS)

        # Save image
        img.save(file_path, "JPEG", quality=85, optimize=True)

        return filename

    except Exception as e:
        current_app.logger.error(f"Failed to save image: {str(e)}")
        raise


def save_tour_image(image_file):
    """
    Save and process uploaded tour image.

    Args:
        image_file: FileStorage object from form upload

    Returns:
        str: Relative URL path to saved image, or None if error
    """
    if not image_file or not allowed_file(image_file.filename):
        return None

    try:
        # Generate unique filename
        filename = secure_filename(image_file.filename)
        name, ext = os.path.splitext(filename)
        unique_filename = f"tour_{uuid.uuid4().hex[:8]}{ext}"

        # Create upload path
        upload_dir = os.path.join(current_app.root_path, "static", "images", "tours")
        os.makedirs(upload_dir, exist_ok=True)

        file_path = os.path.join(upload_dir, unique_filename)

        # Save and resize image
        image = Image.open(image_file)

        # Convert RGBA to RGB if necessary (for JPEG compatibility)
        if image.mode in ("RGBA", "LA", "P"):
            background = Image.new("RGB", image.size, (255, 255, 255))
            if image.mode == "P":
                image = image.convert("RGBA")
            background.paste(
                image, mask=image.split()[-1] if "A" in image.mode else None
            )
            image = background

        # Resize image (max 1200x800, maintain aspect ratio)
        max_size = (1200, 800)
        image.thumbnail(max_size, Image.Resampling.LANCZOS)

        # Save with optimization
        if ext.lower() in [".jpg", ".jpeg"]:
            image.save(file_path, "JPEG", quality=85, optimize=True)
        else:
            image.save(file_path, quality=85, optimize=True)

        # Return relative URL path
        return f"/static/images/tours/{unique_filename}"

    except Exception as e:
        current_app.logger.error(f"Error saving tour image: {str(e)}")
        return None


def delete_tour_image(image_url):
    """
    Delete tour image file from filesystem.

    Args:
        image_url (str): URL path to the image file
    """
    if not image_url or not image_url.startswith("/static/images/tours/"):
        return

    try:
        # Extract filename from URL
        filename = os.path.basename(image_url)
        file_path = os.path.join(
            current_app.root_path, "static", "images", "tours", filename
        )

        if os.path.exists(file_path):
            os.remove(file_path)
            current_app.logger.info(f"Deleted tour image: {filename}")

    except Exception as e:
        current_app.logger.error(f"Error deleting tour image: {str(e)}")


def format_currency(amount, currency="USD"):
    """
    Format currency for display.

    Args:
        amount (float): Amount to format
        currency (str): Currency code

    Returns:
        str: Formatted currency string
    """

    currency_symbols = {"USD": "$", "EUR": "EUR", "GBP": "GBP", "JPY": "JPY"}

    symbol = currency_symbols.get(currency, currency)
    return f"{symbol}{amount:,.2f}"


def calculate_age(birth_date):
    """
    Calculate age from birth date.

    Args:
        birth_date (date): Birth date

    Returns:
        int: Age in years
    """

    today = datetime.now().date()
    age = today.year - birth_date.year

    # Check if birthday hasn't occurred this year
    if today.month < birth_date.month or (
        today.month == birth_date.month and today.day < birth_date.day
    ):
        age -= 1

    return age


def generate_booking_reference():
    """
    Generate a unique booking reference number.

    Returns:
        str: Booking reference
    """

    from app.models import Booking

    while True:
        # Generate reference: TRV-YYYY-XXXXXX
        year = datetime.now().year
        random_part = secrets.token_hex(3).upper()  # 6 character hex string
        reference = f"TRV-{year}-{random_part}"

        # Check if reference already exists
        existing = Booking.query.filter_by(booking_reference=reference).first()
        if not existing:
            return reference


def send_booking_confirmation_email(booking):
    """
    Send booking confirmation email to user.

    Args:
        booking (Booking): Booking object
    """

    subject = f"Booking Confirmation - {booking.booking_reference}"

    html_body = f"""
    <html>
    <body>
        <h2>Booking Confirmation</h2>
        <p>Dear {booking.user.first_name},</p>
        
        <p>Thank you for booking with Travel App! Your booking has been confirmed.</p>
        
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
            <h3>Booking Details</h3>
            <p><strong>Booking Reference:</strong> {booking.booking_reference}</p>
            <p><strong>Tour:</strong> {booking.tour.title}</p>
            <p><strong>Destination:</strong> {booking.tour.destination}</p>
            <p><strong>Travel Date:</strong> {booking.travel_date.strftime('%B %d, %Y')}</p>
            <p><strong>Participants:</strong> {booking.participants}</p>
            <p><strong>Total Amount:</strong> {format_currency(booking.total_amount)}</p>
            <p><strong>Status:</strong> {booking.status.value.title()}</p>
        </div>
        
        <p>We will contact you closer to your travel date with detailed information.</p>
        
        <p>If you have any questions, please contact our support team.</p>
        
        <p>Best regards,<br>The Travel App Team</p>
    </body>
    </html>
    """

    text_body = f"""
    Booking Confirmation
    
    Dear {booking.user.first_name},
    
    Thank you for booking with Travel App! Your booking has been confirmed.
    
    Booking Details:
    - Booking Reference: {booking.booking_reference}
    - Tour: {booking.tour.title}
    - Destination: {booking.tour.destination}
    - Travel Date: {booking.travel_date.strftime('%B %d, %Y')}
    - Participants: {booking.participants}
    - Total Amount: {format_currency(booking.total_amount)}
    - Status: {booking.status.value.title()}
    
    We will contact you closer to your travel date with detailed information.
    
    If you have any questions, please contact our support team.
    
    Best regards,
    The Travel App Team
    """

    send_email(subject, [booking.user.email], text_body, html_body)


def send_inquiry_notification_email(inquiry_data):
    """
    Send inquiry notification email to admin.

    Args:
        inquiry_data (dict): Inquiry data dictionary
    """

    # Get admin users
    admins = User.query.filter_by(is_admin=True).all()
    admin_emails = [admin.email for admin in admins]

    if not admin_emails:
        current_app.logger.warning("No admin users found for inquiry notification")
        # Fallback to configured admin email
        admin_emails = [
            current_app.config.get("MAIL_DEFAULT_SENDER", "admin@travelapp.com")
        ]

    subject = f"New Inquiry: {inquiry_data['subject']}"

    html_body = f"""
    <html>
    <body>
        <h2>New Customer Inquiry</h2>
        
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
            <h3>Inquiry Details</h3>
            <p><strong>From:</strong> {inquiry_data['first_name']} {inquiry_data['last_name']}</p>
            <p><strong>Email:</strong> {inquiry_data['email']}</p>
            {f"<p><strong>Phone:</strong> {inquiry_data['phone']}</p>" if inquiry_data.get('phone') else ""}
            <p><strong>Subject:</strong> {inquiry_data['subject']}</p>
            <p><strong>Date:</strong> {datetime.utcnow().strftime('%B %d, %Y at %I:%M %p')}</p>
        </div>
        
        <h3>Message</h3>
        <div style="background-color: #ffffff; padding: 15px; border-left: 4px solid #007bff;">
            <p>{inquiry_data['message']}</p>
        </div>
        
        <p>Please respond to this inquiry as soon as possible.</p>
        <p>Reply directly to: {inquiry_data['email']}</p>
    </body>
    </html>
    """

    text_body = f"""
    New Customer Inquiry
    
    From: {inquiry_data['first_name']} {inquiry_data['last_name']}
    Email: {inquiry_data['email']}
    {f"Phone: {inquiry_data['phone']}" if inquiry_data.get('phone') else ""}
    Subject: {inquiry_data['subject']}
    Date: {datetime.utcnow().strftime('%B %d, %Y at %I:%M %p')}
    
    Message:
    {inquiry_data['message']}
    
    Please respond to this inquiry as soon as possible.
    Reply directly to: {inquiry_data['email']}
    """

    send_email(subject, admin_emails, text_body, html_body)


def validate_and_format_phone(phone):
    """
    Validate and format phone number.

    Args:
        phone (str): Phone number string

    Returns:
        str or None: Formatted phone number or None if invalid
    """

    import re

    if not phone:
        return None

    # Remove all non-digit characters
    digits = re.sub(r"[^0-9]", "", phone)

    # Check if it's a valid length
    if len(digits) < 10 or len(digits) > 15:
        return None

    # Format for US/Canada numbers
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11 and digits[0] == "1":
        return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    else:
        # International format
        return f"+{digits}"


def create_admin_user():
    """
    Create an admin user if none exists.
    This is useful for initial setup.
    """

    from app.models import UserRole

    # Check if admin exists
    admin = User.query.filter_by(role=UserRole.ADMIN).first()

    if not admin:
        # Create admin user
        admin = User(
            username="admin",
            email="admin@travelapp.com",
            first_name="Admin",
            last_name="User",
            role=UserRole.ADMIN,
        )
        admin.set_password("admin123")  # Change this in production!

        db.session.add(admin)
        db.session.commit()

        current_app.logger.info("Admin user created successfully")
        return admin

    return admin


def send_password_reset_email(user, token):
    """
    Send password reset email to user.

    Args:
        user (User): User object
        token (str): Password reset token
    """

    from flask import url_for, render_template

    subject = "Password Reset Request - Travel App"

    # Create reset link
    reset_link = url_for("auth.reset_password", token=token, _external=True)

    # Create email body
    body = f"""Hello {user.first_name},

You have requested a password reset for your Travel App account.

Please click the following link to reset your password:
{reset_link}

This link will expire in 1 hour for security reasons.

If you did not request this password reset, please ignore this email.

Best regards,
Travel App Team
"""

    # Create HTML email body
    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #007bff;">Travel App</h1>
        </div>
        
        <div style="background: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px;">
            <h2 style="color: #333; margin-top: 0;">Password Reset Request</h2>
            <p>Hello {user.first_name},</p>
            <p>You have requested a password reset for your Travel App account.</p>
        </div>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="{reset_link}" 
               style="background: #007bff; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                Reset Password
            </a>
        </div>
        
        <div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <p style="margin: 0; color: #856404;">
                <strong>Security Notice:</strong> This link will expire in 1 hour for security reasons.
            </p>
        </div>
        
        <p style="color: #6c757d; font-size: 14px;">
            If you did not request this password reset, please ignore this email. 
            Your account will remain secure.
        </p>
        
        <hr style="margin: 30px 0; border: 1px solid #e9ecef;">
        
        <div style="text-align: center; color: #6c757d; font-size: 12px;">
            <p>Travel App Team<br>
            <a href="mailto:support@travelapp.com" style="color: #007bff;">support@travelapp.com</a></p>
        </div>
    </div>
    """

    try:
        send_email(
            subject=subject, recipients=[user.email], body=body, html_body=html_body
        )
        current_app.logger.info(f"Password reset email sent to {user.email}")

    except Exception as e:
        current_app.logger.error(
            f"Failed to send password reset email to {user.email}: {str(e)}"
        )
        raise
