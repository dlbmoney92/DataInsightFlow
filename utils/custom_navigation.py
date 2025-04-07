import streamlit as st
from utils.navigation_config import get_navigation_items, is_developer_mode, authenticate_developer

def render_navigation():
    """Render the navigation bar."""
    # Check if first run and initialize user_role
    if "user_role" not in st.session_state:
        st.session_state["user_role"] = "user"
    
    # Get the current navigation items
    navigation_items = get_navigation_items()
    
    # Create styled navigation bar CSS
    st.markdown("""
    <style>
    .nav-container {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 8px;
        padding: 10px 0;
        background-color: #f8f9fa;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    
    .nav-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 8px 12px;
        border-radius: 8px;
        text-decoration: none;
        color: #495057;
        transition: all 0.3s ease;
        background-color: rgba(255, 255, 255, 0.7);
        min-width: 80px;
        aspect-ratio: 1 / 1;
        justify-content: center;
    }
    
    .nav-item:hover {
        background-color: rgba(52, 152, 219, 0.1);
        color: #3498db;
        transform: translateY(-2px);
    }
    
    .nav-item.active {
        background-color: rgba(52, 152, 219, 0.2);
        color: #2980b9;
        font-weight: bold;
    }
    
    .nav-icon {
        font-size: 1.5rem;
        margin-bottom: 5px;
    }
    
    .nav-label {
        font-size: 0.8rem;
        text-align: center;
    }
    
    .collapsed .nav-label {
        display: none;
    }
    
    .collapsed .nav-item {
        min-width: auto;
        aspect-ratio: 1 / 1;
    }
    
    @media (max-width: 768px) {
        .nav-container {
            overflow-x: auto;
            white-space: nowrap;
            justify-content: flex-start;
        }
    }
    
    .dev-badge {
        position: absolute;
        top: 10px;
        right: 10px;
        background-color: #e74c3c;
        color: white;
        padding: 3px 8px;
        border-radius: 10px;
        font-size: 0.7rem;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Get current page URL
    current_page = st.session_state.get("current_page", "/")
    
    # Create navigation HTML
    nav_html = '<div class="nav-container">'
    
    for item in navigation_items:
        # Skip items that require auth if not authenticated
        if item["require_auth"] and "user" not in st.session_state:
            continue
            
        # Mark the current page as active
        active_class = "active" if item["url"] == current_page else ""
        
        nav_html += f'''
        <a href="{item['url']}" target="_self" class="nav-item {active_class}">
            <div class="nav-icon">{item['icon']}</div>
            <div class="nav-label">{item['name']}</div>
        </a>
        '''
    
    nav_html += '</div>'
    
    # Render the navigation
    st.markdown(nav_html, unsafe_allow_html=True)
    
    # Show developer badge if in developer mode
    if is_developer_mode():
        st.markdown('<div class="dev-badge">DEVELOPER MODE</div>', unsafe_allow_html=True)
        
def render_developer_login():
    """Render the developer login form."""
    with st.sidebar.expander("Developer Login", expanded=False):
        username = st.text_input("Username", key="dev_username")
        password = st.text_input("Password", type="password", key="dev_password")
        
        if st.button("Login as Developer"):
            if authenticate_developer(username, password):
                st.success("Developer mode activated")
                st.rerun()
            else:
                st.error("Invalid credentials")
                
def logout_developer():
    """Logout from developer mode."""
    if is_developer_mode() and st.sidebar.button("Exit Developer Mode"):
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