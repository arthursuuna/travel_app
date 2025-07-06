"""
Forms for the Travel App.
This module contains all form classes for user input validation.
"""

from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    BooleanField,
    SubmitField,
    TextAreaField,
    SelectField,
    IntegerField,
    FloatField,
    DateField,
    HiddenField,
)
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    Length,
    ValidationError,
    NumberRange,
    Optional,
)
from wtforms.widgets import TextArea
from app.models import User, Tour, Category


class RegistrationForm(FlaskForm):
    """
    User registration form with validation.
    Handles new user account creation.
    """

    # Personal Information
    first_name = StringField(
        "First Name",
        validators=[
            DataRequired(message="First name is required"),
            Length(
                min=2, max=50, message="First name must be between 2 and 50 characters"
            ),
        ],
    )

    last_name = StringField(
        "Last Name",
        validators=[
            DataRequired(message="Last name is required"),
            Length(
                min=2, max=50, message="Last name must be between 2 and 50 characters"
            ),
        ],
    )

    # Account Information
    username = StringField(
        "Username",
        validators=[
            DataRequired(message="Username is required"),
            Length(
                min=4, max=20, message="Username must be between 4 and 20 characters"
            ),
        ],
    )

    email = StringField(
        "Email",
        validators=[
            DataRequired(message="Email is required"),
            Email(message="Please enter a valid email address"),
            Length(max=120, message="Email must be less than 120 characters"),
        ],
    )

    phone = StringField(
        "Phone Number",
        validators=[
            Optional(),
            Length(max=20, message="Phone number must be less than 20 characters"),
        ],
    )

    # Password Information
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(message="Password is required"),
            Length(min=8, message="Password must be at least 8 characters long"),
        ],
    )

    password2 = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(message="Please confirm your password"),
            EqualTo("password", message="Passwords must match"),
        ],
    )

    # Terms and Conditions
    terms_accepted = BooleanField(
        "I agree to the Terms and Conditions",
        validators=[DataRequired(message="You must accept the terms and conditions")],
    )

    submit = SubmitField("Register")

    def validate_username(self, username):
        """Check if username is already taken"""
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError(
                "Username already exists. Please choose a different one."
            )

    def validate_email(self, email):
        """Check if email is already registered"""
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError(
                "Email already registered. Please use a different email or login."
            )


class LoginForm(FlaskForm):
    """
    User login form.
    Handles user authentication.
    """

    username_or_email = StringField(
        "Username or Email",
        validators=[
            DataRequired(message="Username or email is required"),
            Length(max=120, message="Input too long"),
        ],
    )

    password = PasswordField(
        "Password", validators=[DataRequired(message="Password is required")]
    )

    remember_me = BooleanField("Remember Me")
    submit = SubmitField("Login")


class ForgotPasswordForm(FlaskForm):
    """
    Forgot password form.
    Handles password reset requests.
    """

    email = StringField(
        "Email",
        validators=[
            DataRequired(message="Email is required"),
            Email(message="Please enter a valid email address"),
        ],
    )

    submit = SubmitField("Reset Password")

    def validate_email(self, email):
        """Check if email exists in database"""
        user = User.query.filter_by(email=email.data).first()
        if not user:
            raise ValidationError("No account found with that email address.")


class ResetPasswordForm(FlaskForm):
    """
    Password reset form.
    Handles setting new password after reset.
    """

    password = PasswordField(
        "New Password",
        validators=[
            DataRequired(message="Password is required"),
            Length(min=8, message="Password must be at least 8 characters long"),
        ],
    )

    password2 = PasswordField(
        "Confirm New Password",
        validators=[
            DataRequired(message="Please confirm your password"),
            EqualTo("password", message="Passwords must match"),
        ],
    )

    submit = SubmitField("Reset Password")


class ChangePasswordForm(FlaskForm):
    """
    Change password form for logged-in users.
    Handles password updates.
    """

    current_password = PasswordField(
        "Current Password",
        validators=[DataRequired(message="Current password is required")],
    )

    new_password = PasswordField(
        "New Password",
        validators=[
            DataRequired(message="New password is required"),
            Length(min=8, message="Password must be at least 8 characters long"),
        ],
    )

    new_password2 = PasswordField(
        "Confirm New Password",
        validators=[
            DataRequired(message="Please confirm your new password"),
            EqualTo("new_password", message="Passwords must match"),
        ],
    )

    submit = SubmitField("Change Password")


class ProfileUpdateForm(FlaskForm):
    """
    Profile update form.
    Handles user profile information updates.
    """

    first_name = StringField(
        "First Name",
        validators=[
            DataRequired(message="First name is required"),
            Length(
                min=2, max=50, message="First name must be between 2 and 50 characters"
            ),
        ],
    )

    last_name = StringField(
        "Last Name",
        validators=[
            DataRequired(message="Last name is required"),
            Length(
                min=2, max=50, message="Last name must be between 2 and 50 characters"
            ),
        ],
    )

    email = StringField(
        "Email",
        validators=[
            DataRequired(message="Email is required"),
            Email(message="Please enter a valid email address"),
            Length(max=120, message="Email must be less than 120 characters"),
        ],
    )

    phone = StringField(
        "Phone Number",
        validators=[
            Optional(),
            Length(max=20, message="Phone number must be less than 20 characters"),
        ],
    )

    submit = SubmitField("Update Profile")

    def __init__(self, original_email, *args, **kwargs):
        """Initialize with current user's email to avoid validation error"""
        super(ProfileUpdateForm, self).__init__(*args, **kwargs)
        self.original_email = original_email

    def validate_email(self, email):
        """Check if email is already taken by another user"""
        if email.data != self.original_email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError(
                    "Email already registered. Please use a different email."
                )


class ContactForm(FlaskForm):
    """
    Contact/Inquiry form.
    Handles customer inquiries and support requests.
    """

    name = StringField(
        "Full Name",
        validators=[
            DataRequired(message="Name is required"),
            Length(min=2, max=100, message="Name must be between 2 and 100 characters"),
        ],
    )

    email = StringField(
        "Email",
        validators=[
            DataRequired(message="Email is required"),
            Email(message="Please enter a valid email address"),
        ],
    )

    phone = StringField(
        "Phone Number",
        validators=[
            Optional(),
            Length(max=20, message="Phone number must be less than 20 characters"),
        ],
    )

    subject = StringField(
        "Subject",
        validators=[
            DataRequired(message="Subject is required"),
            Length(
                min=5, max=200, message="Subject must be between 5 and 200 characters"
            ),
        ],
    )

    inquiry_type = SelectField(
        "Inquiry Type",
        choices=[
            ("general", "General Inquiry"),
            ("booking", "Booking Question"),
            ("complaint", "Complaint"),
            ("suggestion", "Suggestion"),
        ],
        validators=[DataRequired()],
    )

    message = TextAreaField(
        "Message",
        validators=[
            DataRequired(message="Message is required"),
            Length(
                min=10,
                max=1000,
                message="Message must be between 10 and 1000 characters",
            ),
        ],
    )

    submit = SubmitField("Send Message")


class TourSearchForm(FlaskForm):
    """
    Tour search and filter form.
    Handles tour searching and filtering.
    """

    search_query = StringField(
        "Search Tours",
        validators=[
            Optional(),
            Length(max=200, message="Search query must be less than 200 characters"),
        ],
    )

    category = SelectField(
        "Category", choices=[("", "All Categories")], validators=[Optional()]
    )

    min_price = FloatField(
        "Min Price",
        validators=[Optional(), NumberRange(min=0, message="Price must be positive")],
    )

    max_price = FloatField(
        "Max Price",
        validators=[Optional(), NumberRange(min=0, message="Price must be positive")],
    )

    duration = SelectField(
        "Duration",
        choices=[
            ("", "Any Duration"),
            ("1", "1 Day"),
            ("2-3", "2-3 Days"),
            ("4-7", "4-7 Days"),
            ("8+", "8+ Days"),
        ],
        validators=[Optional()],
    )

    difficulty = SelectField(
        "Difficulty",
        choices=[
            ("", "Any Difficulty"),
            ("Easy", "Easy"),
            ("Medium", "Medium"),
            ("Hard", "Hard"),
        ],
        validators=[Optional()],
    )

    submit = SubmitField("Search")

    def __init__(self, *args, **kwargs):
        """Initialize with dynamic category choices"""
        super(TourSearchForm, self).__init__(*args, **kwargs)
        self.category.choices = [("", "All Categories")] + [
            (str(cat.id), cat.name)
            for cat in Category.query.filter_by(is_active=True).all()
        ]


class BookingForm(FlaskForm):
    """
    Tour booking form.
    Handles tour reservations by users.

    Features:
    - Participant count selection
    - Booking date selection
    - Special requests field
    - Contact information validation
    - Terms acceptance
    """

    # Booking Details
    participants = IntegerField(
        "Number of Participants",
        validators=[
            DataRequired(message="Number of participants is required"),
            NumberRange(min=1, max=50, message="Participants must be between 1 and 50"),
        ],
        default=1,
    )

    booking_date = DateField(
        "Preferred Tour Date",
        validators=[DataRequired(message="Tour date is required")],
    )

    # Contact Information
    contact_phone = StringField(
        "Contact Phone",
        validators=[
            DataRequired(message="Contact phone is required"),
            Length(max=20, message="Phone number must be less than 20 characters"),
        ],
    )

    emergency_contact = StringField(
        "Emergency Contact",
        validators=[
            Optional(),
            Length(
                max=100, message="Emergency contact must be less than 100 characters"
            ),
        ],
    )

    # Special Requests
    special_requests = TextAreaField(
        "Special Requests",
        validators=[
            Optional(),
            Length(
                max=500, message="Special requests must be less than 500 characters"
            ),
        ],
        render_kw={
            "rows": 3,
            "placeholder": "Any dietary restrictions, accessibility needs, or special requests...",
        },
    )

    # Terms and Conditions
    terms_accepted = BooleanField(
        "I agree to the booking terms and conditions",
        validators=[
            DataRequired(message="You must accept the booking terms and conditions")
        ],
    )

    submit = SubmitField("Book Now")

    def validate_booking_date(self, booking_date):
        """Check if booking date is in the future"""
        from datetime import date

        if booking_date.data <= date.today():
            raise ValidationError("Booking date must be in the future")


class BookingUpdateForm(FlaskForm):
    """
    Booking update form for users to modify their bookings.
    Only allows certain fields to be updated.
    """

    participants = IntegerField(
        "Number of Participants",
        validators=[
            DataRequired(message="Number of participants is required"),
            NumberRange(min=1, max=50, message="Participants must be between 1 and 50"),
        ],
    )

    booking_date = DateField(
        "Preferred Tour Date",
        validators=[DataRequired(message="Tour date is required")],
    )

    contact_phone = StringField(
        "Contact Phone",
        validators=[
            DataRequired(message="Contact phone is required"),
            Length(max=20, message="Phone number must be less than 20 characters"),
        ],
    )

    emergency_contact = StringField(
        "Emergency Contact",
        validators=[
            Optional(),
            Length(
                max=100, message="Emergency contact must be less than 100 characters"
            ),
        ],
    )

    special_requests = TextAreaField(
        "Special Requests",
        validators=[
            Optional(),
            Length(
                max=500, message="Special requests must be less than 500 characters"
            ),
        ],
        render_kw={"rows": 3},
    )

    submit = SubmitField("Update Booking")

    def validate_booking_date(self, booking_date):
        """Check if booking date is in the future"""
        from datetime import date

        if booking_date.data <= date.today():
            raise ValidationError("Booking date must be in the future")


class BookingCancelForm(FlaskForm):
    """
    Simple form for booking cancellation confirmation.
    """

    cancel_reason = TextAreaField(
        "Reason for Cancellation (Optional)",
        validators=[
            Optional(),
            Length(max=250, message="Reason must be less than 250 characters"),
        ],
        render_kw={
            "rows": 2,
            "placeholder": "Please let us know why you're cancelling...",
        },
    )

    submit = SubmitField("Cancel Booking")


class EditProfileForm(FlaskForm):
    """
    Edit profile form.
    Allows users to update their profile information.

    Features:
    - Update personal information
    - Change username (with validation)
    - Update email (with validation)
    - Update phone number
    - Bio/description field
    - Profile picture upload (optional)
    """

    # Personal Information
    first_name = StringField(
        "First Name",
        validators=[
            DataRequired(message="First name is required"),
            Length(
                min=2, max=50, message="First name must be between 2 and 50 characters"
            ),
        ],
    )

    last_name = StringField(
        "Last Name",
        validators=[
            DataRequired(message="Last name is required"),
            Length(
                min=2, max=50, message="Last name must be between 2 and 50 characters"
            ),
        ],
    )

    username = StringField(
        "Username",
        validators=[
            DataRequired(message="Username is required"),
            Length(
                min=4, max=25, message="Username must be between 4 and 25 characters"
            ),
        ],
    )

    email = StringField(
        "Email",
        validators=[
            DataRequired(message="Email is required"),
            Email(message="Please enter a valid email address"),
        ],
    )

    phone = StringField(
        "Phone Number",
        validators=[
            Optional(),
            Length(max=20, message="Phone number must be less than 20 characters"),
        ],
    )

    bio = TextAreaField(
        "Bio",
        validators=[
            Optional(),
            Length(max=500, message="Bio must be less than 500 characters"),
        ],
        render_kw={
            "rows": 4,
            "placeholder": "Tell us a little about yourself...",
        },
    )

    submit = SubmitField("Update Profile")

    def __init__(self, original_username, original_email, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email

    def validate_username(self, username):
        """Check if username is already taken by another user"""
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError(
                    "Username already taken. Please choose a different one."
                )

    def validate_email(self, email):
        """Check if email is already registered by another user"""
        if email.data != self.original_email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError(
                    "Email already registered. Please choose a different one."
                )


class ChangePasswordForm(FlaskForm):
    """
    Change password form.
    Allows users to change their password.
    """

    current_password = PasswordField(
        "Current Password",
        validators=[DataRequired(message="Current password is required")],
    )

    new_password = PasswordField(
        "New Password",
        validators=[
            DataRequired(message="New password is required"),
            Length(min=8, message="Password must be at least 8 characters long"),
        ],
    )

    confirm_password = PasswordField(
        "Confirm New Password",
        validators=[
            DataRequired(message="Please confirm your new password"),
            EqualTo("new_password", message="Passwords must match"),
        ],
    )

    submit = SubmitField("Change Password")
