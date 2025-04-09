import streamlit as st
import json
import base64
from datetime import datetime, timedelta

def get_cookie_token():
    """Get auth token from cookies if available."""
    try:
        if "analytics_assist_auth" in st.experimental_get_query_params():
            # Get token from URL if present
            encoded_token = st.experimental_get_query_params()["analytics_assist_auth"][0]
            token_data = json.loads(base64.b64decode(encoded_token).decode())
            
            # Check token expiration
            expiry = datetime.fromisoformat(token_data["expiry"])
            if datetime.now() < expiry:
                # Valid token, update session state
                st.session_state.logged_in = True
                st.session_state.user_id = token_data["user_id"]
                st.session_state.user_email = token_data["email"]
                st.session_state.user_name = token_data["name"]
                st.session_state.user_subscription = token_data["subscription"]
                
                # Clear the token from URL to avoid issues
                params = st.experimental_get_query_params()
                if "analytics_assist_auth" in params:
                    del params["analytics_assist_auth"]
                    st.experimental_set_query_params(**params)
                
                return True
    except Exception as e:
        print(f"Error parsing auth token: {str(e)}")
    
    return False

def set_auth_cookie():
    """Set a cookie with auth information."""
    if st.session_state.get("logged_in", False):
        try:
            # Create token with user info and 7-day expiry
            token_data = {
                "user_id": st.session_state.user_id,
                "email": st.session_state.user_email,
                "name": st.session_state.user_name,
                "subscription": st.session_state.user_subscription,
                "expiry": (datetime.now() + timedelta(days=7)).isoformat()
            }
            
            # Convert to base64 encoded JSON
            token = base64.b64encode(json.dumps(token_data).encode()).decode()
            
            # Create a script to store in localStorage
            script = f"""
            <script>
                localStorage.setItem('analytics_assist_auth', '{token}');
                
                // Check on page load if we need to restore the auth state
                document.addEventListener('DOMContentLoaded', function() {{
                    if (!window.location.search.includes('analytics_assist_auth')) {{
                        const token = localStorage.getItem('analytics_assist_auth');
                        if (token) {{
                            // If we're not on login/signup page, add the token
                            const currentPath = window.location.pathname;
                            if (!currentPath.includes('login') && !currentPath.includes('signup')) {{
                                const separator = window.location.search ? '&' : '?';
                                window.location.href = window.location.href + separator + 'analytics_assist_auth=' + token;
                            }}
                        }}
                    }}
                }});
            </script>
            """
            
            st.markdown(script, unsafe_allow_html=True)
            return True
        except Exception as e:
            print(f"Error setting auth cookie: {str(e)}")
    
    return False

def require_auth():
    """
    Check if user is authenticated and redirect to login if not.
    Returns True if authenticated, False if not and redirected.
    """
    # First try to get auth from cookie
    if not st.session_state.get("logged_in", False):
        get_cookie_token()
    
    # Set cookie if logged in
    if st.session_state.get("logged_in", True):
        set_auth_cookie()
    
    # Check auth status
    if not st.session_state.get("logged_in", False):
        st.warning("Please log in to access this page.")
        
        # Add login and signup buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Login", key="login_redirect_btn"):
                st.switch_page("pages/login.py")
        with col2:
            if st.button("Sign Up", key="signup_redirect_btn"):
                st.switch_page("pages/signup.py")
                
        # Remember where the user tried to access for post-login redirect
        current_page = st.session_state.get("current_page", "/")
        if current_page != "/" and current_page != "/pages/login.py" and current_page != "/pages/signup.py":
            st.session_state["redirect_after_login"] = current_page
            
        return False
    
    return True