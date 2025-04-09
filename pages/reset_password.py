import streamlit as st
import hashlib
from utils.database import get_user_by_email, create_password_reset_token
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
                # Generate a reset token (whether the email exists or not)
                token = create_password_reset_token(email)
                
                # Show the same message regardless of whether the email exists
                st.success(f"If an account exists with the email {email}, a password reset link has been sent. Please check your email.")
                
                # Store token in session state for after form completion
                if token:  # Only if the email actually exists
                    # Store the token in session state to use later
                    st.session_state["reset_token"] = token
                    
                    # Add a note about checking email
                    st.info("A reset link has been sent to your email. Please check your inbox and spam folder.")
                    
                    # Display a direct reset button outside the form
                    st.success("For this demo, click the button below to reset your password immediately:")
        
        # Add the reset button outside the form
        if "reset_token" in st.session_state and st.session_state["reset_token"]:
            if st.button("Reset My Password Now", type="primary"):
                token = st.session_state["reset_token"]
                # Clear the token from session state after use
                del st.session_state["reset_token"]
                st.query_params["token"] = token
                st.switch_page("pages/reset_password_confirm.py")
    
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center;'>Remember your password? Return to login</div>", 
        unsafe_allow_html=True
    )
    
    if st.button("Back to Login", use_container_width=True):
        st.switch_page("pages/login.py")

if __name__ == "__main__":
    app()