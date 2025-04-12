import streamlit.components.v1 as components

def add_google_analytics():
    """
    Create and inject Google Analytics component that will properly add GA to the page.
    This implements Google's recommended gtag.js implementation with the GA4 tracking ID.
    """
    GA_TRACKING_ID = "G-HGSH7TS3LX"
    
    # Create the HTML with the Google Analytics tracking code
    ga_html = f"""
    <html>
        <head>
            <!-- Google tag (gtag.js) -->
            <script async src="https://www.googletagmanager.com/gtag/js?id={GA_TRACKING_ID}"></script>
            <script>
                window.dataLayer = window.dataLayer || [];
                function gtag(){{dataLayer.push(arguments);}}
                gtag('js', new Date());
                gtag('config', '{GA_TRACKING_ID}');
                console.log("Google Analytics initialized with ID: {GA_TRACKING_ID}");
            </script>
        </head>
        <body>
            <!-- Google Analytics container -->
        </body>
    </html>
    """
    
    # Use Streamlit components to inject the HTML
    return components.html(ga_html, height=0, width=0)