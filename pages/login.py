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
        
        # Create a Google "G" logo as inline SVG instead of using an external image
        google_g_logo = """
        <svg width="20" height="20" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
          <g transform="matrix(1, 0, 0, 1, 27.009001, -39.238998)">
            <path fill="#4285F4" d="M -3.264 51.509 C -3.264 50.719 -3.334 49.969 -3.454 49.239 L -14.754 49.239 L -14.754 53.749 L -8.284 53.749 C -8.574 55.229 -9.424 56.479 -10.684 57.329 L -10.684 60.329 L -6.824 60.329 C -4.564 58.239 -3.264 55.159 -3.264 51.509 Z"/>
            <path fill="#34A853" d="M -14.754 63.239 C -11.514 63.239 -8.804 62.159 -6.824 60.329 L -10.684 57.329 C -11.764 58.049 -13.134 58.489 -14.754 58.489 C -17.884 58.489 -20.534 56.379 -21.484 53.529 L -25.464 53.529 L -25.464 56.619 C -23.494 60.539 -19.444 63.239 -14.754 63.239 Z"/>
            <path fill="#FBBC05" d="M -21.484 53.529 C -21.734 52.809 -21.864 52.039 -21.864 51.239 C -21.864 50.439 -21.724 49.669 -21.484 48.949 L -21.484 45.859 L -25.464 45.859 C -26.284 47.479 -26.754 49.299 -26.754 51.239 C -26.754 53.179 -26.284 54.999 -25.464 56.619 L -21.484 53.529 Z"/>
            <path fill="#EA4335" d="M -14.754 43.989 C -12.984 43.989 -11.404 44.599 -10.154 45.789 L -6.734 42.369 C -8.804 40.429 -11.514 39.239 -14.754 39.239 C -19.444 39.239 -23.494 41.939 -25.464 45.859 L -21.484 48.949 C -20.534 46.099 -17.884 43.989 -14.754 43.989 Z"/>
          </g>
        </svg>
        """
        
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
                    {google_g_logo}
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