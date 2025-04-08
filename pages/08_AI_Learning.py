import streamlit as st

# Set page configuration - must be the first Streamlit command
st.set_page_config(
    page_title="AI Learning | Analytics Assist",
    page_icon="🧠",
    layout="wide"
)

import pandas as pd
import numpy as np
import json
import plotly.express as px
import plotly.graph_objects as go
from utils.ai_learning import display_learning_preferences_form, get_ai_learning_stats
from utils.access_control import check_access
from utils.ai_providers import get_ai_manager, AIProvider
from utils.auth_redirect import require_auth
from utils.global_config import apply_global_css
from utils.custom_navigation import render_navigation, initialize_navigation

# Apply global CSS
apply_global_css()

# Initialize navigation
initialize_navigation()

# Hide Streamlit's default multipage navigation menu
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {
            display: none !important;
        }
    </style>
""", unsafe_allow_html=True)

# Render custom navigation bar
render_navigation()

# Check authentication
if not require_auth():
    st.stop()

def app():
    st.title("AI Learning System")
    
    # Show user info if authenticated
    if "user" in st.session_state:
        st.sidebar.success(f"Logged in as: {st.session_state.user.get('email', 'User')}")
        st.sidebar.info(f"Subscription: {st.session_state.subscription_tier.capitalize()}")
    
    # Check access level
    if not check_access("ai_learning"):
        st.warning("AI Learning is available on Pro and Enterprise plans only.")
        
        st.markdown("""
        ### Upgrade to access AI Learning
        
        The AI Learning System allows Analytics Assist to learn from your data and preferences 
        to provide better insights and recommendations over time.
        
        Upgrade to Pro or Enterprise to access this feature.
        """)
        
        if st.button("View Subscription Plans"):
            st.switch_page("pages/subscription.py")
        
        return
    
    # Check if AI is available
    ai_manager = get_ai_manager()
    if not ai_manager.is_available():
        st.warning("AI features require an OpenAI API key. Please add your API key to use this feature.")
        
        # Add OpenAI key input
        st.subheader("Add OpenAI API Key")
        api_key = st.text_input("OpenAI API Key", type="password")
        
        if st.button("Save API Key") and api_key:
            st.session_state.temp_openai_key = api_key
            st.success("API key saved for this session. Please restart the application for full integration.")
        
        return
    
    # Main content for AI Learning
    st.markdown("""
    The AI Learning System collects feedback on insights, visualizations, and transformations 
    to improve recommendations and results over time.
    """)
    
    # Create tabs for different sections
    tab1, tab2, tab3 = st.tabs(["Learning Status", "Preferences", "Data Performance"])
    
    with tab1:
        st.header("Learning Status")
        
        # Get AI learning stats
        stats = get_ai_learning_stats()
        
        if stats:
            # Display stats in columns
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Feedback Collected", stats.get("total_feedback", 0))
            
            with col2:
                st.metric("Transformations Learned", stats.get("transformations_count", 0))
            
            with col3:
                avg_rating = stats.get("average_rating", 0)
                st.metric("Average Rating", f"{avg_rating:.1f}/5")
            
            with col4:
                st.metric("Learning Preferences Set", stats.get("preferences_count", 0))
            
            # Show learning improvement over time
            st.subheader("Learning Progress")
            
            if "rating_history" in stats and stats["rating_history"]:
                # Convert to DataFrame for plotting
                history_df = pd.DataFrame(stats["rating_history"])
                
                # Create a line chart showing the trend
                fig = px.line(
                    history_df, 
                    x="date", 
                    y="average_rating",
                    title="User Feedback Ratings Over Time",
                    labels={"date": "Date", "average_rating": "Average Rating"}
                )
                
                # Customize the chart
                fig.update_layout(
                    yaxis=dict(range=[0, 5]),
                    hovermode="x unified"
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Not enough data collected to show learning progress over time.")
            
            # Show feedback by category
            st.subheader("Feedback by Category")
            
            if "feedback_by_category" in stats and stats["feedback_by_category"]:
                # Convert to DataFrame for plotting
                category_df = pd.DataFrame(
                    list(stats["feedback_by_category"].items()),
                    columns=["Category", "Count"]
                )
                
                # Create a bar chart
                fig = px.bar(
                    category_df,
                    x="Category",
                    y="Count",
                    title="Feedback Distribution by Category",
                    color="Category"
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No category data available yet.")
        else:
            st.info("No learning data available yet. Use the system more and provide feedback to see stats here.")
    
    with tab2:
        st.header("AI Learning Preferences")
        
        st.markdown("""
        Set your preferences for AI-generated content. These preferences will be used to tailor 
        insights, visualizations, and transformations to your specific needs and preferences.
        """)
        
        # Display preferences form
        display_learning_preferences_form()
    
    with tab3:
        st.header("Data Performance Analysis")
        
        # Check if a dataset is loaded
        if "dataset" not in st.session_state or st.session_state.dataset is None:
            st.info("Load a dataset to see how well AI works with your data.")
            
            if st.button("Upload Data"):
                st.switch_page("pages/01_Upload_Data.py")
        else:
            # Show analysis of AI performance on the current dataset
            st.subheader("AI Performance with Current Dataset")
            
            # Get the current dataset
            df = st.session_state.dataset
            
            # Basic stats
            st.markdown(f"**Dataset Shape**: {df.shape[0]} rows × {df.shape[1]} columns")
            
            # Calculate AI confidence based on data characteristics
            numeric_columns = len(df.select_dtypes(include=np.number).columns)
            categorical_columns = len(df.select_dtypes(include=["object", "category"]).columns)
            datetime_columns = len([col for col in df.columns if pd.api.types.is_datetime64_any_dtype(df[col])])
            
            # Missing values
            missing_percentage = (df.isnull().sum().sum() / (df.shape[0] * df.shape[1])) * 100
            
            # Calculate a confidence score (simplified example)
            if df.shape[0] < 100:
                size_factor = 0.5
            elif df.shape[0] < 1000:
                size_factor = 0.8
            else:
                size_factor = 1.0
            
            missing_factor = max(0, 1 - (missing_percentage / 50))
            
            # Higher confidence for balanced datasets
            balance_factor = 0.7
            if numeric_columns > 0 and categorical_columns > 0:
                balance_factor = 0.9
            if datetime_columns > 0:
                balance_factor = 1.0
            
            confidence_score = (size_factor * 0.4 + missing_factor * 0.3 + balance_factor * 0.3) * 100
            
            # Display the confidence score
            st.markdown(f"**AI Confidence Score**: {confidence_score:.1f}%")
            
            # Create a gauge chart for the confidence score
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=confidence_score,
                domain={"x": [0, 1], "y": [0, 1]},
                title={"text": "AI Confidence Score"},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": "darkblue"},
                    "steps": [
                        {"range": [0, 40], "color": "red"},
                        {"range": [40, 70], "color": "orange"},
                        {"range": [70, 100], "color": "green"}
                    ]
                }
            ))
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Tips for improvement
            st.subheader("Tips for Improvement")
            
            tips = []
            
            if df.shape[0] < 100:
                tips.append("Add more data rows for better AI learning (at least 100 rows recommended).")
            
            if missing_percentage > 10:
                tips.append(f"Your dataset has {missing_percentage:.1f}% missing values. Clean your data for better results.")
            
            if numeric_columns == 0:
                tips.append("Add numeric columns to enable statistical insights and correlations.")
            
            if categorical_columns == 0:
                tips.append("Add categorical columns to enable grouping and categorical analysis.")
            
            if datetime_columns == 0:
                tips.append("Add datetime columns to enable time-based analysis and trends.")
            
            if not tips:
                st.success("Your dataset is well-structured for AI analysis. No improvements needed!")
            else:
                for i, tip in enumerate(tips):
                    st.markdown(f"{i+1}. {tip}")
    
    # Call to action
    st.markdown("---")
    st.write("Continue using Analytics Assist and provide feedback to improve the AI learning system.")
    
    # Navigation buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("← Version History", use_container_width=True):
            st.switch_page("pages/07_Version_History.py")
    with col2:
        if st.button("Home", use_container_width=True):
            st.switch_page("app.py")
    with col3:
        if st.button("Dataset Management →", use_container_width=True):
            st.switch_page("pages/09_Dataset_Management.py")

# Call the main function
app()
