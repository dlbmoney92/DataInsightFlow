import streamlit as st
import json
import os
import stripe
from utils.payment import handle_webhook_event

def app():
    """Handle Stripe webhook events."""
    # Set the Stripe API key
    stripe_secret_key = os.environ.get("STRIPE_SECRET_KEY")
    if not stripe_secret_key:
        st.error("Stripe secret key not found. Please set the STRIPE_SECRET_KEY environment variable.")
        return
    
    stripe.api_key = stripe_secret_key
    
    # Get the webhook signing secret (would be set in a real deployment)
    webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
    
    st.title("Stripe Webhook Handler")
    
    if st.session_state.get("show_webhook_form", True):
        # In a real implementation, this would be an automatic endpoint
        # For this demo, we'll simulate webhook events manually
        
        st.write("This page is for handling Stripe webhook events.")
        st.write("In a production environment, this would be a server-side endpoint that receives webhook events directly from Stripe.")
        
        # Event type selection
        event_types = [
            "checkout.session.completed",
            "customer.subscription.updated",
            "customer.subscription.deleted"
        ]
        event_type = st.selectbox("Event Type", event_types)
        
        # User selection (for simulation)
        if "logged_in" in st.session_state and st.session_state.logged_in:
            user_id = st.session_state.user_id
            st.write(f"User ID: {user_id}")
        else:
            user_id = st.text_input("User ID")
        
        # Subscription tier selection
        tiers = ["basic", "pro"]
        tier = st.selectbox("Subscription Tier", tiers)
        
        # Billing cycle selection
        billing_cycles = ["monthly", "yearly"]
        billing_cycle = st.selectbox("Billing Cycle", billing_cycles)
        
        # Submit button
        if st.button("Simulate Webhook Event"):
            # Create a simulated event object
            if event_type == "checkout.session.completed":
                event_data = {
                    "type": event_type,
                    "data": {
                        "object": {
                            "metadata": {
                                "user_id": user_id,
                                "tier": tier,
                                "billing_cycle": billing_cycle
                            },
                            "payment_status": "paid"
                        }
                    }
                }
                
                # Process the webhook event
                result = handle_webhook_event(event_data)
                
                if result.get("success"):
                    st.success(f"Webhook handled successfully: {event_type}")
                    st.json(result)
                    
                    # Hide the form after successful processing
                    st.session_state.show_webhook_form = False
                else:
                    st.error(f"Error handling webhook: {result.get('message', 'Unknown error')}")
            else:
                st.info(f"Event type '{event_type}' simulation not implemented in this demo")
    else:
        # Show success message and button to reset
        st.success("Webhook event processed successfully!")
        if st.button("Process Another Webhook Event"):
            st.session_state.show_webhook_form = True
            st.rerun()

if __name__ == "__main__":
    app()