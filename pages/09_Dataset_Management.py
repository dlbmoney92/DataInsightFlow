import streamlit as st
import pandas as pd
from datetime import datetime
import os
import json

from utils.auth_redirect import require_auth
from utils.custom_navigation import render_navigation
from utils.global_config import apply_global_css
from utils.database import list_datasets, delete_dataset
from utils.access_control import check_access, get_dataset_count

def app():
    # Apply global CSS
    apply_global_css()
    
    # Render navigation
    render_navigation()
    
    # Check if user is logged in
    if not require_auth():
        return
    
    st.title("Dataset Management")
    
    # Get user's current dataset count and limit
    datasets = list_datasets()
    current_count = len(datasets) if datasets else 0
    
    # Get dataset limit based on subscription tier
    subscription_tier = st.session_state.get("subscription_tier", "free")
    dataset_limit = check_access("dataset_count")
    
    # Display usage information
    st.info(f"You are currently using {current_count} datasets out of your {dataset_limit if dataset_limit > 0 else 'unlimited'} dataset limit.")
    
    # Progress bar for dataset usage
    if dataset_limit > 0:  # Only show progress bar if there's a limit
        progress_percentage = min(1.0, current_count / dataset_limit)
        st.progress(progress_percentage, f"Dataset Usage: {int(progress_percentage * 100)}%")
    
    # List datasets with delete option
    if datasets:
        st.subheader("Your Datasets")
        
        # Create a container for the dataset list
        with st.container():
            for dataset in datasets:
                with st.container(border=True):
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        st.markdown(f"**{dataset['name']}**")
                        st.caption(f"Type: {dataset['file_type'].upper()} | Created: {dataset['created_at'].strftime('%Y-%m-%d %H:%M')}")
                        if dataset['description']:
                            st.caption(f"Description: {dataset['description']}")
                    
                    with col2:
                        st.metric("Rows", dataset['row_count'])
                        st.metric("Columns", dataset['column_count'])
                    
                    with col3:
                        # Use a unique key for each delete button
                        if st.button("Delete", key=f"delete_{dataset['id']}", type="primary", help="Permanently delete this dataset and all associated versions and insights"):
                            # Confirm deletion
                            st.session_state.confirm_delete_id = dataset['id']
                            st.session_state.confirm_delete_name = dataset['name']
                            st.rerun()
        
        # Handle confirmation dialog
        if "confirm_delete_id" in st.session_state:
            dataset_id = st.session_state.confirm_delete_id
            dataset_name = st.session_state.confirm_delete_name
            
            # Create a modal-like dialog
            with st.container(border=True):
                st.warning(f"Are you sure you want to delete the dataset '{dataset_name}'? This action cannot be undone.")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Cancel", key="cancel_delete"):
                        del st.session_state.confirm_delete_id
                        del st.session_state.confirm_delete_name
                        st.rerun()
                with col2:
                    if st.button("Delete Permanently", key="confirm_delete", type="primary"):
                        success = delete_dataset(dataset_id)
                        if success:
                            st.success(f"Dataset '{dataset_name}' has been deleted.")
                            # Clean up session state
                            del st.session_state.confirm_delete_id
                            del st.session_state.confirm_delete_name
                            # Refresh the page
                            st.rerun()
                        else:
                            st.error("Failed to delete the dataset. Please try again.")
    else:
        st.info("You don't have any datasets yet. Go to the 'Upload Data' page to get started!")
        
        # Add a button to navigate to the upload page
        if st.button("Upload Data", type="primary"):
            st.switch_page("pages/01_Upload_Data.py")
    
    # Tips and best practices
    with st.expander("Tips for Managing Datasets"):
        st.markdown("""
        ### Best Practices for Dataset Management
        
        - **Regular Cleanup**: Delete datasets you no longer need to stay within your plan limits.
        - **Descriptive Names**: Use clear, descriptive names for your datasets to easily identify them later.
        - **Add Descriptions**: Provide detailed descriptions when uploading data to help remember its purpose.
        - **Version Control**: For important datasets, create versions before making significant changes.
        - **Export Results**: Export processed data and reports to share with others instead of giving them access to your account.
        """)

if __name__ == "__main__":
    app()