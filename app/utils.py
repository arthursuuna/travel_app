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
    Check if file extension is allowed.

    Args:
        filename (str): Filename to check

    Returns:
        bool: True if allowed, False otherwise
    """

    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in current_app.config["ALLOWED_EXTENSIONS"]
    )


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


def format_currency(amount, currency="USD"):
    """
    Format currency for display.

    Args:
        amount (float): Amount to format
        currency (str): Currency code

    Returns:
        str: Formatted currency string
    """

    currency_symbols = {"USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥"}

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


def send_inquiry_notification_email(inquiry):
    """
    Send inquiry notification email to admin.

    Args:
        inquiry (Inquiry): Inquiry object
    """

    # Get admin users
    admins = User.query.filter_by(role="admin").all()
    admin_emails = [admin.email for admin in admins]

    if not admin_emails:
        current_app.logger.warning("No admin users found for inquiry notification")
        return

    subject = f"New Inquiry: {inquiry.subject}"

    html_body = f"""
    <html>
    <body>
        <h2>New Customer Inquiry</h2>
        
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
            <h3>Inquiry Details</h3>
            <p><strong>From:</strong> {inquiry.name}</p>
            <p><strong>Email:</strong> {inquiry.email}</p>
            {f"<p><strong>Phone:</strong> {inquiry.phone}</p>" if inquiry.phone else ""}
            <p><strong>Type:</strong> {inquiry.inquiry_type.title()}</p>
            <p><strong>Subject:</strong> {inquiry.subject}</p>
            <p><strong>Date:</strong> {inquiry.created_at.strftime('%B %d, %Y at %I:%M %p')}</p>
        </div>
        
        <h3>Message</h3>
        <div style="background-color: #ffffff; padding: 15px; border-left: 4px solid #007bff;">
            <p>{inquiry.message}</p>
        </div>
        
        <p>Please respond to this inquiry as soon as possible.</p>
    </body>
    </html>
    """

    text_body = f"""
    New Customer Inquiry
    
    Inquiry Details:
    - From: {inquiry.name}
    - Email: {inquiry.email}
    {f"- Phone: {inquiry.phone}" if inquiry.phone else ""}
    - Type: {inquiry.inquiry_type.title()}
    - Subject: {inquiry.subject}
    - Date: {inquiry.created_at.strftime('%B %d, %Y at %I:%M %p')}
    
    Message:
    {inquiry.message}
    
    Please respond to this inquiry as soon as possible.
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
