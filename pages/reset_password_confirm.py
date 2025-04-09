import streamlit as st
import hashlib
import re
from utils.database import validate_password_reset_token, update_user_password, mark_token_as_used, get_user_by_id
from utils.global_config import apply_global_css
from utils.custom_navigation import render_navigation, initialize_navigation

# Set page configuration - must be the first Streamlit command
st.set_page_config(
    page_title="Set New Password | Analytics Assist",
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

def is_strong_password(password):
    """Check if password is strong enough."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one number."
    
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character."
    
    return True, "Password is strong."

def app():
    st.title("Set New Password")
    
    # Get token from URL parameters
    query_params = st.experimental_get_query_params()
    token = query_params.get("token", [""])[0]
    
    if not token:
        st.error("Invalid or missing reset token. Please request a new password reset link.")
        if st.button("Back to Reset Password"):
            st.switch_page("pages/reset_password.py")
        return
    
    # Validate token
    user_id = validate_password_reset_token(token)
    
    if not user_id:
        st.error("Invalid or expired reset token. Please request a new password reset link.")
        if st.button("Back to Reset Password"):
            st.switch_page("pages/reset_password.py")
        return
    
    # Get user details
    user = get_user_by_id(user_id)
    
    if not user:
        st.error("User not found. Please request a new password reset link.")
        if st.button("Back to Reset Password"):
            st.switch_page("pages/reset_password.py")
        return
    
    st.write(f"Setting new password for: {user['email']}")
    
    # Create form for new password
    with st.form("new_password_form"):
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        
        submit = st.form_submit_button("Set New Password")
        
        if submit:
            if not new_password or not confirm_password:
                st.error("Please fill in all fields.")
            elif new_password != confirm_password:
                st.error("Passwords do not match.")
            else:
                # Check password strength
                is_strong, message = is_strong_password(new_password)
                if not is_strong:
                    st.error(message)
                else:
                    # Hash the new password
                    password_hash = hashlib.sha256(new_password.encode()).hexdigest()
                    
                    # Update the password and mark the token as used
                    if update_user_password(user_id, password_hash) and mark_token_as_used(token):
                        st.success("Your password has been updated successfully!")
                        st.info("You can now login with your new password.")
                        
                        if st.button("Go to Login"):
                            st.switch_page("pages/login.py")
                    else:
                        st.error("There was an error updating your password. Please try again.")
    
    st.markdown("---")
    if st.button("Back to Login", use_container_width=True):
        st.switch_page("pages/login.py")

if __name__ == "__main__":
    app()