import streamlit as st
import pandas as pd
import numpy as np
import os
import json
from datetime import datetime
from utils.file_processor import supported_file_types
from utils.database import initialize_database
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

# Main page header
st.title("Analytics Assist")
st.subheader("Your AI-powered data analysis co-pilot")

# Dashboard layout
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("""
    ## Welcome to Analytics Assist! 👋
    
    Analytics Assist is a modern, AI-driven data science application that empowers users 
    of all backgrounds to perform exploratory data analysis (EDA), data cleaning, 
    and machine learning on their datasets with no coding required.
    
    ### Getting Started
    1. 📁 **Upload Data**: Start by uploading your dataset in the Upload Data page
    2. 🔍 **Preview & Validate**: Review and validate the detected schema
    3. 📊 **Explore**: Get automatic visualizations and statistics
    4. 🧹 **Transform**: Apply AI-suggested transformations to clean your data
    5. 💡 **Discover Insights**: Review AI-generated insights about your data
    6. 📤 **Export**: Export your findings as reports or download transformed data
    
    ### Supported File Types
    """)
    
    # Display supported file types
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
            st.metric("Rows", rows)
            st.metric("Columns", cols)
            st.metric("Transformations Applied", len(st.session_state.transformations))
    else:
        st.info("No active project. Start by uploading data.")
    
    # Recent activity
    st.markdown("### Recent Activity")
    if st.session_state.transformation_history:
        for i, history in enumerate(reversed(st.session_state.transformation_history[-3:])):
            st.text(f"{history['timestamp']}: {history['action']}")
    else:
        st.text("No recent activity")

# Display a guide to navigate the app
st.markdown("---")
st.markdown("## Navigation Guide")

nav_cols = st.columns(4)
with nav_cols[0]:
    st.markdown("### 📁 Data Upload")
    st.markdown("Start here to upload your data files.")
    if st.button("Go to Upload", key="nav_upload"):
        st.switch_page("pages/01_Upload_Data.py")

with nav_cols[1]:
    st.markdown("### 📊 EDA Dashboard")
    st.markdown("View automatic analysis of your data.")
    if st.button("Go to EDA", key="nav_eda"):
        st.switch_page("pages/03_EDA_Dashboard.py")

with nav_cols[2]:
    st.markdown("### 🧹 Data Transformation")
    st.markdown("Clean and transform your dataset.")
    if st.button("Go to Transform", key="nav_transform"):
        st.switch_page("pages/04_Data_Transformation.py")

with nav_cols[3]:
    st.markdown("### 💡 Insights")
    st.markdown("Discover AI-generated insights.")
    if st.button("Go to Insights", key="nav_insights"):
        st.switch_page("pages/05_Insights_Dashboard.py")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style="text-align:center">
        <p>Analytics Assist v0.1.0 | Made with ❤️ for data enthusiasts</p>
    </div>
    """, 
    unsafe_allow_html=True
)
