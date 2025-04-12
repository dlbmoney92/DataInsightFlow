import streamlit as st

# Set page configuration - must be the first Streamlit command
st.set_page_config(
    page_title="Analytics Assist",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add Google Analytics tracking code using direct HTML approach
from utils.direct_ga import add_ga_tag
add_ga_tag()

import pandas as pd
import numpy as np
import os
import json
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from utils.file_processor import supported_file_types
from utils.database import initialize_database
from utils.feedback import initialize_feedback_database
from utils.access_control import check_and_handle_trial_expiration
from utils.subscription import SUBSCRIPTION_PLANS, format_price, get_trial_days_remaining
from utils.global_config import apply_global_css, render_footer
import uuid
from utils.custom_navigation import render_navigation, initialize_navigation
# Removed quick start wizard functionality
# from utils.quick_start import (
#     initialize_quick_start, 
#     should_show_quick_start, 
#     show_quick_start_wizard,
#     add_quick_start_button
# )

# Create demo data and visualizations for the landing page
def create_sample_chart(chart_type='bar'):
    """Create sample charts for landing page demonstration"""
    if chart_type == 'bar':
        # Sample sales data
        categories = ['Electronics', 'Apparel', 'Home Goods', 'Sports', 'Beauty']
        values = [42000, 28500, 19200, 15700, 23400]
        
        fig = px.bar(
            x=categories,
            y=values,
            title="Sample Sales by Category",
            labels={'x': 'Category', 'y': 'Sales ($)'},
            color=values,
            color_continuous_scale='Viridis',
        )
        fig.update_layout(
            height=300,
            margin=dict(l=10, r=10, t=50, b=40),
            coloraxis_showscale=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            title_font=dict(size=16),
            title_x=0.5
        )
        return fig
    
    elif chart_type == 'line':
        # Sample time series data
        dates = pd.date_range(start='2023-01-01', periods=12, freq='ME')
        values = [10, 13, 15, 22, 28, 32, 30, 28, 25, 30, 35, 42]
        
        fig = px.line(
            x=dates,
            y=values,
            title="Sales Growth Over Time",
            labels={'x': 'Month', 'y': 'Revenue ($K)'},
            markers=True,
        )
        fig.update_layout(
            height=300,
            margin=dict(l=10, r=10, t=50, b=40),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            title_font=dict(size=16),
            title_x=0.5
        )
        return fig
    
    elif chart_type == 'scatter':
        # Sample correlation data
        np.random.seed(42)
        marketing = np.random.normal(50, 15, 30)
        sales = marketing * 2.3 + np.random.normal(100, 25, 30)
        
        fig = px.scatter(
            x=marketing,
            y=sales,
            title="Marketing Spend vs. Sales",
            labels={'x': 'Marketing ($K)', 'y': 'Sales ($K)'},
            color=marketing,
            color_continuous_scale='Viridis',
            trendline="ols"
        )
        fig.update_layout(
            height=300,
            margin=dict(l=10, r=10, t=50, b=40),
            coloraxis_showscale=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            title_font=dict(size=16),
            title_x=0.5
        )
        return fig
    
    elif chart_type == 'pie':
        # Sample market share data
        labels = ['Product A', 'Product B', 'Product C', 'Product D', 'Product E']
        values = [38, 27, 18, 10, 7]
        
        fig = px.pie(
            values=values,
            names=labels,
            title="Market Share Analysis",
            color_discrete_sequence=px.colors.sequential.Viridis,
        )
        fig.update_layout(
            height=300,
            margin=dict(l=10, r=10, t=50, b=30),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            title_font=dict(size=16),
            title_x=0.5,
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
        )
        return fig
    
    elif chart_type == 'heatmap':
        # Sample correlation matrix
        corr_data = np.array([
            [1.0, 0.8, 0.3, -0.2, 0.5],
            [0.8, 1.0, 0.4, -0.1, 0.6],
            [0.3, 0.4, 1.0, 0.7, 0.2],
            [-0.2, -0.1, 0.7, 1.0, -0.3],
            [0.5, 0.6, 0.2, -0.3, 1.0]
        ])
        
        labels = ['Sales', 'Marketing', 'Customer Satisfaction', 'Returns', 'Social Media']
        
        fig = px.imshow(
            corr_data,
            x=labels,
            y=labels,
            title="Variable Correlation Analysis",
            color_continuous_scale='Viridis',
            text_auto=".2f"
        )
        
        fig.update_layout(
            height=300,
            margin=dict(l=10, r=10, t=50, b=10),
            title_font=dict(size=16),
            title_x=0.5,
            coloraxis_showscale=False
        )
        return fig

# Apply global CSS to add styling to Streamlit's native navigation
apply_global_css()

# Google Analytics is now added directly at the top of the page
# No need to call add_google_analytics() here anymore

# Initialize database
initialize_database()

# Initialize feedback database
initialize_feedback_database()

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

# Display quick feedback option in the sidebar if user is logged in
if st.session_state.logged_in:
    st.sidebar.markdown("---")
    from utils.feedback import display_quick_feedback
    display_quick_feedback("home_page", "sidebar")

# Main content
if not st.session_state.logged_in:
    # User is not logged in, show landing page
    
    # Enhanced Hero section with gradient background
    st.markdown("""
    <div style="background: linear-gradient(to right, #1e3c72, #2a5298); padding: 40px; border-radius: 10px; text-align: center; margin-bottom: 20px;">
        <h1 style="color: white; margin-bottom: 10px; font-size: 3.5em;">Analytics Assist</h1>
        <h3 style="color: white; margin-bottom: 20px; font-weight: 300;">Transform Data into Insights with AI</h3>
        <p style="color: white; font-size: 1.2em; margin-bottom: 30px; max-width: 800px; margin-left: auto; margin-right: auto;">
            Your intelligent data analysis companion. Upload your data, explore patterns, 
            transform and visualize information, and leverage AI to uncover valuable insights.
        </p>
        <div style="background: rgba(255,255,255,0.2); width: fit-content; margin: 0 auto; padding: 10px 20px; border-radius: 30px;">
            <span style="color: white; font-weight: bold;">✨ AI-Powered Analytics Made Simple ✨</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Feature highlights with visual examples
    st.markdown("### Key Features")
    
    # Showcase visual analytics examples
    st.markdown("#### 📊 Powerful Visualizations & Analytics")
    
    # Create a showcase row with visualization examples
    viz_col1, viz_col2, viz_col3 = st.columns(3)
    
    with viz_col1:
        st.plotly_chart(create_sample_chart('bar'), use_container_width=True)
    
    with viz_col2:
        st.plotly_chart(create_sample_chart('line'), use_container_width=True)
    
    with viz_col3:
        st.plotly_chart(create_sample_chart('scatter'), use_container_width=True)
    
    # Add a second row of visualizations
    viz_col4, viz_col5, viz_col6 = st.columns(3)
    
    with viz_col4:
        st.plotly_chart(create_sample_chart('pie'), use_container_width=True)
    
    with viz_col5:
        st.plotly_chart(create_sample_chart('heatmap'), use_container_width=True)
    
    with viz_col6:
        # Sample AI insights presentation
        st.markdown("#### AI Insights")
        with st.container(border=True):
            st.markdown("⭐⭐⭐⭐ **High Importance**")
            st.markdown("**Seasonal Sales Pattern**")
            st.markdown("*Sales consistently increase by 28% during Q4 each year, suggesting opportunity for increased inventory planning.*")
        
        with st.container(border=True):
            st.markdown("⭐⭐⭐ **Medium Importance**")
            st.markdown("**Customer Segment Analysis**")
            st.markdown("*Premium segment customers have 3.2x higher lifetime value but are 24% more sensitive to delivery delays.*")
    
    # Create columns for feature highlights text
    st.markdown("### Comprehensive Analytics Toolkit")
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
    
    # Add an attractive CTA with visual elements
    st.markdown("""
    <div style="background: linear-gradient(to right, #4b6cb7, #182848); padding: 30px; border-radius: 10px; text-align: center; margin: 30px 0;">
        <h2 style="color: white; margin-bottom: 15px;">Ready to Transform Your Data Analytics?</h2>
        <p style="color: white; font-size: 1.1em; margin-bottom: 25px;">
            Join thousands of analysts and data scientists who are already using Analytics Assist
            to unlock the power of their data. Get started in less than 2 minutes.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create columns for action buttons
    cta_col1, cta_col2 = st.columns(2)
    
    # Use custom button styling
    with cta_col1:
        # Custom styled button with container
        if st.button("✨ Create Free Account", key="signup_main_cta", use_container_width=True):
            st.switch_page("pages/signup.py")
        st.caption("No credit card required")
    
    with cta_col2:
        if st.button("Already have an account? Log In", key="login_main_cta", use_container_width=True):
            st.switch_page("pages/login.py")
    
    # How it works section
    st.markdown("---")
    st.markdown("### How It Works")
    
    how_col1, how_col2, how_col3, how_col4 = st.columns(4)
    
    with how_col1:
        st.markdown("#### 1. Upload Data")
        st.markdown("Upload CSV, Excel, or other structured data files.")
        
        # Visual icon with container
        with st.container(border=True, height=120):
            st.markdown(
                """
                <div style="text-align: center; font-size: 40px; margin-bottom: 10px;">
                    📤
                </div>
                <div style="text-align: center; font-style: italic;">
                    Drag & drop or browse files
                </div>
                """, 
                unsafe_allow_html=True
            )
    
    with how_col2:
        st.markdown("#### 2. Explore & Transform")
        st.markdown("Clean, visualize, and transform your data with ease.")
        
        # Visual icon with container
        with st.container(border=True, height=120):
            st.markdown(
                """
                <div style="text-align: center; font-size: 40px; margin-bottom: 10px;">
                    🔍
                </div>
                <div style="text-align: center; font-style: italic;">
                    Interactive data exploration
                </div>
                """, 
                unsafe_allow_html=True
            )
    
    with how_col3:
        st.markdown("#### 3. Generate Insights")
        st.markdown("Get AI-powered insights and analysis automatically.")
        
        # Visual icon with container
        with st.container(border=True, height=120):
            st.markdown(
                """
                <div style="text-align: center; font-size: 40px; margin-bottom: 10px;">
                    💡
                </div>
                <div style="text-align: center; font-style: italic;">
                    AI insight generation
                </div>
                """, 
                unsafe_allow_html=True
            )
    
    with how_col4:
        st.markdown("#### 4. Export Results")
        st.markdown("Download reports, visualizations, and transformed data.")
        
        # Visual icon with container
        with st.container(border=True, height=120):
            st.markdown(
                """
                <div style="text-align: center; font-size: 40px; margin-bottom: 10px;">
                    📊
                </div>
                <div style="text-align: center; font-style: italic;">
                    Professional reports & exports
                </div>
                """, 
                unsafe_allow_html=True
            )
    
    # Enhanced Pricing section with visual elements
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; margin-bottom: 30px;">
        <h2>Choose the Right Plan for Your Needs</h2>
        <p style="font-size: 1.1em; color: #666; margin-top: 5px;">
            All plans include our core analytics features. Upgrade for advanced capabilities.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create columns for pricing plans
    pricing_cols = st.columns(len(SUBSCRIPTION_PLANS))
    
    # Color schemes for different tiers
    color_schemes = {
        "free": {"gradient": "linear-gradient(135deg, #f5f7fa, #c3cfe2)", "text": "#2c3e50", "highlight": "#3498db"},
        "basic": {"gradient": "linear-gradient(135deg, #e0c3fc, #8ec5fc)", "text": "#2c3e50", "highlight": "#8e44ad"},
        "pro": {"gradient": "linear-gradient(135deg, #a1c4fd, #c2e9fb)", "text": "#2c3e50", "highlight": "#2980b9"},
        "enterprise": {"gradient": "linear-gradient(135deg, #5ee7df, #b490ca)", "text": "#2c3e50", "highlight": "#6c5ce7"}
    }
    
    for i, (tier, plan) in enumerate(SUBSCRIPTION_PLANS.items()):
        with pricing_cols[i]:
            colors = color_schemes.get(tier, color_schemes["free"])
            
            # Pricing card with gradient background
            with st.container(border=True):
                st.markdown(f"""
                <div style="text-align: center; background: {colors['gradient']}; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
                    <h3 style="color: {colors['text']}; margin-bottom: 5px;">{plan['name']}</h3>
                </div>
                """, unsafe_allow_html=True)
                
                # Price display
                if plan['monthly_price'] == 0:
                    st.markdown("<div style='text-align: center; margin: 15px 0;'><span style='font-size: 28px; font-weight: bold;'>Free</span></div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style='text-align: center; margin: 15px 0;'>
                        <span style='font-size: 28px; font-weight: bold;'>{format_price(plan['monthly_price'])}</span>
                        <span style='font-size: 16px;'> / month</span><br>
                        <span style='font-size: 14px; color: #666;'>or {format_price(plan['annual_price'])} / year</span>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Feature list
                st.markdown("<div style='margin: 20px 0;'>", unsafe_allow_html=True)
                for feature in plan['features']:
                    st.markdown(f"""
                    <div style='display: flex; margin-bottom: 8px; align-items: center;'>
                        <div style='color: {colors["highlight"]}; margin-right: 8px; font-size: 18px;'>✓</div>
                        <div>{feature}</div>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
                
                # Special callout for Pro trial
                if tier == "pro":
                    st.markdown(f"""
                    <div style='background-color: rgba(0,0,0,0.05); padding: 10px; border-radius: 5px; text-align: center; margin: 15px 0;'>
                        <span style='font-weight: bold; color: {colors["highlight"]};'>Includes 7-day free trial</span>
                    </div>
                    """, unsafe_allow_html=True)
                
                # CTA button
                if st.button(f"Choose {plan['name']}", key=f"pricing_{tier}", use_container_width=True):
                    # Store the selected plan and redirect to signup
                    st.session_state.selected_plan = tier
                    st.switch_page("pages/subscription_selection.py")
    
    # Testimonials
    st.markdown("---")
    st.markdown("### What Our Users Say")
    
    # Create testimonial cards with visual elements
    testimonial_cols = st.columns(3)
    
    with testimonial_cols[0]:
        with st.container(border=True):
            st.markdown("""
            <div style="text-align: center; margin-bottom: 15px;">
                <span style="font-size: 40px;">⭐⭐⭐⭐⭐</span>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            > "Analytics Assist has transformed how our marketing team analyzes campaign data. The AI insights save us hours every week."
            """)
            
            st.markdown("""
            <div style="text-align: right; margin-top: 15px;">
                <img src="https://img.icons8.com/fluency/48/000000/user-female-circle.png" width="30" 
                style="border-radius: 50%; vertical-align: middle; margin-right: 5px;">
                <em>Sage B., Marketing Director</em>
            </div>
            """, unsafe_allow_html=True)
    
    with testimonial_cols[1]:
        with st.container(border=True):
            st.markdown("""
            <div style="text-align: center; margin-bottom: 15px;">
                <span style="font-size: 40px;">⭐⭐⭐⭐⭐</span>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            > "As a data scientist, I appreciate how quickly I can clean and prepare data for analysis. The transformation tools are exceptional."
            """)
            
            st.markdown("""
            <div style="text-align: right; margin-top: 15px;">
                <img src="https://img.icons8.com/fluency/48/000000/user-male-circle.png" width="30" 
                style="border-radius: 50%; vertical-align: middle; margin-right: 5px;">
                <em>Quan F., Data Scientist</em>
            </div>
            """, unsafe_allow_html=True)
    
    with testimonial_cols[2]:
        with st.container(border=True):
            st.markdown("""
            <div style="text-align: center; margin-bottom: 15px;">
                <span style="font-size: 40px;">⭐⭐⭐⭐⭐</span>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            > "The visualization capabilities help me present complex findings to stakeholders in a clear, compelling way."
            """)
            
            st.markdown("""
            <div style="text-align: right; margin-top: 15px;">
                <img src="https://img.icons8.com/fluency/48/000000/user-female-circle.png" width="30" 
                style="border-radius: 50%; vertical-align: middle; margin-right: 5px;">
                <em>Elena K., Business Analyst</em>
            </div>
            """, unsafe_allow_html=True)
else:
    # User is logged in, show dashboard
    
    # Quick start wizard functionality removed
    # Removed: initialize_quick_start()
    # Removed: if should_show_quick_start(): show_quick_start_wizard()
    # Removed: add_quick_start_button()
    
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
