#!/usr/bin/env python3
"""
Email Configuration Test Script for Travel App

This script helps you test if your Gmail App Password is working correctly
before running the full application.

Usage:
1. Set up your Gmail App Password (see EMAIL_SETUP_GUIDE.md)
2. Update the .env file with your App Password
3. Run this script: python test_email.py
"""

import os
import sys
from flask import Flask
from flask_mail import Mail, Message
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_email_configuration():
    """Test email configuration with your Gmail App Password"""

    # Create a minimal Flask app for testing
    app = Flask(__name__)

    # Configure email settings from environment variables
    app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT", 587))
    app.config["MAIL_USE_TLS"] = os.getenv("MAIL_USE_TLS", "true").lower() == "true"
    app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
    app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
    app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_DEFAULT_SENDER")

    # Check if configuration is complete
    if not app.config["MAIL_USERNAME"]:
        print("❌ MAIL_USERNAME not set in .env file")
        return False

    if not app.config["MAIL_PASSWORD"]:
        print("❌ MAIL_PASSWORD not set in .env file")
        return False

    if app.config["MAIL_PASSWORD"] == "your-gmail-app-password-here":
        print("❌ MAIL_PASSWORD still has placeholder value")
        print("   Please update your .env file with your actual Gmail App Password")
        return False

    print("✅ Email configuration loaded from .env file")
    print(f"   Server: {app.config['MAIL_SERVER']}:{app.config['MAIL_PORT']}")
    print(f"   Username: {app.config['MAIL_USERNAME']}")
    print(f"   TLS: {app.config['MAIL_USE_TLS']}")
    print()

    # Initialize Flask-Mail
    mail = Mail(app)

    # Test sending an email
    try:
        with app.app_context():
            print("📧 Sending test email...")

            msg = Message(
                subject="Test Email from Travel App",
                recipients=[app.config["MAIL_USERNAME"]],  # Send to yourself
                body="This is a test email to verify your Gmail App Password configuration.\n\n"
                "If you receive this email, your configuration is working correctly!",
                sender=app.config["MAIL_DEFAULT_SENDER"],
            )

            mail.send(msg)
            print("✅ Test email sent successfully!")
            print(f"   Check your inbox at {app.config['MAIL_USERNAME']}")
            return True

    except Exception as e:
        print(f"❌ Failed to send test email: {str(e)}")
        print()
        print("Common solutions:")
        print(
            "1. Make sure you're using a Gmail App Password (not your regular password)"
        )
        print("2. Ensure 2-Factor Authentication is enabled on your Google account")
        print("3. Check that your App Password is correct in the .env file")
        print("4. Verify your Gmail username is correct")
        return False


def main():
    """Main function to run the email test"""
    print("🔧 Travel App Email Configuration Test")
    print("=" * 40)

    # Check if .env file exists
    if not os.path.exists(".env"):
        print("❌ .env file not found")
        print("   Please create a .env file with your email configuration")
        print("   See EMAIL_SETUP_GUIDE.md for detailed instructions")
        sys.exit(1)

    # Test email configuration
    success = test_email_configuration()

    if success:
        print()
        print("🎉 Email configuration test passed!")
        print("   You can now start your travel app and emails will be sent correctly.")
        print("   Run: python run.py")
    else:
        print()
        print("❌ Email configuration test failed!")
        print("   Please check the error messages above and fix your configuration.")
        print("   See EMAIL_SETUP_GUIDE.md for detailed setup instructions.")
        sys.exit(1)


if __name__ == "__main__":
    main()
