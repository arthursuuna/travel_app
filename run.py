"""
Main application entry point.
This file creates and runs the Flask application.
Run this file to start the development server.
"""

from app import create_app, db

# Create the Flask application instance using the application factory
app = create_app()


@app.shell_context_processor
def make_shell_context():
    """
    Shell context processor.
    Makes database instance available in Flask shell.
    This is useful for testing and debugging.
    """
    return {"db": db}


# Create database tables if they don't exist
with app.app_context():
    """
    Application context is needed for database operations.
    This ensures all tables are created when the app starts.
    """
    db.create_all()
    print("✅ Database tables created successfully!")

# Run the application
if __name__ == "__main__":
    """
    This block runs only when the script is executed directly,
    not when it's imported as a module.
    """
    print("🚀 Starting Travel App...")
    print("🌐 Visit: http://localhost:5000")
    app.run(
        debug=True,  # Enable debug mode for development
        host="0.0.0.0",  # Allow external connections
        port=5000,  # Port number
        use_reloader=True,  # Auto-reload when files change
    )
