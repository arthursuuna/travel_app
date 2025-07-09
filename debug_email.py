#!/usr/bin/env python3
"""
Quick email test to debug your configuration.
This will help us see exactly what's happening with your email setup.
"""

import os
from dotenv import load_dotenv
from flask import Flask
from flask_mail import Mail, Message

# Load environment variables
load_dotenv()


def test_email_debug():
    """Test email configuration with detailed debugging"""

    print("=== EMAIL CONFIGURATION TEST ===")
    print(f"MAIL_SERVER: {os.environ.get('MAIL_SERVER')}")
    print(f"MAIL_PORT: {os.environ.get('MAIL_PORT')}")
    print(f"MAIL_USE_TLS: {os.environ.get('MAIL_USE_TLS')}")
    print(f"MAIL_USERNAME: {os.environ.get('MAIL_USERNAME')}")
    print(
        f"MAIL_PASSWORD: {'*' * len(os.environ.get('MAIL_PASSWORD', '')) if os.environ.get('MAIL_PASSWORD') else 'NOT SET'}"
    )
    print(f"MAIL_DEFAULT_SENDER: {os.environ.get('MAIL_DEFAULT_SENDER')}")
    print()

    # Create Flask app
    app = Flask(__name__)
    app.config["MAIL_SERVER"] = os.environ.get("MAIL_SERVER")
    app.config["MAIL_PORT"] = int(os.environ.get("MAIL_PORT", 587))
    app.config["MAIL_USE_TLS"] = (
        os.environ.get("MAIL_USE_TLS", "true").lower() == "true"
    )
    app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME")
    app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD")
    app.config["MAIL_DEFAULT_SENDER"] = os.environ.get("MAIL_DEFAULT_SENDER")

    # Check if required values are set
    if not app.config["MAIL_USERNAME"]:
        print("❌ MAIL_USERNAME is not set")
        return False

    if not app.config["MAIL_PASSWORD"]:
        print("❌ MAIL_PASSWORD is not set")
        return False

    # Initialize Flask-Mail
    mail = Mail(app)

    try:
        with app.app_context():
            print("📧 Attempting to send test email...")

            msg = Message(
                subject="Test Email - Travel App Debug",
                recipients=[app.config["MAIL_USERNAME"]],  # Send to yourself
                body="This is a test email to debug your configuration.\n\nIf you receive this, your email setup is working!",
                sender=app.config["MAIL_DEFAULT_SENDER"],
            )

            mail.send(msg)
            print("✅ Email sent successfully!")
            print(f"📩 Check your inbox at {app.config['MAIL_USERNAME']}")
            return True

    except Exception as e:
        print(f"❌ Failed to send email: {str(e)}")

        # Common error messages and solutions
        if "Authentication failed" in str(e):
            print("\n🔧 SOLUTION: Check your Gmail App Password")
            print(
                "   - Make sure you're using an App Password, not your regular password"
            )
            print("   - Verify 2FA is enabled on your Google account")
            print("   - Try generating a new App Password")

        elif "Connection refused" in str(e):
            print("\n🔧 SOLUTION: Check your network/firewall")
            print("   - Your firewall might be blocking SMTP connections")
            print("   - Try temporarily disabling your firewall")

        elif "timeout" in str(e).lower():
            print("\n🔧 SOLUTION: Network timeout")
            print("   - Check your internet connection")
            print("   - Try using a different network")

        return False


if __name__ == "__main__":
    success = test_email_debug()

    if success:
        print("\n🎉 Email configuration is working!")
        print("   Your Flask app should now be able to send emails.")
        print("   Make sure to restart your Flask app: python run.py")
    else:
        print("\n❌ Email configuration failed!")
        print("   Fix the issues above and try again.")
