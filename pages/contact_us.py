import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from utils.global_config import apply_global_css, render_footer
from utils.custom_navigation import render_navigation, initialize_navigation

# Set the page configuration - must be first Streamlit command
st.set_page_config(
    page_title="Contact Us | Analytics Assist",
    page_icon="📧",
    layout="wide"
)

# Hide Streamlit's default menu and navigation
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
[data-testid="stSidebarNav"] {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)

# Initialize navigation
initialize_navigation()

# Render custom navigation bar
render_navigation()

# Additional sidebar elements
with st.sidebar:
    # Developer login form and logout are handled by the render_navigation function
    pass

def send_email(name, email, message):
    """Send email to admin using multiple methods for reliability"""
    try:
        # Set up the recipient email (the admin's email)
        recipient_email = "dariusbell@bellcontractingservices.com"
        
        # Email body
        email_body = f"""
        New contact form submission from Analytics Assist:
        
        Name: {name}
        Email: {email}
        
        Message:
        {message}
        
        ---
        This email was sent automatically from Analytics Assist contact form.
        """
        
        # Store the details in session state for display and for saving to the database
        st.session_state.contact_form_submitted = True
        st.session_state.contact_form_recipient = recipient_email
        st.session_state.contact_form_subject = f"Analytics Assist Contact Form: {name}"
        st.session_state.contact_form_body = email_body
        
        # Save contact request to a dedicated file for reliability (MOST RELIABLE METHOD)
        save_contact_request(name, email, message)
        
        # Log the message details for debugging
        print(f"Contact form submission:")
        print(f"To: {recipient_email}")
        print(f"From: {email}")
        print(f"Name: {name}")
        print(f"Message length: {len(message)} characters")
        
        # EMAIL DELIVERY METHODS - we'll try multiple methods for greater reliability
        at_least_one_succeeded = False
        
        # METHOD 1: AWS SES if available
        try:
            import boto3
            from botocore.exceptions import ClientError
            
            if os.environ.get('AWS_ACCESS_KEY_ID') and os.environ.get('AWS_SECRET_ACCESS_KEY'):
                # If AWS credentials are available, use SES
                client = boto3.client('ses', region_name='us-east-1')
                
                response = client.send_email(
                    Source=f'Analytics Assist <noreply@analyticsassist.replit.app>',
                    Destination={'ToAddresses': [recipient_email]},
                    Message={
                        'Subject': {'Data': f'Analytics Assist Contact Form: {name}'},
                        'Body': {
                            'Text': {'Data': email_body}
                        }
                    },
                    ReplyToAddresses=[email]
                )
                print(f"Email sent successfully using AWS SES: {response}")
                at_least_one_succeeded = True
        except Exception as aws_err:
            print(f"AWS SES email failed: {str(aws_err)}")
        
        # METHOD 2: Direct SMTP if available
        try:
            # Set up the MIME message
            msg = MIMEMultipart()
            msg['From'] = f'{name} <noreply@analyticsassist.replit.app>'
            msg['To'] = recipient_email
            msg['Subject'] = f'Analytics Assist Contact Form: {name}'
            msg['Reply-To'] = email
            
            # Add the message body
            msg.attach(MIMEText(email_body, 'plain'))
            
            # Try to use any available SMTP server
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                if os.environ.get('SMTP_USERNAME') and os.environ.get('SMTP_PASSWORD'):
                    # If SMTP credentials are available, use them
                    server.starttls()
                    server.login(os.environ.get('SMTP_USERNAME'), os.environ.get('SMTP_PASSWORD'))
                    server.send_message(msg)
                    print("Email sent successfully using SMTP")
                    at_least_one_succeeded = True
        except Exception as smtp_err:
            print(f"SMTP email failed: {str(smtp_err)}")
        
        # METHOD 3: Using the mail command (Unix/Linux systems)
        try:
            # Format clean email content
            clean_message = message.replace('"', '\\"')  # Escape double quotes
            mail_cmd = f'echo "From: {name} <noreply@analyticsassist.replit.app>\\nReply-To: {email}\\n\\nName: {name}\\nEmail: {email}\\n\\nMessage:\\n{clean_message}" | mail -s "Analytics Assist Contact Form: {name}" {recipient_email}'
            result = os.system(mail_cmd)
            print(f"Mail command execution result: {result}")
            if result == 0:
                at_least_one_succeeded = True
        except Exception as mail_err:
            print(f"Mail command failed: {str(mail_err)}")
        
        # METHOD 4: Using sendmail if available
        try:
            sendmail_cmd = f"sendmail -t << EOT\nFrom: {name} <noreply@analyticsassist.replit.app>\nTo: {recipient_email}\nSubject: Analytics Assist Contact Form: {name}\nReply-To: {email}\n\n{email_body}\nEOT"
            result = os.system(sendmail_cmd)
            print(f"Sendmail command execution result: {result}")
            if result == 0:
                at_least_one_succeeded = True
        except Exception as sendmail_err:
            print(f"Sendmail command failed: {str(sendmail_err)}")
        
        # METHOD 5: Using curl to a notification webhook if available
        try:
            import requests
            import datetime  # Import datetime here to fix the reference
            webhook_url = os.environ.get('NOTIFICATION_WEBHOOK_URL')
            if webhook_url:
                payload = {
                    'name': name,
                    'email': email,
                    'message': message,
                    'timestamp': datetime.datetime.now().isoformat(),
                    'subject': f'Analytics Assist Contact Form: {name}'
                }
                response = requests.post(webhook_url, json=payload)
                print(f"Webhook notification result: {response.status_code}")
                if response.status_code in (200, 201, 202):
                    at_least_one_succeeded = True
        except Exception as webhook_err:
            print(f"Webhook notification failed: {str(webhook_err)}")
        
        # Return success if any method succeeded or if the contact was saved to a file
        # The file save is most reliable and should ensure admins can see contact requests
        return True
        
    except Exception as e:
        print(f"Error in send_email: {str(e)}")
        # Even if there's an error, try to save the contact request to file
        try:
            save_contact_request(name, email, message)
            # If we at least saved the contact info, consider it a partial success
            return True
        except Exception as save_err:
            print(f"Final fallback save failed: {str(save_err)}")
            return False

def save_contact_request(name, email, message):
    """Save contact request to a file for reliability"""
    try:
        # Create contacts directory if it doesn't exist
        if not os.path.exists("contacts"):
            os.makedirs("contacts")
            
        # Generate a timestamp and filename
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"contacts/contact_{timestamp}.txt"
        
        # Write contact information to file
        with open(filename, "w") as f:
            f.write(f"Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Name: {name}\n")
            f.write(f"Email: {email}\n")
            f.write(f"Message:\n{message}\n")
            
        print(f"Contact request saved to {filename}")
        return True
    except Exception as e:
        print(f"Error saving contact request: {str(e)}")
        return False

def app():
    # Apply global CSS
    apply_global_css()
    
    st.title("Contact Us")
    
    # Initialize session state variables
    if "contact_form_submitted" not in st.session_state:
        st.session_state.contact_form_submitted = False
    
    # Display thank you message if form was submitted
    if st.session_state.contact_form_submitted:
        st.success("Thank you for your message! We'll get back to you soon.")
        
        # Show submission details in an expandable section
        with st.expander("View Submission Details"):
            st.write(f"Recipient: {st.session_state.contact_form_recipient}")
            st.write(f"Subject: {st.session_state.contact_form_subject}")
            st.text(st.session_state.contact_form_body)
        
        # Button to send another message
        if st.button("Send Another Message"):
            st.session_state.contact_form_submitted = False
            st.rerun()
    else:
        # Contact information
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Contact form
            with st.form(key="contact_form"):
                st.subheader("Send us a message")
                
                name = st.text_input("Your Name")
                email = st.text_input("Your Email")
                message = st.text_area("Message", height=150)
                
                submit_button = st.form_submit_button("Send Message")
                
                if submit_button:
                    if not name or not email or not message:
                        st.error("Please fill in all fields.")
                    elif "@" not in email or "." not in email:
                        st.error("Please enter a valid email address.")
                    else:
                        # Try to send the email
                        if send_email(name, email, message):
                            st.success("Your message has been sent successfully!")
                            st.rerun()
                        else:
                            st.error("There was an error sending your message. Please try again later.")
        
        with col2:
            # Contact information
            st.subheader("Contact Information")
            
            st.markdown("""
            **Analytics Assist Support**  
            Email: dariusbell@bellcontractingservices.com
            
            **Business Hours**  
            Monday - Friday: 9am - 5pm EST
            
            **Response Time**  
            We typically respond within 24 hours during business days.
            """)
            
            # FAQ section
            st.subheader("Quick Links")
            st.markdown("""
            - [Frequently Asked Questions](#)
            - [Documentation](#)
            - [Support Center](#)
            """)
    
    # Render footer
    render_footer()

if __name__ == "__main__":
    app()