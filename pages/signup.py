import streamlit as st
import hashlib
import re
import json
from utils.database import create_user, start_user_trial
from utils.oauth import initialize_google_oauth, get_google_auth_url

def is_valid_email(email):
    """Check if email is valid using regex."""
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

def is_strong_password(password):
    """Check if password is strong enough."""
    # At least 8 characters, one uppercase, one lowercase, one number
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter."
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter."
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number."
    return True, ""

def app():
    st.title("Sign Up for Analytics Assist")
    
    # If already logged in, redirect to home
    if "logged_in" in st.session_state and st.session_state.logged_in:
        st.info("You are already logged in.")
        if st.button("Go to Home"):
            st.session_state.go_to_home = True
            st.rerun()
        
        # Handle navigation to home
        if "go_to_home" in st.session_state and st.session_state.go_to_home:
            st.session_state.go_to_home = False
            st.switch_page("app.py")
            
        return
    
    # Create tabs for different signup methods
    tab1, tab2 = st.tabs(["Sign Up with Email", "Sign Up with Google"])
    
    with tab1:
        with st.form("signup_form"):
            full_name = st.text_input("Full Name")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            
            start_trial = st.checkbox("Start with a free 7-day Pro trial")
            
            terms_accepted = st.checkbox("I accept the terms and conditions")
            
            submit = st.form_submit_button("Sign Up", use_container_width=True)
            
            if submit:
                # Validate inputs
                if not full_name or not email or not password or not confirm_password:
                    st.error("Please fill in all fields.")
                    return
                    
                if not is_valid_email(email):
                    st.error("Please enter a valid email address.")
                    return
                    
                if password != confirm_password:
                    st.error("Passwords do not match.")
                    return
                    
                is_strong, password_message = is_strong_password(password)
                if not is_strong:
                    st.error(password_message)
                    return
                    
                if not terms_accepted:
                    st.error("You must accept the terms and conditions.")
                    return
                
                # Hash the password (SHA-256)
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                
                # Create user
                result = create_user(email, password_hash, full_name)
                
                if result['success']:
                    user_id = result['user_id']
                    
                    # Start trial if requested
                    if start_trial:
                        start_user_trial(user_id)
                        st.success("Your account has been created and your 7-day Pro trial has been activated!")
                    else:
                        st.success("Your account has been created successfully!")
                    
                    # Set user in session state
                    user = {"id": user_id, "email": email, "full_name": full_name, "subscription_tier": "free"}
                    st.session_state.user = user
                    st.session_state.logged_in = True
                    st.session_state.user_id = user_id
                    st.session_state.subscription_tier = "free"
                    
                    # Store a flag to redirect to subscription selection
                    st.session_state.redirect_to_subscription = True
                else:
                    st.error(f"Error creating account: {result['message']}")
    
    with tab2:
        st.markdown(
            """
            <style>
            .social-btn {
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 10px 20px;
                margin: 10px 0;
                border-radius: 4px;
                cursor: pointer;
                font-weight: bold;
                transition: background-color 0.3s;
            }
            .google-btn {
                background-color: white;
                color: #444;
                border: 1px solid #ddd;
            }
            .google-btn:hover {
                background-color: #f5f5f5;
            }
            .google-icon {
                margin-right: 10px;
                width: 20px;
                height: 20px;
            }
            </style>
            """,
            unsafe_allow_html=True
        )
        
        st.markdown("### Continue with Google")
        st.write("Create an account using your Google credentials. We'll only access your basic profile information.")
        
        # Add Terms and Pro trial options for Google signup too
        start_trial_google = st.checkbox("Start with a free 7-day Pro trial", key="start_trial_google")
        terms_accepted_google = st.checkbox("I accept the terms and conditions", key="terms_google")
        
        # Create a Google "G" logo as inline SVG
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
        
        # Get the Google auth URL for the signup flow
        google_auth_url = get_google_auth_url()
        
        if terms_accepted_google:
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
                            Sign up with Google
                        </span>
                    </div>
                </a>
                """,
                unsafe_allow_html=True
            )
        else:
            # If terms not accepted, show a disabled button
            st.markdown(
                f"""
                <div style="
                    background-color:#f8f9fa;
                    border:1px solid #dadce0;
                    border-radius:4px;
                    padding:10px 15px;
                    display:flex;
                    align-items:center;
                    justify-content:center;
                    gap:10px;
                    margin:20px 0;
                    opacity: 0.6;
                ">
                    {google_g_logo}
                    <span style="color:#333;font-family:Roboto,sans-serif;font-size:14px;font-weight:500;">
                        Sign up with Google
                    </span>
                </div>
                """,
                unsafe_allow_html=True
            )
            st.warning("Please accept the terms and conditions to continue with Google Sign-up")
        
        if google_clicked:
            if not terms_accepted_google:
                st.error("You must accept the terms and conditions.")
            else:
                try:
                    # Here we'd normally implement the OAuth flow
                    # For now, we'll simulate success with a message
                    st.info("Google OAuth will be implemented with your credentials")
                    st.warning("""
                    To implement Google Sign-In, you'll need to:
                    1. Create a project in Google Cloud Console
                    2. Configure OAuth consent screen
                    3. Create OAuth credentials (Client ID and Secret)
                    4. Add authorized redirect URIs for your app
                    """)
                    
                    # For demonstration purposes - simulating a successful OAuth signup
                    if st.button("Simulate Successful Google Signup (Demo)", key="simulate_google_signup"):
                        # Create a mock Google user profile
                        google_user = {
                            "email": "demo_google_user@example.com",
                            "name": "Google Demo User",
                            "oauth_provider": "google"
                        }
                        
                        # Generate a random secure password for OAuth users
                        import secrets
                        random_password = secrets.token_hex(16)
                        password_hash = hashlib.sha256(random_password.encode()).hexdigest()
                        
                        # Create new user
                        result = create_user(google_user["email"], password_hash, google_user["name"])
                        
                        if result['success']:
                            user_id = result['user_id']
                            
                            # Start trial if requested
                            if start_trial_google:
                                start_user_trial(user_id)
                                st.success("Your account has been created and your 7-day Pro trial has been activated!")
                            else:
                                st.success("Your account has been created successfully!")
                            
                            # Set user in session state
                            user = {"id": user_id, "email": google_user["email"], "full_name": google_user["name"], "subscription_tier": "free"}
                            st.session_state.user = user
                            st.session_state.logged_in = True
                            st.session_state.user_id = user_id
                            st.session_state.subscription_tier = "free"
                            
                            # Store a flag to redirect to subscription selection
                            st.session_state.redirect_to_subscription = True
                        else:
                            st.error(f"Error creating account: {result['message']}")
                
                except Exception as e:
                    st.error(f"Error with Google signup: {str(e)}")
    
    # Check if we need to redirect after successful signup
    if "redirect_to_subscription" in st.session_state and st.session_state.redirect_to_subscription:
        st.session_state.redirect_to_subscription = False
        st.switch_page("pages/subscription_selection.py")
    elif "redirect_to_login" in st.session_state and st.session_state.redirect_to_login:
        st.session_state.redirect_to_login = False
        st.switch_page("pages/login.py")
        
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center;'>Already have an account?</div>", 
        unsafe_allow_html=True
    )
    
    if st.button("Log In to Your Account", use_container_width=True):
        st.session_state.go_to_login = True
        st.rerun()
        
    # Check if we need to navigate to login page
    if "go_to_login" in st.session_state and st.session_state.go_to_login:
        st.session_state.go_to_login = False
        st.switch_page("pages/login.py")

if __name__ == "__main__":
    app()