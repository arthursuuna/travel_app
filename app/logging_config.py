"""
Logging configuration for the Travel App.
Provides comprehensive error and exception logging for maintenance.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from flask import request, g
import time


def setup_logging(app):
    """
    Set up comprehensive logging for the application.
    Configures file logging, error handlers, and request logging.
    """
    
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    # Configure logging level based on environment
    if app.debug:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO
    
    # Main application log file with rotation
    file_handler = RotatingFileHandler(
        'logs/travel_app.log', 
        maxBytes=10240000,  # 10MB
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(log_level)
    app.logger.addHandler(file_handler)
    
    # Error-specific log file
    error_handler = RotatingFileHandler(
        'logs/errors.log',
        maxBytes=10240000,  # 10MB
        backupCount=5
    )
    error_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]\n'
        'Request: %(method)s %(url)s\n'
        'User: %(user)s\n'
        'IP: %(ip)s\n'
        'User-Agent: %(user_agent)s\n'
        '--- End Error ---\n'
    ))
    error_handler.setLevel(logging.ERROR)
    
    # Create custom error logger
    error_logger = logging.getLogger('travel_app.errors')
    error_logger.addHandler(error_handler)
    error_logger.setLevel(logging.ERROR)
    
    # Set application logger level
    app.logger.setLevel(log_level)
    
    # Log application startup
    app.logger.info('Travel App startup')
    
    return app


def log_error(app, error, context=None):
    """
    Enhanced error logging with request context and user information.
    """
    from flask_login import current_user
    
    error_logger = logging.getLogger('travel_app.errors')
    
    # Gather context information
    user_info = 'Anonymous'
    if hasattr(current_user, 'id') and current_user.is_authenticated:
        user_info = f"User ID: {current_user.id}, Username: {current_user.username}"
    
    ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'Unknown'))
    user_agent = request.headers.get('User-Agent', 'Unknown')
    
    # Create detailed error message
    error_details = {
        'error': str(error),
        'method': request.method if request else 'Unknown',
        'url': request.url if request else 'Unknown',
        'user': user_info,
        'ip': ip_address,
        'user_agent': user_agent,
    }
    
    if context:
        error_details['context'] = context
    
    # Log the error with context
    error_logger.error(
        f"Application Error: {str(error)}",
        extra={
            'method': error_details['method'],
            'url': error_details['url'],
            'user': error_details['user'],
            'ip': error_details['ip'],
            'user_agent': error_details['user_agent']
        }
    )
    
    # Also log to main application logger
    app.logger.error(f"Error occurred: {str(error)} | Context: {context or 'None'}")


def log_security_event(app, event_type, details):
    """
    Log security-related events for monitoring.
    """
    from flask_login import current_user
    
    security_logger = logging.getLogger('travel_app.security')
    
    user_info = 'Anonymous'
    if hasattr(current_user, 'id') and current_user.is_authenticated:
        user_info = f"User ID: {current_user.id}"
    
    ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'Unknown'))
    
    security_logger.warning(
        f"Security Event: {event_type} | User: {user_info} | IP: {ip_address} | Details: {details}"
    )


def log_user_activity(app, activity, user_id=None, details=None):
    """
    Log user activities for audit trail.
    """
    activity_logger = logging.getLogger('travel_app.activity')
    
    user_info = user_id or 'Unknown'
    ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'Unknown'))
    
    activity_logger.info(
        f"User Activity: {activity} | User ID: {user_info} | IP: {ip_address} | Details: {details or 'None'}"
    )


def setup_request_logging(app):
    """
    Set up request-level logging to track performance and errors.
    """
    
    @app.before_request
    def before_request_logging():
        """Log request start and set up timing."""
        g.start_time = time.time()
        
        # Log all requests in debug mode
        if app.debug:
            app.logger.debug(f"Request started: {request.method} {request.url}")
    
    @app.after_request
    def after_request_logging(response):
        """Log request completion and performance."""
        if hasattr(g, 'start_time'):
            response_time = time.time() - g.start_time
            
            # Log slow requests
            if response_time > 2.0:
                app.logger.warning(
                    f"Slow request: {request.method} {request.url} "
                    f"took {response_time:.2f}s | Status: {response.status_code}"
                )
            
            # Log all requests in debug mode
            if app.debug:
                app.logger.debug(
                    f"Request completed: {request.method} {request.url} "
                    f"in {response_time:.3f}s | Status: {response.status_code}"
                )
        
        return response


def setup_error_monitoring(app):
    """
    Set up comprehensive error monitoring and logging.
    """
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        """Global exception handler to log all unhandled exceptions."""
        
        # Log the error with full context
        log_error(app, error, context="Unhandled exception")
        
        # Check if it's an HTTP error
        if hasattr(error, 'code'):
            return error
        
        # For non-HTTP exceptions, return 500
        from flask import render_template
        try:
            return render_template('errors/500.html'), 500
        except:
            # Fallback if template doesn't exist
            return "<h1>500 - Internal Server Error</h1><p>Something went wrong. Please try again later.</p>", 500
    
    @app.errorhandler(403)
    def forbidden_error(error):
        """Handle 403 Forbidden errors."""
        log_security_event(app, "403_FORBIDDEN", f"Attempted access to forbidden resource: {request.url}")
        try:
            from flask import render_template
            return render_template('errors/403.html'), 403
        except:
            return "<h1>403 - Forbidden</h1><p>You don't have permission to access this resource.</p>", 403
    
    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 Not Found errors."""
        app.logger.info(f"404 error: {request.method} {request.url}")
        try:
            from flask import render_template
            return render_template('errors/404.html'), 404
        except:
            return "<h1>404 - Page Not Found</h1><p>The page you're looking for doesn't exist.</p>", 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 Internal Server errors."""
        from app import db
        db.session.rollback()
        log_error(app, error, context="500 Internal Server Error")
        try:
            from flask import render_template
            return render_template('errors/500.html'), 500
        except:
            return "<h1>500 - Internal Server Error</h1><p>Something went wrong on our end.</p>", 500
