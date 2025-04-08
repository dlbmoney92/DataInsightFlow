import streamlit as st

# Set page configuration - must be the first Streamlit command
st.set_page_config(
    page_title="Analytics Assist",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

import pandas as pd
import numpy as np
import os
import json
from datetime import datetime
from utils.file_processor import supported_file_types
from utils.database import initialize_database
from utils.access_control import check_and_handle_trial_expiration
from utils.subscription import SUBSCRIPTION_PLANS, format_price, get_trial_days_remaining
from utils.global_config import apply_global_css, render_footer
import uuid
from utils.custom_navigation import render_navigation, initialize_navigation

# Apply global CSS to add styling to Streamlit's native navigation
apply_global_css()

# Initialize database
initialize_database()

# Initialize session state variables if they don't exist
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if 'user' not in st.session_state:
    st.session_state.user = None

if 'user_id' not in st.session_state:
    st.session_state.user_id = None

if 'auth_token' not in st.session_state:
    st.session_state.auth_token = str(uuid.uuid4())

if 'subscription_tier' not in st.session_state:
    st.session_state.subscription_tier = "free"

if 'trial_end_date' not in st.session_state:
    st.session_state.trial_end_date = None

# Initialize OpenAI if API key is available
import os
from utils.ai_providers import AIManager
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if OPENAI_API_KEY:
    # Store in session state for persistence
    st.session_state.openai_api_key = OPENAI_API_KEY
    st.session_state.ai_manager = AIManager()

# Check if trial has expired
check_and_handle_trial_expiration()

# Initialize navigation
initialize_navigation()

# Hide Streamlit's default menu
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {
            display: none !important;
        }
    </style>
""", unsafe_allow_html=True)

# Render custom navigation bar
render_navigation()

# Main content
if not st.session_state.logged_in:
    # User is not logged in, show landing page
    
    # Hero section
    st.title("Analytics Assist")
    st.subheader("Transform Data into Insights with AI")
    
    st.markdown("""
    Welcome to Analytics Assist, your intelligent data analysis companion. Upload your data, explore 
    patterns, transform and visualize information, and leverage AI to uncover valuable insights.
    """)
    
    # Feature highlights
    st.markdown("### Key Features")
    
    # Create columns for feature highlights
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### 🧹 Effortless Data Cleaning")
        st.markdown("""
        * Automatically detect data types
        * Handle missing values and outliers
        * Standardize and normalize data
        * Smart transformations with AI suggestions
        """)
    
    with col2:
        st.markdown("#### 📊 Powerful Visualization")
        st.markdown("""
        * Interactive charts and graphs
        * Correlation analysis
        * Time series exploration
        * Custom dashboards
        """)
    
    with col3:
        st.markdown("#### 💡 AI-Powered Insights")
        st.markdown("""
        * Discover patterns and trends
        * Get intelligent recommendations
        * Answer questions about your data
        * Generate comprehensive reports
        """)
    
    # Add a CTA
    st.markdown("### Get Started Today")
    
    # Create columns for action buttons
    cta_col1, cta_col2 = st.columns(2)
    
    with cta_col1:
        if st.button("Sign Up", use_container_width=True):
            st.switch_page("pages/signup.py")
    
    with cta_col2:
        if st.button("Log In", use_container_width=True):
            st.switch_page("pages/login.py")
    
    # How it works section
    st.markdown("---")
    st.markdown("### How It Works")
    
    how_col1, how_col2, how_col3, how_col4 = st.columns(4)
    
    with how_col1:
        st.markdown("#### 1. Upload Data")
        st.markdown("Upload CSV, Excel, or other structured data files.")
    
    with how_col2:
        st.markdown("#### 2. Explore & Transform")
        st.markdown("Clean, visualize, and transform your data with ease.")
    
    with how_col3:
        st.markdown("#### 3. Generate Insights")
        st.markdown("Get AI-powered insights and analysis automatically.")
    
    with how_col4:
        st.markdown("#### 4. Export Results")
        st.markdown("Download reports, visualizations, and transformed data.")
    
    # Pricing section
    st.markdown("---")
    st.markdown("### Subscription Plans")
    
    # Create columns for pricing plans
    pricing_cols = st.columns(len(SUBSCRIPTION_PLANS))
    
    for i, (tier, plan) in enumerate(SUBSCRIPTION_PLANS.items()):
        with pricing_cols[i]:
            st.markdown(f"#### {plan['name']}")
            
            # Price
            if plan['monthly_price'] == 0:
                st.markdown("**Free**")
            else:
                st.markdown(f"**{format_price(plan['monthly_price'])}** / month")
                st.markdown(f"or {format_price(plan['annual_price'])} / year")
            
            # Features
            for feature in plan['features']:
                st.markdown(f"✓ {feature}")
            
            # Special callout for Pro trial
            if tier == "pro":
                st.markdown("**Includes 7-day free trial**")
            
            # CTA button
            if st.button(f"Choose {plan['name']}", key=f"pricing_{tier}", use_container_width=True):
                # Store the selected plan and redirect to signup
                st.session_state.selected_plan = tier
                st.switch_page("pages/subscription_selection.py")
    
    # Testimonials
    st.markdown("---")
    st.markdown("### What Our Users Say")
    
    testimonial_cols = st.columns(3)
    
    with testimonial_cols[0]:
        st.markdown("""
        > "Analytics Assist has transformed how our marketing team analyzes campaign data. The AI insights save us hours every week."
        
        *Sarah J., Marketing Director*
        """)
    
    with testimonial_cols[1]:
        st.markdown("""
        > "As a data scientist, I appreciate how quickly I can clean and prepare data for analysis. The transformation tools are exceptional."
        
        *Michael T., Data Scientist*
        """)
    
    with testimonial_cols[2]:
        st.markdown("""
        > "The visualization capabilities help me present complex findings to stakeholders in a clear, compelling way."
        
        *Elena K., Business Analyst*
        """)
else:
    # User is logged in, show dashboard
    
    # Greeting with user info
    if "user" in st.session_state and st.session_state.user:
        user_email = st.session_state.user.get('email', 'User')
        st.sidebar.success(f"Logged in as: {user_email}")
        st.sidebar.info(f"Subscription: {st.session_state.subscription_tier.capitalize()}")
        
        # Show trial information if applicable
        if st.session_state.subscription_tier == "pro" and st.session_state.trial_end_date:
            days_remaining = get_trial_days_remaining()
            if days_remaining > 0:
                st.sidebar.warning(f"Pro Trial: {days_remaining} days remaining")
    
    # Dashboard header
    st.title("Analytics Assist Dashboard")
    
    # Create layout with two columns - one for recent activity, one for quick actions
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Recent Projects")
        
        # Get recent datasets
        from utils.database import list_datasets
        datasets = list_datasets()
        
        if datasets:
            # Convert to DataFrame for display
            df_datasets = pd.DataFrame(datasets)
            
            # Format the creation date and rename columns for display
            if 'created_at' in df_datasets.columns:
                df_datasets['created_at'] = pd.to_datetime(df_datasets['created_at']).dt.strftime('%Y-%m-%d %H:%M')
            
            # Rename columns for better display
            display_df = df_datasets.rename(columns={
                'id': 'ID',
                'name': 'Name',
                'description': 'Description',
                'file_name': 'File Name',
                'file_type': 'File Type',
                'created_at': 'Created At'
            })
            
            # Convert file type to uppercase
            if 'File Type' in display_df.columns:
                display_df['File Type'] = display_df['File Type'].str.upper()
            
            # Display the datasets in a table
            st.dataframe(
                display_df[['Name', 'File Name', 'File Type', 'Created At']],
                hide_index=True,
                use_container_width=True
            )
            
            # Load selected dataset
            if st.button("Open Selected Project"):
                st.switch_page("pages/01_Upload_Data.py")
        else:
            st.info("You haven't created any projects yet. Upload data to get started.")
    
    with col2:
        st.subheader("Quick Actions")
        
        # Upload data button
        if st.button("Upload Data", use_container_width=True):
            st.switch_page("pages/01_Upload_Data.py")
        
        # Manage datasets button
        if st.button("Manage Datasets", use_container_width=True):
            st.switch_page("pages/09_Dataset_Management.py")
        
        # View insights button
        if st.button("View Insights", use_container_width=True):
            st.switch_page("pages/05_Insights_Dashboard.py")
        
        # Account settings
        if st.button("Account Settings", use_container_width=True):
            st.switch_page("pages/account.py")
        
        # Subscription management
        if st.button("Manage Subscription", use_container_width=True):
            st.switch_page("pages/subscription.py")
        
        # Logout
        if st.button("Logout", use_container_width=True):
            # Clear session state
            for key in ["logged_in", "user", "user_id", "auth_token"]:
                if key in st.session_state:
                    del st.session_state[key]
            
            # Redirect to home page
            st.success("Logged out successfully!")
            st.rerun()
    
    # Usage statistics
    st.markdown("---")
    st.subheader("Account Usage")
    
    # Get subscription limits
    from utils.access_control import check_access
    dataset_limit = check_access("dataset_count")
    
    # Get current usage
    from utils.access_control import get_dataset_count
    current_count = get_dataset_count(st.session_state.get("user_id", None))
    
    # Usage overview with progress bars
    usage_col1, usage_col2 = st.columns(2)
    
    with usage_col1:
        st.markdown("#### Dataset Storage")
        if dataset_limit > 0:
            progress = min(1.0, current_count / dataset_limit)
            st.progress(progress, f"Datasets: {current_count} / {dataset_limit}")
        else:
            st.progress(0.0, "Datasets: Unlimited")
        
        st.markdown(f"You are currently using {current_count} datasets.")
        
        if current_count >= dataset_limit and dataset_limit > 0:
            st.warning("You've reached your dataset limit. Consider upgrading your subscription.")
            if st.button("Upgrade Now"):
                st.switch_page("pages/subscription.py")
    
    with usage_col2:
        st.markdown("#### Subscription Status")
        
        # Show different status based on tier
        if st.session_state.subscription_tier == "free":
            st.info("You're on the Free tier. Upgrade to access more features.")
            if st.button("View Pro Features"):
                st.switch_page("pages/subscription.py")
        elif st.session_state.subscription_tier == "pro":
            if st.session_state.trial_end_date:
                days_remaining = get_trial_days_remaining()
                if days_remaining > 0:
                    st.warning(f"Pro Trial: {days_remaining} days remaining")
                    if st.button("Activate Pro"):
                        st.switch_page("pages/subscription.py")
                else:
                    st.error("Your Pro trial has expired. Please upgrade to continue using Pro features.")
                    if st.button("Upgrade Now"):
                        st.switch_page("pages/subscription.py")
            else:
                st.success("You're on the Pro plan. Enjoy all features!")
        elif st.session_state.subscription_tier == "enterprise":
            st.success("You're on the Enterprise plan. Enjoy unlimited features!")
        
        # Show contact support button
        if st.button("Contact Support"):
            st.switch_page("pages/contact_us.py")

# Render footer
render_footer()
