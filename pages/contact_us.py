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
    """Send email to admin"""
    try:
        # Set up the email server - these settings work for most SMTP providers
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        
        # Create sender email credentials (using the form submitter's email as the reply-to)
        sender_email = email  # Use the user's email as the sender
        reply_to_email = email
        
        # Set recipient email (the admin's email)
        recipient_email = "dariusbell@bellcontractingservices.com"
        
        # Create email message
        msg = MIMEMultipart()
        msg['From'] = f"{name} <{sender_email}>"
        msg['To'] = recipient_email
        msg['Subject'] = f"Analytics Assist Contact Form: {name}"
        msg['Reply-To'] = reply_to_email  # Ensure replies go back to the person who filled the form
        
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
        
        msg.attach(MIMEText(email_body, 'plain'))
        
        # Log the message details for debugging and session state
        st.session_state.contact_form_submitted = True
        st.session_state.contact_form_recipient = recipient_email
        st.session_state.contact_form_subject = f"Analytics Assist Contact Form: {name}"
        st.session_state.contact_form_body = email_body
        
        # Log the message details for debugging
        print(f"Contact form submission:")
        print(f"To: {recipient_email}")
        print(f"From: {email}")
        print(f"Name: {name}")
        print(f"Message: {message}")
        
        # Using the mail() command which works on most Unix systems including Replit
        # This approach avoids needing SMTP credentials
        
        # Format headers
        headers = f"From: {name} <{sender_email}>\n"
        headers += f"To: {recipient_email}\n"
        headers += f"Reply-To: {reply_to_email}\n"
        headers += f"Subject: Analytics Assist Contact Form: {name}\n\n"
        
        # Combine headers and body
        full_email = headers + email_body
        
        # Use the mail command directly
        os.system(f'echo "{full_email}" | mail -s "Analytics Assist Contact Form: {name}" {recipient_email}')
        
        # Return success
        return True
        
    except Exception as e:
        print(f"Error sending email: {str(e)}")
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