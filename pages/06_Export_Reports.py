import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json
import base64
import io
from utils.export import (
    generate_excel_download_link,
    generate_csv_download_link,
    generate_json_download_link,
    generate_transformation_log,
    generate_insights_download_link,
    export_summary_report,
    save_project,
    load_project
)

st.set_page_config(
    page_title="Export Reports | Analytics Assist",
    page_icon="📤",
    layout="wide"
)

# Check if dataset exists in session state
if 'dataset' not in st.session_state or st.session_state.dataset is None:
    st.warning("Please upload a dataset first.")
    st.button("Go to Upload Page", on_click=lambda: st.switch_page("pages/01_Upload_Data.py"))
    st.stop()

# Header and description
st.title("Export Reports & Save Work")
st.markdown("""
Save your analysis results, export transformed data, and generate reports to share with others.
This page allows you to preserve your work and communicate your findings effectively.
""")

# Get data from session state
df = st.session_state.dataset
transformations = st.session_state.transformations if 'transformations' in st.session_state else []
insights = st.session_state.insights if 'insights' in st.session_state else []

# Create tabs for different export options
tab1, tab2, tab3 = st.tabs([
    "📊 Export Data", 
    "📝 Generate Reports", 
    "💾 Save Project"
])

# Tab 1: Export Data
with tab1:
    st.subheader("Export Transformed Data")
    st.markdown("""
    Export your cleaned and transformed dataset in various formats for use in other tools.
    """)
    
    # Preview of the data to be exported
    st.markdown("### Data Preview")
    st.dataframe(df.head(5), use_container_width=True)
    
    # Data statistics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Rows", df.shape[0])
    
    with col2:
        st.metric("Columns", df.shape[1])
    
    with col3:
        missing_vals = df.isna().sum().sum()
        missing_pct = round(missing_vals / (df.shape[0] * df.shape[1]) * 100, 2)
        st.metric("Missing Values", f"{missing_vals} ({missing_pct}%)")
    
    # Options for export
    st.markdown("### Export Options")
    
    # Export format selection
    export_format = st.selectbox(
        "Select export format",
        ["Excel (.xlsx)", "CSV (.csv)", "JSON (.json)"]
    )
    
    # Customization options
    with st.expander("Customization Options"):
        # Option to include/exclude columns
        include_all_columns = st.checkbox("Include all columns", value=True)
        
        if not include_all_columns:
            selected_columns = st.multiselect(
                "Select columns to include",
                options=df.columns.tolist(),
                default=df.columns.tolist()[:5]  # Default to first 5 columns
            )
        else:
            selected_columns = df.columns.tolist()
        
        # Option to filter rows
        filter_rows = st.checkbox("Filter rows", value=False)
        
        filtered_df = df.copy()
        
        if filter_rows and len(selected_columns) > 0:
            filter_column = st.selectbox("Filter by column", options=selected_columns)
            
            if filter_column:
                # Different filter options based on column type
                if pd.api.types.is_numeric_dtype(df[filter_column]):
                    # Numeric filter
                    min_val = float(df[filter_column].min())
                    max_val = float(df[filter_column].max())
                    
                    filter_range = st.slider(
                        f"Range for {filter_column}",
                        min_value=min_val,
                        max_value=max_val,
                        value=(min_val, max_val)
                    )
                    
                    filtered_df = filtered_df[(filtered_df[filter_column] >= filter_range[0]) & 
                                             (filtered_df[filter_column] <= filter_range[1])]
                
                elif pd.api.types.is_datetime64_dtype(df[filter_column]):
                    # Date filter
                    min_date = df[filter_column].min().date()
                    max_date = df[filter_column].max().date()
                    
                    filter_date_range = st.date_input(
                        f"Date range for {filter_column}",
                        value=(min_date, max_date)
                    )
                    
                    if len(filter_date_range) == 2:
                        start_date, end_date = filter_date_range
                        filtered_df = filtered_df[(filtered_df[filter_column].dt.date >= start_date) & 
                                                 (filtered_df[filter_column].dt.date <= end_date)]
                
                else:
                    # Categorical filter
                    categories = df[filter_column].unique().tolist()
                    selected_categories = st.multiselect(
                        f"Select values for {filter_column}",
                        options=categories,
                        default=categories
                    )
                    
                    if selected_categories:
                        filtered_df = filtered_df[filtered_df[filter_column].isin(selected_categories)]
        
        # Limit to selected columns
        if selected_columns:
            filtered_df = filtered_df[selected_columns]
        
        # Preview filtered data
        st.markdown("### Filtered Data Preview")
        st.dataframe(filtered_df.head(5), use_container_width=True)
        st.info(f"The export will contain {filtered_df.shape[0]} rows and {filtered_df.shape[1]} columns.")
    
    # Export button
    if st.button("Generate Export"):
        if export_format == "Excel (.xlsx)":
            # Generate Excel download link
            excel_link = generate_excel_download_link(filtered_df, "analytics_assist_export.xlsx")
            st.markdown(excel_link, unsafe_allow_html=True)
        
        elif export_format == "CSV (.csv)":
            # Generate CSV download link
            csv_link = generate_csv_download_link(filtered_df, "analytics_assist_export.csv")
            st.markdown(csv_link, unsafe_allow_html=True)
        
        elif export_format == "JSON (.json)":
            # Generate JSON download link
            json_link = generate_json_download_link(filtered_df, "analytics_assist_export.json")
            st.markdown(json_link, unsafe_allow_html=True)
    
    # Transformation log export
    if transformations:
        st.markdown("### Export Transformation Log")
        st.markdown("""
        Export the log of all transformations applied to your dataset.
        This is useful for documenting your data cleaning process.
        """)
        
        log_link = generate_transformation_log(transformations, "transformation_log.json")
        st.markdown(log_link, unsafe_allow_html=True)

# Tab 2: Generate Reports
with tab2:
    st.subheader("Generate Analysis Reports")
    st.markdown("""
    Create comprehensive reports summarizing your data analysis, insights, and transformations.
    These reports can be shared with stakeholders or used for documentation.
    """)
    
    # Report types
    report_type = st.selectbox(
        "Select report type",
        [
            "Comprehensive Summary Report",
            "Data Profile Report",
            "Insights Report",
            "Transformation Report"
        ]
    )
    
    # Comprehensive Summary Report
    if report_type == "Comprehensive Summary Report":
        st.markdown("### Comprehensive Summary Report")
        st.markdown("""
        This report includes:
        - Dataset summary
        - Data sample
        - Key insights
        - Applied transformations
        - Statistical summaries
        """)
        
        # Options for the report
        include_insights = st.checkbox("Include AI-generated insights", value=True)
        include_transformations = st.checkbox("Include transformation history", value=True)
        include_visualizations = st.checkbox("Include visualizations", value=True)
        
        # Generate and download report
        if st.button("Generate Comprehensive Report"):
            with st.spinner("Generating comprehensive report..."):
                # Generate summary report
                report_html = export_summary_report(
                    df,
                    transformations if include_transformations else [],
                    insights if include_insights else [],
                    include_visualizations
                )
                
                # Create download link
                from utils.export import generate_report_download_link
                report_link = generate_report_download_link(report_html, "comprehensive_report.html")
                
                st.success("Report generated successfully!")
                st.markdown(report_link, unsafe_allow_html=True)
    
    # Data Profile Report
    elif report_type == "Data Profile Report":
        st.markdown("### Data Profile Report")
        st.markdown("""
        This report includes:
        - Detailed data type information
        - Distribution visualizations
        - Correlation analyses
        - Missing value summaries
        - Descriptive statistics
        """)
        
        # Generate and download report
        if st.button("Generate Profile Report"):
            with st.spinner("Generating profile report... This may take a minute."):
                try:
                    from utils.data_analyzer import generate_quick_eda_report
                    
                    # Generate profile report
                    report_data = generate_quick_eda_report(df)
                    
                    if report_data:
                        # Decode the base64 report
                        report_html = base64.b64decode(report_data).decode('utf-8')
                        
                        # Create download link
                        from utils.export import generate_report_download_link
                        report_link = generate_report_download_link(report_html, "profile_report.html")
                        
                        st.success("Profile report generated successfully!")
                        st.markdown(report_link, unsafe_allow_html=True)
                    else:
                        st.error("Failed to generate profile report.")
                except Exception as e:
                    st.error(f"Error generating profile report: {str(e)}")
    
    # Insights Report
    elif report_type == "Insights Report":
        st.markdown("### AI Insights Report")
        st.markdown("""
        This report includes:
        - Key insights discovered by AI
        - Importance ratings
        - Recommended actions
        """)
        
        if not insights:
            st.warning("No insights available. Please generate insights in the Insights Dashboard first.")
        else:
            # Generate and download report
            if st.button("Generate Insights Report"):
                with st.spinner("Generating insights report..."):
                    # Sort insights by importance
                    sorted_insights = sorted(insights, key=lambda x: x.get('importance', 0), reverse=True)
                    
                    # Create HTML content for insights report
                    html_content = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>Analytics Assist - Insights Report</title>
                        <style>
                            body {{ font-family: Arial, sans-serif; margin: 20px; }}
                            h1, h2, h3 {{ color: #4F8BF9; }}
                            .insight {{ background-color: #f9f9f9; padding: 15px; margin-bottom: 15px; border-left: 4px solid #4F8BF9; }}
                            .importance {{ font-weight: bold; }}
                            .recommended-action {{ background-color: #e8f4f8; padding: 10px; margin-top: 10px; }}
                        </style>
                    </head>
                    <body>
                        <h1>Analytics Assist - Insights Report</h1>
                        <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                        
                        <h2>Key Insights</h2>
                    """
                    
                    # Add each insight
                    for i, insight in enumerate(sorted_insights):
                        importance = insight.get('importance', 3)
                        stars = '⭐' * importance
                        
                        html_content += f"""
                        <div class="insight">
                            <h3>{i+1}. {insight.get('title', 'Insight')}</h3>
                            <p class="importance">Importance: {stars} ({importance}/5)</p>
                            <p><strong>Type:</strong> {insight.get('type', 'general').title()}</p>
                            <p>{insight.get('description', 'No description available')}</p>
                        """
                        
                        if 'recommended_action' in insight and insight['recommended_action']:
                            html_content += f"""
                            <div class="recommended-action">
                                <p><strong>Recommended Action:</strong> {insight['recommended_action']}</p>
                            </div>
                            """
                        
                        html_content += "</div>"
                    
                    # Close HTML
                    html_content += """
                    </body>
                    </html>
                    """
                    
                    # Create download link
                    from utils.export import generate_report_download_link
                    report_link = generate_report_download_link(html_content, "insights_report.html")
                    
                    st.success("Insights report generated successfully!")
                    st.markdown(report_link, unsafe_allow_html=True)
                    
                    # Also offer JSON download option
                    json_link = generate_insights_download_link(insights, "insights.json")
                    st.markdown("Or download as JSON:")
                    st.markdown(json_link, unsafe_allow_html=True)
    
    # Transformation Report
    elif report_type == "Transformation Report":
        st.markdown("### Transformation Report")
        st.markdown("""
        This report documents all the transformations applied to your data,
        providing a complete audit trail of your data cleaning process.
        """)
        
        if not transformations:
            st.warning("No transformations available. Please apply transformations in the Data Transformation page first.")
        else:
            # Generate and download report
            if st.button("Generate Transformation Report"):
                with st.spinner("Generating transformation report..."):
                    # Create HTML content for transformation report
                    html_content = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>Analytics Assist - Transformation Report</title>
                        <style>
                            body {{ font-family: Arial, sans-serif; margin: 20px; }}
                            h1, h2, h3 {{ color: #4F8BF9; }}
                            table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                            th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
                            th {{ background-color: #f2f2f2; }}
                            .transformation {{ background-color: #f0f8ff; padding: 15px; margin-bottom: 15px; border-left: 4px solid #4F8BF9; }}
                        </style>
                    </head>
                    <body>
                        <h1>Analytics Assist - Transformation Report</h1>
                        <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                        
                        <h2>Transformation Summary</h2>
                        <p>Total transformations applied: {len(transformations)}</p>
                        
                        <h2>Detailed Transformation Log</h2>
                    """
                    
                    # Add each transformation
                    for i, transform in enumerate(transformations):
                        html_content += f"""
                        <div class="transformation">
                            <h3>{i+1}. {transform.get('name', 'Transformation')}</h3>
                            <p><strong>Applied on:</strong> {transform.get('timestamp', '-')}</p>
                            <p><strong>Description:</strong> {transform.get('description', '-')}</p>
                            <p><strong>Affected columns:</strong> {', '.join(transform.get('columns', []))}</p>
                        """
                        
                        # Add parameters if available
                        if 'params' in transform and transform['params']:
                            html_content += "<p><strong>Parameters:</strong></p><ul>"
                            for param, value in transform['params'].items():
                                html_content += f"<li>{param}: {value}</li>"
                            html_content += "</ul>"
                        
                        html_content += "</div>"
                    
                    # Close HTML
                    html_content += """
                    </body>
                    </html>
                    """
                    
                    # Create download link
                    from utils.export import generate_report_download_link
                    report_link = generate_report_download_link(html_content, "transformation_report.html")
                    
                    st.success("Transformation report generated successfully!")
                    st.markdown(report_link, unsafe_allow_html=True)
                    
                    # Also offer JSON download option
                    json_link = generate_transformation_log(transformations, "transformation_log.json")
                    st.markdown("Or download as JSON:")
                    st.markdown(json_link, unsafe_allow_html=True)

# Tab 3: Save Project
with tab3:
    st.subheader("Save & Load Projects")
    st.markdown("""
    Save your current project to return to it later, or load a previously saved project.
    This allows you to continue your analysis across multiple sessions.
    """)
    
    # Create columns for save and load
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Save Current Project")
        
        # Project name input
        current_name = st.session_state.current_project['name'] if 'current_project' in st.session_state and st.session_state.current_project else "My Project"
        project_name = st.text_input("Project name", value=current_name)
        
        # Save button
        if st.button("Save Project"):
            if not project_name:
                st.error("Please enter a project name.")
            else:
                success = save_project(project_name, df, transformations, insights)
                
                if success:
                    # Update current project in session state
                    st.session_state.current_project = {
                        'name': project_name,
                        'file_name': st.session_state.file_name if 'file_name' in st.session_state else "Unknown",
                        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    st.success(f"Project '{project_name}' saved successfully!")
                else:
                    st.error("Failed to save project. Please try again.")
    
    with col2:
        st.markdown("### Load Saved Project")
        
        # Check if there are saved projects
        if 'projects' not in st.session_state or not st.session_state.projects:
            st.info("No saved projects found.")
        else:
            # List of saved projects
            project_names = [p['name'] for p in st.session_state.projects]
            selected_project = st.selectbox("Select a project to load", project_names)
            
            # Load button
            if st.button("Load Project"):
                if not selected_project:
                    st.error("Please select a project to load.")
                else:
                    success = load_project(selected_project)
                    
                    if success:
                        st.success(f"Project '{selected_project}' loaded successfully!")
                        st.rerun()
                    else:
                        st.error(f"Failed to load project '{selected_project}'. Please try again.")
    
    # Export project as file
    st.markdown("### Export/Import Project File")
    
    # Create columns for export and import
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Export Project File")
        st.markdown("""
        Export your entire project as a file that can be shared or imported later.
        This includes the dataset, transformations, and insights.
        """)
        
        if st.button("Export Project File"):
            if 'current_project' not in st.session_state or not st.session_state.current_project:
                st.error("No active project to export.")
            else:
                # Create project export data
                project_export = {
                    'name': st.session_state.current_project.get('name', 'Exported Project'),
                    'created_at': st.session_state.current_project.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                    'exported_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'dataset': df.to_dict() if df is not None else None,
                    'transformations': transformations,
                    'insights': insights
                }
                
                # Convert to JSON
                json_str = json.dumps(project_export, indent=2, default=str)
                
                # Create download link
                b64 = base64.b64encode(json_str.encode()).decode()
                project_file_name = f"{st.session_state.current_project.get('name', 'project').replace(' ', '_')}.aap"  # .aap = Analytics Assist Project
                href = f'<a href="data:file/json;base64,{b64}" download="{project_file_name}">Download Project File</a>'
                
                st.success("Project file created successfully!")
                st.markdown(href, unsafe_allow_html=True)
    
    with col2:
        st.markdown("#### Import Project File")
        st.markdown("""
        Import a previously exported project file to continue your analysis.
        """)
        
        # File uploader for project import
        uploaded_project = st.file_uploader("Upload project file", type=['aap', 'json'])
        
        if uploaded_project is not None:
            if st.button("Import Project"):
                try:
                    # Load project data from file
                    project_data = json.loads(uploaded_project.read())
                    
                    # Check if it has the required structure
                    if 'name' in project_data and 'dataset' in project_data:
                        # Load dataset
                        if project_data['dataset']:
                            imported_df = pd.DataFrame.from_dict(project_data['dataset'])
                            st.session_state.dataset = imported_df
                        
                        # Load transformations
                        if 'transformations' in project_data:
                            st.session_state.transformations = project_data['transformations']
                        
                        # Load insights
                        if 'insights' in project_data:
                            st.session_state.insights = project_data['insights']
                        
                        # Set current project
                        st.session_state.current_project = {
                            'name': project_data['name'],
                            'file_name': uploaded_project.name,
                            'created_at': project_data.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                            'imported_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        
                        st.success(f"Project '{project_data['name']}' imported successfully!")
                        st.rerun()
                    else:
                        st.error("Invalid project file format.")
                except Exception as e:
                    st.error(f"Error importing project: {str(e)}")

# Navigation buttons
st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    if st.button("← Back to Insights Dashboard", key="back_to_insights"):
        st.switch_page("pages/05_Insights_Dashboard.py")

with col2:
    if st.button("Go to Version History →", key="go_to_version"):
        st.switch_page("pages/07_Version_History.py")

# Add a sidebar with tips
with st.sidebar:
    st.header("Export & Sharing Tips")
    
    st.markdown("""
    ### Why Export Your Analysis?
    
    - **Documentation**: Keep a record of your data cleaning process
    - **Collaboration**: Share insights with team members
    - **Presentation**: Create professional reports for stakeholders
    - **Continuity**: Save your work to continue later
    
    ### Best Practices
    
    1. **Include metadata** in your reports (date, author, data source)
    
    2. **Export transformed data** for use in other tools
    
    3. **Save projects regularly** to avoid losing work
    
    4. **Export the transformation log** for data governance
    
    5. **Share insights** with context and recommendations
    """)
    
    st.markdown("---")
    
    st.markdown("""
    **Export formats**:
    - **Excel**: Best for viewing and simple further analysis
    - **CSV**: Most compatible with other tools
    - **JSON**: Best for preserving data structures
    - **HTML Reports**: Best for sharing with non-technical users
    """)
