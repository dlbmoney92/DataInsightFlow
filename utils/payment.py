import os
import stripe
import streamlit as st
from utils.subscription import SUBSCRIPTION_PLANS
from utils.database import update_user_subscription

# Set up Stripe API key
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "pk_live_51RB3nwECzEFv0PT1bYl0SK9zMDczypQrPZ1ovgjmLe4fNPtTuGZKSys2l5nd5H2JsDkoKyt82aEfrSeex05yfbbX00O0oyguqI")

# Check for API key on module load
if not stripe.api_key:
    print("WARNING: STRIPE_SECRET_KEY environment variable is not set")
    print("Payment functionality will not work correctly")

# Pre-defined product and price IDs for each tier and billing cycle
# In a production environment, these would be created in the Stripe dashboard
# and stored in environment variables or a database
STRIPE_PRODUCTS = {
    "basic": {
        "monthly": {"product_id": "prod_basic_monthly", "price_id": "price_basic_monthly"},
        "yearly": {"product_id": "prod_basic_yearly", "price_id": "price_basic_yearly"}
    },
    "pro": {
        "monthly": {"product_id": "prod_pro_monthly", "price_id": "price_pro_monthly"},
        "yearly": {"product_id": "prod_pro_yearly", "price_id": "price_pro_yearly"}
    },
    "enterprise": {
        "monthly": {"product_id": "prod_enterprise_monthly", "price_id": "price_enterprise_monthly"},
        "yearly": {"product_id": "prod_enterprise_yearly", "price_id": "price_enterprise_yearly"}
    }
}

def get_stripe_checkout_session(user_id, tier, billing_cycle, success_url, cancel_url):
    """
    Create a Stripe checkout session for a subscription.
    
    Parameters:
    - user_id: The ID of the user making the purchase
    - tier: The subscription tier to purchase (basic, pro, etc.)
    - billing_cycle: Either "monthly" or "yearly"
    - success_url: URL to redirect to after successful payment
    - cancel_url: URL to redirect to if payment is canceled
    
    Returns:
    - Dictionary with success status and either checkout URL or error message
    """
    # Validate inputs
    if tier not in SUBSCRIPTION_PLANS:
        return {"success": False, "message": f"Invalid subscription tier: {tier}"}
    
    if billing_cycle not in ["monthly", "yearly"]:
        return {"success": False, "message": f"Invalid billing cycle: {billing_cycle}"}
    
    if not stripe.api_key:
        return {
            "success": False,
            "message": "Stripe API key is not configured. Please contact support."
        }
    
    try:
        price_id = None
        
        # First try to use a predefined price ID
        if tier in STRIPE_PRODUCTS and billing_cycle in STRIPE_PRODUCTS[tier]:
            # Use predefined price ID if available
            try:
                # Try to get price from Stripe to verify it exists
                price_id = STRIPE_PRODUCTS[tier][billing_cycle]["price_id"]
                stripe.Price.retrieve(price_id)
                print(f"Using existing price ID: {price_id}")
            except Exception as e:
                # Could be stripe.error.InvalidRequestError but handling all exceptions
                # Price doesn't exist yet, will create it
                price_id = None
                print(f"Price ID {price_id} not found, will create a new one")
        
        # If no predefined price or it doesn't exist, create a new one
        if not price_id:
            # Get the price based on the tier and billing cycle
            if billing_cycle == "monthly":
                price = SUBSCRIPTION_PLANS[tier]["monthly_price"]
            else:
                price = SUBSCRIPTION_PLANS[tier]["annual_price"]
            
            # Convert price to cents (Stripe uses the smallest currency unit)
            price_in_cents = int(price * 100)
            
            # Get or create product
            product_id = None
            if tier in STRIPE_PRODUCTS and billing_cycle in STRIPE_PRODUCTS[tier]:
                product_id = STRIPE_PRODUCTS[tier][billing_cycle]["product_id"]
            
            try:
                if product_id:
                    # Try to get existing product
                    product = stripe.Product.retrieve(product_id)
                    print(f"Using existing product: {product_id}")
                else:
                    raise Exception("Product not found")
            except Exception as e:
                # Create a new product
                product = stripe.Product.create(
                    id=product_id if product_id else None,
                    name=f"Analytics Assist {SUBSCRIPTION_PLANS[tier]['name']} ({billing_cycle})",
                    description=f"{SUBSCRIPTION_PLANS[tier]['name']} tier subscription for Analytics Assist - {billing_cycle} billing"
                )
                print(f"Created new product: {product.id}")
            
            # Create a price object
            if billing_cycle == "monthly":
                price_obj = stripe.Price.create(
                    id=price_id if price_id else None,
                    product=product.id,
                    unit_amount=price_in_cents,
                    currency="usd",
                    recurring={"interval": "month"}
                )
            else:
                price_obj = stripe.Price.create(
                    id=price_id if price_id else None,
                    product=product.id,
                    unit_amount=price_in_cents,
                    currency="usd",
                    recurring={"interval": "year"}
                )
            
            price_id = price_obj.id
            print(f"Created new price: {price_id}")
        
        # Create checkout session with the price
        checkout_session = stripe.checkout.Session.create(
            success_url=success_url,
            cancel_url=cancel_url,
            mode="subscription",
            payment_method_types=["card"],
            line_items=[{
                "price": price_id,
                "quantity": 1
            }],
            client_reference_id=str(user_id),
            metadata={
                "user_id": str(user_id),
                "tier": tier,
                "billing_cycle": billing_cycle
            }
        )
        
        return {
            "success": True,
            "checkout_url": checkout_session.url
        }
    
    except Exception as e:
        return {
            "success": False,
            "message": f"Error creating checkout session: {str(e)}"
        }

def handle_stripe_webhook_event(event_json):
    """
    Handle Stripe webhook events.
    
    Parameters:
    - event_json: The parsed JSON from the Stripe webhook
    
    Returns:
    - Dictionary with success status and message
    """
    # Check if this is a supported event type
    event_type = event_json.get("type")
    
    if event_type == "checkout.session.completed":
        # Payment was successful, activate the subscription
        session = event_json.get("data", {}).get("object", {})
        metadata = session.get("metadata", {})
        
        user_id = metadata.get("user_id")
        tier = metadata.get("tier")
        
        if user_id and tier:
            # Update user subscription in the database
            update_user_subscription(user_id, tier)
            return {"success": True, "message": f"Subscription activated: {tier} for user {user_id}"}
        else:
            return {"success": False, "message": "Missing user_id or tier in metadata"}
    
    elif event_type == "customer.subscription.updated":
        # Subscription was updated (upgrade, downgrade, or renewal)
        subscription = event_json.get("data", {}).get("object", {})
        metadata = subscription.get("metadata", {})
        
        user_id = metadata.get("user_id")
        tier = metadata.get("tier")
        
        if user_id and tier:
            # Update user subscription in the database
            update_user_subscription(user_id, tier)
            return {"success": True, "message": f"Subscription updated: {tier} for user {user_id}"}
        else:
            return {"success": False, "message": "Missing user_id or tier in metadata"}
    
    elif event_type == "customer.subscription.deleted":
        # Subscription was canceled or expired
        subscription = event_json.get("data", {}).get("object", {})
        metadata = subscription.get("metadata", {})
        
        user_id = metadata.get("user_id")
        
        if user_id:
            # Downgrade user to free tier
            update_user_subscription(user_id, "free")
            return {"success": True, "message": f"Subscription canceled for user {user_id}"}
        else:
            return {"success": False, "message": "Missing user_id in metadata"}
    
    # Return success for other event types to avoid webhook errors
    return {"success": True, "message": f"Unsupported event type: {event_type}"}

def create_subscription_management_link(user_id):
    """
    Create a link for users to manage their subscription.
    
    In a real implementation, this would create a Stripe customer portal session.
    
    Parameters:
    - user_id: The ID of the user
    
    Returns:
    - The URL of the subscription management page
    """
    if not stripe.api_key:
        st.warning("Stripe API key is not configured. Please contact support.")
        return None
    
    try:
        # In a real implementation, you'd store the Stripe customer ID in your database
        # and look it up here. For demo purposes, we'll create a new customer.
        customer = stripe.Customer.create(
            metadata={"user_id": str(user_id)}
        )
        
        # Get base URL from environment or use a default for development
        base_url = os.environ.get("REPL_SLUG", "localhost:5000")
        protocol = "https" if "replit" in base_url else "http"
        return_url = f"{protocol}://{base_url}/pages/subscription.py"
            
        # Create a customer portal session
        session = stripe.billing_portal.Session.create(
            customer=customer.id,
            return_url=return_url
        )
        
        return session.url
    
    except Exception as e:
        st.error(f"Error creating subscription management link: {str(e)}")
        return None
