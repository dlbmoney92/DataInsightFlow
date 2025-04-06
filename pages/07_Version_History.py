import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json
import base64
import io
from utils.transformations import apply_transformations

st.set_page_config(
    page_title="Version History | Analytics Assist",
    page_icon="📜",
    layout="wide"
)

# Check if dataset exists in session state
if 'dataset' not in st.session_state or st.session_state.dataset is None:
    st.warning("Please upload a dataset first.")
    st.button("Go to Upload Page", on_click=lambda: st.switch_page("pages/01_Upload_Data.py"))
    st.stop()

# Header and description
st.title("Version History & Management")
st.markdown("""
Track and manage different versions of your dataset as you apply transformations.
You can view, compare, and restore previous versions of your data.
""")

# Initialize version history if it doesn't exist
if 'version_history' not in st.session_state:
    # Create initial version entry (original dataset)
    if 'file_name' in st.session_state:
        st.session_state.version_history = [
            {
                'version': 1,
                'name': 'Original Dataset',
                'description': f'Original uploaded file: {st.session_state.file_name}',
                'timestamp': st.session_state.current_project.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S')) if 'current_project' in st.session_state else datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'transformations': [],
                'shape': st.session_state.dataset.shape
            }
        ]
    else:
        st.session_state.version_history = []

# Get current version information
current_version = len(st.session_state.version_history)
if 'transformations' in st.session_state and st.session_state.transformations:
    transformation_count = len(st.session_state.transformations)
    # Check if we need to add a new version
    if current_version == 0 or transformation_count > len(st.session_state.version_history[-1]['transformations']):
        # Create a new version entry
        new_version = {
            'version': current_version + 1,
            'name': f'Version {current_version + 1}',
            'description': f'Dataset with {transformation_count} transformations applied',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'transformations': st.session_state.transformations.copy(),
            'shape': st.session_state.dataset.shape
        }
        st.session_state.version_history.append(new_version)
        current_version += 1

# Create tabs
tab1, tab2, tab3 = st.tabs([
    "📋 Version List", 
    "🔄 Compare Versions", 
    "⏮️ Restore Version"
])

# Tab 1: Version List
with tab1:
    st.subheader("Dataset Version History")
    
    # Display current version info
    st.info(f"**Current Version:** {current_version}")
    
    # Create a DataFrame from version history
    if st.session_state.version_history:
        version_data = []
        for version in st.session_state.version_history:
            version_data.append({
                'Version': version['version'],
                'Name': version['name'],
                'Description': version['description'],
                'Created On': version['timestamp'],
                'Transformations': len(version['transformations']),
                'Rows': version['shape'][0],
                'Columns': version['shape'][1]
            })
        
        version_df = pd.DataFrame(version_data)
        
        # Allow editing version names and descriptions
        edited_df = st.data_editor(
            version_df,
            column_config={
                'Version': st.column_config.NumberColumn(
                    'Version',
                    help='Version number',
                    disabled=True
                ),
                'Name': st.column_config.TextColumn(
                    'Name',
                    help='Version name',
                    disabled=False
                ),
                'Description': st.column_config.TextColumn(
                    'Description',
                    help='Version description',
                    disabled=False
                ),
                'Created On': st.column_config.TextColumn(
                    'Created On',
                    help='Creation timestamp',
                    disabled=True
                ),
                'Transformations': st.column_config.NumberColumn(
                    'Transformations',
                    help='Number of transformations',
                    disabled=True
                ),
                'Rows': st.column_config.NumberColumn(
                    'Rows',
                    help='Number of rows',
                    disabled=True
                ),
                'Columns': st.column_config.NumberColumn(
                    'Columns',
                    help='Number of columns',
                    disabled=True
                )
            },
            hide_index=True,
            use_container_width=True
        )
        
        # Update version names and descriptions if edited
        for i, row in edited_df.iterrows():
            version_idx = row['Version'] - 1
            if version_idx < len(st.session_state.version_history):
                st.session_state.version_history[version_idx]['name'] = row['Name']
                st.session_state.version_history[version_idx]['description'] = row['Description']
        
        # Display transformation details for a selected version
        st.subheader("Version Details")
        selected_version = st.selectbox(
            "Select version to view details",
            options=version_df['Version'].tolist()
        )
        
        if selected_version:
            version_idx = selected_version - 1
            selected_version_data = st.session_state.version_history[version_idx]
            
            st.markdown(f"### {selected_version_data['name']} (Version {selected_version_data['version']})")
            st.markdown(f"**Description:** {selected_version_data['description']}")
            st.markdown(f"**Created on:** {selected_version_data['timestamp']}")
            
            # Show transformations for this version
            transformations = selected_version_data['transformations']
            if transformations:
                st.markdown(f"**Transformations applied ({len(transformations)}):**")
                
                for i, transform in enumerate(transformations):
                    with st.expander(f"{i+1}. {transform.get('name', 'Transformation')}"):
                        st.markdown(f"**Applied on:** {transform.get('timestamp', '-')}")
                        st.markdown(f"**Description:** {transform.get('description', '-')}")
                        st.markdown(f"**Affected columns:** {', '.join(transform.get('columns', []))}")
                        
                        # Show parameters if available
                        if 'params' in transform and transform['params']:
                            st.markdown("**Parameters:**")
                            for param, value in transform['params'].items():
                                st.markdown(f"- {param}: {value}")
            else:
                st.markdown("**No transformations applied to this version.**")
            
            # Option to create a snapshot of this version
            if st.button(f"Create Snapshot of Version {selected_version}"):
                # Create a copy of the version with a new name
                snapshot_name = f"Snapshot of {selected_version_data['name']} - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                
                # Add to version history
                st.session_state.version_history.append({
                    'version': len(st.session_state.version_history) + 1,
                    'name': snapshot_name,
                    'description': f"Snapshot created from Version {selected_version}",
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'transformations': transformations.copy(),
                    'shape': selected_version_data['shape']
                })
                
                st.success(f"Created snapshot: {snapshot_name}")
                st.rerun()
    else:
        st.info("No version history available yet. Apply transformations to create new versions.")
    
    # Create a new version from current state
    st.subheader("Create New Version")
    new_version_name = st.text_input("Version name", value=f"Version {current_version + 1}")
    new_version_description = st.text_area("Version description", value="Custom version")
    
    if st.button("Create New Version"):
        # Create a new version entry
        new_version = {
            'version': len(st.session_state.version_history) + 1,
            'name': new_version_name,
            'description': new_version_description,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'transformations': st.session_state.transformations.copy() if 'transformations' in st.session_state else [],
            'shape': st.session_state.dataset.shape
        }
        st.session_state.version_history.append(new_version)
        st.success(f"Created new version: {new_version_name}")
        st.rerun()

# Tab 2: Compare Versions
with tab2:
    st.subheader("Compare Dataset Versions")
    
    if len(st.session_state.version_history) < 2:
        st.info("You need at least 2 versions to make a comparison.")
    else:
        # Select versions to compare
        col1, col2 = st.columns(2)
        
        with col1:
            version1 = st.selectbox(
                "Select first version",
                options=[f"V{v['version']}: {v['name']}" for v in st.session_state.version_history],
                index=0,
                key="version1"
            )
            version1_num = int(version1.split(":")[0][1:])
        
        with col2:
            version2 = st.selectbox(
                "Select second version",
                options=[f"V{v['version']}: {v['name']}" for v in st.session_state.version_history],
                index=len(st.session_state.version_history)-1 if len(st.session_state.version_history) > 1 else 0,
                key="version2"
            )
            version2_num = int(version2.split(":")[0][1:])
        
        if version1_num == version2_num:
            st.warning("Please select different versions to compare.")
        else:
            # Get version data
            v1_idx = version1_num - 1
            v2_idx = version2_num - 1
            
            v1_data = st.session_state.version_history[v1_idx]
            v2_data = st.session_state.version_history[v2_idx]
            
            # Display version metadata comparison
            st.markdown("### Version Metadata Comparison")
            
            metadata_df = pd.DataFrame({
                'Attribute': ['Name', 'Description', 'Created On', 'Transformations', 'Rows', 'Columns'],
                f'Version {v1_data["version"]}': [
                    v1_data['name'],
                    v1_data['description'],
                    v1_data['timestamp'],
                    len(v1_data['transformations']),
                    v1_data['shape'][0],
                    v1_data['shape'][1]
                ],
                f'Version {v2_data["version"]}': [
                    v2_data['name'],
                    v2_data['description'],
                    v2_data['timestamp'],
                    len(v2_data['transformations']),
                    v2_data['shape'][0],
                    v2_data['shape'][1]
                ]
            })
            
            st.table(metadata_df)
            
            # Compare transformations
            st.markdown("### Transformation Comparison")
            
            # Identify common and unique transformations
            v1_transforms = v1_data['transformations']
            v2_transforms = v2_data['transformations']
            
            # Count transformations by type
            v1_transform_types = {}
            for t in v1_transforms:
                v1_transform_types[t['name']] = v1_transform_types.get(t['name'], 0) + 1
            
            v2_transform_types = {}
            for t in v2_transforms:
                v2_transform_types[t['name']] = v2_transform_types.get(t['name'], 0) + 1
            
            # Get all unique transformation types
            all_transform_types = set(list(v1_transform_types.keys()) + list(v2_transform_types.keys()))
            
            # Create comparison DataFrame
            transform_comp_data = []
            for t_type in sorted(all_transform_types):
                transform_comp_data.append({
                    'Transformation Type': t_type,
                    f'Version {v1_data["version"]} Count': v1_transform_types.get(t_type, 0),
                    f'Version {v2_data["version"]} Count': v2_transform_types.get(t_type, 0)
                })
            
            transform_comp_df = pd.DataFrame(transform_comp_data)
            st.table(transform_comp_df)
            
            # Visualize transformation differences
            if transform_comp_data:
                st.markdown("### Transformation Comparison Chart")
                
                # Prepare data for bar chart
                chart_data = []
                for row in transform_comp_data:
                    t_type = row['Transformation Type']
                    chart_data.append({
                        'Transformation Type': t_type,
                        'Version': f"Version {v1_data['version']}",
                        'Count': row[f'Version {v1_data["version"]} Count']
                    })
                    chart_data.append({
                        'Transformation Type': t_type,
                        'Version': f"Version {v2_data['version']}",
                        'Count': row[f'Version {v2_data["version"]} Count']
                    })
                
                chart_df = pd.DataFrame(chart_data)
                
                # Create grouped bar chart
                fig = px.bar(
                    chart_df,
                    x='Transformation Type',
                    y='Count',
                    color='Version',
                    barmode='group',
                    title="Transformation Types by Version",
                    color_discrete_sequence=['#4F8BF9', '#FF6B6B']
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            # Option to load and compare the actual data
            st.markdown("### Data Comparison")
            st.markdown("""
            To compare the actual data between versions, you can load the datasets and view differences
            in shape, structure, and sample values.
            """)
            
            if st.button("Load and Compare Data"):
                with st.spinner("Loading and comparing datasets..."):
                    # Load the datasets by applying the respective transformations
                    original_df = None
                    if 'file_name' in st.session_state:
                        try:
                            import os
                            if st.session_state.file_name.endswith('.csv'):
                                original_df = pd.read_csv(st.session_state.file_name)
                            elif st.session_state.file_name.endswith(('.xlsx', '.xls')):
                                original_df = pd.read_excel(st.session_state.file_name)
                        except:
                            st.warning("Could not load original file. Using session dataset for comparisons.")
                            original_df = st.session_state.dataset
                    else:
                        original_df = st.session_state.dataset
                    
                    if original_df is None:
                        st.error("Could not access dataset for comparison.")
                    else:
                        # Apply transformations for each version
                        df1 = apply_transformations(original_df, v1_data['transformations'])
                        df2 = apply_transformations(original_df, v2_data['transformations'])
                        
                        # Compare shape
                        st.markdown("#### Dataset Shape Comparison")
                        shape_diff_rows = df2.shape[0] - df1.shape[0]
                        shape_diff_cols = df2.shape[1] - df1.shape[1]
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric(
                                f"Version {v1_data['version']} Shape", 
                                f"{df1.shape[0]} rows, {df1.shape[1]} columns"
                            )
                        
                        with col2:
                            st.metric(
                                f"Version {v2_data['version']} Shape", 
                                f"{df2.shape[0]} rows, {df2.shape[1]} columns"
                            )
                        
                        with col3:
                            st.metric(
                                "Difference", 
                                f"{shape_diff_rows:+d} rows, {shape_diff_cols:+d} columns",
                                delta_color="normal"
                            )
                        
                        # Compare column names
                        st.markdown("#### Column Comparison")
                        
                        columns_v1 = set(df1.columns)
                        columns_v2 = set(df2.columns)
                        
                        common_columns = columns_v1.intersection(columns_v2)
                        v1_only = columns_v1 - columns_v2
                        v2_only = columns_v2 - columns_v1
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.markdown(f"**Common Columns ({len(common_columns)})**")
                            for col in sorted(common_columns):
                                st.markdown(f"- {col}")
                        
                        with col2:
                            st.markdown(f"**Columns only in V{v1_data['version']} ({len(v1_only)})**")
                            for col in sorted(v1_only):
                                st.markdown(f"- {col}")
                        
                        with col3:
                            st.markdown(f"**Columns only in V{v2_data['version']} ({len(v2_only)})**")
                            for col in sorted(v2_only):
                                st.markdown(f"- {col}")
                        
                        # Compare data samples
                        st.markdown("#### Data Sample Comparison")
                        
                        st.markdown(f"**Version {v1_data['version']} Sample:**")
                        st.dataframe(df1.head(5), use_container_width=True)
                        
                        st.markdown(f"**Version {v2_data['version']} Sample:**")
                        st.dataframe(df2.head(5), use_container_width=True)
                        
                        # Compare numerical statistics for common columns
                        numeric_common_cols = [col for col in common_columns if pd.api.types.is_numeric_dtype(df1[col]) and pd.api.types.is_numeric_dtype(df2[col])]
                        
                        if numeric_common_cols:
                            st.markdown("#### Numeric Column Statistics Comparison")
                            
                            # Let user select a column to compare
                            selected_col = st.selectbox(
                                "Select column to compare",
                                options=numeric_common_cols
                            )
                            
                            if selected_col:
                                # Calculate statistics
                                stats1 = df1[selected_col].describe()
                                stats2 = df2[selected_col].describe()
                                
                                # Create comparison dataframe
                                stats_df = pd.DataFrame({
                                    'Statistic': stats1.index,
                                    f'Version {v1_data["version"]}': stats1.values,
                                    f'Version {v2_data["version"]}': stats2.values,
                                    'Difference': stats2.values - stats1.values
                                })
                                
                                # Format values
                                stats_df[f'Version {v1_data["version"]}'] = stats_df[f'Version {v1_data["version"]}'].round(4)
                                stats_df[f'Version {v2_data["version"]}'] = stats_df[f'Version {v2_data["version"]}'].round(4)
                                stats_df['Difference'] = stats_df['Difference'].round(4)
                                
                                st.table(stats_df)
                                
                                # Create visualization
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    # Distribution comparison
                                    fig = go.Figure()
                                    
                                    # Add histograms
                                    fig.add_trace(go.Histogram(
                                        x=df1[selected_col],
                                        opacity=0.7,
                                        name=f"Version {v1_data['version']}",
                                        marker_color='#4F8BF9'
                                    ))
                                    
                                    fig.add_trace(go.Histogram(
                                        x=df2[selected_col],
                                        opacity=0.7,
                                        name=f"Version {v2_data['version']}",
                                        marker_color='#FF6B6B'
                                    ))
                                    
                                    fig.update_layout(
                                        title=f"Distribution of {selected_col}",
                                        xaxis_title=selected_col,
                                        yaxis_title="Count",
                                        bargap=0.1,
                                        bargroupgap=0.2,
                                        barmode='overlay'
                                    )
                                    
                                    st.plotly_chart(fig, use_container_width=True)
                                
                                with col2:
                                    # Box plot comparison
                                    box_data = []
                                    box_data.append({
                                        'Version': f"Version {v1_data['version']}",
                                        'Values': df1[selected_col].dropna().tolist()
                                    })
                                    
                                    box_data.append({
                                        'Version': f"Version {v2_data['version']}",
                                        'Values': df2[selected_col].dropna().tolist()
                                    })
                                    
                                    # Create box plot
                                    fig = go.Figure()
                                    
                                    fig.add_trace(go.Box(
                                        y=df1[selected_col].dropna(),
                                        name=f"Version {v1_data['version']}",
                                        boxmean=True,
                                        marker_color='#4F8BF9'
                                    ))
                                    
                                    fig.add_trace(go.Box(
                                        y=df2[selected_col].dropna(),
                                        name=f"Version {v2_data['version']}",
                                        boxmean=True,
                                        marker_color='#FF6B6B'
                                    ))
                                    
                                    fig.update_layout(
                                        title=f"Box Plot of {selected_col}",
                                        yaxis_title=selected_col
                                    )
                                    
                                    st.plotly_chart(fig, use_container_width=True)

# Tab 3: Restore Version
with tab3:
    st.subheader("Restore Previous Version")
    
    if not st.session_state.version_history:
        st.info("No version history available yet.")
    else:
        # Select version to restore
        restore_version = st.selectbox(
            "Select version to restore",
            options=[f"V{v['version']}: {v['name']}" for v in st.session_state.version_history],
            key="restore_version"
        )
        restore_version_num = int(restore_version.split(":")[0][1:])
        restore_idx = restore_version_num - 1
        
        # Get version data
        restore_data = st.session_state.version_history[restore_idx]
        
        # Display version info
        st.markdown(f"### {restore_data['name']} (Version {restore_data['version']})")
        st.markdown(f"**Description:** {restore_data['description']}")
        st.markdown(f"**Created on:** {restore_data['timestamp']}")
        st.markdown(f"**Transformations:** {len(restore_data['transformations'])}")
        st.markdown(f"**Shape:** {restore_data['shape'][0]} rows, {restore_data['shape'][1]} columns")
        
        # Restore options
        restore_option = st.radio(
            "How would you like to restore this version?",
            ["Replace current version", "Create new version from this one"]
        )
        
        # Restore button
        if st.button("Restore Version"):
            with st.spinner(f"Restoring version {restore_version_num}..."):
                # Load original dataset
                original_df = None
                if 'file_name' in st.session_state:
                    try:
                        if st.session_state.file_name.endswith('.csv'):
                            original_df = pd.read_csv(st.session_state.file_name)
                        elif st.session_state.file_name.endswith(('.xlsx', '.xls')):
                            original_df = pd.read_excel(st.session_state.file_name)
                    except:
                        st.warning("Could not load original file. Using session dataset as base.")
                        original_df = st.session_state.dataset
                else:
                    original_df = st.session_state.dataset
                
                if original_df is None:
                    st.error("Could not access dataset for restoration.")
                else:
                    # Apply transformations for the version
                    restored_df = apply_transformations(original_df, restore_data['transformations'])
                    
                    if restore_option == "Replace current version":
                        # Replace current dataset and transformations
                        st.session_state.dataset = restored_df
                        st.session_state.transformations = restore_data['transformations'].copy()
                        
                        st.success(f"Successfully restored version {restore_version_num} as the current version.")
                    else:
                        # Create a new version
                        st.session_state.dataset = restored_df
                        st.session_state.transformations = restore_data['transformations'].copy()
                        
                        # Add to version history
                        new_version = {
                            'version': len(st.session_state.version_history) + 1,
                            'name': f"Restored from {restore_data['name']}",
                            'description': f"Restoration of Version {restore_version_num}: {restore_data['description']}",
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'transformations': restore_data['transformations'].copy(),
                            'shape': restored_df.shape
                        }
                        st.session_state.version_history.append(new_version)
                        
                        st.success(f"Successfully created new version from version {restore_version_num}.")
                    
                    st.rerun()

# Navigation buttons
st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    if st.button("← Back to Export Reports", key="back_to_export"):
        st.switch_page("pages/06_Export_Reports.py")

with col2:
    if st.button("Go to Home", key="go_to_home"):
        st.switch_page("app.py")

# Add a sidebar with explanations
with st.sidebar:
    st.header("Version Control Explained")
    
    st.markdown("""
    ### Why Version Control Matters
    
    - **Track changes**: Keep a record of all data transformations
    - **Compare versions**: See how your data has evolved
    - **Restore points**: Go back to previous states if needed
    - **Experimentation**: Try different approaches without fear
    
    ### Best Practices
    
    1. **Create versions** at significant milestones
    
    2. **Use meaningful names** and descriptions for versions
    
    3. **Compare versions** to understand the impact of transformations
    
    4. **Restore with care** - consider creating a new version instead of replacing
    
    5. **Document your process** by adding notes to each version
    """)
    
    st.markdown("---")
    
    st.markdown("""
    **Version Management Tips**:
    
    - Create a snapshot before making significant changes
    - Use the comparison tool to validate transformations
    - Consider exporting important versions as separate files
    """)
