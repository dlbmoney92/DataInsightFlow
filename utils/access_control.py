import streamlit as st
from utils.subscription import SUBSCRIPTION_TIERS
from utils.database import execute_with_retry
from sqlalchemy import text

def check_access(feature_type, feature_name=None):
    """Check if current user can access a feature based on subscription tier."""
    # Default to free if not logged in
    if "logged_in" not in st.session_state or not st.session_state.logged_in:
        tier = "free"
    else:
        tier = st.session_state.subscription_tier
        
    tier_limits = SUBSCRIPTION_TIERS[tier]["limits"]
    
    if feature_type == "ai_features" and not tier_limits["ai_features_enabled"]:
        st.warning("AI-powered features are only available on paid plans. Please upgrade to access this feature.")
        st.button("View Plans", on_click=lambda: st.switch_page("pages/subscription.py"))
        return False
        
    elif feature_type == "ai" and feature_name:
        # Check if the specific AI feature is available in the current tier
        if not tier_limits.get("ai_features_enabled", False):
            st.warning(f"AI features are only available on paid plans. Please upgrade to access this feature.")
            st.button("View Plans", on_click=lambda: st.switch_page("pages/subscription.py"))
            return False
        
        # Check for AI learning features
        if feature_name in ["learning_preferences", "learning_stats"]:
            if not tier_limits.get("ai_learning", False):
                st.warning(f"AI learning features are available on Pro and Enterprise plans. Please upgrade to access this feature.")
                st.button("View Plans", on_click=lambda: st.switch_page("pages/subscription.py"))
                return False
        
        return True
        
    elif feature_type == "export_format":
        if feature_name not in tier_limits["export_formats"]:
            st.warning(f"Export to {feature_name} is not available on your current plan. Please upgrade to access this feature.")
            st.button("View Plans", on_click=lambda: st.switch_page("pages/subscription.py"))
            return False
            
    elif feature_type == "dataset_count":
        if "user_id" in st.session_state:
            current_count = get_dataset_count(st.session_state.user_id)
            if current_count >= tier_limits["max_datasets"] and tier_limits["max_datasets"] != float("inf"):
                st.warning(f"You've reached the maximum number of datasets ({tier_limits['max_datasets']}) for your plan. Please upgrade to add more.")
                st.button("View Plans", on_click=lambda: st.switch_page("pages/subscription.py"))
                return False
        
    elif feature_type == "row_count":
        if feature_name and feature_name > tier_limits["max_rows_per_dataset"]:
            st.warning(f"Your plan allows a maximum of {tier_limits['max_rows_per_dataset']} rows per dataset. This dataset has {feature_name} rows. Please upgrade to process larger datasets.")
            st.button("View Plans", on_click=lambda: st.switch_page("pages/subscription.py"))
            return False
    
    elif feature_type == "ai_learning":
        if not tier_limits.get("ai_learning", False):
            st.warning("AI learning features are available on Pro and Enterprise plans. Please upgrade to access this feature.")
            st.button("View Plans", on_click=lambda: st.switch_page("pages/subscription.py"))
            return False
        
        # Check for advanced learning features
        if feature_name == "advanced" and not tier_limits.get("advanced_learning", False):
            st.warning("Advanced AI learning features are available on Enterprise plans. Please contact sales to upgrade.")
            return False
            
    return True

def get_dataset_count(user_id):
    """Get the number of datasets for a user."""
    def _count_datasets_operation():
        from sqlalchemy import func
        from utils.database import Session, datasets
        
        session = Session()
        try:
            count = session.query(func.count(datasets.c.id)).filter(datasets.c.user_id == user_id).scalar()
            return count or 0
        except Exception as e:
            st.error(f"Error counting datasets: {str(e)}")
            return 0
        finally:
            session.close()
    
    return execute_with_retry(_count_datasets_operation)

def is_trial_expired():
    """Check if user's trial has expired."""
    if "logged_in" not in st.session_state or not st.session_state.logged_in:
        return False
        
    user = st.session_state.user
    if not user.get("is_trial"):
        return False
        
    import datetime
    now = datetime.datetime.utcnow()
    trial_end = user.get("trial_end_date")
    
    if not trial_end:
        return False
        
    return now > trial_end

def check_and_handle_trial_expiration():
    """Check if trial has expired and handle appropriately."""
    if "logged_in" in st.session_state and st.session_state.logged_in and is_trial_expired():
        from utils.database import update_user_subscription
        
        # Trial expired, revert to free tier
        update_user_subscription(st.session_state.user_id, "free")
        
        # Update session state
        st.session_state.subscription_tier = "free"
        st.session_state.user["subscription_tier"] = "free"
        st.session_state.user["is_trial"] = False
        
        # Show message
        st.warning("Your Pro trial has expired. You've been switched to the Free plan.")
        st.button("Upgrade Now", on_click=lambda: st.switch_page("pages/subscription.py"))