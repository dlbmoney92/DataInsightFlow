import streamlit as st
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

# Set page configuration - must be the first Streamlit command
st.set_page_config(
    page_title="Analytics Assist",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply global CSS to add styling to Streamlit's native navigation
apply_global_css()

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
if 'user_role' not in st.session_state:
    st.session_state.user_role = "user"

# Use custom navigation in the sidebar
from utils.custom_navigation import render_navigation, initialize_navigation

# Initialize navigation
initialize_navigation()

# Render custom navigation bar
render_navigation()

# Add CSS for sidebar behavior
with st.sidebar:
    st.markdown("""
    <style>
    /* Default styles for sidebar - expanded state */
    div[data-testid="stSidebarUserContent"] > div:nth-of-type(1) { display: none; }
    div[data-testid="stSidebarUserContent"] > div:nth-of-type(2) { display: block; }
    
    /* Collapsed sidebar styles */
    [data-collapsed="true"] div[data-testid="stSidebarUserContent"] > div:nth-of-type(1) { display: block; }
    [data-collapsed="true"] div[data-testid="stSidebarUserContent"] > div:nth-of-type(2) { display: none; }
    </style>
    """, unsafe_allow_html=True)

# Main content
# Check if user is logged in
if "logged_in" in st.session_state and st.session_state.logged_in:
    # Check for login message
    if "login_message" in st.session_state:
        st.success(st.session_state.login_message)
        # Remove the message after displaying it once
        del st.session_state.login_message
        
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
        tier_info = SUBSCRIPTION_PLANS[current_tier]
        
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
    # Splash screen for anonymous users
    # First add the CSS styles
    st.markdown(
        """
        <style>
        .splash-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            padding: 2rem;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            border-radius: 10px;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .splash-logo {
            font-size: 3.5rem;
            font-weight: bold;
            margin-bottom: 1rem;
            background: linear-gradient(to right, #3a7bd5, #00d2ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .splash-tagline {
            font-size: 1.5rem;
            margin-bottom: 2rem;
            color: #4a4a4a;
        }
        .cta-buttons {
            display: flex;
            gap: 1rem;
            margin-top: 2rem;
        }
        .main-cta {
            background: linear-gradient(to right, #3a7bd5, #00d2ff);
            color: white;
            padding: 0.8rem 2rem;
            border-radius: 50px;
            font-weight: bold;
            text-decoration: none;
            border: none;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .main-cta:hover {
            transform: scale(1.05);
            box-shadow: 0 4px 12px rgba(58, 123, 213, 0.3);
        }
        .secondary-cta {
            background: white;
            color: #3a7bd5;
            border: 2px solid #3a7bd5;
            padding: 0.8rem 2rem;
            border-radius: 50px;
            font-weight: bold;
            text-decoration: none;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .secondary-cta:hover {
            background: #f0f7ff;
            transform: scale(1.05);
        }
        .or-divider {
            display: flex;
            align-items: center;
            color: #777;
            margin: 1.5rem 0;
        }
        .or-divider::before, .or-divider::after {
            content: '';
            flex: 1;
            border-bottom: 1px solid #ddd;
            margin: 0 10px;
        }
        </style>
        """, 
        unsafe_allow_html=True
    )
    
    # Then create the splash container
    st.markdown(
        """
        <div class="splash-container">
            <div class="splash-logo">Analytics Assist</div>
            <div class="splash-tagline">Transform your data into actionable insights with AI</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Add the step cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(
            """
            <div style="background: rgba(255, 255, 255, 0.1); padding: 1.5rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); text-align: center;">
                <div style="font-size: 2.5rem; margin-bottom: 1rem;">📤</div>
                <div style="font-weight: bold; margin-bottom: 0.5rem; color: inherit;">Upload</div>
                <p style="color: inherit;">Upload any data source with our smart importer</p>
            </div>
            """, 
            unsafe_allow_html=True
        )
    
    with col2:
        st.markdown(
            """
            <div style="background: rgba(255, 255, 255, 0.1); padding: 1.5rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); text-align: center;">
                <div style="font-size: 2.5rem; margin-bottom: 1rem;">🧹</div>
                <div style="font-weight: bold; margin-bottom: 0.5rem; color: inherit;">Transform</div>
                <p style="color: inherit;">Clean and prepare your data with AI assistance</p>
            </div>
            """, 
            unsafe_allow_html=True
        )
    
    with col3:
        st.markdown(
            """
            <div style="background: rgba(255, 255, 255, 0.1); padding: 1.5rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); text-align: center;">
                <div style="font-size: 2.5rem; margin-bottom: 1rem;">📊</div>
                <div style="font-weight: bold; margin-bottom: 0.5rem; color: inherit;">Visualize</div>
                <p style="color: inherit;">Create beautiful, insightful visualizations</p>
            </div>
            """, 
            unsafe_allow_html=True
        )
    
    with col4:
        st.markdown(
            """
            <div style="background: rgba(255, 255, 255, 0.1); padding: 1.5rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); text-align: center;">
                <div style="font-size: 2.5rem; margin-bottom: 1rem;">💡</div>
                <div style="font-weight: bold; margin-bottom: 0.5rem; color: inherit;">Discover</div>
                <p style="color: inherit;">Gain valuable insights from your data</p>
            </div>
            """, 
            unsafe_allow_html=True
        )
    
    # Add the example analytics section
    st.subheader("Example Analytics")
    
    # Use columns for the example analytics cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Created box with color and visualization example
        st.markdown(
            """
            <div style="background-color: #f0f7ff; padding: 20px; border-radius: 10px; text-align: center; margin-bottom: 10px;">
                <div style="font-size: 40px; color: #3a7bd5; margin-bottom: 10px;">📊</div>
                <div style="height: 100px; background-color: #e6eefa; border-radius: 5px; display: flex; align-items: center; justify-content: center; margin-bottom: 10px;">
                    <div style="width: 80%; height: 80px; background: linear-gradient(45deg, #ff9a9e 0%, #fad0c4 99%, #fad0c4 100%); border-radius: 5px;"></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.markdown("**Correlation Analysis**")
        st.markdown("Discover relationships between variables")
    
    with col2:
        # Created box with color and visualization example
        st.markdown(
            """
            <div style="background-color: #f0fff7; padding: 20px; border-radius: 10px; text-align: center; margin-bottom: 10px;">
                <div style="font-size: 40px; color: #3ab795; margin-bottom: 10px;">📈</div>
                <div style="height: 100px; background-color: #e6faf2; border-radius: 5px; display: flex; align-items: center; justify-content: center; margin-bottom: 10px;">
                    <div style="width: 80%; height: 80px; background: linear-gradient(to right, #a1c4fd 0%, #c2e9fb 100%); border-radius: 5px;"></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.markdown("**Sales Performance**")
        st.markdown("Track sales trends and forecasts")
    
    with col3:
        # Created box with color and visualization example
        st.markdown(
            """
            <div style="background-color: #fff7f0; padding: 20px; border-radius: 10px; text-align: center; margin-bottom: 10px;">
                <div style="font-size: 40px; color: #d57a3a; margin-bottom: 10px;">⚠️</div>
                <div style="height: 100px; background-color: #faf0e6; border-radius: 5px; display: flex; align-items: center; justify-content: center; margin-bottom: 10px;">
                    <div style="width: 80%; height: 80px; background: linear-gradient(to right, #ffecd2 0%, #fcb69f 100%); border-radius: 5px;"></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.markdown("**Anomaly Detection**")
        st.markdown("Automatically find outliers in your data")
    
    # Add the platform description
    st.markdown("### All Your Data Tools in One Platform")
    st.markdown("Analytics Assist combines powerful data analysis with an AI assistant to help you make better decisions.")
    st.markdown("Get started today and join thousands of users who trust Analytics Assist with their data needs.")
    
    # Sign-up container
    st.markdown(
        """
        <style>
        .signup-container {
            background: rgba(255, 255, 255, 0.1);
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin-bottom: 2rem;
            text-align: center;
        }
        </style>
        <div class="signup-container">
            <h2 style="color: inherit;">Start Your Analytics Journey Today</h2>
            <p style="color: inherit;">Create an account to access all features and begin analyzing your data</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Sign-up buttons
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if st.button("Create an Account", use_container_width=True, key="main_signup"):
            st.switch_page("pages/signup.py")
        

    
    # Feature highlights
    st.markdown("---")
    st.markdown("## Why Choose Analytics Assist")
    
    feature_cols = st.columns(3)
    
    with feature_cols[0]:
        st.markdown("### 🤖 AI-Powered Analysis")
        st.markdown("""
        - Get intelligent data cleaning suggestions
        - Automatically detect patterns and anomalies
        - Generate natural language insights
        - Learn from your feedback
        - Receive personalized recommendations
        """)
    
    with feature_cols[1]:
        st.markdown("### 🔒 Secure & Private")
        st.markdown("""
        - Your data stays private and secure
        - Role-based access controls
        - Compliant with data protection standards
        - Fine-grained permission management
        - Complete audit trail
        """)
    
    with feature_cols[2]:
        st.markdown("### 🚀 Enterprise Ready")
        st.markdown("""
        - Scales to handle large datasets
        - Integration with existing systems
        - Collaboration features for teams
        - Custom reporting options
        - Priority support available
        """)
    
    # Pricing section
    st.markdown("---")
    st.markdown("## Choose Your Plan")
    
    pricing_cols = st.columns(3)
    
    with pricing_cols[0]:
        st.markdown(
            """
            <div style="padding: 1.5rem; border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 8px; height: 100%;">
                <h3 style="color: inherit;">Free</h3>
                <div style="font-size: 1.8rem; margin: 1rem 0; color: inherit;">$0<span style="font-size: 1rem;">/month</span></div>
                <ul style="list-style-type: none; padding-left: 0; color: inherit;">
            """, 
            unsafe_allow_html=True
        )
        for feature in SUBSCRIPTION_PLANS['free']['features']:
            st.markdown(f"<li style='color: inherit;'>✓ {feature}</li>", unsafe_allow_html=True)
        st.markdown("</ul>", unsafe_allow_html=True)
        if st.button("Get Started Free", key="pricing_free", use_container_width=True):
            st.switch_page("pages/signup.py")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with pricing_cols[1]:
        st.markdown(
            """
            <div style="padding: 1.5rem; border: 1px solid #3a7bd5; border-radius: 8px; box-shadow: 0 4px 12px rgba(58, 123, 213, 0.2); height: 100%;">
                <h3 style="color: inherit;">Basic</h3>
                <div style="font-size: 1.8rem; margin: 1rem 0; color: inherit;">$9.99<span style="font-size: 1rem;">/month</span></div>
                <ul style="list-style-type: none; padding-left: 0; color: inherit;">
            """, 
            unsafe_allow_html=True
        )
        for feature in SUBSCRIPTION_PLANS['basic']['features']:
            st.markdown(f"<li style='color: inherit;'>✓ {feature}</li>", unsafe_allow_html=True)
        st.markdown("</ul>", unsafe_allow_html=True)
        if st.button("Choose Basic", key="pricing_basic", use_container_width=True):
            st.switch_page("pages/signup.py")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with pricing_cols[2]:
        st.markdown(
            """
            <div style="padding: 1.5rem; border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 8px; height: 100%;">
                <h3 style="color: inherit;">Pro</h3>
                <div style="font-size: 1.8rem; margin: 1rem 0; color: inherit;">$29.99<span style="font-size: 1rem;">/month</span></div>
                <ul style="list-style-type: none; padding-left: 0; color: inherit;">
            """, 
            unsafe_allow_html=True
        )
        for feature in SUBSCRIPTION_PLANS['pro']['features']:
            st.markdown(f"<li style='color: inherit;'>✓ {feature}</li>", unsafe_allow_html=True)
        st.markdown("</ul>", unsafe_allow_html=True)
        if st.button("Start 7-Day Trial", key="pricing_pro", use_container_width=True):
            st.switch_page("pages/signup.py")
        st.markdown("</div>", unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style="text-align:center">
        <p style="color: inherit;">
            Analytics Assist v1.0.0 | Made with ❤️ for data enthusiasts<br/>
            <a href="pages/terms_of_service.py" target="_self" style="color: #4361ee; text-decoration: none; margin: 0 10px;">Terms of Service</a> | 
            <a href="pages/privacy_policy.py" target="_self" style="color: #4361ee; text-decoration: none; margin: 0 10px;">Privacy Policy</a>
        </p>
        <p style="font-size: 0.8rem; color: rgba(255, 255, 255, 0.6); margin-top: 5px;">© 2025 Analytics Assist. All rights reserved.</p>
    </div>
    """, 
    unsafe_allow_html=True
)
