import stripe
import os
import streamlit as st
from datetime import datetime, timedelta
from utils.database import update_user_subscription, get_user_by_id
from utils.subscription import SUBSCRIPTION_TIERS, format_price

# Set Stripe API keys
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY")

# Define price IDs (in a real implementation, you would create these in your Stripe dashboard)
# For testing purposes, we'll define placeholder IDs for different subscription tiers and billing cycles
PRICE_IDS = {
    "basic": {
        "monthly": "price_basic_monthly",  # Replace with actual Stripe price ID
        "yearly": "price_basic_yearly"     # Replace with actual Stripe price ID
    },
    "pro": {
        "monthly": "price_pro_monthly",    # Replace with actual Stripe price ID
        "yearly": "price_pro_yearly"       # Replace with actual Stripe price ID
    }
}

def get_stripe_checkout_session(user_id, tier, billing_cycle, success_url, cancel_url):
    """Create a Stripe checkout session for subscription."""
    user = get_user_by_id(user_id)
    if not user:
        return {"success": False, "message": "User not found"}
    
    try:
        # Get the pricing details for the selected plan
        plan_details = SUBSCRIPTION_TIERS[tier]
        price_amount = plan_details["price_monthly"] if billing_cycle == "monthly" else plan_details["price_yearly"]
        
        # Create a Stripe Product on the fly if needed
        product = stripe.Product.create(
            name=f"Analytics Assist {plan_details['name']} Plan - {billing_cycle.capitalize()}",
            description=f"Analytics Assist {plan_details['name']} Plan subscription ({billing_cycle})",
        )
        
        # Create a Price for the product
        price = stripe.Price.create(
            product=product.id,
            unit_amount=int(price_amount * 100),  # Convert to cents
            currency="usd",
            recurring={
                "interval": "month" if billing_cycle == "monthly" else "year",
                "interval_count": 1,
            },
        )
        
        # Create checkout session
        checkout_session = stripe.checkout.Session.create(
            success_url=success_url,
            cancel_url=cancel_url,
            payment_method_types=["card"],
            mode="subscription",
            customer_email=user["email"],
            line_items=[{
                "price": price.id,
                "quantity": 1
            }],
            metadata={
                "user_id": user_id,
                "tier": tier,
                "billing_cycle": billing_cycle
            }
        )
        
        return {"success": True, "checkout_url": checkout_session.url, "session_id": checkout_session.id}
    except Exception as e:
        st.error(f"Error creating checkout session: {str(e)}")
        return {"success": False, "message": str(e)}

def handle_webhook_event(event_data):
    """Handle incoming Stripe webhook events."""
    event_type = event_data["type"]
    
    if event_type == "checkout.session.completed":
        # Payment successful, activate subscription
        session = event_data["data"]["object"]
        user_id = session["metadata"]["user_id"]
        tier = session["metadata"]["tier"]
        billing_cycle = session["metadata"]["billing_cycle"]
        
        # Calculate subscription end date based on billing cycle
        start_date = datetime.utcnow()
        if billing_cycle == "monthly":
            end_date = start_date + timedelta(days=30)
        else:  # yearly
            end_date = start_date + timedelta(days=365)
        
        # Update user's subscription
        success = update_user_subscription(
            user_id=user_id,
            tier=tier,
            subscription_start_date=start_date,
            subscription_end_date=end_date
        )
        
        return {"success": success, "user_id": user_id, "tier": tier}
    
    elif event_type == "customer.subscription.updated":
        # Subscription updated
        subscription = event_data["data"]["object"]
        # Process subscription update logic here
        return {"success": True, "message": "Subscription updated"}
    
    elif event_type == "customer.subscription.deleted":
        # Subscription cancelled or expired
        subscription = event_data["data"]["object"]
        # Process subscription cancellation logic here
        return {"success": True, "message": "Subscription cancelled"}
    
    return {"success": True, "message": f"Event {event_type} received but not processed"}

def display_payment_button(tier, billing_cycle, button_text="Subscribe"):
    """Display a Stripe checkout button for the specified tier and billing cycle."""
    if not STRIPE_PUBLISHABLE_KEY:
        st.error("Stripe publishable key not found. Please check your environment variables.")
        return
    
    # Get current user ID from session state
    if "user_id" not in st.session_state:
        st.warning("Please log in to subscribe.")
        return
    
    user_id = st.session_state.user_id
    
    # Set success and cancel URLs
    success_url = f"{st.get_url()}payment_success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{st.get_url()}subscription"
    
    # Create checkout session
    checkout_result = get_stripe_checkout_session(
        user_id=user_id,
        tier=tier,
        billing_cycle=billing_cycle,
        success_url=success_url,
        cancel_url=cancel_url
    )
    
    if checkout_result["success"]:
        # Display checkout button using Stripe's checkout.js
        checkout_id = checkout_result["session_id"]
        checkout_url = checkout_result["checkout_url"]
        
        # In a real application, you would use Stripe's JavaScript SDK
        # Here, we'll use a simplified approach
        if st.button(button_text, key=f"stripe_{tier}_{billing_cycle}"):
            st.markdown(f'<meta http-equiv="refresh" content="0;url={checkout_url}">', unsafe_allow_html=True)
            st.info("Redirecting to Stripe checkout...")
    else:
        st.error(f"Error: {checkout_result['message']}")

def handle_payment_success():
    """Handle successful payment redirect from Stripe."""
    query_params = st.experimental_get_query_params()
    session_id = query_params.get("session_id", [None])[0]
    
    if session_id:
        try:
            # Verify the checkout session
            session = stripe.checkout.Session.retrieve(session_id)
            
            if session.payment_status == "paid":
                # Get metadata from session
                user_id = session.metadata.get("user_id")
                tier = session.metadata.get("tier")
                
                # Update user subscription in database
                user = get_user_by_id(user_id)
                
                if user:
                    st.session_state.user = user
                    st.session_state.subscription_tier = user["subscription_tier"]
                
                return {"success": True, "tier": tier}
            else:
                return {"success": False, "message": "Payment not completed"}
        
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    return {"success": False, "message": "Invalid session ID"}

def create_stripe_webhook_handler():
    """Create a handler for Stripe webhooks."""
    # This would typically be implemented as a separate API endpoint
    # For Streamlit, you'd need to use a framework like FastAPI alongside
    # In a real implementation, you would validate the webhook signature
    pass