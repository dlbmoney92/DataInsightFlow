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
                
                # Since this is a demo, show a simulated email for convenience
                if token:  # Only if the email actually exists
                    # Get base_url from query params or use default empty string
                    base_url = ""
                    if "base_url" in st.query_params:
                        base_url = st.query_params["base_url"]
                    
                    reset_url = f"{base_url}/pages/reset_password_confirm.py?token={token}"
                    if not reset_url.startswith("http"):
                        reset_url = f"http://{reset_url}"
                    
                    st.info("### Simulated Email:")
                    st.markdown(f"""
                    **From:** Analytics Assist <noreply@analytics-assist.com>  
                    **To:** {email}  
                    **Subject:** Reset Your Password
                    
                    ---
                    
                    Dear User,
                    
                    You requested a password reset for your Analytics Assist account. Please click the link below to reset your password:
                    
                    [Reset Password]({reset_url})
                    
                    This link will expire in 24 hours. If you did not request a password reset, please ignore this email.
                    
                    ---
                    
                    For demo purposes, you can click the link below to reset your password:
                    """)
                    
                    if st.button("Go to Password Reset Page"):
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