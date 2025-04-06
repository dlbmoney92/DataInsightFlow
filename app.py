import streamlit as st
import pandas as pd
import numpy as np
import os
import json
from datetime import datetime
from utils.file_processor import supported_file_types
from utils.database import initialize_database
from utils.access_control import check_and_handle_trial_expiration
from utils.subscription import SUBSCRIPTION_TIERS, format_price, get_trial_days_remaining
import uuid

# Set page configuration
st.set_page_config(
    page_title="Analytics Assist",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
initialize_database()

# Initialize session state variables if they don't exist
if 'dataset' not in st.session_state:
    st.session_state.dataset = None
if 'file_name' not in st.session_state:
    st.session_state.file_name = None
if 'column_types' not in st.session_state:
    st.session_state.column_types = {}
if 'transformations' not in st.session_state:
    st.session_state.transformations = []
if 'transformation_history' not in st.session_state:
    st.session_state.transformation_history = []
if 'insights' not in st.session_state:
    st.session_state.insights = []
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if 'projects' not in st.session_state:
    st.session_state.projects = []
if 'current_project' not in st.session_state:
    st.session_state.current_project = None
if 'ai_suggestions' not in st.session_state:
    st.session_state.ai_suggestions = []
if 'dataset_id' not in st.session_state:
    st.session_state.dataset_id = None

# Sidebar for navigation and user info
with st.sidebar:
    st.title("Analytics Assist")
    
    # User authentication section
    if "logged_in" in st.session_state and st.session_state.logged_in:
        # Check if trial has expired
        check_and_handle_trial_expiration()
        
        # Display user info
        st.write(f"Welcome, {st.session_state.user['full_name']}")
        
        # Show current plan
        current_tier = st.session_state.subscription_tier
        plan_name = SUBSCRIPTION_TIERS[current_tier]["name"]
        st.write(f"Plan: {plan_name}")
        
        # Show trial info if applicable
        if st.session_state.user["is_trial"]:
            trial_end = st.session_state.user["trial_end_date"]
            if trial_end:
                days_left = get_trial_days_remaining(trial_end)
                if days_left > 0:
                    st.info(f"Trial: {days_left} days left")
        
        # Account and logout buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Account", use_container_width=True):
                st.switch_page("pages/account.py")
        with col2:
            if st.button("Logout", use_container_width=True):
                # Clear session state for user
                for key in ['user', 'logged_in', 'user_id', 'subscription_tier']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
    else:
        # Login/signup buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Login", use_container_width=True):
                st.switch_page("pages/login.py")
        with col2:
            if st.button("Sign Up", use_container_width=True):
                st.switch_page("pages/signup.py")
    
    st.divider()
    
    # Navigation menu
    st.header("Navigation")
    
    # Main pages
    if st.button("📁 Upload Data", use_container_width=True):
        st.switch_page("pages/01_Upload_Data.py")
    
    if st.button("🔍 Data Preview", use_container_width=True):
        st.switch_page("pages/02_Data_Preview.py")
    
    if st.button("📊 EDA Dashboard", use_container_width=True):
        st.switch_page("pages/03_EDA_Dashboard.py")
    
    if st.button("🧹 Transformations", use_container_width=True):
        st.switch_page("pages/04_Data_Transformation.py")
    
    if st.button("💡 Insights", use_container_width=True):
        st.switch_page("pages/05_Insights_Dashboard.py")
    
    if st.button("📤 Export Reports", use_container_width=True):
        st.switch_page("pages/06_Export_Reports.py")
    
    if st.button("📜 Version History", use_container_width=True):
        st.switch_page("pages/07_Version_History.py")
    
    st.divider()
    
    # Subscription
    if st.button("💼 Subscription Plans", use_container_width=True):
        st.switch_page("pages/subscription.py")

# Main content
# Check if user is logged in
if "logged_in" in st.session_state and st.session_state.logged_in:
    # Personalized dashboard for logged-in users
    st.title(f"Welcome, {st.session_state.user['full_name']}!")
    st.subheader("Your AI-powered data analysis co-pilot")
    
    # Dashboard layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ## Your Analytics Dashboard 📊
        
        Analytics Assist helps you understand your data and discover insights with AI assistance.
        """)
        
        # Stats overview
        stats_col1, stats_col2, stats_col3 = st.columns(3)
        
        with stats_col1:
            current_dataset = "None" if st.session_state.dataset is None else st.session_state.current_project.get('name', 'Unnamed dataset')
            st.metric("Current Dataset", current_dataset)
        
        with stats_col2:
            if st.session_state.dataset is not None:
                rows = st.session_state.dataset.shape[0]
                st.metric("Rows", rows)
            else:
                st.metric("Rows", 0)
        
        with stats_col3:
            transformations_count = len(st.session_state.transformations)
            st.metric("Transformations", transformations_count)
        
        st.markdown("### Getting Started")
        st.markdown("""
        1. 📁 **Upload Data**: Start by uploading your dataset in the Upload Data page
        2. 🔍 **Preview & Validate**: Review and validate the detected schema
        3. 📊 **Explore**: Get automatic visualizations and statistics
        4. 🧹 **Transform**: Apply AI-suggested transformations to clean your data
        5. 💡 **Discover Insights**: Review AI-generated insights about your data
        6. 📤 **Export**: Export your findings as reports or download transformed data
        """)
        
        # Supported file types
        with st.expander("Supported File Types"):
            file_types_cols = st.columns(3)
            for i, file_type in enumerate(supported_file_types):
                file_types_cols[i % 3].markdown(f"- {file_type}")
    
    with col2:
        st.markdown("### Current Project")
        
        if st.session_state.current_project:
            st.success(f"Working on: {st.session_state.current_project['name']}")
            
            # Display project stats
            if st.session_state.dataset is not None:
                rows, cols = st.session_state.dataset.shape
                st.metric("Columns", cols)
                st.write(f"Last modified: {st.session_state.current_project.get('updated_at', 'Unknown')}")
        else:
            st.info("No active project. Start by uploading data.")
        
        # Recent activity
        st.markdown("### Recent Activity")
        if st.session_state.transformation_history:
            for i, history in enumerate(reversed(st.session_state.transformation_history[-3:])):
                st.text(f"{history['timestamp']}: {history['action']}")
        else:
            st.text("No recent activity")
        
        # Subscription info
        st.markdown("### Your Subscription")
        current_tier = st.session_state.subscription_tier
        tier_info = SUBSCRIPTION_TIERS[current_tier]
        
        st.write(f"Current plan: **{tier_info['name']}**")
        
        # Trial information
        if st.session_state.user["is_trial"]:
            trial_end = st.session_state.user["trial_end_date"]
            if trial_end:
                days_left = get_trial_days_remaining(trial_end)
                if days_left > 0:
                    st.info(f"Your Pro trial ends in {days_left} days.")
                    if st.button("Upgrade Now"):
                        st.switch_page("pages/subscription.py")
    
    # Quick access buttons
    st.markdown("---")
    st.markdown("## Quick Actions")
    
    quick_cols = st.columns(4)
    with quick_cols[0]:
        if st.button("📤 Upload New Data", use_container_width=True):
            st.switch_page("pages/01_Upload_Data.py")
    
    with quick_cols[1]:
        if st.button("🔍 Explore Current Data", use_container_width=True):
            st.switch_page("pages/03_EDA_Dashboard.py")
    
    with quick_cols[2]:
        if st.button("🧹 Transform Data", use_container_width=True):
            st.switch_page("pages/04_Data_Transformation.py")
    
    with quick_cols[3]:
        if st.button("💡 Generate Insights", use_container_width=True):
            st.switch_page("pages/05_Insights_Dashboard.py")

else:
    # Landing page for anonymous users
    st.title("Analytics Assist")
    st.subheader("Your AI-powered data analysis co-pilot")
    
    # Hero section
    st.markdown("""
    ## Transform Your Data into Actionable Insights 🚀
    
    Analytics Assist is a powerful AI-driven platform that helps you:
    - **Explore** and understand your data
    - **Clean** and transform your datasets with ease
    - **Discover** valuable insights automatically
    - **Visualize** your findings with beautiful charts
    - **Share** your results with customizable reports
    """)
    
    # Call to action
    cta_col1, cta_col2 = st.columns(2)
    with cta_col1:
        if st.button("Sign Up Free", use_container_width=True):
            st.switch_page("pages/signup.py")
    with cta_col2:
        if st.button("Start 7-Day Pro Trial", use_container_width=True):
            st.switch_page("pages/signup.py")
    
    # Features showcase
    st.markdown("---")
    st.markdown("## Key Features")
    
    feature_cols = st.columns(3)
    
    with feature_cols[0]:
        st.markdown("### 🤖 AI-Powered Analysis")
        st.markdown("""
        Leverage the power of AI to:
        - Get intelligent data cleaning suggestions
        - Automatically detect patterns and anomalies
        - Generate natural language insights
        - Receive personalized recommendations
        """)
    
    with feature_cols[1]:
        st.markdown("### 📊 Powerful Visualizations")
        st.markdown("""
        Create insightful visualizations:
        - Interactive charts and graphs
        - Correlation analysis
        - Distribution plots
        - Time series analysis
        - Automated dashboard generation
        """)
    
    with feature_cols[2]:
        st.markdown("### 🧩 No-Code Experience")
        st.markdown("""
        Designed for users of all skill levels:
        - Intuitive drag-and-drop interface
        - Guided data transformation workflows
        - Human-readable explanations
        - Export in multiple formats
        - Share insights with your team
        """)
    
    # Pricing section
    st.markdown("---")
    st.markdown("## Subscription Plans")
    
    pricing_cols = st.columns(3)
    
    with pricing_cols[0]:
        st.markdown("### Free")
        st.markdown(f"**{format_price(SUBSCRIPTION_TIERS['free']['price_monthly'])}**/month")
        for feature in SUBSCRIPTION_TIERS['free']['features']:
            st.markdown(f"✓ {feature}")
        if st.button("Sign Up Free", key="pricing_free", use_container_width=True):
            st.switch_page("pages/signup.py")
    
    with pricing_cols[1]:
        st.markdown("### Basic")
        st.markdown(f"**{format_price(SUBSCRIPTION_TIERS['basic']['price_monthly'])}**/month")
        for feature in SUBSCRIPTION_TIERS['basic']['features']:
            st.markdown(f"✓ {feature}")
        if st.button("Choose Basic", key="pricing_basic", use_container_width=True):
            st.switch_page("pages/signup.py")
    
    with pricing_cols[2]:
        st.markdown("### Pro")
        st.markdown(f"**{format_price(SUBSCRIPTION_TIERS['pro']['price_monthly'])}**/month")
        for feature in SUBSCRIPTION_TIERS['pro']['features']:
            st.markdown(f"✓ {feature}")
        if st.button("Start 7-Day Trial", key="pricing_pro", use_container_width=True):
            st.switch_page("pages/signup.py")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style="text-align:center">
        <p>Analytics Assist v1.0.0 | Made with ❤️ for data enthusiasts</p>
    </div>
    """, 
    unsafe_allow_html=True
)
