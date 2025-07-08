"""
Application factory module.
This module creates and configures the Flask application instance.
"""

from flask import Flask
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from config import Config
import os

# Import db from models
from app.models import db

# Initialize other extensions
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()
csrf = CSRFProtect()


def create_app(config_class=Config):
    """
    Application factory function.
    Creates and configures a Flask application instance.

    Args:
        config_class: Configuration class to use (default: Config)

    Returns:
        Flask application instance
    """

    # Create Flask application instance
    app = Flask(__name__)

    # Load configuration from config class
    app.config.from_object(config_class)

    # Initialize extensions with the app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)  # Re-enabled CSRF protection

    # Initialize Flask-Admin
    admin_instance = Admin(app, name="Travel App Admin", template_mode="bootstrap4")

    # Configure Flask-Login
    login_manager.login_view = "auth.login"  # Redirect unauthorized users to login
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "info"

    @login_manager.user_loader
    def load_user(user_id):
        """
        Load user by ID for Flask-Login.
        This callback is used to reload the user object from the user ID stored in the session.
        """
        from app.models import User

        return User.query.get(int(user_id))

    # Set up Flask-Admin views
    from app.models import User, Tour, Category, Booking
    from flask_admin.contrib.sqla import ModelView

    class UserAdmin(ModelView):
        column_display_pk = True  # Show primary key
        column_list = [
            "id",
            "email",
            "first_name",
            "last_name",
            "is_admin",
            "created_at",
        ]
        column_labels = {
            "id": "ID (PK)",
            "email": "Email",
            "first_name": "First Name",
            "last_name": "Last Name",
            "is_admin": "Admin Status",
            "created_at": "Created",
        }

    class TourAdmin(ModelView):
        column_display_pk = True
        column_list = [
            "id",
            "title",
            "category_id",
            "destination",
            "price",
            "duration_days",
            "is_active",
        ]
        column_labels = {
            "id": "ID (PK)",
            "category_id": "Category ID (FK)",
            "title": "Title",
            "destination": "Destination",
            "price": "Price",
            "duration_days": "Duration (Days)",
            "is_active": "Active",
        }

    class CategoryAdmin(ModelView):
        column_display_pk = True
        column_list = ["id", "name", "description"]
        column_labels = {"id": "ID (PK)", "name": "Name", "description": "Description"}

    class BookingAdmin(ModelView):
        column_display_pk = True
        column_list = [
            "id",
            "user_id",
            "tour_id",
            "status",
            "total_price",
            "created_at",
        ]
        column_labels = {
            "id": "ID (PK)",
            "user_id": "User ID (FK)",
            "tour_id": "Tour ID (FK)",
            "status": "Status",
            "total_price": "Total Price",
            "created_at": "Created",
        }

    admin_instance.add_view(UserAdmin(User, db.session, name="Users"))
    admin_instance.add_view(TourAdmin(Tour, db.session, name="Tours"))
    admin_instance.add_view(CategoryAdmin(Category, db.session, name="Categories"))
    admin_instance.add_view(BookingAdmin(Booking, db.session, name="Bookings"))

    # Add a custom view for database schema information
    from flask_admin import BaseView, expose
    from flask import render_template_string

    class SchemaView(BaseView):
        @expose("/")
        def index(self):
            # Get table information from SQLAlchemy metadata
            tables_info = []
            for table_name, table in db.metadata.tables.items():
                columns_info = []
                for column in table.columns:
                    col_info = {
                        "name": column.name,
                        "type": str(column.type),
                        "nullable": column.nullable,
                        "primary_key": column.primary_key,
                        "foreign_keys": [
                            str(fk.target_fullname) for fk in column.foreign_keys
                        ],
                        "default": str(column.default) if column.default else None,
                    }
                    columns_info.append(col_info)

                tables_info.append({"name": table_name, "columns": columns_info})

            html_template = """
            <html>
            <head>
                <title>Database Schema</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    table { border-collapse: collapse; width: 100%; margin-bottom: 30px; }
                    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                    th { background-color: #f2f2f2; }
                    .primary-key { background-color: #ffffcc; font-weight: bold; }
                    .foreign-key { background-color: #e6f3ff; }
                    .table-name { color: #333; font-size: 18px; font-weight: bold; margin-top: 20px; }
                </style>
            </head>
            <body>
                <h1>Database Schema Information</h1>
                {% for table in tables_info %}
                    <div class="table-name">{{ table.name }}</div>
                    <table>
                        <thead>
                            <tr>
                                <th>Column Name</th>
                                <th>Type</th>
                                <th>Nullable</th>
                                <th>Primary Key</th>
                                <th>Foreign Keys</th>
                                <th>Default</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for column in table.columns %}
                            <tr class="{% if column.primary_key %}primary-key{% elif column.foreign_keys %}foreign-key{% endif %}">
                                <td>{{ column.name }}</td>
                                <td>{{ column.type }}</td>
                                <td>{{ column.nullable }}</td>
                                <td>{{ column.primary_key }}</td>
                                <td>{{ column.foreign_keys|join(', ') }}</td>
                                <td>{{ column.default or 'None' }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                {% endfor %}
            </body>
            </html>
            """

            return render_template_string(html_template, tables_info=tables_info)

    admin_instance.add_view(SchemaView(name="Database Schema", endpoint="schema"))

    # Create upload directories if they don't exist
    upload_path = os.path.join(app.instance_path, "static", "images", "uploads")
    os.makedirs(upload_path, exist_ok=True)

    # Register blueprints (URL routing modules)
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.tours import tours_bp
    from app.routes.bookings import bookings_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(tours_bp, url_prefix="/tours")
    app.register_blueprint(bookings_bp, url_prefix="/bookings")

    # Basic error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return (
            "<h1>404 - Page Not Found</h1><p>The page you're looking for doesn't exist.</p>",
            404,
        )

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return (
            "<h1>500 - Internal Server Error</h1><p>Something went wrong on our end.</p>",
            500,
        )

    return app
