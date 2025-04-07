import streamlit as st
from utils.global_config import apply_global_css, render_footer
from utils.custom_navigation import initialize_navigation, render_navigation, render_developer_login, logout_developer
from utils.auth_redirect import require_auth

def init_page(title, require_login=True, wide_mode=True):
    """
    Initialize a page with standard configuration.
    
    Parameters:
    - title: The page title to display
    - require_login: Whether login is required to access this page
    - wide_mode: Whether to use wide layout
    
    Returns:
    - True if page initialization was successful, False if login redirect occurred
    """
    # Apply global CSS
    apply_global_css()
    
    # Initialize navigation
    initialize_navigation()
    
    # Render navigation in sidebar
    render_navigation()
    
    # If developer mode is active, show logout option
    logout_developer()
    
    # Show developer login (hidden in sidebar expander)
    render_developer_login()
    
    # Check login if required
    if require_login:
        if not require_auth():
            return False
    
    # Display page title
    st.title(title)
    
    # Render footer
    render_footer()
    
    return True