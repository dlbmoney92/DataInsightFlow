import streamlit as st
import datetime
from datetime import timedelta
import sqlalchemy as sa
from utils.subscription import get_trial_days_remaining
from utils.database import execute_with_retry

# Define feature access by tier
FEATURE_ACCESS = {
    # Data Upload & Management
    "dataset_count": {
        "free": 1,      # Free: 1 dataset
        "basic": 5,     # Basic: 5 datasets
        "pro": 20,      # Pro: 20 datasets 
        "enterprise": -1  # Unlimited
    },
    "file_size_limit": {
        "free": 5,    # Free: 5MB limit
        "basic": 50,  # Basic: 50MB limit
        "pro": 200,   # Pro: 200MB limit
        "enterprise": 500  # MB
    },
    
    # Data Transformation
    "transformation": {
        "free": ["basic_cleaning", "data_type_conversion", "rename_columns"],
        "basic": ["basic_cleaning", "data_type_conversion", "rename_columns", 
                 "fill_missing", "outlier_removal", "basic_filtering"],
        "pro": ["basic_cleaning", "data_type_conversion", "rename_columns", 
               "fill_missing", "outlier_removal", "basic_filtering",
               "normalization", "binning", "encoding", "aggregation", "pivot", 
               "text_processing", "date_processing"],
        "enterprise": "all"
    },
    
    # Visualization
    "visualization": {
        "free": ["bar_chart", "line_chart", "scatter_plot", "basic_table"],  # Basic visualizations
        "basic": ["bar_chart", "line_chart", "scatter_plot", "basic_table",
                 "histogram", "box_plot", "heatmap", "pie_chart"],  # 8 visualization types
        "pro": "all",  # All visualization types
        "enterprise": "all"
    },
    
    # Export
    "export_format": {
        "free": ["csv"],  # CSV export only
        "basic": ["csv", "excel", "pdf"],  # Excel, CSV, PDF exports
        "pro": ["csv", "excel", "pdf", "json", "sql", "api"],  # All export formats
        "enterprise": "all"
    },
    
    # Analysis
    "analysis": {
        "free": ["basic_stats", "correlation"],
        "basic": ["basic_stats", "correlation", "distribution", "outlier_detection"],
        "pro": ["basic_stats", "correlation", "distribution", "outlier_detection",
               "trend_analysis", "forecasting", "clustering", "basic_ml"],
        "enterprise": "all"
    },
    
    # AI Features
    "ai_features": {
        "free": [],
        "basic": ["basic_insights", "data_quality_suggestions"],
        "pro": ["basic_insights", "data_quality_suggestions", 
               "advanced_insights", "natural_language_query",
               "transformation_suggestions", "visualization_suggestions"],
        "enterprise": "all"
    },
    
    # Version History
    "version_history": {
        "free": False,
        "basic": True,
        "pro": True,
        "enterprise": True
    },
    
    # Collaboration
    "collaboration": {
        "free": False,
        "basic": False,
        "pro": False,
        "enterprise": True
    }
}

def check_access(feature_type, feature_name=None):
    """Check if current user can access a feature based on subscription tier."""
    # If not logged in, default to free tier
    if "subscription_tier" not in st.session_state:
        st.session_state.subscription_tier = "free"
    
    # Get the user's subscription tier
    tier = st.session_state.subscription_tier
    
    # Check if user is on a trial (grants pro tier access)
    is_trial = False
    if "user" in st.session_state and st.session_state.user.get("is_trial", False):
        days_left = get_trial_days_remaining()
        if days_left > 0:
            is_trial = True
            tier = "pro"  # Set tier to Pro for trial users
    
    # Check feature access based on feature type
    if feature_type not in FEATURE_ACCESS:
        return False
    
    access_rules = FEATURE_ACCESS[feature_type]
    
    # Numeric limits (like dataset count)
    if isinstance(access_rules[tier], (int, float)):
        # -1 means unlimited
        if access_rules[tier] == -1:
            return True
        
        # For dataset count, we need to check against the database
        if feature_type == "dataset_count":
            current_count = get_dataset_count(st.session_state.get("user_id", None))
            return current_count < access_rules[tier]
        
        # For file size, feature_name would contain the file size in MB
        if feature_type == "file_size_limit" and feature_name is not None:
            return float(feature_name) <= access_rules[tier]
        
        return True
    
    # Boolean flags
    elif isinstance(access_rules[tier], bool):
        return access_rules[tier]
    
    # List of allowed features
    elif isinstance(access_rules[tier], list):
        if feature_name is None:
            return len(access_rules[tier]) > 0
        return feature_name in access_rules[tier]
    
    # "all" means full access
    elif access_rules[tier] == "all":
        return True
    
    return False

def get_dataset_count(user_id):
    """Get the number of datasets for a user."""
    def _count_datasets_operation():
        from sqlalchemy import text
        
        # If no user is logged in, return a high number to restrict access
        if user_id is None:
            return 999
        
        # Build query
        query = text("SELECT COUNT(*) FROM datasets WHERE user_id = :user_id")
        
        # Execute query using the DATABASE_URL environment variable
        import os
        database_url = os.environ.get("DATABASE_URL")
        
        if database_url:
            with sa.create_engine(database_url).connect() as conn:
                result = conn.execute(query, {"user_id": user_id}).fetchone()
                return result[0] if result else 0
        else:
            st.error("Database connection information not found")
            return 0
    
    # Execute with retry
    return execute_with_retry(_count_datasets_operation)

def is_trial_expired():
    """Check if user's trial has expired."""
    if "user" not in st.session_state or not st.session_state.get("logged_in", False):
        return False
    
    # Check if the user is on a trial
    if not st.session_state.user.get("is_trial", False):
        return False
    
    days_left = get_trial_days_remaining()
    return days_left <= 0

def check_and_handle_trial_expiration():
    """Check if trial has expired and handle appropriately."""
    if is_trial_expired():
        # The trial has expired, downgrade to free tier
        from utils.database import update_user_subscription
        
        user_id = st.session_state.get("user_id")
        if user_id:
            # Downgrade to free tier in DB
            update_user_subscription(user_id, "free")
            
            # Update session state
            st.session_state.subscription_tier = "free"
            
            # Update user record in session
            if "user" in st.session_state:
                st.session_state.user["is_trial"] = False
                st.session_state.user["subscription_tier"] = "free"
                
            # Show trial expiration message
            st.warning("Your Pro trial has expired. You've been downgraded to the Free tier. Upgrade to continue using Pro features.")
            
            return True
    
    return False