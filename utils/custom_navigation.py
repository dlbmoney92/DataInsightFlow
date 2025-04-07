import streamlit as st
from utils.navigation_config import get_navigation_items, is_developer_mode, authenticate_developer
from utils.subscription import SUBSCRIPTION_TIERS, format_price, get_trial_days_remaining

def render_navigation():
    """Render the navigation bar in the sidebar."""
    # Check if first run and initialize user_role
    if "user_role" not in st.session_state:
        st.session_state["user_role"] = "user"
    
    # Get the current navigation items
    navigation_items = get_navigation_items()
    
    # Create styled navigation CSS
    st.markdown("""
    <style>
    .sidebar-nav-container {
        display: flex;
        flex-direction: column;
        gap: 8px;
        padding: 10px 0;
        margin-bottom: 20px;
    }
    
    .sidebar-nav-item {
        display: flex;
        align-items: center;
        padding: 8px 12px;
        border-radius: 8px;
        text-decoration: none;
        color: #495057;
        transition: all 0.3s ease;
        background-color: rgba(255, 255, 255, 0.7);
    }
    
    .sidebar-nav-item:hover {
        background-color: rgba(52, 152, 219, 0.1);
        color: #3498db;
    }
    
    .sidebar-nav-item.active {
        background-color: rgba(52, 152, 219, 0.2);
        color: #2980b9;
        font-weight: bold;
    }
    
    .sidebar-nav-icon {
        font-size: 1.2rem;
        margin-right: 10px;
        width: 25px;
        text-align: center;
    }
    
    .sidebar-nav-label {
        font-size: 0.9rem;
    }
    
    .user-profile-container {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 20px;
    }
    
    .user-name {
        font-weight: bold;
        margin-bottom: 5px;
    }
    
    .subscription-info {
        font-size: 0.9rem;
        color: #666;
    }
    
    .trial-info {
        font-size: 0.8rem;
        margin-top: 5px;
        padding: 5px;
        background-color: #e3f2fd;
        border-radius: 5px;
        color: #0d47a1;
    }
    
    .dev-badge {
        margin-top: 5px;
        background-color: #e74c3c;
        color: white;
        padding: 3px 8px;
        border-radius: 10px;
        font-size: 0.7rem;
        font-weight: bold;
        display: inline-block;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Get current page URL
    current_page = st.session_state.get("current_page", "/")
    
    # User Profile Section in Sidebar
    with st.sidebar:
        # Check if user is logged in
        if "logged_in" in st.session_state and st.session_state.logged_in and "user" in st.session_state:
            user_html = f'''
            <div class="user-profile-container">
                <div class="user-name">{st.session_state.user.get("full_name", "User")}</div>
                <div class="subscription-info">
                    {st.session_state.user.get("email", "")}
                </div>
                <div class="subscription-info">
                    Plan: {st.session_state.subscription_tier.capitalize()}
                </div>
            '''
            
            # Add trial info if applicable
            if st.session_state.user.get("is_trial", False):
                trial_end = st.session_state.user.get("trial_end_date")
                if trial_end:
                    days_left = get_trial_days_remaining(trial_end)
                    if days_left > 0:
                        user_html += f'''
                        <div class="trial-info">
                            Pro Trial: {days_left} days remaining
                        </div>
                        '''
            
            # Add dev badge if in developer mode
            if is_developer_mode():
                user_html += '<div class="dev-badge">DEVELOPER MODE</div>'
                
            user_html += '</div>'
            
            st.markdown(user_html, unsafe_allow_html=True)
            
            # Account and logout buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Account", key="nav_account_btn", use_container_width=True):
                    st.switch_page("pages/account.py")
            with col2:
                if st.button("Logout", key="nav_logout_btn", use_container_width=True):
                    # Clear session state for user
                    for key in ['user', 'logged_in', 'user_id', 'subscription_tier']:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()
        else:
            # Login/signup buttons for non-logged-in users
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Login", key="nav_login_btn", use_container_width=True):
                    st.switch_page("pages/login.py")
            with col2:
                if st.button("Sign Up", key="nav_signup_btn", use_container_width=True):
                    st.switch_page("pages/signup.py")
        
        st.markdown("---")
        st.markdown("## Navigation")
        
        # Create navigation HTML
        nav_html = '<div class="sidebar-nav-container">'
        
        for item in navigation_items:
            # Skip items that require auth if not authenticated
            if item["require_auth"] and "user" not in st.session_state:
                continue
                
            # Mark the current page as active
            active_class = "active" if item["url"] == current_page else ""
            
            nav_html += f'''
            <a href="{item['url']}" target="_self" class="sidebar-nav-item {active_class}">
                <div class="sidebar-nav-icon">{item['icon']}</div>
                <div class="sidebar-nav-label">{item['name']}</div>
            </a>
            '''
        
        nav_html += '</div>'
        
        # Render the navigation
        st.markdown(nav_html, unsafe_allow_html=True)
        
def render_developer_login():
    """Render the developer login form."""
    with st.sidebar.expander("Developer Login", expanded=False):
        username = st.text_input("Username", key="dev_username")
        password = st.text_input("Password", type="password", key="dev_password")
        
        if st.button("Login as Developer", key="dev_login_btn"):
            if authenticate_developer(username, password):
                st.success("Developer mode activated")
                st.rerun()
            else:
                st.error("Invalid credentials")
                
def logout_developer():
    """Logout from developer mode."""
    if is_developer_mode() and st.sidebar.button("Exit Developer Mode", key="exit_dev_mode_btn"):
        st.session_state["user_role"] = "user"
        st.rerun()
        
def initialize_navigation():
    """Initialize the navigation by determining the current page."""
    import inspect
    import os
    from pathlib import Path
    
    # Get the calling script path
    caller_frame = inspect.currentframe()
    if caller_frame and caller_frame.f_back:
        caller_frame = caller_frame.f_back
        caller_filename = inspect.getframeinfo(caller_frame).filename
        
        # Convert to relative path for comparison
        root_dir = Path(os.getcwd())
        relative_path = Path(caller_filename).relative_to(root_dir)
        
        # Update current page in session state
        url_path = f"/{relative_path}"
        if relative_path.name == "app.py":
            url_path = "/"
            
        st.session_state["current_page"] = url_path
    else:
        # Fallback if we can't determine the current page
        st.session_state["current_page"] = "/"