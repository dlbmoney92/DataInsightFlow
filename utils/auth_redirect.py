import streamlit as st

def require_auth():
    """
    Check if user is authenticated and redirect to login if not.
    Returns True if authenticated, False if not and redirected.
    """
    if "logged_in" not in st.session_state or not st.session_state.logged_in:
        st.warning("⚠️ You need to log in to use this feature.")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Log In", key="auth_login_btn", use_container_width=True):
                st.switch_page("pages/login.py")
        with col2:
            if st.button("Sign Up", key="auth_signup_btn", use_container_width=True):
                st.switch_page("pages/signup.py")
                
        # Preview message
        st.markdown("---")
        st.info("Sign up for a free account to analyze your data and get AI-powered insights!")
        return False
        
    # User is authenticated
    return True