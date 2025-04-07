import streamlit as st
import hashlib
import re
from utils.database import create_user, start_user_trial

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
        st.button("Go to Home", on_click=lambda: st.switch_page("app.py"))
        return
    
    with st.form("signup_form"):
        full_name = st.text_input("Full Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        
        start_trial = st.checkbox("Start with a free 7-day Pro trial")
        
        terms_accepted = st.checkbox("I accept the terms and conditions")
        
        submit = st.form_submit_button("Sign Up")
        
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
    
    # Check if we need to redirect to login page after successful signup
    if "redirect_to_login" in st.session_state and st.session_state.redirect_to_login:
        st.session_state.redirect_to_login = False
        st.switch_page("pages/login.py")
        
    st.markdown("---")
    st.markdown("Already have an account? [Log in here](/login)")
    st.button("Log In", on_click=lambda: st.switch_page("pages/login.py"))

if __name__ == "__main__":
    app()