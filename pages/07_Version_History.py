import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import json
from utils.database import get_versions, get_version, get_dataset, save_version, get_transformations
from utils.export import generate_excel_download_link, generate_csv_download_link

st.set_page_config(
    page_title="Version History | Analytics Assist",
    page_icon="📚",
    layout="wide"
)

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
if 'dataset_id' not in st.session_state or st.session_state.dataset_id is None:
    st.warning("No dataset ID found. Please reload your dataset.")
    if st.button("Go to Upload Data"):
        st.switch_page("pages/01_Upload_Data.py")
    st.stop()

# Get dataset info
dataset_id = st.session_state.dataset_id
dataset_info = get_dataset(dataset_id)

if not dataset_info:
    st.error("Could not retrieve dataset information.")
    st.stop()

# Display dataset info
st.subheader(f"Dataset: {dataset_info['name']}")
st.markdown(f"**Description:** {dataset_info['description']}")
st.markdown(f"**Original file:** {dataset_info['file_name']}")
st.markdown(f"**Created on:** {dataset_info['created_at'].strftime('%Y-%m-%d %H:%M:%S')}")
st.markdown(f"**Last updated:** {dataset_info['updated_at'].strftime('%Y-%m-%d %H:%M:%S')}")

# Get list of versions
versions = get_versions(dataset_id)

# Create new version
st.markdown("---")
with st.expander("Create New Version", expanded=False):
    st.markdown("Save the current state of your dataset as a new version.")
    
    version_name = st.text_input("Version Name", f"Version {len(versions) + 1}")
    version_description = st.text_area("Version Description", "Description of changes made in this version.")
    
    if st.button("Save Current State as New Version"):
        # Get current transformations
        transformations = st.session_state.transformations
        
        # Determine version number
        version_number = len(versions) + 1
        
        # Save version
        with st.spinner("Saving version..."):
            version_id = save_version(
                dataset_id=dataset_id,
                version_number=version_number,
                name=version_name,
                description=version_description,
                df=st.session_state.dataset,
                transformations_applied=transformations
            )
            
            if version_id:
                st.success(f"Successfully saved version: {version_name}")
                st.rerun()
            else:
                st.error("Failed to save version.")

# Display versions
st.markdown("---")
st.subheader("Available Versions")

if not versions:
    st.info("No versions available. Create your first version to track changes.")
else:
    # Create a DataFrame for the versions
    versions_df = pd.DataFrame([
        {
            'ID': v['id'],
            'Version': f"v{v['version_number']}",
            'Name': v['name'],
            'Created': v['created_at'].strftime('%Y-%m-%d %H:%M'),
            'Rows': v['row_count'],
            'Columns': v['column_count'],
            'Transformations': v['transformations_count']
        }
        for v in versions
    ])
    
    st.dataframe(versions_df)
    
    # Select a version to view
    selected_version_id = st.selectbox("Select a version to view details", 
                                      options=[v['id'] for v in versions],
                                      format_func=lambda x: next((f"{v['name']} (v{v['version_number']})" for v in versions if v['id'] == x), ''))
    
    if selected_version_id:
        # Get version details
        version_data = get_version(selected_version_id)
        
        if version_data:
            st.markdown("---")
            st.subheader(f"Version Details: {version_data['name']} (v{version_data['version_number']})")
            
            # Layout with columns
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"**Description:** {version_data['description']}")
                st.markdown(f"**Created on:** {version_data['created_at'].strftime('%Y-%m-%d %H:%M:%S')}")
                st.markdown(f"**Rows:** {version_data['row_count']}")
                st.markdown(f"**Columns:** {version_data['column_count']}")
                
                # Display transformations
                if version_data['transformations_applied']:
                    st.markdown("### Applied Transformations")
                    
                    for i, transform in enumerate(version_data['transformations_applied']):
                        with st.expander(f"{i+1}. {transform['name']}"):
                            st.markdown(f"**Description:** {transform['description']}")
                            st.markdown(f"**Function:** {transform['function']}")
                            st.markdown(f"**Applied to columns:** {', '.join(transform['columns'])}")
                            st.markdown(f"**Applied on:** {transform['timestamp']}")
                            
                            if transform.get('params'):
                                st.markdown("**Parameters:**")
                                st.json(transform['params'])
                else:
                    st.info("No transformations applied in this version.")
            
            with col2:
                # Preview data
                st.markdown("### Data Preview")
                st.dataframe(version_data['dataset'].head(10))
                
                # Download options
                st.markdown("### Export Version")
                col_dl1, col_dl2 = st.columns(2)
                
                with col_dl1:
                    csv_link = generate_csv_download_link(
                        version_data['dataset'], 
                        filename=f"{dataset_info['name']}_v{version_data['version_number']}.csv"
                    )
                    st.markdown(csv_link, unsafe_allow_html=True)
                
                with col_dl2:
                    excel_link = generate_excel_download_link(
                        version_data['dataset'], 
                        filename=f"{dataset_info['name']}_v{version_data['version_number']}.xlsx",
                        sheet_name=f"Version {version_data['version_number']}"
                    )
                    st.markdown(excel_link, unsafe_allow_html=True)
                
                # Restore version
                st.markdown("### Actions")
                if st.button("Restore This Version"):
                    st.session_state.dataset = version_data['dataset']
                    st.session_state.transformations = version_data['transformations_applied']
                    
                    # Update history
                    if 'transformation_history' not in st.session_state:
                        st.session_state.transformation_history = []
                    
                    history_entry = {
                        'action': f"Restored version {version_data['version_number']} - {version_data['name']}",
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'details': f"Restored to version created on {version_data['created_at'].strftime('%Y-%m-%d %H:%M:%S')}"
                    }
                    
                    st.session_state.transformation_history.append(history_entry)
                    
                    st.success(f"Successfully restored to version {version_data['version_number']} - {version_data['name']}")
                    st.rerun()
            
            # Compare with current data
            st.markdown("---")
            st.subheader("Version Comparison")
            
            # Get column differences
            current_cols = set(st.session_state.dataset.columns)
            version_cols = set(version_data['dataset'].columns)
            
            new_cols = current_cols - version_cols
            removed_cols = version_cols - current_cols
            common_cols = current_cols.intersection(version_cols)
            
            # Display column differences
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("### New Columns")
                if new_cols:
                    for col in new_cols:
                        st.markdown(f"- {col}")
                else:
                    st.info("No new columns")
            
            with col2:
                st.markdown("### Removed Columns")
                if removed_cols:
                    for col in removed_cols:
                        st.markdown(f"- {col}")
                else:
                    st.info("No removed columns")
            
            with col3:
                st.markdown("### Row Count Changes")
                current_count = st.session_state.dataset.shape[0]
                version_count = version_data['dataset'].shape[0]
                
                diff = current_count - version_count
                
                if diff > 0:
                    st.markdown(f"**+{diff}** rows added since this version")
                elif diff < 0:
                    st.markdown(f"**{diff}** rows removed since this version")
                else:
                    st.markdown("No change in row count")
            
            # Sample value changes in common columns
            if common_cols:
                st.markdown("### Sample Value Changes in Common Columns")
                
                # Select a subset of common columns to display
                display_cols = st.multiselect("Select columns to compare", list(common_cols), default=list(common_cols)[:3])
                
                if display_cols:
                    # Get sample records from both datasets
                    sample_current = st.session_state.dataset[display_cols].head(5)
                    sample_version = version_data['dataset'][display_cols].head(5)
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("#### Current Values")
                        st.dataframe(sample_current)
                    
                    with col2:
                        st.markdown(f"#### Version {version_data['version_number']} Values")
                        st.dataframe(sample_version)
        else:
            st.error("Could not retrieve version data.")

# Sidebar
with st.sidebar:
    st.header("Version Management Tips")
    
    st.markdown("""
    ### Best Practices
    
    1. **Regular Snapshots**: Create versions at meaningful points in your analysis
    
    2. **Descriptive Names**: Use clear names and descriptions for your versions
    
    3. **Track Changes**: Note what transformations you've applied between versions
    
    4. **Export Important Versions**: Download critical versions for offline storage
    """)