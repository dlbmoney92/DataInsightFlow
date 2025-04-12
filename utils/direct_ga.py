import streamlit as st

def add_ga_tag():
    """
    Add Google Analytics tracking tag directly to the HTML of the page.
    This uses a more direct approach that should work across all browsers.
    """
    # Google Analytics Tracking ID
    GA_TRACKING_ID = "G-HGSH7TS3LX"
    
    # Create the HTML with the Google Analytics tracking code
    ga_html = f"""
    <!-- Google tag (gtag.js) -->
    <script async src="https://www.googletagmanager.com/gtag/js?id={GA_TRACKING_ID}"></script>
    <script>
        window.dataLayer = window.dataLayer || [];
        function gtag(){{dataLayer.push(arguments);}}
        gtag('js', new Date());
        gtag('config', '{GA_TRACKING_ID}', {{ 'send_page_view': true }});
        console.log('Google Analytics loaded with ID: {GA_TRACKING_ID}');
    </script>
    """
    
    # Inject the HTML directly into the page head
    st.markdown(ga_html, unsafe_allow_html=True)