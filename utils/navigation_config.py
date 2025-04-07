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
    
    # User-specific navigation items (require login)
    user_items = [
        {
            "name": "Upload Data",
            "url": "/pages/01_Upload_Data.py",
            "icon": "📁",
            "require_auth": True
        },
        {
            "name": "Data Preview",
            "url": "/pages/02_Data_Preview.py",
            "icon": "🔍",
            "require_auth": True
        },
        {
            "name": "EDA Dashboard",
            "url": "/pages/03_EDA_Dashboard.py",
            "icon": "📊",
            "require_auth": True
        },
        {
            "name": "Transformations",
            "url": "/pages/04_Data_Transformation.py",
            "icon": "🧹",
            "require_auth": True
        },
        {
            "name": "Insights",
            "url": "/pages/05_Insights_Dashboard.py",
            "icon": "💡",
            "require_auth": True
        },
        {
            "name": "Export",
            "url": "/pages/06_Export_Reports.py",
            "icon": "📤",
            "require_auth": True
        },
        {
            "name": "Version History",
            "url": "/pages/07_Version_History.py",
            "icon": "📜",
            "require_auth": True
        },
        {
            "name": "AI Learning",
            "url": "/pages/08_AI_Learning.py",
            "icon": "🧠",
            "require_auth": True
        },
        {
            "name": "Subscription",
            "url": "/pages/subscription.py",
            "icon": "💼",
            "require_auth": True
        },
        {
            "name": "Account",
            "url": "/pages/account.py",
            "icon": "👤",
            "require_auth": True
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
    
    # Combine appropriate items based on user role
    combined_items = base_items + user_items
    
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