import streamlit as st

# Set page configuration - must be the first Streamlit command
st.set_page_config(
    page_title="Choose a Plan | Analytics Assist",
    page_icon="💰",
    layout="wide"
)

import os
from utils.subscription import SUBSCRIPTION_PLANS, format_price
from utils.database import update_user_subscription, start_user_trial, get_user_by_id
from utils.payment import get_stripe_checkout_session
from utils.auth_redirect import require_auth
from utils.global_config import apply_global_css
from utils.custom_navigation import render_navigation, initialize_navigation

# Apply global CSS
apply_global_css()

# Initialize navigation
initialize_navigation()

# Hide Streamlit's default menu and navigation
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        [data-testid="stSidebarNav"] {
            display: none !important;
        }
        
        /* Ensure page loads at the top */
        html {
            scroll-behavior: smooth;
        }
        body {
            scroll-behavior: auto;
            overflow-y: auto;
        }
        section.main {
            scroll-behavior: auto;
            overflow-y: auto;
        }
    </style>
    
    <script>
        // Ensure page starts at top when loaded
        window.onload = function() {
            window.scrollTo(0, 0);
        }
    </script>
""", unsafe_allow_html=True)

# Render custom navigation bar
render_navigation()

def app():
    # Display trial activation message for logged-in users
    if st.session_state.get("logged_in", False) and "trial_activated" in st.session_state:
        st.success("Your 7-day Pro trial has been activated!")
        del st.session_state.trial_activated
        # Update user information
        user = get_user_by_id(st.session_state.user_id)
        st.session_state.user = user
        st.session_state.subscription_tier = user["subscription_tier"] 
        # Redirect to home page using JavaScript instead of st.rerun()
        st.markdown("""
        <script>
        setTimeout(function() {
            window.location.href = "/";
        }, 2000);
        </script>
        """, unsafe_allow_html=True)
    
    # Create a normal container without modal styling
    with st.container():
        st.title("Select Your Plan")
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
    
    # Add custom CSS to style the subscription containers
    st.markdown("""
    <style>
        /* Plan container styling */
        div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"] > div[data-testid="element-container"] div.element-container {
            margin-bottom: 0.5rem;
        }
        
        /* More compact feature spacing */
        p {
            margin-bottom: 0.3rem;
            line-height: 1.3;
        }
        
        /* Ensure content fits without scrolling */
        div.stButton {
            margin-top: 0.5rem;
            margin-bottom: 0.5rem;
        }
    </style>
    """, unsafe_allow_html=True)
    
    with cols[0]:
        free_selected = selected_tier == "free" or selected_tier is None
        with st.container(border=True, height=660):
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
        
        with st.container(border=True, height=660):
            st.markdown("### Basic Plan")
            st.markdown(f"<h2 style='text-align: center;'>{format_price(SUBSCRIPTION_PLANS['basic']['monthly_price'])}</h2>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center;'>per month</p>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align: center;'>{format_price(SUBSCRIPTION_PLANS['basic']['annual_price'])} billed annually</p>", unsafe_allow_html=True)
            
            # Features
            st.markdown("#### Features:")
            feature_list = ""
            for feature in SUBSCRIPTION_PLANS["basic"]["features"]:
                feature_list += f"<p>✓ {feature}</p>"
            st.markdown(feature_list, unsafe_allow_html=True)
            
            # Add spacer to ensure buttons are at the bottom
            st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
            
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
        
        with st.container(border=True, height=660):
            st.markdown("### Pro Plan")
            st.markdown(f"<h2 style='text-align: center;'>{format_price(SUBSCRIPTION_PLANS['pro']['monthly_price'])}</h2>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center;'>per month</p>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align: center;'>{format_price(SUBSCRIPTION_PLANS['pro']['annual_price'])} billed annually</p>", unsafe_allow_html=True)
            
            # Features
            st.markdown("#### Features:")
            feature_list = ""
            for feature in SUBSCRIPTION_PLANS["pro"]["features"]:
                feature_list += f"<p>✓ {feature}</p>"
            st.markdown(feature_list, unsafe_allow_html=True)
            
            # Add spacer to ensure buttons are at the bottom
            st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
            
            # Trial option for logged-in users
            if st.session_state.get("logged_in", False) and st.session_state.get("subscription_tier", "") == "free" and not st.session_state.get("user", {}).get("is_trial", False):
                if st.button("Start 7-Day Free Trial", key="pro_trial", use_container_width=True):
                    # Start user trial
                    start_user_trial(st.session_state.user_id)
                    st.session_state.trial_activated = True
                    st.success("Your 7-day Pro trial has been activated!")
                    # Use JavaScript to redirect after a short delay
                    st.markdown("""
                    <script>
                    setTimeout(function() {
                        window.location.href = window.location.pathname;
                    }, 1500);
                    </script>
                    """, unsafe_allow_html=True)
            
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
            if st.button("Contact Sales", use_container_width=True):
                st.switch_page("pages/contact_us.py")
    
    # Option to skip subscription selection
    st.markdown("---")
    st.markdown("<div style='text-align: center;'>Not ready to decide?</div>", unsafe_allow_html=True)
    if st.button("Continue with Free Plan", use_container_width=False, key="skip"):
        # Check if user is logged in
        if not st.session_state.get("logged_in", False):
            st.session_state.selected_plan = {"tier": "free", "billing_cycle": "monthly"}
            st.switch_page("pages/signup.py")
        else:
            st.switch_page("app.py")
        
    # Simple footer
    st.markdown("---")
    if st.button("Return to Home", key="return_home"):
        st.switch_page("app.py")

def redirect_to_payment(tier, billing_cycle):
    """Redirect to Stripe payment for the selected plan."""
    # Check if user is logged in
    if not st.session_state.get("logged_in", False):
        # Save the selected plan in session state
        st.session_state.selected_plan = {"tier": tier, "billing_cycle": billing_cycle}
        
        # Redirect to signup page
        st.info("Please create an account or login to continue with your subscription")
        st.switch_page("pages/signup.py")
        return
    
    # User is logged in, proceed with payment
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