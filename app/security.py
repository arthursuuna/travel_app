"""
Security middleware for HTTPS enforcement and proxy handling.
This module provides middleware to handle HTTPS enforcement properly
when running behind reverse proxies like nginx or load balancers.
"""

from flask import request
from werkzeug.middleware.proxy_fix import ProxyFix


class HTTPSRedirectMiddleware:
    """
    Middleware to handle HTTPS redirects properly when behind a proxy.
    """

    def __init__(self, app, force_https=False):
        self.app = app
        self.force_https = force_https

    def __call__(self, environ, start_response):
        # Check if we're behind a proxy and adjust scheme accordingly
        if self.force_https:
            # Check various proxy headers
            forwarded_proto = environ.get('HTTP_X_FORWARDED_PROTO', '').lower()
            forwarded_ssl = environ.get('HTTP_X_FORWARDED_SSL', '').lower()
            cloudflare_visitor = environ.get('HTTP_CF_VISITOR', '')

            # Determine if request is secure
            is_secure = (
                environ.get('wsgi.url_scheme') == 'https' or
                forwarded_proto == 'https' or
                forwarded_ssl == 'on' or
                'https' in cloudflare_visitor
            )

            # Force HTTPS if not secure and not a static file
            if not is_secure and not environ.get('PATH_INFO', '').startswith('/static'):
                # Build redirect URL
                host = environ.get('HTTP_HOST', 'localhost')
                path = environ.get('PATH_INFO', '')
                query = environ.get('QUERY_STRING', '')
                
                redirect_url = f"https://{host}{path}"
                if query:
                    redirect_url += f"?{query}"

                # Return 301 redirect
                start_response('301 Moved Permanently', [
                    ('Location', redirect_url),
                    ('Content-Type', 'text/html')
                ])
                return [b'<h1>Moved Permanently</h1><p>This page has moved to HTTPS.</p>']

        return self.app(environ, start_response)


def setup_https_middleware(app):
    """
    Set up HTTPS enforcement middleware for the Flask app.
    """
    # Add proxy fix for proper header handling
    app.wsgi_app = ProxyFix(
        app.wsgi_app, 
        x_for=1, 
        x_proto=1, 
        x_host=1, 
        x_prefix=1
    )
    
    # Add HTTPS redirect middleware if configured
    if app.config.get('FORCE_HTTPS', False):
        app.wsgi_app = HTTPSRedirectMiddleware(
            app.wsgi_app, 
            force_https=True
        )

    return app
