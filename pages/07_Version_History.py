import streamlit as st

# Set page configuration - must be the first Streamlit command
st.set_page_config(
    page_title="Version History | Analytics Assist",
    page_icon="📚",
    layout="wide"
)

import pandas as pd
import numpy as np
from datetime import datetime
import json
from utils.database import get_versions, get_version, get_dataset, save_version, get_transformations
from utils.export import generate_excel_download_link, generate_csv_download_link
from utils.auth_redirect import require_auth
from utils.custom_navigation import render_navigation, initialize_navigation
from utils.global_config import apply_global_css

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

# Check authentication first
if not require_auth():
    st.stop()  # Stop if not authenticated

# Show user info if authenticated
if "user" in st.session_state:
    st.sidebar.success(f"Logged in as: {st.session_state.user.get('email', 'User')}")
    st.sidebar.info(f"Subscription: {st.session_state.subscription_tier.capitalize()}")

# Header
st.title("Version History")
st.markdown("""
Track and manage different versions of your dataset as you apply transformations.
This page allows you to view, compare, and restore previous versions.
""")

# Check if a dataset is loaded
if 'dataset' not in st.session_state or st.session_state.dataset is None:
    st.warning("Please load a dataset first.")
    if st.button("Go to Upload Data"):
        st.switch_page("pages/01_Upload_Data.py")
    st.stop()

# Check if dataset_id is available
if 'dataset_id' not in st.session_state:
    st.warning("The current dataset is not yet saved to the database. Please save it first.")
    
    if st.button("Go to Export Page"):
        st.switch_page("pages/06_Export_Reports.py")
    
    st.stop()

# Get dataset information
try:
    dataset_info = get_dataset(st.session_state.dataset_id)
    
    if not dataset_info:
        st.error("Could not retrieve dataset information.")
        st.stop()
    
    # Display dataset info in the sidebar
    st.sidebar.subheader("Dataset Info")
    st.sidebar.info(f"""
    - **Name**: {dataset_info.get('name', 'Unknown')}
    - **File**: {dataset_info.get('file_name', 'Unknown')}
    - **Created**: {dataset_info.get('created_at', 'Unknown')}
    """)
    
    # Current dataset
    current_df = st.session_state.dataset
    
    # Get all versions
    versions = get_versions(st.session_state.dataset_id)
except Exception as e:
    st.error(f"Error retrieving data: {str(e)}")
    versions = []

# Display versions if available
if versions:
    # Convert versions to DataFrame for display
    versions_df = pd.DataFrame(versions)
    
    # Ensure all columns exist and add empty values if they don't
    required_columns = ['version', 'name', 'description', 'created_at']
    for col in required_columns:
        if col not in versions_df.columns:
            versions_df[col] = ""
    
    # Format the DataFrame for display
    display_df = versions_df[['version', 'name', 'description', 'created_at']]
    display_df = display_df.rename(columns={
        'version': 'Version',
        'name': 'Name',
        'description': 'Description',
        'created_at': 'Created At'
    })
    
    # Show versions table
    st.subheader("Saved Versions")
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    # Version selection
    selected_version = st.selectbox(
        "Select a version to view or compare",
        options=list(range(len(versions))),
        format_func=lambda i: f"Version {versions[i]['version']} - {versions[i]['name']} ({versions[i]['created_at']})"
    )
    
    # Get the selected version
    version = versions[selected_version]
    
    # Create tabs for different actions
    tab1, tab2, tab3 = st.tabs(["View Version", "Compare Versions", "Version Actions"])
    
    with tab1:
        st.header(f"Version {version['version']}: {version['name']}")
        st.markdown(f"**Description**: {version['description']}")
        st.markdown(f"**Created**: {version['created_at']}")
        
        # Fetch the version data
        version_data = get_version(version['id'])
        
        if version_data and 'df' in version_data:
            version_df = version_data['df']
            
            # Display the data preview
            st.subheader("Data Preview")
            st.dataframe(version_df.head(10), use_container_width=True)
            
            # Show basic stats
            st.subheader("Dataset Statistics")
            stats_cols = st.columns(4)
            with stats_cols[0]:
                st.metric("Rows", version_df.shape[0])
            with stats_cols[1]:
                st.metric("Columns", version_df.shape[1])
            with stats_cols[2]:
                st.metric("Missing Values", version_df.isnull().sum().sum())
            with stats_cols[3]:
                memory_usage = round(version_df.memory_usage(deep=True).sum() / (1024 * 1024), 2)
                st.metric("Memory", f"{memory_usage} MB")
            
            # Transformations applied
            st.subheader("Transformations Applied")
            if 'transformations_applied' in version_data and version_data['transformations_applied']:
                try:
                    transformations = json.loads(version_data['transformations_applied'])
                    
                    if transformations:
                        # Create columns for the transformation history
                        history_cols = st.columns([3, 1])
                        with history_cols[0]:
                            st.markdown("**Transformation**")
                        with history_cols[1]:
                            st.markdown("**Applied At**")
                            
                        # Create a separator
                        st.markdown("---")
                        
                        # Display the transformations
                        for i, t in enumerate(transformations):
                            cols = st.columns([3, 1])
                            
                            with cols[0]:
                                st.markdown(f"**{i+1}. {t['name']}**")
                            
                            with cols[1]:
                                st.markdown(t.get("timestamp", "N/A"))
                            
                            # Add a separator between transformations
                            st.markdown("---")
                    else:
                        st.info("No transformations were applied to this version.")
                except:
                    st.warning("Could not parse transformation data.")
            else:
                st.info("No transformations were applied to this version.")
            
            # Download options
            st.subheader("Download Options")
            col1, col2 = st.columns(2)
            
            with col1:
                excel_link = generate_excel_download_link(version_df, filename=f"Version_{version['version']}_{version['name']}.xlsx")
                st.markdown(excel_link, unsafe_allow_html=True)
                
            with col2:
                csv_link = generate_csv_download_link(version_df, filename=f"Version_{version['version']}_{version['name']}.csv")
                st.markdown(csv_link, unsafe_allow_html=True)
        else:
            st.error("Could not retrieve version data.")
    
    with tab2:
        st.header("Compare Versions")
        
        # Select another version to compare with
        other_versions = [v for i, v in enumerate(versions) if i != selected_version]
        
        if other_versions:
            compare_version = st.selectbox(
                "Select a version to compare with",
                options=list(range(len(other_versions))),
                format_func=lambda i: f"Version {other_versions[i]['version']} - {other_versions[i]['name']} ({other_versions[i]['created_at']})"
            )
            
            # Get the data for both versions
            version_data = get_version(version['id'])
            compare_data = get_version(other_versions[compare_version]['id'])
            
            if version_data and 'df' in version_data and compare_data and 'df' in compare_data:
                version_df = version_data['df']
                compare_df = compare_data['df']
                
                # Display comparison
                st.subheader("Structure Comparison")
                
                # Calculate differences in structure
                v1_cols = set(version_df.columns)
                v2_cols = set(compare_df.columns)
                
                common_cols = v1_cols.intersection(v2_cols)
                only_v1_cols = v1_cols - v2_cols
                only_v2_cols = v2_cols - v1_cols
                
                # Display structure differences
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Rows in Version 1", version_df.shape[0])
                    st.metric("Columns in Version 1", version_df.shape[1])
                
                with col2:
                    st.metric("Rows in Version 2", compare_df.shape[0])
                    st.metric("Columns in Version 2", compare_df.shape[1])
                
                with col3:
                    st.metric("Row Difference", version_df.shape[0] - compare_df.shape[0])
                    st.metric("Column Difference", version_df.shape[1] - compare_df.shape[1])
                
                # Display column differences
                st.subheader("Column Differences")
                
                if only_v1_cols:
                    st.markdown(f"**Columns only in Version {version['version']}:**")
                    st.write(", ".join(only_v1_cols))
                
                if only_v2_cols:
                    st.markdown(f"**Columns only in Version {other_versions[compare_version]['version']}:**")
                    st.write(", ".join(only_v2_cols))
                
                if not only_v1_cols and not only_v2_cols:
                    st.success("Both versions have the same columns.")
                
                # Data comparison for common columns
                if common_cols:
                    st.subheader("Data Comparison")
                    
                    # Select a column to compare
                    compare_col = st.selectbox("Select a column to compare", list(common_cols))
                    
                    if compare_col:
                        # Basic statistics comparison
                        if pd.api.types.is_numeric_dtype(version_df[compare_col]) and pd.api.types.is_numeric_dtype(compare_df[compare_col]):
                            # Numeric column
                            stats1 = version_df[compare_col].describe()
                            stats2 = compare_df[compare_col].describe()
                            
                            # Create side-by-side comparison
                            stats_df = pd.DataFrame({
                                f"Version {version['version']}": stats1,
                                f"Version {other_versions[compare_version]['version']}": stats2,
                                "Difference": stats1 - stats2
                            })
                            
                            st.dataframe(stats_df)
                            
                            # Visualization comparison
                            st.subheader("Visual Comparison")
                            
                            # Create a histogram to compare distributions
                            import plotly.express as px
                            
                            fig = px.histogram(
                                title=f"Distribution of {compare_col} Across Versions",
                                opacity=0.7
                            )
                            
                            # Add traces for both versions
                            fig.add_histogram(
                                x=version_df[compare_col], 
                                name=f"Version {version['version']}"
                            )
                            fig.add_histogram(
                                x=compare_df[compare_col], 
                                name=f"Version {other_versions[compare_version]['version']}"
                            )
                            
                            # Update layout for better display
                            fig.update_layout(barmode='overlay')
                            
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            # Non-numeric column
                            # Compare value counts
                            counts1 = version_df[compare_col].value_counts().head(10)
                            counts2 = compare_df[compare_col].value_counts().head(10)
                            
                            # Create DataFrames for display
                            counts1_df = pd.DataFrame(counts1).reset_index()
                            counts1_df.columns = ['Value', 'Count']
                            counts1_df['Version'] = f"Version {version['version']}"
                            
                            counts2_df = pd.DataFrame(counts2).reset_index()
                            counts2_df.columns = ['Value', 'Count']
                            counts2_df['Version'] = f"Version {other_versions[compare_version]['version']}"
                            
                            # Combine for visualization
                            combined_counts = pd.concat([counts1_df, counts2_df])
                            
                            # Create bar chart comparing value counts
                            import plotly.express as px
                            
                            fig = px.bar(
                                combined_counts,
                                x='Value',
                                y='Count',
                                color='Version',
                                barmode='group',
                                title=f"Top Values in {compare_col} Across Versions"
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Show unique value counts
                            st.write(f"Unique values in Version {version['version']}: {version_df[compare_col].nunique()}")
                            st.write(f"Unique values in Version {other_versions[compare_version]['version']}: {compare_df[compare_col].nunique()}")
                else:
                    st.warning("No common columns to compare data.")
            else:
                st.error("Could not retrieve data for both versions.")
        else:
            st.info("You need at least two versions to compare.")
    
    with tab3:
        st.header("Version Actions")
        
        # Fetch the version data
        version_data = get_version(version['id'])
        
        if version_data and 'df' in version_data:
            version_df = version_data['df']
            
            # Restore version
            st.subheader("Restore Version")
            st.warning("Restoring will replace your current working dataset with this version.")
            
            if st.button("Restore This Version"):
                # Update the session state
                st.session_state.dataset = version_df
                
                # Parse transformations if available
                if 'transformations_applied' in version_data and version_data['transformations_applied']:
                    try:
                        st.session_state.transformations = json.loads(version_data['transformations_applied'])
                    except:
                        st.session_state.transformations = []
                else:
                    st.session_state.transformations = []
                
                st.success(f"Version {version['version']} restored. You are now working with this version.")
                st.rerun()
            
            # Create a new version based on this one
            st.subheader("Create New Version")
            
            version_name = st.text_input("Version Name", value=f"Based on Version {version['version']}")
            version_desc = st.text_area("Version Description", value=f"Created from Version {version['version']} on {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            
            if st.button("Create New Version"):
                try:
                    # Get the next version number
                    next_version = max([v['version'] for v in versions]) + 1
                    
                    # Get transformations
                    transformations = []
                    if 'transformations_applied' in version_data and version_data['transformations_applied']:
                        try:
                            transformations = version_data['transformations_applied']
                        except:
                            transformations = json.dumps([])
                    
                    # Save as a new version
                    new_version_id = save_version(
                        st.session_state.dataset_id,
                        next_version,
                        version_name,
                        version_desc,
                        version_df,
                        transformations
                    )
                    
                    if new_version_id:
                        st.success(f"New version created with ID: {new_version_id}")
                        st.rerun()
                    else:
                        st.error("Failed to create new version.")
                except Exception as e:
                    st.error(f"Error creating new version: {str(e)}")
        else:
            st.error("Could not retrieve version data.")
else:
    st.info("No versions found for this dataset. Create a version by saving your work in the Export Reports page.")
    
    # Create initial version
    st.subheader("Create Initial Version")
    
    version_name = st.text_input("Version Name", value=f"Initial Version")
    version_desc = st.text_area("Version Description", value=f"Initial version created on {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    if st.button("Save Current State as Initial Version"):
        try:
            # Save as version 1
            transformations = []
            if 'transformations' in st.session_state:
                transformations = json.dumps(st.session_state.transformations)
            else:
                transformations = json.dumps([])
            
            # Save the version
            version_id = save_version(
                st.session_state.dataset_id,
                1,
                version_name,
                version_desc,
                st.session_state.dataset,
                transformations
            )
            
            if version_id:
                st.success(f"Initial version created with ID: {version_id}")
                st.rerun()
            else:
                st.error("Failed to create initial version.")
        except Exception as e:
            st.error(f"Error creating initial version: {str(e)}")

# Navigation buttons at the bottom
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("← Export Reports", use_container_width=True):
        st.switch_page("pages/06_Export_Reports.py")
with col2:
    if st.button("Home", use_container_width=True):
        st.switch_page("app.py")
with col3:
    if st.button("AI Learning →", use_container_width=True):
        st.switch_page("pages/08_AI_Learning.py")