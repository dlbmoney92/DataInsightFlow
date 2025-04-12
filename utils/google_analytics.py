import streamlit as st
from streamlit.components.v1 import html

# Google Analytics tracking ID
GA_TRACKING_ID = "G-HGSH7TS3LX"

def inject_ga_tracking_code():
    """
    Inject Google Analytics tracking code directly into the page using a custom HTML component.
    This approach ensures the scripts are loaded properly.
    """
    # Create a complete HTML document with the GA tracking code
    tracking_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <!-- Google tag (gtag.js) -->
        <script async src="https://www.googletagmanager.com/gtag/js?id={GA_TRACKING_ID}"></script>
        <script>
            window.dataLayer = window.dataLayer || [];
            function gtag(){{dataLayer.push(arguments);}}
            gtag('js', new Date());
            gtag('config', '{GA_TRACKING_ID}');
        </script>
    </head>
    <body>
        <!-- Google Analytics code injector -->
    </body>
    </html>
    """
    
    # Use the html component to inject the tracking code
    # The height=0 makes it invisible on the page
    return html(tracking_code, height=0, width=0)

def add_ga_tracking():
    """
    Add Google Analytics tracking code to a Streamlit page.
    This should be called near the top of each page, after st.set_page_config.
    """
    # Check if we've already added tracking to this page
    if 'ga_added' not in st.session_state:
        st.session_state.ga_added = False
    
    if not st.session_state.ga_added:
        inject_ga_tracking_code()
        st.session_state.ga_added = True
        
        # Also add tracking to page changes 
        track_page_view_script = f"""
        <script>
            // Track page views when URL changes
            const reportPageView = () => {{
                gtag('event', 'page_view', {{
                    page_title: document.title,
                    page_location: window.location.href
                }});
                console.log('Analytics: Page view tracked');
            }};
            
            // Listen for URL changes
            const oldPushState = window.history.pushState;
            window.history.pushState = function() {{
                oldPushState.apply(this, arguments);
                reportPageView();
            }};
            
            // Listen for popstate events (browser back/forward)
            window.addEventListener('popstate', reportPageView);
            
            // Initial page view
            reportPageView();
        </script>
        """
        
        # Inject the page view tracking script
        st.markdown(track_page_view_script, unsafe_allow_html=True)