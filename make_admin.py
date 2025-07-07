"""
Make an existing user an admin
"""

from app import create_app, db
from app.models import User, UserRole


def make_user_admin():
    app = create_app()

    with app.app_context():
        print("=== Make User Admin ===")

        # Show all users
        users = User.query.all()
        if not users:
            print("❌ No users found! Create a user first.")
            return

        print("Available users:")
        for i, user in enumerate(users, 1):
            print(f"{i}. {user.username} ({user.email}) - Role: {user.role.value}")

        # Get user choice
        try:
            choice = int(input(f"\nSelect user (1-{len(users)}): ")) - 1
            if choice < 0 or choice >= len(users):
                print("❌ Invalid choice!")
                return

            selected_user = users[choice]

            # Make admin
            selected_user.role = UserRole.ADMIN
            db.session.commit()

            print(f"✅ User '{selected_user.username}' is now an admin!")

        except ValueError:
            print("❌ Please enter a valid number!")


if __name__ == "__main__":
    make_user_admin()
