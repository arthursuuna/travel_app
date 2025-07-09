# Email Setup Guide for Travel App

## Overview
This guide will help you set up Gmail integration for your travel app so that booking confirmations and contact form inquiries are sent via email instead of just being logged.

## Step 1: Enable Gmail App Password

### 1.1 Enable 2-Factor Authentication (if not already enabled)
1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Under "How you sign in to Google", click "2-Step Verification"
3. Follow the setup process to enable 2FA

### 1.2 Generate App Password
1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Under "How you sign in to Google", click "App passwords"
3. Select "Mail" for the app
4. Select "Windows Computer" (or your device type)
5. Click "Generate"
6. Copy the 16-character password (it will look like: `abcd efgh ijkl mnop`)

## Step 2: Update Your .env File

Open your `.env` file and update the following:

```properties
# Email Configuration (Gmail example - you need to set up App Password)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=jassimkasule@gmail.com
MAIL_PASSWORD=abcd efgh ijkl mnop  # Replace with your actual App Password
MAIL_DEFAULT_SENDER=jassimkasule@gmail.com
```

**Important:** 
- Replace `abcd efgh ijkl mnop` with your actual 16-character App Password
- Keep the spaces in the App Password as they appear
- Do NOT use your regular Gmail password

## Step 3: Test Email Functionality

### 3.1 Start Your Application
```bash
cd d:\travel_app
python run.py
```

### 3.2 Test Contact Form
1. Go to your homepage at `http://localhost:5000`
2. Scroll down to the contact form
3. Fill out the form and submit
4. Check your Gmail inbox for the inquiry notification

### 3.3 Test Booking Confirmation
1. Create a booking for any tour
2. Check your Gmail inbox for the booking confirmation

## Step 4: Troubleshooting

### Common Issues:

1. **"Authentication failed" error**
   - Make sure you're using the App Password, not your regular Gmail password
   - Ensure 2FA is enabled on your Google account

2. **"Less secure app access" error**
   - This shouldn't happen with App Passwords, but if it does, check your Google Account security settings

3. **Emails still being logged instead of sent**
   - Check that your `.env` file has the correct App Password
   - Restart your Flask application after updating `.env`

4. **SSL/TLS connection errors**
   - Ensure `MAIL_USE_TLS=true` in your `.env`
   - Check that `MAIL_PORT=587` (not 465 or 25)

### Testing Email Configuration:

You can test if your email configuration is working by running this Python script:

```python
from flask import Flask
from flask_mail import Mail, Message
import os

app = Flask(__name__)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'jassimkasule@gmail.com'
app.config['MAIL_PASSWORD'] = 'your-app-password-here'  # Replace with actual App Password

mail = Mail(app)

with app.app_context():
    msg = Message(
        subject='Test Email',
        recipients=['jassimkasule@gmail.com'],
        body='This is a test email from your travel app!',
        sender='jassimkasule@gmail.com'
    )
    mail.send(msg)
    print("Test email sent successfully!")
```

## Step 5: Production Considerations

### Security:
- Never commit your `.env` file to version control
- Use environment variables in production instead of `.env` files
- Consider using a dedicated email service like SendGrid or AWS SES for production

### Email Templates:
- Your app already has HTML email templates
- Booking confirmations include tour details and booking information
- Contact form inquiries include user details and message

### Monitoring:
- Check your Gmail "Sent" folder to verify emails are being sent
- Monitor your application logs for email sending errors
- Consider setting up email delivery monitoring in production

## Current Email Features in Your App:

1. **Booking Confirmations**: Sent when a user books a tour
2. **Contact Form Inquiries**: Sent when someone submits the contact form
3. **Password Reset**: Ready for implementation (tokens are generated)
4. **Admin Notifications**: Contact form submissions notify admin

## Next Steps:

1. Set up your Gmail App Password following Step 1
2. Update your `.env` file with the App Password
3. Restart your application
4. Test both contact form and booking confirmation emails
5. Monitor your Gmail inbox for successful delivery

If you encounter any issues, check the application logs for error messages and ensure your App Password is correct.
