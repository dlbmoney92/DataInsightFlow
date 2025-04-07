import streamlit as st
import hashlib
import datetime
from utils.database import get_user_by_email, check_valid_credentials, update_last_login
from utils.oauth import get_google_auth_url
from utils.global_config import apply_global_css, render_footer
from utils.custom_navigation import initialize_navigation, render_navigation

def app():
    # Apply global CSS
    apply_global_css()
    
    # Initialize and render navigation
    initialize_navigation()
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
                    # Hash the password
                    password_hash = hashlib.sha256(password.encode()).hexdigest()
                    
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
                            
                            # Update last login time
                            update_last_login(user["id"])
                            
                            st.success("Login successful!")
                            
                            # Check if there's a redirect after login
                            if "redirect_after_login" in st.session_state:
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
        
        st.markdown("Don't have an account? [Sign up here](/pages/signup.py)")
        st.markdown("Forgot your password? [Reset it here](/pages/reset_password.py)")
    
    with col2:
        st.markdown("### Or use a social account")
        
        # Google OAuth button with some styling
        google_auth_url = get_google_auth_url()
        
        st.markdown(
            f"""
            <a href="{google_auth_url}" target="_self" style="text-decoration:none;">
                <div style="
                    background-color:white;
                    border:1px solid #dadce0;
                    border-radius:4px;
                    padding:10px 15px;
                    display:flex;
                    align-items:center;
                    justify-content:center;
                    gap:10px;
                    margin:20px 0;
                    transition: background-color 0.3s;
                    cursor:pointer;
                ">
                    <img src="https://upload.wikimedia.org/wikipedia/commons/5/53/Google_%22G%22_Logo.svg" height="20">
                    <span style="color:#333;font-family:Roboto,sans-serif;font-size:14px;font-weight:500;">
                        Sign in with Google
                    </span>
                </div>
            </a>
            """,
            unsafe_allow_html=True
        )
        
        # Add info box at the bottom
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