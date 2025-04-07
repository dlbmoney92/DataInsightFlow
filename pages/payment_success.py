import streamlit as st
from utils.payment import handle_payment_success
from utils.database import get_user_by_id
from utils.subscription import SUBSCRIPTION_TIERS

def app():
    """Handle successful payment redirect from Stripe."""
    st.title("Payment Successful")
    
    # Handle the payment success
    result = handle_payment_success()
    
    if result.get("success"):
        tier = result.get("tier", "")
        tier_info = SUBSCRIPTION_TIERS.get(tier, SUBSCRIPTION_TIERS["free"])
        
        # Display success message
        st.success("🎉 Thank you for your subscription!")
        
        st.markdown(f"""
        ## Welcome to Analytics Assist {tier_info['name']}!
        
        Your subscription has been successfully activated. You now have access to all the 
        {tier_info['name']} plan features.
        
        ### What's included in your plan:
        """)
        
        # List features
        for feature in tier_info["features"]:
            st.markdown(f"✓ {feature}")
        
        # Next steps
        st.markdown("### Next Steps")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Go to Dashboard", use_container_width=True):
                st.switch_page("app.py")
        with col2:
            if st.button("Explore Features", use_container_width=True):
                st.switch_page("pages/01_Upload_Data.py")
    else:
        # Display error message
        st.error("There was an issue processing your payment: " + result.get("message", "Unknown error"))
        
        st.markdown("""
        Don't worry! If your payment was processed but you're seeing this message, 
        your subscription will still be activated automatically.
        
        If you have any questions or need assistance, please contact our support team.
        """)
        
        if st.button("Go to Home"):
            st.switch_page("app.py")

if __name__ == "__main__":
    app()