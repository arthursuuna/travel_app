# HTTPS Deployment Guide for Travel App

## Overview

This guide explains how to enforce HTTPS for all data exchanges in the Travel App.

## Features Implemented

### 1. Configuration-Based HTTPS Enforcement

- Set `FORCE_HTTPS=true` in environment variables to enable
- Automatic HTTP to HTTPS redirects (301 redirects)
- Secure cookie settings when HTTPS is enabled

### 2. Security Headers

The application automatically adds these security headers when HTTPS is enforced:

- `Strict-Transport-Security`: Forces HTTPS for future requests
- `X-Content-Type-Options`: Prevents MIME type sniffing
- `X-Frame-Options`: Prevents clickjacking attacks
- `X-XSS-Protection`: Enables XSS filtering
- `Referrer-Policy`: Controls referrer information

### 3. Route-Level HTTPS Enforcement

Critical routes are protected with `@require_https` decorator:

- All payment processing routes
- Authentication routes (login, register)
- Admin routes (automatically via global enforcement)

### 4. Proxy Support

The app properly handles HTTPS when deployed behind:

- Nginx reverse proxy
- Load balancers
- Cloudflare
- AWS ALB/ELB

## Deployment Steps

### 1. Environment Configuration

Create a `.env` file for production:

```bash
FORCE_HTTPS=true
SESSION_COOKIE_SECURE=true
SECRET_KEY=your-super-secret-production-key
# ... other settings
```

### 2. Web Server Configuration

#### For Nginx:

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;

    # Security headers (additional to app headers)
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### For Apache:

```apache
<VirtualHost *:80>
    ServerName yourdomain.com
    Redirect permanent / https://yourdomain.com/
</VirtualHost>

<VirtualHost *:443>
    ServerName yourdomain.com

    SSLEngine on
    SSLCertificateFile /path/to/certificate.crt
    SSLCertificateKeyFile /path/to/private.key

    # Security headers
    Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains"

    ProxyPass / http://127.0.0.1:5000/
    ProxyPassReverse / http://127.0.0.1:5000/
    ProxyPreserveHost On
    ProxyAddHeaders On

    # Set forwarded headers
    ProxyPassReverse / http://127.0.0.1:5000/
    RequestHeader set X-Forwarded-Proto "https"
    RequestHeader set X-Forwarded-Port "443"
</VirtualHost>
```

### 3. SSL Certificate

Obtain an SSL certificate:

#### Using Let's Encrypt (Free):

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

#### Using Commercial Certificate:

1. Purchase certificate from a CA
2. Generate CSR and private key
3. Install certificate files on server

### 4. Application Deployment

```bash
# Set environment variables
export FORCE_HTTPS=true
export SESSION_COOKIE_SECURE=true

# Start the application
gunicorn --bind 127.0.0.1:5000 --workers 4 run:app
```

## Testing HTTPS Enforcement

### 1. Test HTTP to HTTPS Redirect

```bash
curl -I http://yourdomain.com
# Should return 301 redirect to https://
```

### 2. Test Security Headers

```bash
curl -I https://yourdomain.com
# Should include security headers like HSTS
```

### 3. Test Payment Security

- Navigate to payment pages
- Verify browser shows secure connection (lock icon)
- Check that forms submit over HTTPS

### 4. SSL/TLS Testing

Use online tools:

- SSL Labs Server Test: https://www.ssllabs.com/ssltest/
- Mozilla Observatory: https://observatory.mozilla.org/

## Development vs Production

### Development (HTTP allowed):

```bash
FORCE_HTTPS=false
SESSION_COOKIE_SECURE=false
```

### Production (HTTPS required):

```bash
FORCE_HTTPS=true
SESSION_COOKIE_SECURE=true
```

## Security Best Practices

1. **Always use HTTPS in production**
2. **Regularly update SSL certificates**
3. **Use strong SSL/TLS configuration**
4. **Enable HSTS (handled by the app)**
5. **Redirect all HTTP traffic to HTTPS**
6. **Use secure cookies for sessions**

## Troubleshooting

### Common Issues:

1. **Redirect loop**: Check proxy headers configuration
2. **Mixed content warnings**: Ensure all resources use HTTPS URLs
3. **Certificate errors**: Verify certificate chain and validity
4. **Performance issues**: Enable SSL session caching

### Debug Mode:

Add logging to check HTTPS enforcement:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Monitoring

Monitor HTTPS compliance:

1. Set up SSL certificate expiration alerts
2. Monitor redirect performance
3. Check for mixed content warnings
4. Validate security headers

This implementation ensures that all data exchanges in the Travel App are encrypted and secure, meeting the NFR requirement for HTTPS enforcement.
