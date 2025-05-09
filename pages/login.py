import streamlit as st
import hashlib
import datetime
from utils.database import get_user_by_email, check_valid_credentials, update_last_login
from utils.global_config import apply_global_css, render_footer
from utils.custom_navigation import initialize_navigation, render_navigation

def app():
    # Apply global CSS
    apply_global_css()
    
    # Initialize and render navigation
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
    render_navigation()
    
    # Main content area
    st.title("Welcome Back")
    
    # Check if already logged in
    if st.session_state.get("logged_in", False):
        st.success("You are already logged in!")
        
        # Check if there's a redirect after login
        if "redirect_after_login" in st.session_state:
            redirect_page = st.session_state.pop("redirect_after_login")
            st.markdown(f"Redirecting to {redirect_page.split('/')[-1].replace('.py', '')}...")
            st.switch_page(redirect_page)
        
        # Otherwise show a button to go to the main page
        if st.button("Go to Dashboard"):
            st.switch_page("app.py")
            
        return
    
    # Login form
    col1, col2 = st.columns([3, 2])
    
    with col1:
        with st.form("login_form"):
            st.subheader("Login with Email")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            
            if submit:
                if not email or not password:
                    st.error("Please fill in all fields")
                else:
                    # Hash the password with salt for admin
                    salt = "analyticsassist"  # Fixed salt for consistency
                    salted_password = password + salt
                    password_hash = hashlib.sha256(salted_password.encode()).hexdigest()
                    
                    # Check credentials
                    if check_valid_credentials(email, password_hash):
                        # Get user details
                        user = get_user_by_email(email)
                        
                        if user:
                            # Set session state
                            st.session_state.logged_in = True
                            st.session_state.user = user
                            st.session_state.user_id = user["id"]
                            st.session_state.subscription_tier = user.get("subscription_tier", "free")
                            st.session_state.is_admin = user.get("is_admin", False)
                            
                            # Update last login time
                            update_last_login(user["id"])
                            
                            st.success("Login successful!")
                            
                            # Check if user was in the middle of subscription selection
                            if "selected_plan" in st.session_state:
                                # Save the plan info and prepare redirect
                                st.markdown("Redirecting back to complete your subscription...")
                                st.session_state.redirect_to_payment = True
                                st.rerun()  # Rerun to clear the form
                                st.switch_page("pages/subscription_selection.py")
                            # Check if there's a redirect after login
                            elif "redirect_after_login" in st.session_state:
                                redirect_page = st.session_state.pop("redirect_after_login")
                                st.markdown(f"Redirecting to {redirect_page.split('/')[-1].replace('.py', '')}...")
                                st.rerun()  # Rerun to clear the form
                                st.switch_page(redirect_page)
                            else:
                                # Redirect to home page
                                st.rerun()  # Rerun to clear the form
                                st.switch_page("app.py")
                        else:
                            st.error("User not found")
                    else:
                        st.error("Invalid email or password")
        
        st.markdown("Don't have an account?")
        if st.button("Sign up here", key="signup_button"):
            st.switch_page("pages/signup.py")
        
        st.markdown("Forgot your password?")
        if st.button("Reset it here", key="reset_password_button"):
            st.switch_page("pages/reset_password.py")
    
    with col2:
        # Add info box
        st.info("""
        Signing in gives you:
        - Personalized analysis
        - Saved projects
        - Access to advanced features
        """)
    
    # Footer
    render_footer()

if __name__ == "__main__":
    app()