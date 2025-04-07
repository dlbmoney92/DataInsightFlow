import streamlit as st
from utils.auth_redirect import require_auth
from utils.global_config import apply_global_css

def app():
    """Handle successful payment redirect from Stripe."""
    # Apply global CSS
    apply_global_css()
    
    # Check if user is logged in
    if not require_auth():
        return
    
    # Get query parameters
    query_params = st.query_params
    success = query_params.get("success", "false") == "true"
    tier = query_params.get("tier", None)
    
    # Clear query params after reading
    if "success" in query_params or "tier" in query_params:
        new_params = {}
        for param in query_params:
            if param != "success" and param != "tier":
                new_params[param] = query_params[param]
        st.query_params.update(new_params)
    
    # Display success message
    st.title("Payment Successful!")
    
    # Show different messages based on the tier
    if tier == "basic":
        st.success("Thank you for subscribing to the Basic tier! Your account has been upgraded.")
        st.markdown("""
        ## What's next?
        
        You now have access to:
        - 10 datasets
        - Advanced data transformations
        - Interactive visualizations
        - CSV, Excel, and JSON support
        - 30-day data history
        - Priority support
        - Data validation tools
        
        Start exploring your new features now!
        """)
    elif tier == "pro":
        st.success("Thank you for subscribing to the Pro tier! Your account has been upgraded.")
        st.markdown("""
        ## What's next?
        
        You now have access to:
        - Unlimited datasets
        - All data transformations
        - Advanced AI-driven insights
        - All file formats supported
        - 90-day data history
        - Priority support
        - Data validation tools
        - Custom reports and exports
        - Team collaboration features
        
        Start exploring your new features now!
        """)
    else:
        st.success("Thank you for your payment! Your account has been upgraded.")
    
    # Button to go to home
    if st.button("Go to Dashboard", use_container_width=True):
        st.switch_page("app.py")
    
    # Button to upload data
    if st.button("Upload Data", use_container_width=True):
        st.switch_page("pages/01_Upload_Data.py")

if __name__ == "__main__":
    app()