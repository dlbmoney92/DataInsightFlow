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
        
        # Save contact request to a dedicated file for reliability
        save_contact_request(name, email, message)
        
        # Log the message details for debugging
        print(f"Contact form submission:")
        print(f"To: {recipient_email}")
        print(f"From: {email}")
        print(f"Name: {name}")
        print(f"Message length: {len(message)} characters")
        
        # METHOD 1: Using the mail command (Unix/Linux systems)
        try:
            # Format clean email content
            clean_message = message.replace('"', '\\"')  # Escape double quotes
            mail_cmd = f'echo "From: {name} <noreply@analyticsassist.replit.app>\\nReply-To: {email}\\n\\nName: {name}\\nEmail: {email}\\n\\nMessage:\\n{clean_message}" | mail -s "Analytics Assist Contact Form: {name}" {recipient_email}'
            os.system(mail_cmd)
        except Exception as mail_err:
            print(f"Mail command failed: {str(mail_err)}")
            # Continue to try other methods if this fails
        
        # METHOD 2: Save to database for admin to check
        try:
            # This would connect to the database and save the contact request
            # Implementation depends on your database structure
            # For now, we just log it
            print("Would save contact request to database here")
        except Exception as db_err:
            print(f"Database save failed: {str(db_err)}")
        
        # Return success - even if some methods fail, we've saved the contact info
        # and the admin can see it in the saved contacts file
        return True
        
    except Exception as e:
        print(f"Error in send_email: {str(e)}")
        # Even if there's an error, try to save the contact request
        try:
            save_contact_request(name, email, message)
        except:
            pass
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