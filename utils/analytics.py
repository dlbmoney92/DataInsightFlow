import streamlit as st

def initialize_google_analytics():
    """
    Initialize Google Analytics on all pages.
    This function should be called at the very beginning of each page,
    right after st.set_page_config.
    """
    # Google Analytics tracking code
    tracking_code = """
    <!-- Google tag (gtag.js) -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-LNS5P4X7H9"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());
      gtag('config', 'G-LNS5P4X7H9');
    </script>
    """
    
    # Add tracking code to the page
    st.markdown(tracking_code, unsafe_allow_html=True)

def include_analytics_in_each_page():
    """
    This function adds a key to the session state that we can check
    to ensure Google Analytics is only added once per page load.
    """
    if 'google_analytics_added' not in st.session_state:
        st.session_state.google_analytics_added = False
        
    if not st.session_state.google_analytics_added:
        initialize_google_analytics()
        st.session_state.google_analytics_added = True