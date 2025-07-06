"""
Complete Database Reset Script
=============================
⚠️ WARNING: This script completely wipes the database and recreates it.
This will delete EVERYTHING including user accounts.

Use this only if you want to start completely fresh.
"""

from app import create_app
from app.models import db


def reset_database():
    """
    Completely reset the database.
    ⚠️ This deletes ALL data including users!
    """
    app = create_app()

    with app.app_context():
        print("⚠️ WARNING: This will delete ALL data including users!")
        print("🗑️ Starting complete database reset...")

        try:
            # Drop all tables
            db.drop_all()
            print("✅ All tables dropped")

            # Recreate all tables
            db.create_all()
            print("✅ All tables recreated")

            print("✅ Database reset completed!")
            print("🔄 You'll need to register a new user account")

        except Exception as e:
            print(f"❌ Error during reset: {str(e)}")
            raise


if __name__ == "__main__":
    # Safety check
    confirm = input(
        "Are you sure you want to reset the ENTIRE database? (type 'YES' to confirm): "
    )
    if confirm == "YES":
        reset_database()
    else:
        print("❌ Database reset cancelled")
