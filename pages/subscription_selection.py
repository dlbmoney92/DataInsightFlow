import os
import streamlit as st
from utils.subscription import SUBSCRIPTION_PLANS, format_price
from utils.database import update_user_subscription, start_user_trial, get_user_by_id
from utils.payment import get_stripe_checkout_session
from utils.auth_redirect import require_auth
from utils.global_config import apply_global_css

def app():
    # Apply global CSS
    apply_global_css()
    
    # Check if user is logged in
    if not require_auth():
        return
        
    # Check if trial was activated
    if "trial_activated" in st.session_state:
        st.success("Your 7-day Pro trial has been activated!")
        del st.session_state.trial_activated
        # Update user information
        user = get_user_by_id(st.session_state.user_id)
        st.session_state.user = user
        st.session_state.subscription_tier = user["subscription_tier"] 
        # Redirect to home page
        st.rerun()
    
    # Create a modal-like container
    with st.container():
        st.markdown('<div class="modal-container">', unsafe_allow_html=True)
        
        # Modal header
        st.markdown('''
        <div class="modal-header">
            <h2 class="modal-title">Select Your Plan</h2>
            <a href="/" class="modal-close">×</a>
        </div>
        ''', unsafe_allow_html=True)
        
        st.markdown('<div class="modal-body">', unsafe_allow_html=True)
        st.subheader("Choose the Analytics Assist subscription that fits your needs")
    
    # Get access level from query parameters if available
    query_params = st.query_params
    selected_tier = query_params.get("tier", None)
    
    # Clear query params after reading
    if "tier" in query_params:
        new_params = {}
        for param in query_params:
            if param != "tier":
                new_params[param] = query_params[param]
        st.query_params.update(new_params)
    
    # Create columns for the subscription tiers
    cols = st.columns(3)
    
    with cols[0]:
        free_selected = selected_tier == "free" or selected_tier is None
        with st.container(border=True, height=600):
            st.markdown("### Free Plan")
            st.markdown(f"<h2 style='text-align: center;'>{format_price(0)}</h2>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center;'>Always free</p>", unsafe_allow_html=True)
            
            # Features
            st.markdown("#### Features:")
            for feature in SUBSCRIPTION_PLANS["free"]["features"]:
                st.markdown(f"✓ {feature}")
            
            # Call to action
            if free_selected:
                st.success("This is your current plan")
            else:
                if st.button("Select Free Plan", use_container_width=True):
                    # Update user subscription to free
                    update_user_subscription(st.session_state.user_id, "free")
                    
                    # Update session state
                    st.session_state.subscription_tier = "free"
                    st.success("You've been subscribed to the Free plan!")
                    
                    # Redirect to home
                    st.switch_page("app.py")
    
    with cols[1]:
        basic_selected = selected_tier == "basic"
        highlight = " highlight-plan" if basic_selected else ""
        
        with st.container(border=True, height=600):
            st.markdown("### Basic Plan")
            st.markdown(f"<h2 style='text-align: center;'>{format_price(SUBSCRIPTION_PLANS['basic']['monthly_price'])}</h2>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center;'>per month</p>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align: center;'>{format_price(SUBSCRIPTION_PLANS['basic']['annual_price'])} billed annually</p>", unsafe_allow_html=True)
            
            # Features
            st.markdown("#### Features:")
            for feature in SUBSCRIPTION_PLANS["basic"]["features"]:
                st.markdown(f"✓ {feature}")
            
            # Call to action
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Monthly", key="basic_monthly", use_container_width=True):
                    redirect_to_payment("basic", "monthly")
            with col2:
                if st.button("Annual", key="basic_annual", use_container_width=True):
                    redirect_to_payment("basic", "yearly")
    
    with cols[2]:
        pro_selected = selected_tier == "pro"
        highlight = " highlight-plan" if pro_selected else ""
        
        with st.container(border=True, height=600):
            st.markdown("### Pro Plan")
            st.markdown(f"<h2 style='text-align: center;'>{format_price(SUBSCRIPTION_PLANS['pro']['monthly_price'])}</h2>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center;'>per month</p>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align: center;'>{format_price(SUBSCRIPTION_PLANS['pro']['annual_price'])} billed annually</p>", unsafe_allow_html=True)
            
            # Features
            st.markdown("#### Features:")
            for feature in SUBSCRIPTION_PLANS["pro"]["features"]:
                st.markdown(f"✓ {feature}")
            
            # Trial option
            if st.session_state.subscription_tier == "free" and not st.session_state.user.get("is_trial", False):
                if st.button("Start 7-Day Free Trial", key="pro_trial", use_container_width=True):
                    # Start user trial
                    start_user_trial(st.session_state.user_id)
                    st.session_state.trial_activated = True
                    st.success("Your 7-day Pro trial has been activated!")
                    # Don't call st.rerun() directly in a callback
            
            # Payment buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Monthly", key="pro_monthly", use_container_width=True):
                    redirect_to_payment("pro", "monthly")
            with col2:
                if st.button("Annual", key="pro_annual", use_container_width=True):
                    redirect_to_payment("pro", "yearly")
    
    # Enterprise option
    st.markdown("---")
    with st.container(border=True):
        st.subheader("Enterprise Plan")
        st.write("For larger organizations with custom needs. Contact our sales team for a personalized quote.")
        
        # Display enterprise features
        col1, col2 = st.columns([3, 1])
        with col1:
            feature_cols = st.columns(2)
            features = SUBSCRIPTION_PLANS["enterprise"]["features"]
            half = len(features) // 2
            
            for i, feature in enumerate(features[:half]):
                feature_cols[0].markdown(f"✓ {feature}")
            
            for i, feature in enumerate(features[half:]):
                feature_cols[1].markdown(f"✓ {feature}")
        
        with col2:
            st.button("Contact Sales", use_container_width=True)
    
    # Option to skip subscription selection
    st.markdown("---")
    st.markdown("<div style='text-align: center;'>Not ready to decide?</div>", unsafe_allow_html=True)
    if st.button("Continue with Free Plan", use_container_width=False, key="skip"):
        st.switch_page("app.py")
        
    # Close the modal body and container divs
    st.markdown('</div>', unsafe_allow_html=True)  # Close modal-body
    
    # Modal footer
    st.markdown('''
    <div class="modal-footer">
        <a href="/" class="btn">Cancel</a>
    </div>
    ''', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close modal-container

def redirect_to_payment(tier, billing_cycle):
    """Redirect to Stripe payment for the selected plan."""
    # Use absolute URLs for Stripe (relative URLs don't work with Stripe)
    # Get the base URL from environment or use a default for development
    base_url = os.environ.get("REPL_SLUG", "localhost:5000")
    protocol = "https" if "replit" in base_url else "http"
    success_url = f"{protocol}://{base_url}/pages/payment_success.py?success=true&tier={tier}"
    cancel_url = f"{protocol}://{base_url}/pages/subscription_selection.py?cancelled=true"
    
    print(f"Success URL: {success_url}")
    print(f"Cancel URL: {cancel_url}")
    
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
    else:
        st.error(f"Error creating checkout session: {checkout_result.get('message', 'Unknown error')}")

if __name__ == "__main__":
    app()