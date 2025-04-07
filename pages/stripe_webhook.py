import streamlit as st
import json
import os
import stripe
from utils.payment import handle_stripe_webhook_event
from utils.global_config import apply_global_css

def app():
    """Handle Stripe webhook events."""
    # Apply global CSS
    apply_global_css()
    
    # Set up Stripe API key
    stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")
    
    # Display a simplified webhook management interface
    st.title("Stripe Webhook Management")
    
    # Explain this is a demo
    st.info("""
    This is a demo webhook endpoint for Stripe events. In a production environment, this would be a proper API endpoint 
    that receives webhook events from Stripe and processes them without a UI.
    
    For demonstration purposes, you can simulate webhook events here.
    """)
    
    # Create a form to simulate webhook events
    with st.form("webhook_form"):
        event_type = st.selectbox(
            "Event Type", 
            [
                "checkout.session.completed",
                "customer.subscription.updated",
                "customer.subscription.deleted"
            ]
        )
        
        user_id = st.text_input("User ID", value="1")
        tier = st.selectbox("Subscription Tier", ["free", "basic", "pro", "enterprise"])
        
        submitted = st.form_submit_button("Simulate Webhook Event")
        
        if submitted:
            # Create a simulated event payload
            if event_type == "checkout.session.completed":
                event_json = {
                    "type": event_type,
                    "data": {
                        "object": {
                            "metadata": {
                                "user_id": user_id,
                                "tier": tier
                            }
                        }
                    }
                }
            else:
                event_json = {
                    "type": event_type,
                    "data": {
                        "object": {
                            "metadata": {
                                "user_id": user_id,
                                "tier": tier
                            }
                        }
                    }
                }
            
            # Handle the webhook event
            result = handle_stripe_webhook_event(event_json)
            
            if result['success']:
                st.success(f"Success: {result['message']}")
            else:
                st.error(f"Error: {result['message']}")
    
    # Display webhook configuration instructions
    st.markdown("## How to set up webhooks in Stripe")
    st.markdown("""
    1. Go to the [Stripe Dashboard](https://dashboard.stripe.com/)
    2. Navigate to Developers > Webhooks
    3. Click "Add endpoint"
    4. Enter your webhook URL (e.g., https://yourdomain.com/stripe_webhook)
    5. Select the events you want to listen for (e.g., checkout.session.completed)
    6. Click "Add endpoint"
    """)
    
    st.markdown("## Events to listen for")
    st.markdown("""
    - `checkout.session.completed`: When a customer completes checkout
    - `customer.subscription.updated`: When a subscription is updated
    - `customer.subscription.deleted`: When a subscription is canceled
    """)
    
    # Show test webhook data
    if st.checkbox("Show test webhook data"):
        st.json({
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_a1b2c3d4e5f6g7h8i9j0",
                    "object": "checkout.session",
                    "client_reference_id": "1",
                    "metadata": {
                        "user_id": "1",
                        "tier": "pro",
                        "billing_cycle": "monthly"
                    }
                }
            }
        })

if __name__ == "__main__":
    app()