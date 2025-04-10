import streamlit as st
import hashlib
import time
from utils.database import get_user_by_email, create_password_reset_token
from utils.global_config import apply_global_css
from utils.custom_navigation import render_navigation, initialize_navigation
from utils.email_sender import send_password_reset_email, get_last_sent_email

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
                
                # Send email and store token only if the email exists and token was generated
                if token:  # Only if the email actually exists
                    # Use a consistent base URL
                    base_url = ""
                    # Try to get the base URL from the current request if available
                    try:
                        base_url = st.get_option("server.baseUrlPath") or ""
                    except:
                        # Default to empty string if not available
                        base_url = ""
                    
                    # Build the reset URL
                    reset_url = f"{base_url}/pages/reset_password_confirm.py?token={token}"
                    
                    # Make sure it's a full URL (for email links)
                    if not reset_url.startswith("http"):
                        # Add a placeholder domain for demo
                        reset_url = f"https://analytics-assist.com{reset_url}"
                    
                    # Send the reset email
                    success, message = send_password_reset_email(email, reset_url)
                    
                    if success:
                        # Store the token in session state for the demo button
                        st.session_state["reset_token"] = token
                        # Also store the email for demo display
                        st.session_state["reset_email"] = email
                    else:
                        # Log the error but don't show to user (for security)
                        print(f"Failed to send reset email: {message}")
                        # Still store token for the demo button
                        st.session_state["reset_token"] = token
    
    # Only show these messages and buttons OUTSIDE the form
    if "reset_token" in st.session_state and st.session_state["reset_token"]:
        # Add a note about checking email
        st.info("A reset link has been sent to your email. Please check your inbox and spam folder.")
        
        # Get the last sent email for demo purposes
        last_email = get_last_sent_email()
        
        # Display a nice preview of the reset email sent
        if last_email:
            with st.expander("📧 View the email that was sent", expanded=True):
                st.markdown(f"""
                **From:** Analytics Assist <noreply@analytics-assist.com>  
                **To:** {st.session_state.get('reset_email', 'user@example.com')}  
                **Subject:** {last_email['subject']}
                
                ---
                
                <iframe 
                    style="border: 1px solid #ddd; border-radius: 5px;" 
                    width="100%" 
                    height="500px" 
                    srcdoc='{last_email['content']}'>
                </iframe>
                """, unsafe_allow_html=True)
        
        # Add a separator
        st.markdown("---")
        
        # Display a direct reset button
        st.success("For this demo, click the button below to reset your password immediately:")
        
        if st.button("Reset My Password Now", type="primary"):
            # Keep the token in session state for the confirmation page to use
            # Do NOT remove it here as it will be used on the confirmation page
            
            # Redirect to the confirmation page
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