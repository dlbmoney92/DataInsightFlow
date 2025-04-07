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
                    
                    # Store a flag to redirect after form
                    st.session_state.redirect_to_login = True
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
        
        google_clicked = st.button("Sign up with Google", key="google_signup", use_container_width=True)
        
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
                            
                            # Store a flag to redirect after form
                            st.session_state.redirect_to_login = True
                        else:
                            st.error(f"Error creating account: {result['message']}")
                
                except Exception as e:
                    st.error(f"Error with Google signup: {str(e)}")
    
    # Check if we need to redirect to login page after successful signup
    if "redirect_to_login" in st.session_state and st.session_state.redirect_to_login:
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