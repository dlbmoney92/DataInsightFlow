import streamlit as st
from streamlit.components.v1 import html

def inject_ga_tracking():
    """
    Inject Google Analytics tracking code directly into the HTML head
    using a custom component approach.
    """
    # Google Analytics tracking ID
    GA_TRACKING_ID = "G-LNS5P4X7H9"
    
    # HTML with script injected in head
    ga_html = f"""
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
        <div id="ga-tracking-injector"></div>
        <script>
            // This is just a minimum implementation to get GA loaded in the head
            console.log("Google Analytics tracking code loaded for {GA_TRACKING_ID}");
        </script>
    </body>
    </html>
    """
    
    # Use streamlit components to inject HTML with head properly
    html(ga_html, height=0, width=0)