import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import streamlit as st
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_email(recipient_email, subject, html_content, text_content=None):
    """
    Send an email using SMTP.
    
    Parameters:
    - recipient_email: Email address of the recipient
    - subject: Email subject
    - html_content: HTML content of the email
    - text_content: Plain text content (optional)
    
    Returns:
    - success: Boolean indicating if the email was sent successfully
    - message: Error message if not successful
    """
    # Since this is a demo application, we'll log the email content instead of actually sending it
    # In a production environment, you would use a real email service like SendGrid, Mailgun, etc.
    
    # For demo purposes, we'll simulate email sending and return success
    logger.info(f"Sending email to: {recipient_email}")
    logger.info(f"Subject: {subject}")
    logger.info(f"Content: {html_content[:100]}...")
    
    # Store the email in session state for demo purposes
    if "sent_emails" not in st.session_state:
        st.session_state.sent_emails = []
    
    st.session_state.sent_emails.append({
        "to": recipient_email,
        "subject": subject,
        "content": html_content
    })
    
    # Return success for demo
    return True, "Email sent successfully (demo mode)"
    
    # The code below would be used in a production environment
    """
    # Get email configuration from environment variables
    smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", 587))
    smtp_username = os.environ.get("SMTP_USERNAME")
    smtp_password = os.environ.get("SMTP_PASSWORD")
    
    # Check if SMTP credentials are available
    if not smtp_username or not smtp_password:
        return False, "SMTP credentials not configured"
    
    sender_email = smtp_username
    
    # Create message
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = f"Analytics Assist <{sender_email}>"
    message["To"] = recipient_email
    
    # Add text content if provided
    if text_content:
        message.attach(MIMEText(text_content, "plain"))
    
    # Add HTML content
    message.attach(MIMEText(html_content, "html"))
    
    try:
        # Connect to server and send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Secure connection
            server.login(smtp_username, smtp_password)
            server.sendmail(sender_email, recipient_email, message.as_string())
        return True, "Email sent successfully"
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False, f"Failed to send email: {str(e)}"
    """

def send_password_reset_email(email, reset_url):
    """
    Send a password reset email with a reset link.
    
    Parameters:
    - email: Recipient's email address
    - reset_url: URL for password reset
    
    Returns:
    - success: Boolean indicating if the email was sent successfully
    - message: Error message if not successful
    """
    subject = "Reset Your Analytics Assist Password"
    
    # Create HTML content
    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #4CAF50; color: white; padding: 10px 20px; text-align: center; }}
            .content {{ padding: 20px; }}
            .button {{ display: inline-block; background-color: #4CAF50; color: white; padding: 10px 20px; 
                      text-decoration: none; border-radius: 5px; margin: 20px 0; }}
            .footer {{ text-align: center; font-size: 12px; color: #777; margin-top: 30px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>Analytics Assist Password Reset</h2>
            </div>
            <div class="content">
                <p>Hello,</p>
                <p>We received a request to reset your password for your Analytics Assist account. 
                   Click the button below to set a new password:</p>
                
                <p style="text-align: center;">
                    <a href="{reset_url}" class="button">Reset Password</a>
                </p>
                
                <p>If you didn't request a password reset, you can ignore this email and your password 
                   will remain unchanged.</p>
                
                <p>The link will expire in 24 hours for security reasons.</p>
                
                <p>Best regards,<br>The Analytics Assist Team</p>
            </div>
            <div class="footer">
                <p>This is an automated message, please do not reply to this email.</p>
                <p>&copy; 2025 Analytics Assist. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Create plain text content
    text_content = f"""
    Analytics Assist Password Reset
    
    Hello,
    
    We received a request to reset your password for your Analytics Assist account.
    Please visit the following link to set a new password:
    
    {reset_url}
    
    If you didn't request a password reset, you can ignore this email and your password will remain unchanged.
    
    The link will expire in 24 hours for security reasons.
    
    Best regards,
    The Analytics Assist Team
    """
    
    return send_email(email, subject, html_content, text_content)

def get_last_sent_email():
    """Get the last sent email from session state (for demo purposes)"""
    if "sent_emails" in st.session_state and st.session_state.sent_emails:
        return st.session_state.sent_emails[-1]
    return None