import streamlit as st
import hashlib
from utils.database import get_user_by_id, execute_with_retry
from utils.subscription import SUBSCRIPTION_PLANS, format_price, get_trial_days_remaining, get_subscription_expires_in_days
from sqlalchemy import text

def update_password(user_id, current_password, new_password):
    """Update user password."""
    def _update_password_operation():
        from utils.database import Session, users
        
        # Get current user data
        user = get_user_by_id(user_id)
        if not user:
            return {'success': False, 'message': 'User not found'}
        
        # Check current password
        current_password_hash = hashlib.sha256(current_password.encode()).hexdigest()
        if user['password_hash'] != current_password_hash:
            return {'success': False, 'message': 'Current password is incorrect'}
        
        # Update password
        new_password_hash = hashlib.sha256(new_password.encode()).hexdigest()
        
        session = Session()
        try:
            session.execute(
                users.update().where(users.c.id == user_id).values(
                    password_hash=new_password_hash
                )
            )
            session.commit()
            return {'success': True}
        except Exception as e:
            session.rollback()
            return {'success': False, 'message': str(e)}
        finally:
            session.close()
    
    return execute_with_retry(_update_password_operation)

def update_profile(user_id, full_name, email):
    """Update user profile information."""
    def _update_profile_operation():
        from utils.database import Session, users
        
        # Check if email exists and belongs to a different user
        session = Session()
        try:
            existing = session.query(users).filter(users.c.email == email, users.c.id != user_id).first()
            if existing:
                return {'success': False, 'message': 'Email already in use by another account'}
            
            # Update profile
            session.execute(
                users.update().where(users.c.id == user_id).values(
                    full_name=full_name,
                    email=email
                )
            )
            session.commit()
            return {'success': True}
        except Exception as e:
            session.rollback()
            return {'success': False, 'message': str(e)}
        finally:
            session.close()
    
    return execute_with_retry(_update_profile_operation)

def app():
    st.title("Account Settings")
    
    # Check if user is logged in
    if "logged_in" not in st.session_state or not st.session_state.logged_in:
        st.warning("Please log in to access your account settings.")
        st.button("Go to Login", on_click=lambda: st.switch_page("pages/login.py"))
        return
    
    # Get user data
    user = get_user_by_id(st.session_state.user_id)
    if not user:
        st.error("Error loading user data.")
        return
    
    # Update session state with latest user data
    st.session_state.user = user
    
    # Tabs for different sections
    tab1, tab2, tab3 = st.tabs(["Profile", "Password", "Subscription"])
    
    # Profile tab
    with tab1:
        st.header("Personal Information")
        
        with st.form("profile_form"):
            full_name = st.text_input("Full Name", value=user['full_name'])
            email = st.text_input("Email", value=user['email'])
            
            submit = st.form_submit_button("Save Changes")
            
            if submit:
                if not full_name or not email:
                    st.error("Please fill in all fields.")
                else:
                    result = update_profile(user['id'], full_name, email)
                    if result['success']:
                        st.success("Profile updated successfully!")
                        # Update session state
                        user = get_user_by_id(st.session_state.user_id)
                        st.session_state.user = user
                    else:
                        st.error(f"Error updating profile: {result['message']}")
    
    # Password tab
    with tab2:
        st.header("Change Password")
        
        with st.form("password_form"):
            current_password = st.text_input("Current Password", type="password")
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm New Password", type="password")
            
            submit = st.form_submit_button("Change Password")
            
            if submit:
                if not current_password or not new_password or not confirm_password:
                    st.error("Please fill in all password fields.")
                elif new_password != confirm_password:
                    st.error("New passwords do not match.")
                elif len(new_password) < 8:
                    st.error("New password must be at least 8 characters long.")
                else:
                    result = update_password(user['id'], current_password, new_password)
                    if result['success']:
                        st.success("Password changed successfully!")
                    else:
                        st.error(f"Error changing password: {result['message']}")
    
    # Subscription tab
    with tab3:
        st.header("Subscription Information")
        
        tier_info = SUBSCRIPTION_PLANS[user['subscription_tier']]
        
        st.subheader(f"Current Plan: {tier_info['name']}")
        
        # Trial information
        if user['is_trial']:
            trial_days = get_trial_days_remaining(user['trial_end_date'])
            if trial_days > 0:
                st.info(f"You are currently on a Pro trial with {trial_days} days remaining.")
                st.write("After your trial ends, you'll be moved to the Free plan unless you upgrade.")
            else:
                st.warning("Your Pro trial has expired. You've been moved to the Free plan.")
        
        # Paid subscription information
        if user['subscription_tier'] != 'free' and not user['is_trial']:
            expires_in = get_subscription_expires_in_days(user['subscription_end_date'])
            if expires_in > 0:
                st.write(f"Your subscription will renew in {expires_in} days.")
            else:
                st.warning("Your subscription has expired. Please renew to continue using premium features.")
        
        # Plan features
        st.subheader("Plan Features")
        for feature in tier_info['features']:
            st.write(f"✓ {feature}")
        
        # Upgrade button
        if user['subscription_tier'] != 'pro' and user['subscription_tier'] != 'enterprise':
            st.button("Upgrade Plan", on_click=lambda: st.switch_page("pages/subscription.py"))
    
    # Account deletion section
    st.markdown("---")
    with st.expander("Delete Account"):
        st.warning("Account deletion is permanent and cannot be undone.")
        st.write("All your datasets, transformations, and insights will be permanently deleted.")
        
        confirm_text = st.text_input("Type 'DELETE' to confirm account deletion", key="delete_confirm")
        if st.button("Delete My Account", type="primary", use_container_width=True):
            if confirm_text == "DELETE":
                # Implement account deletion logic
                st.error("Account deletion functionality will be implemented soon.")
            else:
                st.error("Please type 'DELETE' to confirm account deletion.")

if __name__ == "__main__":
    app()