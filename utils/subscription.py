import streamlit as st
import datetime
from datetime import timedelta

# Subscription plans data for UI display
SUBSCRIPTION_PLANS = {
    "free": {
        "name": "Free",
        "monthly_price": 0,
        "annual_price": 0,
        "features": [
            "1 dataset",
            "5 MB file size limit",
            "Basic visualizations",
            "Basic cleaning transformations",
            "CSV export only"
        ],
        "cta": "Current Plan",
        "highlight": False
    },
    "basic": {
        "name": "Basic",
        "monthly_price": 9.99,
        "annual_price": 99.99,  # ~16% discount
        "features": [
            "5 datasets",
            "50 MB file size limit",
            "8 visualization types",
            "Extended transformations",
            "Excel, CSV, PDF exports",
            "Basic AI insights"
        ],
        "cta": "Upgrade",
        "highlight": False
    },
    "pro": {
        "name": "Pro",
        "monthly_price": 29.99,
        "annual_price": 299.99,  # ~16% discount
        "features": [
            "20 datasets",
            "200 MB file size limit",
            "All visualization types",
            "All transformations",
            "All export formats",
            "Advanced AI insights",
            "Data version history"
        ],
        "cta": "Upgrade",
        "highlight": True
    },
    "enterprise": {
        "name": "Enterprise",
        "monthly_price": 99.99,
        "annual_price": 999.99,  # ~16% discount
        "features": [
            "Unlimited datasets",
            "500 MB file size limit",
            "All features in Pro",
            "Team collaboration",
            "Priority support",
            "Custom integrations",
            "White labeling"
        ],
        "cta": "Contact Us",
        "highlight": False
    }
}

def format_price(price):
    """Format a price with correct currency symbol."""
    if price == 0:
        return "Free"
    return f"${price:.2f}"

def get_trial_days_remaining(trial_end_date_str=None):
    """Get the number of days remaining in the trial."""
    if not trial_end_date_str:
        if "user" not in st.session_state or not st.session_state.get("logged_in", False):
            return 0
        
        # Check if user is on a trial
        if not st.session_state.user.get("is_trial", False):
            return 0
        
        # Get trial end date from session state
        trial_end_date_str = st.session_state.user.get("subscription_end_date")
        if not trial_end_date_str:
            return 0
    
    # Parse date string to datetime
    try:
        trial_end_date = datetime.datetime.fromisoformat(trial_end_date_str.replace('Z', '+00:00'))
        today = datetime.datetime.now(datetime.timezone.utc)
        
        # Calculate days difference
        days_left = (trial_end_date - today).days
        return max(0, days_left)
    except Exception as e:
        print(f"Error calculating trial days: {e}")
        return 0

def get_subscription_expires_in_days(subscription_end_date_str=None):
    """Get the number of days remaining until subscription expires."""
    if not subscription_end_date_str:
        if "user" not in st.session_state or not st.session_state.get("logged_in", False):
            return 0
        
        # Get subscription end date from session state
        subscription_end_date_str = st.session_state.user.get("subscription_end_date")
        if not subscription_end_date_str:
            return 0
    
    # Parse date string to datetime
    try:
        subscription_end_date = datetime.datetime.fromisoformat(subscription_end_date_str.replace('Z', '+00:00'))
        today = datetime.datetime.now(datetime.timezone.utc)
        
        # Calculate days difference
        days_left = (subscription_end_date - today).days
        return max(0, days_left)
    except Exception as e:
        print(f"Error calculating subscription days: {e}")
        return 0