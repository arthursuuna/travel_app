"""
Create an admin user for the travel app
"""

from app import create_app, db
from app.models import User, UserRole
from getpass import getpass


def create_admin_user():
    app = create_app()

    with app.app_context():
        print("=== Create Admin User ===")

        # Get user details
        username = input("Enter username: ")
        email = input("Enter email: ")
        first_name = input("Enter first name: ")
        last_name = input("Enter last name: ")
        password = getpass("Enter password: ")
        confirm_password = getpass("Confirm password: ")

        # Validate password
        if password != confirm_password:
            print("❌ Passwords don't match!")
            return

        # Check if user already exists
        if User.query.filter_by(username=username).first():
            print(f"❌ Username '{username}' already exists!")
            return

        if User.query.filter_by(email=email).first():
            print(f"❌ Email '{email}' already exists!")
            return

        # Create admin user
        admin_user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=UserRole.ADMIN,
        )
        admin_user.set_password(password)

        # Save to database
        db.session.add(admin_user)
        db.session.commit()

        print(f"✅ Admin user '{username}' created successfully!")
        print(f"   Name: {first_name} {last_name}")
        print(f"   Email: {email}")
        print(f"   Role: {admin_user.role.value}")


if __name__ == "__main__":
    create_admin_user()
