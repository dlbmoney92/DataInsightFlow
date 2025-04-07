import streamlit as st
import datetime
from utils.subscription import SUBSCRIPTION_PLANS, format_price
from utils.database import update_user_subscription, get_user_by_id, start_user_trial

def app():
    st.title("Subscription Plans")
    
    # Check if user is logged in
    if "logged_in" not in st.session_state or not st.session_state.logged_in:
        st.warning("Please log in to manage your subscription.")
        st.button("Go to Login", on_click=lambda: st.switch_page("pages/login.py"))
        return
    
    # Check for query parameters using non-experimental API
    query_params = st.query_params
    
    # Handle success redirect from Stripe
    if "success" in query_params and query_params["success"] == "true":
        tier = query_params.get("tier", "")
        st.success(f"Thank you for your subscription! Your {tier.capitalize()} plan is now active.")
        
        # Clear query parameters after handling
        query_params.clear()
        
        # Update user information
        user = get_user_by_id(st.session_state.user_id)
        st.session_state.user = user
        st.session_state.subscription_tier = user["subscription_tier"]
        
        # Add a small delay to refresh the page
        st.markdown("""
        <script>
        setTimeout(function() {
            window.location.href = window.location.pathname;
        }, 3000);
        </script>
        """, unsafe_allow_html=True)
    
    # Handle cancelled checkout
    elif "cancelled" in query_params and query_params["cancelled"] == "true":
        st.warning("Your subscription process was cancelled. You can try again when you're ready.")
        
        # Clear query parameters after handling
        query_params.clear()
    
    # Get current user information
    user = st.session_state.user
    current_tier = user["subscription_tier"]
    
    # Display current subscription
    st.header("Your Current Plan")
    current_plan = SUBSCRIPTION_PLANS[current_tier]
    st.subheader(f"{current_plan['name']} Plan")
    
    # Show subscription dates if applicable
    if current_tier != "free" and not user["is_trial"]:
        start_date = user["subscription_start_date"]
        end_date = user["subscription_end_date"]
        
        if start_date and end_date:
            st.write(f"Subscription period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
            days_left = (end_date - datetime.datetime.utcnow()).days
            if days_left > 0:
                st.write(f"Days remaining: {days_left}")
            else:
                st.warning("Your subscription has expired. Please renew to continue using premium features.")
    
    # Show trial information if applicable
    if user["is_trial"]:
        trial_end = user["trial_end_date"]
        if trial_end:
            days_left = (trial_end - datetime.datetime.utcnow()).days
            if days_left > 0:
                st.info(f"You are currently on a Pro trial. {days_left} days remaining.")
            else:
                st.warning("Your Pro trial has expired. You've been moved to the Free plan.")
                
                # Update user subscription if trial expired
                if current_tier == "pro":
                    # Call the function to update user's subscription tier
                    update_user_subscription(user["id"], "free")
                    
                    # Update session state
                    user = get_user_by_id(user["id"])
                    st.session_state.user = user
                    st.session_state.subscription_tier = "free"
                    
                    # Rerun to refresh UI
                    st.rerun()
    
    # Display features
    st.subheader("Features")
    for feature in current_plan["features"]:
        st.write(f"✓ {feature}")
    
    # Display available plans
    st.header("Available Plans")
    
    # Create columns for plan display
    col1, col2, col3 = st.columns(3)
    
    with col1:
        display_plan("free", current_tier)
        
    with col2:
        display_plan("basic", current_tier)
        
    with col3:
        display_plan("pro", current_tier)
    
    # Enterprise plan
    st.markdown("---")
    st.subheader("Enterprise Plan")
    st.write("For larger organizations with custom needs.")
    
    # Display enterprise features
    for feature in SUBSCRIPTION_PLANS["enterprise"]["features"]:
        st.write(f"✓ {feature}")
    
    # Enterprise contact button
    if st.button("Contact Sales for Enterprise Plan"):
        st.info("Our sales team will contact you soon. Please check your email for further information.")

def display_plan(tier, current_tier):
    """Display a subscription plan card."""
    plan = SUBSCRIPTION_PLANS[tier]
    
    # Style based on if it's the current plan
    if tier == current_tier:
        st.markdown(f"### 🔹 {plan['name']} Plan (Current)")
    else:
        st.markdown(f"### {plan['name']} Plan")
    
    # Display price
    if isinstance(plan["monthly_price"], (int, float)):
        st.write(f"Monthly: {format_price(plan['monthly_price'])}")
        
        # Calculate yearly savings only if monthly price is not zero
        if plan['monthly_price'] > 0:
            yearly_savings = int((1 - plan['annual_price']/(plan['monthly_price']*12))*100)
            st.write(f"Yearly: {format_price(plan['annual_price'])} (Save {yearly_savings}%)")
        else:
            st.write(f"Yearly: {format_price(plan['annual_price'])}")
    else:
        st.write(plan["monthly_price"])
    
    # Display features
    for feature in plan["features"]:
        st.write(f"✓ {feature}")
    
    # Subscribe buttons (don't show for current plan)
    if tier != current_tier:
        # For free plan, show downgrade button
        if tier == "free":
            if st.button("Downgrade to Free Plan", key=f"downgrade_{tier}"):
                if downgrade_subscription(tier):
                    st.success("Successfully downgraded to Free plan.")
                    st.rerun()
        # For paid plans, show monthly and yearly options
        else:
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"Monthly", key=f"monthly_{tier}"):
                    if upgrade_subscription(tier, "monthly"):
                        st.success(f"Successfully upgraded to {plan['name']} plan (Monthly).")
                        st.rerun()
            with col2:
                if st.button(f"Yearly", key=f"yearly_{tier}"):
                    if upgrade_subscription(tier, "yearly"):
                        st.success(f"Successfully upgraded to {plan['name']} plan (Yearly).")
                        st.rerun()

def upgrade_subscription(tier, billing_cycle):
    """Upgrade user subscription to a higher tier using Stripe."""
    from utils.payment import get_stripe_checkout_session
    
    # Set success and cancel URLs - using hardcoded URLs instead of st.get_url()
    success_url = f"/pages/payment_success.py?success=true&tier={tier}"
    cancel_url = f"/pages/subscription.py?cancelled=true"
    
    # Create checkout session
    checkout_result = get_stripe_checkout_session(
        user_id=st.session_state.user_id,
        tier=tier,
        billing_cycle=billing_cycle,
        success_url=success_url,
        cancel_url=cancel_url
    )
    
    if checkout_result["success"]:
        # Redirect to Stripe checkout
        checkout_url = checkout_result["checkout_url"]
        st.markdown(f'<meta http-equiv="refresh" content="0;url={checkout_url}">', unsafe_allow_html=True)
        st.info("Redirecting to secure payment page...")
        st.markdown(f"If you are not redirected automatically, [click here]({checkout_url})")
        return True
    else:
        st.error(f"Error creating checkout session: {checkout_result.get('message', 'Unknown error')}")
        return False

def downgrade_subscription(tier):
    """Downgrade user subscription to a lower tier."""
    # Update user subscription in database
    success = update_user_subscription(
        st.session_state.user_id,
        tier,
        None,
        None
    )
    
    if success:
        # Update session state
        user = get_user_by_id(st.session_state.user_id)
        st.session_state.user = user
        st.session_state.subscription_tier = tier
        
        return True
    
    return False

if __name__ == "__main__":
    app()