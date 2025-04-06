import streamlit as st
import hashlib
from utils.database import check_valid_credentials, update_last_login

def app():
    st.title("Login to Analytics Assist")
    
    # If already logged in, redirect to home
    if "logged_in" in st.session_state and st.session_state.logged_in:
        st.info("You are already logged in.")
        st.button("Go to Home", on_click=lambda: st.switch_page("app.py"))
        return
    
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Log In")
        
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
                    
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid email or password. Please try again.")
            else:
                st.error("Please enter both email and password.")
    
    st.markdown("---")
    st.markdown("Don't have an account? [Sign up here](/signup)")
    st.button("Sign Up", on_click=lambda: st.switch_page("pages/signup.py"))

if __name__ == "__main__":
    app()