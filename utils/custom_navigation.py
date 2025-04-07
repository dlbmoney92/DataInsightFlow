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
    /* Navigation Button Styles */
    div[data-testid="stButton"] > button {
        display: flex;
        align-items: center;
        padding: 12px 16px;
        border-radius: 12px;
        color: #444;
        transition: all 0.2s ease;
        background-color: rgba(255, 255, 255, 0.3);
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        font-size: 0.92rem;
        border: none;
        cursor: pointer;
        width: 100%;
        text-align: left;
        margin-bottom: 6px;
    }
    
    div[data-testid="stButton"] > button:hover {
        background-color: rgba(144, 175, 255, 0.15);
        color: #4361ee;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(67, 97, 238, 0.1);
    }
    
    div[data-testid="stButton"] > button:active {
        transform: translateY(0);
        box-shadow: 0 1px 3px rgba(67, 97, 238, 0.2);
    }
    
    /* Active navigation button style will be applied via dynamic CSS */
    div.nav-button-container {
        margin-bottom: 6px;
    }
    
    /* User Profile Section */
    .user-profile-container {
        background: linear-gradient(145deg, #f8faff 0%, #f1f5fe 100%);
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 24px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
        border: 1px solid rgba(230, 236, 250, 0.7);
        position: relative;
        overflow: hidden;
    }
    
    .user-profile-container::before {
        content: "";
        position: absolute;
        top: -10px;
        right: -10px;
        width: 80px;
        height: 80px;
        border-radius: 50%;
        background: linear-gradient(135deg, rgba(67, 97, 238, 0.1) 0%, rgba(144, 175, 255, 0.05) 100%);
        z-index: 0;
    }
    
    .user-name {
        font-weight: 600;
        font-size: 1.1rem;
        margin-bottom: 8px;
        color: #2b3674;
        position: relative;
    }
    
    .subscription-info {
        font-size: 0.9rem;
        color: #697586;
        margin-bottom: 5px;
        position: relative;
    }
    
    .trial-info {
        font-size: 0.85rem;
        margin-top: 12px;
        padding: 8px 12px;
        background: linear-gradient(135deg, #e0ecff 0%, #d1e3ff 100%);
        border-radius: 8px;
        color: #2d62ed;
        font-weight: 500;
        display: inline-block;
        box-shadow: 0 2px 8px rgba(41, 94, 255, 0.1);
    }
    
    .dev-badge {
        margin-top: 10px;
        background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%);
        color: white;
        padding: 4px 10px;
        border-radius: 30px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
        box-shadow: 0 2px 8px rgba(255, 65, 108, 0.2);
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }
    
    /* Improve default Streamlit sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #f8f9fa;
        border-right: 1px solid #eaecef;
    }
    
    /* Custom button styles for navigation */
    div.stButton > button {
        background-color: #f5f7ff;
        border: 1px solid #e1e5f2;
        border-radius: 8px;
        color: #4361ee;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    
    div.stButton > button:hover {
        background-color: #e1e7ff;
        border-color: #c9d1ff;
        transform: translateY(-1px);
        box-shadow: 0 3px 10px rgba(67, 97, 238, 0.1);
    }
    
    /* Better separator */
    hr {
        margin-top: 1.5rem;
        margin-bottom: 1.5rem;
        border: 0;
        height: 1px;
        background-image: linear-gradient(to right, rgba(0, 0, 0, 0), rgba(0, 0, 0, 0.1), rgba(0, 0, 0, 0));
    }
    
    /* Better heading */
    .sidebar h2, .sidebar-heading {
        font-size: 1.1rem;
        font-weight: 600;
        color: #2b3674;
        margin-bottom: 15px;
        margin-top: 5px;
        padding-left: 5px;
        border-left: 3px solid #4361ee;
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
        st.markdown("<h2 class='sidebar-heading'>Navigation</h2>", unsafe_allow_html=True)
        
        # Create a container for sidebar navigation
        with st.container():
            # Display each navigation item as buttons that switch pages
            for item in navigation_items:
                # Skip items that require auth if not authenticated
                if item["require_auth"] and "user" not in st.session_state:
                    continue
                    
                # Determine if this is the active page
                is_active = item["url"] == current_page
                
                # Create a unique key for each button to avoid duplicates
                button_key = f"nav_{item['name'].lower().replace(' ', '_')}"
                
                # Style the button based on whether it's active or not
                if is_active:
                    btn_style = f"""
                    <style>
                    div[data-testid="stButton"] button[kind="secondary"][aria-label="{button_key}"] {{
                        background: linear-gradient(135deg, rgba(67, 97, 238, 0.15) 0%, rgba(47, 73, 175, 0.2) 100%);
                        border-left: 3px solid #4361ee;
                        color: #4361ee;
                        font-weight: 600;
                        box-shadow: 0 4px 12px rgba(67, 97, 238, 0.1);
                    }}
                    </style>
                    """
                    st.markdown(btn_style, unsafe_allow_html=True)
                
                # Create a button with the icon and name
                if st.button(f"{item['icon']} {item['name']}", key=button_key, 
                              use_container_width=True):
                    st.switch_page(item["url"])
        
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