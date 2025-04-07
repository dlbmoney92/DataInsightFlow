import streamlit as st
import hashlib
import secrets
import os
import json
import datetime
import uuid
from urllib.parse import urlencode

def get_redirect_uri():
    """Get the appropriate redirect URI based on the request environment."""
    # In production, this would use the actual domain
    # For development, we use the localhost address
    base_url = os.environ.get("BASE_URL", "http://localhost:5000")
    return f"{base_url}/pages/oauth_callback.py"

def initialize_google_oauth():
    """Initialize Google OAuth configuration.
    
    In a real implementation, this would verify OAuth credentials
    are available and set up the proper flow.
    """
    # In a real implementation, we would get these from environment variables or secrets
    client_id = os.environ.get("GOOGLE_OAUTH_CLIENT_ID", "dummy-client-id")
    client_secret = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET", "dummy-client-secret")
    
    # Store in session state
    st.session_state.google_client_id = client_id
    st.session_state.google_client_secret = client_secret
    
    return True

def get_google_auth_url():
    """Generate the Google authorization URL.
    
    This would direct users to Google's consent screen.
    """
    # Ensure OAuth is initialized
    if not initialize_google_oauth():
        return "#"  # Return dummy URL if initialization fails
    
    # Generate and store state token to prevent CSRF
    state = generate_state_token()
    
    # Build the authorization URL
    auth_params = {
        "client_id": st.session_state.google_client_id,
        "redirect_uri": get_redirect_uri(),
        "scope": "openid email profile",
        "response_type": "code",
        "state": state,
        "access_type": "offline",
        "prompt": "select_account"
    }
    
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(auth_params)}"
    return auth_url

def generate_state_token():
    """Generate a random state token to prevent CSRF attacks."""
    state = secrets.token_hex(16)
    st.session_state.oauth_state = state
    return state

def verify_state_token(state):
    """Verify that the state token matches."""
    return state == st.session_state.get("oauth_state", "")

def exchange_code_for_token(code):
    """Exchange authorization code for access token.
    
    In a real implementation, this would call Google's token endpoint.
    """
    # In a real implementation, this would make an actual HTTP request to Google
    # For demo, we'll simulate a successful token response
    token_data = {
        "access_token": f"simulated-access-token-{uuid.uuid4()}",
        "id_token": f"simulated-id-token-{uuid.uuid4()}",
        "refresh_token": f"simulated-refresh-token-{uuid.uuid4()}",
        "expires_in": 3600
    }
    
    return token_data

def get_user_info(token_data):
    """Get user info from Google using access token.
    
    In a real implementation, this would call Google's userinfo endpoint.
    """
    # In a real implementation, this would make an actual HTTP request to Google
    # For demo, we'll generate dummy user info
    user_info = {
        "sub": f"google-user-{uuid.uuid4()}",
        "email": f"user-{uuid.uuid4().hex[:8]}@example.com",
        "name": "Demo User",
        "picture": "https://ui-avatars.com/api/?name=Demo+User&background=random"
    }
    
    return user_info

def handle_oauth_callback():
    """Handle the OAuth callback from Google.
    
    This would be called on the redirect from Google's consent screen.
    """
    # Get query parameters
    query_params = st.experimental_get_query_params()
    
    # Check for error
    if "error" in query_params:
        error = query_params["error"][0]
        return {
            "success": False,
            "message": f"Authentication failed: {error}"
        }
    
    # Check for code and state
    if "code" not in query_params or "state" not in query_params:
        return {
            "success": False,
            "message": "Missing required parameters in callback"
        }
    
    code = query_params["code"][0]
    state = query_params["state"][0]
    
    # Verify state to prevent CSRF
    if not verify_state_token(state):
        return {
            "success": False,
            "message": "Invalid state token, possible CSRF attack"
        }
    
    # Exchange code for token
    token_data = exchange_code_for_token(code)
    if not token_data:
        return {
            "success": False,
            "message": "Failed to obtain token"
        }
    
    # Get user info
    user_info = get_user_info(token_data)
    if not user_info:
        return {
            "success": False,
            "message": "Failed to get user info"
        }
    
    # Process user info (create or log in user)
    process_result = process_oauth_user(user_info)
    
    return process_result

def process_oauth_user(user_info):
    """Process user info from OAuth provider.
    
    Check if user exists in database, create if not, and log them in.
    """
    from utils.database import get_user_by_email, create_user, update_last_login
    
    # Check if user exists by email
    user = get_user_by_email(user_info["email"])
    
    # If user doesn't exist, create new user
    if not user:
        # Generate random password for user
        random_password = secrets.token_hex(16)
        password_hash = hashlib.sha256(random_password.encode()).hexdigest()
        
        # Create user
        user_id = create_user(
            email=user_info["email"],
            password_hash=password_hash,
            full_name=user_info.get("name", "")
        )
        
        # Get the newly created user
        user = get_user_by_email(user_info["email"])
        
        if not user:
            return {
                "success": False,
                "message": "Failed to create user"
            }
    
    # Update last login time
    update_last_login(user["id"])
    
    # Set session state for user
    st.session_state.logged_in = True
    st.session_state.user = user
    st.session_state.user_id = user["id"]
    st.session_state.subscription_tier = user.get("subscription_tier", "free")
    
    return {
        "success": True,
        "message": "Authentication successful",
        "user": user
    }