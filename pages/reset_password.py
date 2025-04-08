import streamlit as st
import hashlib
from utils.database import get_user_by_email
from utils.global_config import apply_global_css
from utils.custom_navigation import render_navigation, initialize_navigation

# Set page configuration - must be the first Streamlit command
st.set_page_config(
    page_title="Reset Password | Analytics Assist",
    page_icon="🔐",
    layout="wide"
)

# Apply global CSS
apply_global_css()

# Initialize navigation
initialize_navigation()

# Hide Streamlit's default multipage navigation menu
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {
            display: none !important;
        }
    </style>
""", unsafe_allow_html=True)

# Render custom navigation bar
render_navigation()

def app():
    st.title("Reset Password")
    
    # If already logged in, show different message
    if "logged_in" in st.session_state and st.session_state.logged_in:
        st.info("You are already logged in. If you want to change your password, please go to your account settings.")
        if st.button("Go to Account Settings"):
            st.switch_page("pages/account.py")
        return
    
    st.write("Enter your email address below to receive a password reset link.")
    
    # Create reset password form
    with st.form("reset_password_form"):
        email = st.text_input("Email")
        submit = st.form_submit_button("Request Password Reset")
        
        if submit:
            if not email:
                st.error("Please enter your email address.")
            else:
                # Check if email exists in database
                user = get_user_by_email(email)
                
                if user:
                    # In a real app, we would send an email with a reset link
                    # For now, we'll just show a success message
                    st.success(f"If an account exists with the email {email}, we will send a password reset link. Please check your email.")
                    
                    # Provide instructions for the demo
                    st.info("""
                    Since this is a demo application, no actual email will be sent. 
                    
                    In a production environment, this would:
                    1. Generate a unique token
                    2. Store the token in the database with an expiration time
                    3. Send an email with a link containing the token
                    4. The link would direct to a page where the user can set a new password
                    
                    For demonstration purposes, you can use the login page with your current credentials.
                    """)
                else:
                    # Don't reveal if the email exists for security reasons
                    # Show the same message regardless
                    st.success(f"If an account exists with the email {email}, we will send a password reset link. Please check your email.")
    
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center;'>Remember your password? Return to login</div>", 
        unsafe_allow_html=True
    )
    
    if st.button("Back to Login", use_container_width=True):
        st.switch_page("pages/login.py")

if __name__ == "__main__":
    app()