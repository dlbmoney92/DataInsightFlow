import streamlit as st
import os
import base64
from datetime import datetime

from utils.navigation_config import get_navigation_items, authenticate_developer, is_developer_mode, set_developer_mode
from utils.subscription import get_trial_days_remaining

def render_navigation():
    """Render the navigation bar in the sidebar."""
    # Get navigation items based on role
    nav_items = get_navigation_items()
    
    # Current page from session state
    current_page = st.session_state.get("current_page", "/")
    
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
        
        # User profile card
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
                    <div style="
                        width: 40px;
                        height: 40px;
                        border-radius: 50%;
                        background: linear-gradient(120deg, #a1c4fd 0%, #c2e9fb 100%);
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        margin-right: 10px;
                        font-weight: bold;
                        color: #1f1f1f;
                    ">{user.get('full_name', 'User')[0].upper() if user.get('full_name') else 'U'}</div>
                    <div>
                        <div style="font-weight: 600; font-size: 16px;">{user.get('full_name', 'User')}</div>
                        <div style="font-size: 12px; opacity: 0.8;">{user.get('email', '')}</div>
                    </div>
                </div>
                <div style="
                    background: {"#4CAF50" if is_trial else "#3b82f6"};
                    color: white;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-size: 12px;
                    display: inline-block;
                    margin-bottom: 5px;
                ">{tier_display}</div>
                <div style="text-align: right; margin-top: 5px;">
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
    
    # Developer mode toggle at the top corner
    # (Hidden button that appears on double-click)
    st.sidebar.markdown("""
        <div id="dev-toggle-corner" style="
            position: absolute; 
            top: 5px; 
            right: 5px; 
            width: 15px; 
            height: 15px; 
            border-radius: 50%;
            cursor: pointer;
        "></div>
        <script>
            const devToggle = document.getElementById('dev-toggle-corner');
            devToggle.addEventListener('dblclick', function() {
                const devLogin = document.getElementById('dev-login-section');
                if (devLogin) {
                    devLogin.style.display = devLogin.style.display === 'none' ? 'block' : 'none';
                }
            });
        </script>
    """, unsafe_allow_html=True)
    
    # Developer login section (hidden by default)
    with st.sidebar.container():
        st.markdown("""
            <div id="dev-login-section" style="display: none; margin-bottom: 20px;">
                <div style="
                    background: rgba(255, 255, 255, 0.1);
                    border-radius: 8px;
                    padding: 15px;
                    border: 1px solid rgba(0, 0, 0, 0.05);
                ">
                    <h4 style="margin-top: 0;">Developer Access</h4>
                    <div id="dev-login-form"></div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Actual form in a hidden container
        with st.container():
            st.write("")  # Placeholder to ensure container exists
            render_developer_login(form_id="sidebar")
    
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
        </style>
    """, unsafe_allow_html=True)
    
    nav_html = '<ul data-testid="stSidebarNavItems" class="st-emotion-cache-1gczx66 e19011e62">'
    
    for item in nav_items:
        is_active = current_page == item.get("url", "#")
        active_class = "sidebar-nav-item-active" if is_active else ""
        
        nav_html += f'''
        <li>
            <a href="{item.get('url', '#')}" target="_self" class="{active_class}">
                <div>
                    {item.get('icon', '')}
                    {item.get('name', 'Link')}
                </div>
            </a>
        </li>
        '''
    
    nav_html += '</ul>'
    
    st.sidebar.markdown(nav_html, unsafe_allow_html=True)
    
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
    
    # If in developer mode, show a label
    if is_developer_mode():
        st.sidebar.markdown("""
            <div style="
                position: fixed;
                bottom: 10px;
                left: 10px;
                background-color: #FF5722;
                color: white;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 10px;
                z-index: 1000;
            ">DEVELOPER MODE</div>
        """, unsafe_allow_html=True)
        
        # Developer logout button
        if st.sidebar.button("Exit Developer Mode", key="exit_dev_mode"):
            logout_developer()

def render_developer_login(form_id="main"):
    """Render the developer login form.
    
    Args:
        form_id: A unique identifier for the form to avoid duplicate keys
    """
    # Check if already in developer mode
    if is_developer_mode():
        return
    
    # Use a unique key for the form
    with st.form(key=f"dev_login_form_{form_id}"):
        dev_username = st.text_input("Username", key=f"dev_username_{form_id}")
        dev_password = st.text_input("Password", type="password", key=f"dev_password_{form_id}")
        
        submit_button = st.form_submit_button("Login")
        
        if submit_button:
            if authenticate_developer(dev_username, dev_password):
                set_developer_mode(True)
                st.success("Developer mode activated")
                st.rerun()
            else:
                st.error("Invalid credentials")

def logout_developer():
    """Logout from developer mode."""
    set_developer_mode(False)
    st.success("Exited developer mode")
    
    # Redirect to home
    st.switch_page("app.py")

def initialize_navigation():
    """Initialize the navigation by determining the current page."""
    # Get the current page from the URL
    current_url = os.environ.get("STREAMLIT_SERVER_BASE_PATH_INFO", "/")
    
    # Store in session state
    if "current_page" not in st.session_state or st.session_state.current_page != current_url:
        st.session_state.current_page = current_url