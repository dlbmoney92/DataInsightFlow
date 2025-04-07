import streamlit as st
from utils.oauth import handle_oauth_callback

def app():
    """Handle OAuth callback from Google.
    
    This page receives the redirect from Google's OAuth consent screen
    and processes the authorization code to log the user in.
    """
    st.title("Processing Authentication...")
    
    # Display a spinner while processing
    with st.spinner("Completing your sign-in..."):
        # Process the OAuth callback
        success = handle_oauth_callback()
        
        if success:
            st.success("You've been successfully signed in!")
            # Redirect to home page after successful login
            st.session_state.login_success = True
            st.rerun()
        else:
            st.error("Authentication failed. Please try again.")
            
            if st.button("Go to Login"):
                # Clear query params and go to login page
                st.query_params.clear()
                st.switch_page("pages/login.py")
    
    # If login was successful, redirect to home page
    if "login_success" in st.session_state and st.session_state.login_success:
        st.session_state.login_success = False
        # Clear query params before redirecting
        st.query_params.clear()
        st.switch_page("app.py")

if __name__ == "__main__":
    app()