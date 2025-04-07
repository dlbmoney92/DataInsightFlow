import streamlit as st
from utils.auth_redirect import require_auth
from utils.custom_navigation import render_navigation
from utils.navigation_config import is_developer_mode
from utils.global_config import apply_global_css

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
    # Apply global CSS to hide default Streamlit navigation
    apply_global_css()
    
    # Set wide mode if requested
    if wide_mode:
        st.set_page_config(
            page_title=f"Analytics Assist - {title}",
            page_icon="📊",
            layout="wide",
            initial_sidebar_state="expanded"
        )
    else:
        st.set_page_config(
            page_title=f"Analytics Assist - {title}",
            page_icon="📊",
            initial_sidebar_state="expanded"
        )
    
    # Apply global CSS again after page config in case it reset anything
    apply_global_css()
    
    # Check authentication if required
    if require_login:
        if not require_auth():
            return False
    
    # Render navigation in sidebar
    with st.sidebar:
        st.markdown("""
        <style>
        .app-title {
            color: #4361ee;
            font-size: 1.75rem;
            font-weight: 700;
            margin-bottom: 20px;
            background: -webkit-linear-gradient(45deg, #4361ee, #7239ea);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        </style>
        <h1 class="app-title">Analytics Assist</h1>
        """, unsafe_allow_html=True)
        
        render_navigation()
    
    # Display page title
    st.title(title)
    
    return True