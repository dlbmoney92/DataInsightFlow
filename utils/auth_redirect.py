import streamlit as st

def require_auth():
    """
    Check if user is authenticated and redirect to login if not.
    Returns True if authenticated, False if not and redirected.
    """
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