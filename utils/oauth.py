import streamlit as st
import os
import json
import requests
import hashlib
import secrets
from utils.database import get_user_by_email, create_user, update_last_login

# OAuth configuration
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
REDIRECT_URI = os.getenv('REDIRECT_URI', 'http://localhost:5000/oauth_callback')

def initialize_google_oauth():
    """Initialize Google OAuth configuration.
    
    In a real implementation, this would verify OAuth credentials
    are available and set up the proper flow.
    """
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        st.warning("Google OAuth credentials are not configured")
        return False
    return True

def get_google_auth_url():
    """Generate the Google authorization URL.
    
    This would direct users to Google's consent screen.
    """
    if not initialize_google_oauth():
        return None
        
    # Construct the Google authorization URL
    auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={GOOGLE_CLIENT_ID}"
        "&response_type=code"
        f"&redirect_uri={REDIRECT_URI}"
        "&scope=openid%20email%20profile"
        f"&state={generate_state_token()}"
    )
    return auth_url

def generate_state_token():
    """Generate a random state token to prevent CSRF attacks."""
    state_token = secrets.token_hex(16)
    st.session_state.oauth_state = state_token
    return state_token

def verify_state_token(state):
    """Verify that the state token matches."""
    return "oauth_state" in st.session_state and st.session_state.oauth_state == state

def exchange_code_for_token(code):
    """Exchange authorization code for access token.
    
    In a real implementation, this would call Google's token endpoint.
    """
    if not initialize_google_oauth():
        return None
        
    token_url = "https://oauth2.googleapis.com/token"
    payload = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code"
    }
    
    try:
        response = requests.post(token_url, data=payload)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to exchange code for token: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error exchanging code for token: {str(e)}")
        return None

def get_user_info(token_data):
    """Get user info from Google using access token.
    
    In a real implementation, this would call Google's userinfo endpoint.
    """
    if not token_data or "access_token" not in token_data:
        return None
        
    userinfo_url = "https://www.googleapis.com/oauth2/v3/userinfo"
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}
    
    try:
        response = requests.get(userinfo_url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to get user info: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error getting user info: {str(e)}")
        return None

def handle_oauth_callback():
    """Handle the OAuth callback from Google.
    
    This would be called on the redirect from Google's consent screen.
    """
    # Get query parameters from the URL using the new API
    query_params = st.query_params
    
    # Check for errors
    if "error" in query_params:
        st.error(f"Authentication error: {query_params['error']}")
        return False
    
    # Check for authorization code and state
    if "code" not in query_params or "state" not in query_params:
        st.error("Invalid callback: missing code or state")
        return False
    
    # Verify state to prevent CSRF
    if not verify_state_token(query_params["state"]):
        st.error("Invalid state token")
        return False
    
    # Exchange code for token
    token_data = exchange_code_for_token(query_params["code"])
    if not token_data:
        st.error("Failed to get access token")
        return False
    
    # Get user info
    user_info = get_user_info(token_data)
    if not user_info:
        st.error("Failed to get user info")
        return False
    
    # Process user info (email, name, etc.)
    return process_oauth_user(user_info)

def process_oauth_user(user_info):
    """Process user info from OAuth provider.
    
    Check if user exists in database, create if not, and log them in.
    """
    email = user_info.get("email")
    name = user_info.get("name", "")
    
    if not email:
        st.error("Email address not provided by OAuth provider")
        return False
    
    # Check if user exists in database
    existing_user = get_user_by_email(email)
    if not existing_user:
        # Generate a random secure password for OAuth users
        random_password = secrets.token_hex(16)
        password_hash = hashlib.sha256(random_password.encode()).hexdigest()
        
        # Create new user
        try:
            create_user(email, password_hash, name)
            existing_user = get_user_by_email(email)
        except Exception as e:
            st.error(f"Failed to create user: {str(e)}")
            return False
    
    # Log the user in
    if existing_user:
        st.session_state.user = existing_user
        st.session_state.logged_in = True
        st.session_state.user_id = existing_user["id"]
        st.session_state.subscription_tier = existing_user["subscription_tier"]
        
        # Update last login
        update_last_login(existing_user["id"])
        
        return True
    else:
        st.error("Failed to log in with Google account")
        return False