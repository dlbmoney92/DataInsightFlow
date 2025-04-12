import streamlit as st
from components.google_analytics import add_google_analytics

def configure_page(title="Analytics Assist", page_icon="📊", layout="wide", initial_sidebar_state="expanded"):
    """
    Configure page settings including Google Analytics tracking.
    This should be called at the top of each page.
    """
    # Set page configuration
    st.set_page_config(
        page_title=title,
        page_icon=page_icon,
        layout=layout,
        initial_sidebar_state=initial_sidebar_state
    )
    
    # Add Google Analytics tracking
    add_google_analytics()
    
    # Hide Streamlit's default navigation menu
    st.markdown("""
        <style>
            [data-testid="stSidebarNav"] {
                display: none !important;
            }
        </style>
    """, unsafe_allow_html=True)