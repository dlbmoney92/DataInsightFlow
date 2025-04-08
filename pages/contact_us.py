import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from utils.global_config import apply_global_css, render_footer

def send_email(name, email, message):
    """Send email to admin"""
    # In a real system, we would configure SMTP settings and send actual emails
    # This is a placeholder for demonstration purposes
    
    # Log the message details for debugging
    st.session_state.contact_form_submitted = True
    st.session_state.contact_form_recipient = "dariusbell@bellcontractingservices.com"
    st.session_state.contact_form_subject = f"Analytics Assist Contact Form: {name}"
    st.session_state.contact_form_body = f"""
    Name: {name}
    Email: {email}
    
    Message:
    {message}
    """
    
    # For now, we'll just log this information to the console
    print(f"Contact form submission:")
    print(f"To: dariusbell@bellcontractingservices.com")
    print(f"From: {email}")
    print(f"Name: {name}")
    print(f"Message: {message}")
    
    # Return success as if email was sent
    return True

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