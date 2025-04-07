import streamlit as st
import os

def apply_global_css():
    """Apply global CSS styles to all pages."""
    # Path to the CSS file
    css_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.streamlit', 'style.css')
    
    # Check if file exists
    if os.path.exists(css_file):
        with open(css_file, 'r') as f:
            css = f.read()
            st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)
    
    # Additional CSS for hiding default Streamlit navigation
    hide_default_nav = """
    <style>
    /* Hide the default Streamlit sidebar navigation menu */
    [data-testid="stSidebarNavItems"] {
        display: none !important;
    }
    
    /* Hide the navigation collapse button */
    button[kind="headerNoPadding"][data-testid="baseButton-headerNoPadding"] {
        display: none !important;
    }
    
    /* Hide the hamburger menu completely */
    section[data-testid="stSidebarUserContent"] > div:first-child > button {
        display: none !important;
    }
    
    /* Make sure our custom navigation is visible */
    div[data-testid="stSidebarUserContent"] {
        display: block !important;
    }
    </style>
    """
    st.markdown(hide_default_nav, unsafe_allow_html=True)