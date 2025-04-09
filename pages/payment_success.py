import os
import streamlit as st

# Set page configuration - must be the first Streamlit command
st.set_page_config(
    page_title="Payment Success | Analytics Assist",
    page_icon="✅",
    layout="wide"
)

from utils.auth_redirect import require_auth
from utils.global_config import apply_global_css
from utils.custom_navigation import render_navigation, initialize_navigation
from utils.database import get_user_by_id

# Apply global CSS
apply_global_css()

# Initialize navigation
initialize_navigation()

# Hide Streamlit's default multipage navigation menu
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {
            display: none !important;
        }
    </style>
""", unsafe_allow_html=True)

# Render custom navigation bar
render_navigation()

def app():
    """Handle successful payment redirect from Stripe."""
    
    # Check if user is logged in
    if not require_auth():
        return
    
    # Get query parameters
    query_params = st.query_params
    success = query_params.get("success", "false") == "true"
    tier = query_params.get("tier", None)
    
    # Update user information after successful payment
    if success and tier:
        # Get updated user info
        user = get_user_by_id(st.session_state.user_id)
        st.session_state.user = user
        st.session_state.subscription_tier = user["subscription_tier"]
    
    # Clear query params after reading
    if "success" in query_params or "tier" in query_params:
        new_params = {}
        for param in query_params:
            if param != "success" and param != "tier":
                new_params[param] = query_params[param]
        st.query_params.update(new_params)
    
    # Create a modal-like container
    with st.container():
        st.markdown('<div class="modal-container">', unsafe_allow_html=True)
        
        # Modal header
        st.markdown('''
        <div class="modal-header">
            <h2 class="modal-title">Payment Successful!</h2>
            <a href="/" class="modal-close">×</a>
        </div>
        ''', unsafe_allow_html=True)
        
        st.markdown('<div class="modal-body">', unsafe_allow_html=True)
    
    # Show different messages based on the tier
    if tier == "basic":
        st.success("Thank you for subscribing to the Basic tier! Your account has been upgraded.")
        st.markdown("""
        ## What's next?
        
        You now have access to:
        - 10 datasets
        - Advanced data transformations
        - Interactive visualizations
        - CSV, Excel, and PDF support
        - 30-day data history
        - Priority support
        - Data validation tools
        
        Start exploring your new features now!
        """)
    elif tier == "pro":
        st.success("Thank you for subscribing to the Pro tier! Your account has been upgraded.")
        st.markdown("""
        ## What's next?
        
        You now have access to:
        - Unlimited datasets
        - All data transformations
        - Advanced AI-driven insights
        - All file formats supported
        - 90-day data history
        - Priority support
        - Data validation tools
        - Custom reports and exports
        - Team collaboration features
        
        Start exploring your new features now!
        """)
    else:
        st.success("Thank you for your payment! Your account has been upgraded.")
    
    # Add automatic redirect to home page after 5 seconds
    st.markdown("""
    <p>Redirecting to dashboard in 5 seconds...</p>
    <script>
        setTimeout(function() {
            window.location.href = "/";
        }, 5000);
    </script>
    """, unsafe_allow_html=True)
    
    # Button to go to home
    if st.button("Go to Dashboard", use_container_width=True):
        st.switch_page("app.py")
    
    # Button to upload data
    if st.button("Upload Data", use_container_width=True):
        st.switch_page("pages/01_Upload_Data.py")
        
    # Close the modal body and container divs
    st.markdown('</div>', unsafe_allow_html=True)  # Close modal-body
    
    # Modal footer
    st.markdown('''
    <div class="modal-footer">
        <a href="/" class="btn">Return to Home</a>
    </div>
    ''', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close modal-container

if __name__ == "__main__":
    app()