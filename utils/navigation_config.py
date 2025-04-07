import streamlit as st

def is_developer_mode():
    """Check if the app is in developer mode."""
    return st.session_state.get("user_role", "user") == "developer"

def set_developer_mode(enabled=True):
    """Set the developer mode status."""
    st.session_state["user_role"] = "developer" if enabled else "user"

def get_navigation_items():
    """Get the appropriate navigation items based on user role."""
    # Base navigation items for all users
    base_items = [
        {
            "name": "Home",
            "url": "/",
            "icon": "🏠",
            "require_auth": False
        }
    ]
    
    # Core app navigation items - visible to everyone but require login to access
    core_app_items = [
        {
            "name": "Upload Data",
            "url": "/pages/01_Upload_Data.py",
            "icon": "📁",
            "require_auth": False  # Show in nav but auth check is done in the page
        },
        {
            "name": "Data Preview",
            "url": "/pages/02_Data_Preview.py",
            "icon": "🔍",
            "require_auth": False  # Show in nav but auth check is done in the page
        },
        {
            "name": "EDA Dashboard",
            "url": "/pages/03_EDA_Dashboard.py",
            "icon": "📊",
            "require_auth": False  # Show in nav but auth check is done in the page
        },
        {
            "name": "Transformations",
            "url": "/pages/04_Data_Transformation.py",
            "icon": "🧹",
            "require_auth": False  # Show in nav but auth check is done in the page
        },
        {
            "name": "Insights",
            "url": "/pages/05_Insights_Dashboard.py",
            "icon": "💡",
            "require_auth": False  # Show in nav but auth check is done in the page
        },
        {
            "name": "Export",
            "url": "/pages/06_Export_Reports.py",
            "icon": "📤",
            "require_auth": False  # Show in nav but auth check is done in the page
        },
        {
            "name": "Version History",
            "url": "/pages/07_Version_History.py",
            "icon": "📜",
            "require_auth": False  # Show in nav but auth check is done in the page
        },
        {
            "name": "AI Learning",
            "url": "/pages/08_AI_Learning.py",
            "icon": "🧠",
            "require_auth": False  # Show in nav but auth check is done in the page
        }
    ]
    
    # User account pages - only shown to logged-in users
    user_account_items = [
        {
            "name": "Subscription",
            "url": "/pages/subscription.py",
            "icon": "💼",
            "require_auth": True  # Only show if logged in
        },
        {
            "name": "Account",
            "url": "/pages/account.py",
            "icon": "👤",
            "require_auth": True  # Only show if logged in
        }
    ]
    
    # Developer-specific navigation items
    developer_items = [
        {
            "name": "Stripe Webhook",
            "url": "/pages/stripe_webhook.py",
            "icon": "🔄",
            "require_auth": True
        },
        {
            "name": "Payment Success",
            "url": "/pages/payment_success.py",
            "icon": "💰",
            "require_auth": True
        },
        {
            "name": "OAuth Callback",
            "url": "/pages/oauth_callback.py",
            "icon": "🔐",
            "require_auth": True
        }
    ]
    
    # Combine appropriate items based on user role and login status
    combined_items = base_items + core_app_items
    
    # Add user account items if logged in
    if "logged_in" in st.session_state and st.session_state.logged_in:
        combined_items.extend(user_account_items)
    
    # Add developer items if in developer mode
    if is_developer_mode():
        combined_items.extend(developer_items)
    
    return combined_items

def authenticate_developer(username, password):
    """Authenticate a developer login."""
    # In a real application, this would check against secure credentials
    # For demo purposes, hard-coded credentials (this would be a bad practice in production)
    valid_credentials = {
        "admin": "devpass123"
    }
    
    if username in valid_credentials and password == valid_credentials[username]:
        set_developer_mode(True)
        return True
    return False