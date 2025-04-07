import streamlit as st
import hashlib
import json
import os
from utils.database import check_valid_credentials, update_last_login, get_user_by_email, create_user
from utils.oauth import initialize_google_oauth, get_google_auth_url

def app():
    st.title("Login to Analytics Assist")
    
    # Check if we need to redirect after successful login
    if "login_success" in st.session_state and st.session_state.login_success:
        st.session_state.login_success = False
        st.switch_page("app.py")
        
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
    
    # Create a modern login UI with two tabs
    tab1, tab2 = st.tabs(["Login with Email", "Social Login"])
    
    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email", key="email_login")
            password = st.text_input("Password", type="password", key="password_login")
            submit = st.form_submit_button("Log In", use_container_width=True)
            
            if submit:
                if email and password:
                    # Hash the password (SHA-256)
                    password_hash = hashlib.sha256(password.encode()).hexdigest()
                    
                    # Check credentials
                    user = check_valid_credentials(email, password_hash)
                    
                    if user:
                        # Set user in session state
                        st.session_state.user = user
                        st.session_state.logged_in = True
                        st.session_state.user_id = user["id"]
                        st.session_state.subscription_tier = user["subscription_tier"]
                        
                        # Update last login
                        update_last_login(user["id"])
                        
                        # Set a flag to redirect after successful login
                        st.session_state.login_success = True
                        st.session_state.login_message = "Login successful!"
                        st.success("Login successful!")
                        st.rerun()  # Force a rerun to handle the redirection
                    else:
                        st.error("Invalid email or password. Please try again.")
                else:
                    st.error("Please enter both email and password.")
    
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
        
        google_clicked = st.button("Sign in with Google", key="google_login", use_container_width=True)
        
        if google_clicked:
            try:
                # Check if Google OAuth is configured
                if initialize_google_oauth():
                    # Get the Google authorization URL
                    auth_url = get_google_auth_url()
                    if auth_url:
                        # Store the current URL in session state for redirect URI calculation
                        st.query_params["request_uri"] = st.experimental_get_query_params().get("request_uri", [""])[0]
                        
                        # Redirect to Google's authorization page
                        st.markdown(f'<meta http-equiv="refresh" content="0;url={auth_url}">', unsafe_allow_html=True)
                        st.info("Redirecting to Google for authentication...")
                        st.stop()
                    else:
                        st.error("Failed to generate Google authentication URL")
                else:
                    # Show configuration message if Google OAuth is not set up
                    st.warning("""
                    Google Sign-In is not configured. To implement Google Sign-In, you'll need to:
                    1. Create a project in Google Cloud Console
                    2. Configure OAuth consent screen
                    3. Create OAuth credentials (Client ID and Secret)
                    4. Add these authorized redirect URIs for your app:
                       - http://localhost:5000/oauth_callback
                       - http://localhost:5000/pages/oauth_callback
                       - https://analytics-assist.replit.app/oauth_callback
                       - https://analytics-assist.replit.app/pages/oauth_callback
                    """)
                    
                    # For demonstration purposes - simulating a successful OAuth login
                    if st.button("Simulate Successful Google Login (Demo)", key="simulate_google"):
                        # Create a mock Google user profile
                        google_user = {
                            "email": "demo_google_user@example.com",
                            "name": "Google Demo User",
                            "oauth_provider": "google"
                        }
                        
                        # Check if user exists in database or create a new one
                        existing_user = get_user_by_email(google_user["email"])
                        if not existing_user:
                            # Generate a random secure password for OAuth users
                            import secrets
                            random_password = secrets.token_hex(16)
                            password_hash = hashlib.sha256(random_password.encode()).hexdigest()
                            
                            # Create new user
                            create_user(google_user["email"], password_hash, google_user["name"])
                            existing_user = get_user_by_email(google_user["email"])
                        
                        # Log the user in
                        if existing_user:
                            st.session_state.user = existing_user
                            st.session_state.logged_in = True
                            st.session_state.user_id = existing_user["id"]
                            st.session_state.subscription_tier = existing_user["subscription_tier"]
                            
                            # Update last login
                            update_last_login(existing_user["id"])
                            
                            # Set a flag to redirect after successful login
                            st.session_state.login_success = True
                            st.session_state.login_message = "Google login successful!"
                            st.success("Google login successful!")
                            st.rerun()
                
            except Exception as e:
                st.error(f"Error with Google login: {str(e)}")
    
    # Don't have an account section
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center;'>Don't have an account?</div>", 
        unsafe_allow_html=True
    )
    
    if st.button("Create a New Account", use_container_width=True):
        st.session_state.go_to_signup = True
        st.rerun()
        
    # Check if we need to navigate to signup page
    if "go_to_signup" in st.session_state and st.session_state.go_to_signup:
        st.session_state.go_to_signup = False
        st.switch_page("pages/signup.py")

if __name__ == "__main__":
    app()