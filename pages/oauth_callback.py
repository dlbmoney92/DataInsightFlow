import streamlit as st
from utils.oauth import handle_oauth_callback
from utils.global_config import apply_global_css

def app():
    """Handle OAuth callback from Google.
    
    This page receives the redirect from Google's OAuth consent screen
    and processes the authorization code to log the user in.
    """
    # Apply global CSS
    apply_global_css()
    
    st.title("Processing Authentication")
    
    # Handle the OAuth callback
    result = handle_oauth_callback()
    
    if result["success"]:
        st.success(f"Authentication successful! Welcome, {st.session_state.user.get('full_name', 'User')}")
        
        # Show a spinner while redirecting
        with st.spinner("Redirecting to dashboard..."):
            import time
            time.sleep(2)  # Give user time to see the success message
            
            # Check if there's a redirect after login
            if "redirect_after_login" in st.session_state:
                redirect_page = st.session_state.pop("redirect_after_login")
                st.switch_page(redirect_page)
            else:
                # Redirect to home page
                st.switch_page("app.py")
    else:
        st.error(f"Authentication failed: {result['message']}")
        st.button("Try Again", on_click=lambda: st.switch_page("pages/login.py"))

if __name__ == "__main__":
    app()