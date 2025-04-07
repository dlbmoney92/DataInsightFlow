import streamlit as st
import os
import base64
from datetime import datetime

from utils.navigation_config import get_navigation_items, authenticate_developer, is_developer_mode, set_developer_mode
from utils.subscription import get_trial_days_remaining

# Hide Streamlit’s default multipage navigation menu
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {
            display: none !important;
        }
    </style>
""", unsafe_allow_html=True)

def render_navigation():
    """Render the navigation bar in the sidebar."""
    # Get navigation items based on role
    nav_items = get_navigation_items()
    
    # Current page from session state
    current_page = st.session_state.get("current_page", "/")
    
    # Debug info
    print(f"Rendering navigation with current page: {current_page}")
    print(f"Navigation items: {[item.get('url', '#') for item in nav_items]}")
    
    # App title with gradient
    st.sidebar.markdown(
        """
        <div style="
            background: linear-gradient(90deg, #4b6cb7 0%, #182848 100%);
            padding: 10px 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s ease;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        ">
            <h1 style="
                color: white;
                margin: 0;
                font-size: 26px;
                font-weight: 700;
                text-align: center;
                letter-spacing: 0.5px;
            ">Analytics Assist</h1>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    # User profile section if logged in
    if st.session_state.get("logged_in", False):
        user = st.session_state.get("user", {})
        subscription_tier = st.session_state.get("subscription_tier", "free")
        
        # Check if on trial
        trial_days = 0
        is_trial = False
        if user.get("is_trial", False):
            trial_days = get_trial_days_remaining()
            is_trial = trial_days > 0
        
        # Format subscription tier display
        tier_display = subscription_tier.capitalize()
        if is_trial:
            tier_display = f"Pro (Trial: {trial_days} days left)"
        
        # User profile card - simplified
        st.sidebar.markdown(
            f"""
            <div style="
                background: rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 20px;
                border: 1px solid rgba(0, 0, 0, 0.05);
            ">
                <div style="display: flex; align-items: center; margin-bottom: 10px;">
                    <div style="font-weight: 600; font-size: 16px;">
                        Welcome, {user.get('full_name', 'User')}
                    </div>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="
                        background: {"#4CAF50" if is_trial else "#3b82f6"};
                        color: white;
                        border-radius: 4px;
                        padding: 4px 8px;
                        font-size: 12px;
                        display: inline-block;
                    ">{tier_display}</div>
                    <a href="/pages/account.py" style="
                        font-size: 12px;
                        text-decoration: none;
                        color: #3b82f6;
                    ">Manage Account</a>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    
    
    # Navigation Items
    st.sidebar.markdown("""
        <style>
            div[data-testid="stSidebarNavItems"] ul {
                padding-left: 0;
                list-style-type: none;
            }
            
            div[data-testid="stSidebarNavItems"] li {
                margin-bottom: 0.5rem;
            }
            
            div[data-testid="stSidebarNavItems"] a {
                text-decoration: none;
                color: #31333F;
                font-size: 1rem;
                display: block;
                padding: 0.5rem 0.75rem;
                border-radius: 0.375rem;
                transition: all 0.15s ease;
            }
            
            div[data-testid="stSidebarNavItems"] a:hover {
                background-color: rgba(128, 128, 128, 0.1);
            }
            
            div[data-testid="stSidebarNavItems"] a.sidebar-nav-item-active {
                background-color: rgba(128, 128, 128, 0.15);
                font-weight: 600;
                color: #0F52BA;
                border-left: 3px solid #0F52BA;
            }
            
            div[data-testid="stSidebarNavItems"] a div {
                display: flex;
                align-items: center;
            }
            
            div[data-testid="stSidebarNavItems"] a div svg {
                margin-right: 0.75rem;
            }
            
            /* Hide replit domain url in stStatusWidget */
            [data-testid="stStatusWidget"] {
                display: none !important;
            }
        </style>
    """, unsafe_allow_html=True)
    
    # Use standard Streamlit navigation instead of custom HTML
    for item in nav_items:
        is_active = current_page == item.get("url", "#")
        if st.sidebar.button(
            item.get('name', 'Link'), 
            key=f"nav_{item.get('name', 'link').lower().replace(' ', '_')}",
            use_container_width=True,
            type="primary" if is_active else "secondary"
        ):
            # When clicked, navigate to the page
            url = item.get('url', '#')
            # Handle the home page specially
            if url == '/':
                st.switch_page("app.py")
            elif url != '#':
                st.switch_page(url.lstrip('/'))
    
    # Logout button at bottom if logged in
    if st.session_state.get("logged_in", False):
        st.sidebar.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
        if st.sidebar.button("Logout", key="logout_button"):
            # Clear session state
            for key in list(st.session_state.keys()):
                if key != "current_page":  # Keep current page for redirect
                    del st.session_state[key]
            
            st.sidebar.success("Logged out successfully")
            
            # Redirect to home
            st.switch_page("app.py")
    
    # Footer
    st.sidebar.markdown("""
        <div style="
            margin-top: 40px;
            padding-top: 10px;
            border-top: 1px solid rgba(128, 128, 128, 0.2);
            font-size: 0.8rem;
            opacity: 0.7;
            text-align: center;
        ">
            <p>© 2025 Analytics Assist</p>
            <p>
                <a href="/pages/terms_of_service.py" style="text-decoration: none; color: inherit;">Terms</a> · 
                <a href="/pages/privacy_policy.py" style="text-decoration: none; color: inherit;">Privacy</a>
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Developer mode indicators have been removed

# Developer login functionality has been removed as requested
def render_developer_login(form_id="main"):
    """Function stub kept for backward compatibility."""
    pass

def logout_developer():
    """Function stub kept for backward compatibility."""
    pass

def initialize_navigation():
    """Initialize the navigation by determining the current page."""
    # Get the current page from the URL
    current_url = os.environ.get("STREAMLIT_SERVER_BASE_PATH_INFO", "/")
    
    # For the root page, use "/"
    if current_url == "" or current_url is None:
        current_url = "/"
    
    # Print for debugging
    print(f"Current URL detected: {current_url}")
    
    # Store in session state
    if "current_page" not in st.session_state or st.session_state.current_page != current_url:
        st.session_state.current_page = current_url
        print(f"Set current_page to: {current_url}")