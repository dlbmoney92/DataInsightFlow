import streamlit as st

# Set page configuration - must be the first Streamlit command
st.set_page_config(
    page_title="Export Reports | Analytics Assist",
    page_icon="📤",
    layout="wide"
)

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json
import base64
import io
import uuid
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
from utils.auth_redirect import require_auth
from utils.custom_navigation import render_navigation, initialize_navigation
from utils.global_config import apply_global_css
from utils.access_control import check_access

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

# Get the dataset
df = st.session_state.dataset

# Sidebar
st.sidebar.subheader("Dataset Info")
st.sidebar.info(f"""
- **Rows**: {df.shape[0]}
- **Columns**: {df.shape[1]}
- **Project**: {st.session_state.current_project.get('name', 'Unnamed project')}
""")

# Main content
tab1, tab2, tab3, tab4 = st.tabs(["Export Data", "Generate Reports", "Save & Load Work", "Share Reports"])

with tab1:
    st.header("Export Processed Data")
    
    # Data preview
    st.subheader("Data Preview")
    st.dataframe(df.head(5), use_container_width=True)
    
    # Export options
    st.subheader("Export Options")
    
    # Row selection
    row_option = st.radio(
        "Rows to export",
        ["All rows", "First N rows", "Sample rows", "Filter rows"]
    )
    
    if row_option == "First N rows":
        n_rows = st.slider("Number of rows", 1, min(1000, df.shape[0]), 100)
        export_df = df.head(n_rows)
    elif row_option == "Sample rows":
        n_rows = st.slider("Number of rows", 1, min(1000, df.shape[0]), 100)
        export_df = df.sample(n_rows)
    elif row_option == "Filter rows":
        column = st.selectbox("Filter column", df.columns)
        if pd.api.types.is_numeric_dtype(df[column]):
            min_val = float(df[column].min())
            max_val = float(df[column].max())
            filter_range = st.slider(
                "Value range",
                min_val, max_val, (min_val, max_val)
            )
            export_df = df[(df[column] >= filter_range[0]) & (df[column] <= filter_range[1])]
        else:
            unique_values = df[column].unique()
            selected_values = st.multiselect("Select values", unique_values, unique_values[:3])
            export_df = df[df[column].isin(selected_values)]
    else:  # All rows
        export_df = df
    
    # Column selection
    col_option = st.radio(
        "Columns to export",
        ["All columns", "Select columns"]
    )
    
    if col_option == "Select columns":
        selected_columns = st.multiselect("Select columns", df.columns, df.columns[:5])
        export_df = export_df[selected_columns]
    
    # Format selection
    st.subheader("Export Format")
    
    # Get available export formats for the current subscription tier
    available_formats = check_access("export_format", None)
    if isinstance(available_formats, list):
        allowed_formats = available_formats
    else:
        allowed_formats = ["csv"]  # Default to CSV only if check_access fails
    
    # Display a message about available formats
    st.info(f"Your subscription ({st.session_state.subscription_tier.capitalize()}) allows export in the following formats: {', '.join([f.upper() for f in allowed_formats])}")
    
    # Determine how many columns we need based on available formats
    format_cols = st.columns(min(3, len(allowed_formats)))
    
    # CSV (available to all tiers)
    if "csv" in allowed_formats:
        with format_cols[0]:
            if st.button("Export as CSV", use_container_width=True):
                csv_link = generate_csv_download_link(export_df, filename=f"{st.session_state.current_project.get('name', 'data')}.csv")
                st.markdown(csv_link, unsafe_allow_html=True)
    
    # Excel (available to basic, pro and enterprise tiers)
    if "excel" in allowed_formats:
        col_index = min(1, len(format_cols) - 1)
        with format_cols[col_index]:
            if st.button("Export as Excel", use_container_width=True):
                excel_link = generate_excel_download_link(export_df, filename=f"{st.session_state.current_project.get('name', 'data')}.xlsx")
                st.markdown(excel_link, unsafe_allow_html=True)
    
    # JSON (available to pro and enterprise tiers)
    if "json" in allowed_formats:
        col_index = min(2, len(format_cols) - 1)
        with format_cols[col_index]:
            if st.button("Export as JSON", use_container_width=True):
                json_link = generate_json_download_link(export_df, filename=f"{st.session_state.current_project.get('name', 'data')}.json")
                st.markdown(json_link, unsafe_allow_html=True)
    
    # PDF (available to basic, pro and enterprise tiers)
    if "pdf" in allowed_formats:
        st.markdown("---")
        if st.button("Export as PDF", use_container_width=True):
            # Create a simple PDF report
            try:
                import matplotlib.pyplot as plt
                from io import BytesIO
                import base64
                
                buffer = BytesIO()
                plt.figure(figsize=(10, 6))
                plt.axis('off')
                
                # Create a table representation
                table_data = export_df.head(50).values  # Limit to 50 rows for PDF
                table_cols = export_df.columns
                
                # Create a table visualization
                table = plt.table(
                    cellText=table_data,
                    colLabels=table_cols,
                    cellLoc='center',
                    loc='center'
                )
                
                # Adjust table size
                table.auto_set_font_size(False)
                table.set_fontsize(9)
                table.scale(1.2, 1.2)
                
                plt.title(f"{st.session_state.current_project.get('name', 'Data Export')}")
                plt.tight_layout()
                
                # Save to PDF file via png in memory
                plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
                buffer.seek(0)
                
                # Create download link for PDF
                pdf_download_link = f'<a href="data:application/pdf;base64,{base64.b64encode(buffer.getvalue()).decode()}" download="{st.session_state.current_project.get("name", "data")}.pdf">Download PDF Report</a>'
                st.markdown(pdf_download_link, unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"Error creating PDF export: {e}")
    
    # Export transformation history
    if 'transformations' in st.session_state and st.session_state.transformations:
        st.subheader("Export Transformation Log")
        if st.button("Export Transformation History"):
            transformation_link = generate_transformation_log(
                st.session_state.transformations, 
                filename=f"{st.session_state.current_project.get('name', 'data')}_transformations.json"
            )
            st.markdown(transformation_link, unsafe_allow_html=True)

with tab2:
    st.header("Generate Analysis Reports")
    
    # Check if user has access to report exports (requires at least the basic tier)
    can_export_reports = check_access("export_format", "pdf")
    
    # Initialize report_type with a default value
    report_type = None
    
    if not can_export_reports:
        st.warning("Report generation requires a Basic subscription or higher. Please upgrade your subscription to access this feature.")
        
        # Show a button to upgrade
        if st.button("View Subscription Options"):
            st.switch_page("pages/subscription.py")
    else:
        # Report options
        st.subheader("Report Type")
        
        report_type = st.selectbox(
            "Select report type",
            ["Summary Report", "Data Quality Report", "Insight Report", "Custom Report"]
        )
    
    if report_type == "Summary Report" and can_export_reports:
        include_transformations = st.checkbox("Include transformation history", value=True)
        include_insights = st.checkbox("Include insights", value=True)
        include_visualizations = st.checkbox("Include visualizations", value=True)
        
        transformations = st.session_state.transformations if 'transformations' in st.session_state and include_transformations else []
        insights = st.session_state.generated_insights if 'generated_insights' in st.session_state and include_insights else []
        
        if st.button("Generate Summary Report"):
            with st.spinner("Generating report..."):
                report_html = export_summary_report(
                    df, 
                    transformations, 
                    insights
                )
                
                download_link = f'<a href="data:text/html;base64,{base64.b64encode(report_html.encode()).decode()}" download="{st.session_state.current_project.get("name", "report")}_summary.html">Download Summary Report</a>'
                st.markdown(download_link, unsafe_allow_html=True)
    
    elif report_type == "Data Quality Report" and can_export_reports:
        # Options for data quality report
        include_missing_values = st.checkbox("Include missing values analysis", value=True)
        include_outliers = st.checkbox("Include outlier analysis", value=True)
        include_distributions = st.checkbox("Include distribution analysis", value=True)
        
        if st.button("Generate Data Quality Report"):
            with st.spinner("Generating report..."):
                # Create data quality report
                missing_data = df.isnull().sum()
                missing_pct = 100 * missing_data / len(df)
                missing_analysis = pd.concat([missing_data, missing_pct], axis=1)
                missing_analysis.columns = ['Missing Values', '% Missing']
                
                report_html = """
                <html>
                <head>
                    <title>Data Quality Report</title>
                    <style>
                        body { font-family: Arial, sans-serif; margin: 20px; }
                        .header { text-align: center; margin-bottom: 30px; }
                        .section { margin-bottom: 20px; }
                        table { border-collapse: collapse; width: 100%; }
                        th, td { border: 1px solid #ddd; padding: 8px; }
                        th { background-color: #f2f2f2; }
                        tr:nth-child(even) { background-color: #f9f9f9; }
                    </style>
                </head>
                <body>
                    <div class="header">
                        <h1>Data Quality Report</h1>
                        <p>Generated on {date} for project: {project}</p>
                    </div>
                    
                    <div class="section">
                        <h2>Dataset Overview</h2>
                        <p>Rows: {rows}</p>
                        <p>Columns: {cols}</p>
                        <p>Memory Usage: {memory} MB</p>
                    </div>
                """.format(
                    date=datetime.now().strftime("%Y-%m-%d %H:%M"),
                    project=st.session_state.current_project.get('name', 'Unnamed project'),
                    rows=df.shape[0],
                    cols=df.shape[1],
                    memory=round(df.memory_usage(deep=True).sum() / (1024 * 1024), 2)
                )
                
                if include_missing_values:
                    report_html += """
                    <div class="section">
                        <h2>Missing Values Analysis</h2>
                        <table>
                            <tr>
                                <th>Column</th>
                                <th>Missing Values</th>
                                <th>% Missing</th>
                            </tr>
                    """
                    
                    for index, row in missing_analysis[missing_analysis['Missing Values'] > 0].iterrows():
                        report_html += f"""
                            <tr>
                                <td>{index}</td>
                                <td>{row['Missing Values']}</td>
                                <td>{row['% Missing']:.2f}%</td>
                            </tr>
                        """
                    
                    report_html += """
                        </table>
                    </div>
                    """
                
                if include_outliers:
                    report_html += """
                    <div class="section">
                        <h2>Outlier Analysis</h2>
                        <table>
                            <tr>
                                <th>Column</th>
                                <th>Min</th>
                                <th>Max</th>
                                <th>Mean</th>
                                <th>Std Dev</th>
                                <th>Lower Bound</th>
                                <th>Upper Bound</th>
                                <th>Outliers</th>
                            </tr>
                    """
                    
                    for col in df.select_dtypes(include=np.number).columns:
                        mean = df[col].mean()
                        std = df[col].std()
                        lower_bound = mean - 3 * std
                        upper_bound = mean + 3 * std
                        outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)].shape[0]
                        
                        report_html += f"""
                            <tr>
                                <td>{col}</td>
                                <td>{df[col].min():.2f}</td>
                                <td>{df[col].max():.2f}</td>
                                <td>{mean:.2f}</td>
                                <td>{std:.2f}</td>
                                <td>{lower_bound:.2f}</td>
                                <td>{upper_bound:.2f}</td>
                                <td>{outliers} ({100*outliers/df.shape[0]:.2f}%)</td>
                            </tr>
                        """
                    
                    report_html += """
                        </table>
                    </div>
                    """
                
                if include_distributions:
                    report_html += """
                    <div class="section">
                        <h2>Distribution Analysis</h2>
                        <table>
                            <tr>
                                <th>Column</th>
                                <th>Data Type</th>
                                <th>Unique Values</th>
                                <th>Distribution</th>
                            </tr>
                    """
                    
                    for col in df.columns:
                        dtype = df[col].dtype
                        unique = df[col].nunique()
                        
                        if pd.api.types.is_numeric_dtype(df[col]):
                            distribution = "Numeric"
                        elif pd.api.types.is_categorical_dtype(df[col]) or df[col].dtype == 'object':
                            distribution = "Categorical"
                        elif pd.api.types.is_datetime64_any_dtype(df[col]):
                            distribution = "Datetime"
                        else:
                            distribution = "Other"
                        
                        report_html += f"""
                            <tr>
                                <td>{col}</td>
                                <td>{dtype}</td>
                                <td>{unique}</td>
                                <td>{distribution}</td>
                            </tr>
                        """
                    
                    report_html += """
                        </table>
                    </div>
                    """
                
                report_html += """
                </body>
                </html>
                """
                
                download_link = f'<a href="data:text/html;base64,{base64.b64encode(report_html.encode()).decode()}" download="{st.session_state.current_project.get("name", "report")}_data_quality.html">Download Data Quality Report</a>'
                st.markdown(download_link, unsafe_allow_html=True)
    
    elif report_type == "Insight Report" and can_export_reports:
        if 'generated_insights' not in st.session_state or not st.session_state.generated_insights:
            st.warning("No insights have been generated yet. Please go to the Insights Dashboard to generate insights first.")
        else:
            include_visualizations = st.checkbox("Include visualizations", value=True)
            
            if st.button("Generate Insight Report"):
                with st.spinner("Generating report..."):
                    insights = st.session_state.generated_insights
                    
                    report_html = """
                    <html>
                    <head>
                        <title>Insight Report</title>
                        <style>
                            body { font-family: Arial, sans-serif; margin: 20px; }
                            .header { text-align: center; margin-bottom: 30px; }
                            .section { margin-bottom: 30px; }
                            .insight { margin-bottom: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
                            .insight-title { font-weight: bold; margin-bottom: 10px; font-size: 18px; }
                            .insight-category { color: #666; font-style: italic; }
                        </style>
                    </head>
                    <body>
                        <div class="header">
                            <h1>Insight Report</h1>
                            <p>Generated on {date} for project: {project}</p>
                        </div>
                    """.format(
                        date=datetime.now().strftime("%Y-%m-%d %H:%M"),
                        project=st.session_state.current_project.get('name', 'Unnamed project')
                    )
                    
                    # Group insights by category
                    categories = {}
                    for insight in insights:
                        category = insight.get('category', 'general')
                        if category not in categories:
                            categories[category] = []
                        categories[category].append(insight)
                    
                    # Add insights by category
                    for category, category_insights in categories.items():
                        report_html += f"""
                        <div class="section">
                            <h2>{category.capitalize()} Insights</h2>
                        """
                        
                        for insight in category_insights:
                            report_html += f"""
                            <div class="insight">
                                <div class="insight-title">{insight['title']}</div>
                                <div class="insight-category">Category: {insight['category']}</div>
                                <p>{insight['description']}</p>
                            </div>
                            """
                        
                        report_html += """
                        </div>
                        """
                    
                    report_html += """
                    </body>
                    </html>
                    """
                    
                    download_link = f'<a href="data:text/html;base64,{base64.b64encode(report_html.encode()).decode()}" download="{st.session_state.current_project.get("name", "report")}_insights.html">Download Insight Report</a>'
                    st.markdown(download_link, unsafe_allow_html=True)
    
    elif report_type == "Custom Report" and can_export_reports:
        st.subheader("Custom Report Options")
        
        # Title
        title = st.text_input("Report Title", value=f"{st.session_state.current_project.get('name', 'Data')} Analysis Report")
        
        # Sections to include
        include_overview = st.checkbox("Include Dataset Overview", value=True)
        include_transformations = st.checkbox("Include Transformation History", value=True)
        include_insights = st.checkbox("Include AI Insights", value=True)
        include_stats = st.checkbox("Include Statistics", value=True)
        include_visualizations = st.checkbox("Include Visualizations", value=True)
        
        # Custom text
        custom_intro = st.text_area("Introduction Text", value="This report presents the analysis results for the dataset.")
        custom_conclusion = st.text_area("Conclusion Text", value="The analysis provides valuable insights into the dataset patterns and characteristics.")
        
        if st.button("Generate Custom Report"):
            with st.spinner("Generating report..."):
                # Create the report HTML
                report_html = f"""
                <html>
                <head>
                    <title>{title}</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 20px; }}
                        .header {{ text-align: center; margin-bottom: 30px; }}
                        .section {{ margin-bottom: 30px; }}
                        .insight {{ margin-bottom: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
                        table {{ border-collapse: collapse; width: 100%; }}
                        th, td {{ border: 1px solid #ddd; padding: 8px; }}
                        th {{ background-color: #f2f2f2; }}
                        tr:nth-child(even) {{ background-color: #f9f9f9; }}
                    </style>
                </head>
                <body>
                    <div class="header">
                        <h1>{title}</h1>
                        <p>Generated on {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>
                    </div>
                    
                    <div class="section">
                        <h2>Introduction</h2>
                        <p>{custom_intro}</p>
                    </div>
                """
                
                if include_overview:
                    report_html += f"""
                    <div class="section">
                        <h2>Dataset Overview</h2>
                        <p>Rows: {df.shape[0]}</p>
                        <p>Columns: {df.shape[1]}</p>
                        <p>Memory Usage: {round(df.memory_usage(deep=True).sum() / (1024 * 1024), 2)} MB</p>
                        
                        <h3>Columns</h3>
                        <table>
                            <tr>
                                <th>Column</th>
                                <th>Data Type</th>
                                <th>Non-Null Count</th>
                                <th>Unique Values</th>
                            </tr>
                    """
                    
                    for col in df.columns:
                        report_html += f"""
                            <tr>
                                <td>{col}</td>
                                <td>{df[col].dtype}</td>
                                <td>{df[col].count()} ({100 * df[col].count() / len(df):.1f}%)</td>
                                <td>{df[col].nunique()}</td>
                            </tr>
                        """
                    
                    report_html += """
                        </table>
                    </div>
                    """
                
                if include_transformations and 'transformations' in st.session_state and st.session_state.transformations:
                    report_html += """
                    <div class="section">
                        <h2>Transformation History</h2>
                        <table>
                            <tr>
                                <th>#</th>
                                <th>Transformation</th>
                                <th>Applied At</th>
                            </tr>
                    """
                    
                    for i, t in enumerate(st.session_state.transformations):
                        report_html += f"""
                            <tr>
                                <td>{i+1}</td>
                                <td>{t['name']}</td>
                                <td>{t['timestamp']}</td>
                            </tr>
                        """
                    
                    report_html += """
                        </table>
                    </div>
                    """
                
                if include_insights and 'generated_insights' in st.session_state and st.session_state.generated_insights:
                    report_html += """
                    <div class="section">
                        <h2>AI Insights</h2>
                    """
                    
                    for insight in st.session_state.generated_insights:
                        report_html += f"""
                        <div class="insight">
                            <h3>{insight['title']}</h3>
                            <p>{insight['description']}</p>
                        </div>
                        """
                    
                    report_html += """
                    </div>
                    """
                
                if include_stats:
                    report_html += """
                    <div class="section">
                        <h2>Statistical Summary</h2>
                        <table>
                            <tr>
                                <th>Statistic</th>
                    """
                    
                    numeric_cols = df.select_dtypes(include=np.number).columns
                    
                    for col in numeric_cols:
                        report_html += f"""
                                <th>{col}</th>
                        """
                    
                    report_html += """
                            </tr>
                    """
                    
                    stats = ['count', 'mean', 'std', 'min', '25%', '50%', '75%', 'max']
                    desc = df.describe().transpose()
                    
                    for stat in stats:
                        report_html += f"""
                            <tr>
                                <td>{stat}</td>
                        """
                        
                        for col in numeric_cols:
                            report_html += f"""
                                <td>{desc.loc[col, stat]:.2f}</td>
                            """
                        
                        report_html += """
                            </tr>
                        """
                    
                    report_html += """
                        </table>
                    </div>
                    """
                
                report_html += f"""
                    <div class="section">
                        <h2>Conclusion</h2>
                        <p>{custom_conclusion}</p>
                    </div>
                </body>
                </html>
                """
                
                download_link = f'<a href="data:text/html;base64,{base64.b64encode(report_html.encode()).decode()}" download="{title.replace(" ", "_")}.html">Download Custom Report</a>'
                st.markdown(download_link, unsafe_allow_html=True)

with tab3:
    st.header("Save & Load Work")
    
    # Save project
    st.subheader("Save Current Analysis")
    project_name = st.text_input("Project Name", value=st.session_state.current_project.get('name', 'My Analysis Project'))
    
    save_cols = st.columns(2)
    
    with save_cols[0]:
        if st.button("Save to Database", use_container_width=True):
            if 'dataset_id' in st.session_state:
                from utils.database import save_version
                
                # Get version number
                if 'saved_versions' not in st.session_state:
                    st.session_state.saved_versions = []
                
                version_number = len(st.session_state.saved_versions) + 1
                description = f"Version {version_number} - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                
                # Save version
                try:
                    transformations = st.session_state.transformations if 'transformations' in st.session_state else []
                    
                    version_id = save_version(
                        st.session_state.dataset_id,
                        version_number,
                        project_name,
                        description,
                        df,
                        json.dumps(transformations)
                    )
                    
                    # Store version in session state
                    st.session_state.saved_versions.append({
                        "id": version_id,
                        "name": project_name,
                        "description": description,
                        "version": version_number,
                        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
                    
                    st.success(f"Project saved as Version {version_number}!")
                except Exception as e:
                    st.error(f"Error saving project: {str(e)}")
            else:
                st.error("Please save the dataset first by going to the Upload Data page.")
    
    with save_cols[1]:
        if st.button("Save to Session", use_container_width=True):
            try:
                transformations = st.session_state.transformations if 'transformations' in st.session_state else []
                insights = st.session_state.generated_insights if 'generated_insights' in st.session_state else []
                
                save_project(project_name, df, transformations, insights)
                
                st.success(f"Project '{project_name}' saved to session!")
            except Exception as e:
                st.error(f"Error saving project: {str(e)}")
    
    # Load project
    st.subheader("Load Saved Work")
    
    # Load from database
    if 'dataset_id' in st.session_state:
        from utils.database import get_versions
        
        # Get all versions for the dataset
        try:
            versions = get_versions(st.session_state.dataset_id)
            
            if versions:
                st.session_state.saved_versions = versions
                
                # Create a selection for versions
                version_options = [f"Version {v['version']} - {v['name']} ({v['timestamp']})" for v in versions]
                selected_version = st.selectbox("Select saved version", version_options)
                
                if st.button("Load Selected Version"):
                    # Find the selected version
                    version_index = version_options.index(selected_version)
                    version = versions[version_index]
                    
                    # Load version
                    from utils.database import get_version
                    version_data = get_version(version['id'])
                    
                    if version_data and 'df' in version_data:
                        # Update session state
                        st.session_state.dataset = version_data['df']
                        
                        # Parse transformations if available
                        if 'transformations_applied' in version_data and version_data['transformations_applied']:
                            try:
                                st.session_state.transformations = json.loads(version_data['transformations_applied'])
                            except:
                                st.session_state.transformations = []
                        
                        st.success(f"Version {version['version']} loaded successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to load version data.")
            else:
                st.info("No saved versions found for this dataset.")
        except Exception as e:
            st.error(f"Error loading versions: {str(e)}")
    
    # Load from session
    if 'saved_projects' in st.session_state and st.session_state.saved_projects:
        project_names = list(st.session_state.saved_projects.keys())
        selected_project = st.selectbox("Select session project", project_names)
        
        if st.button("Load Project from Session"):
            try:
                loaded_project = load_project(selected_project)
                
                if loaded_project:
                    # Update session state
                    st.session_state.dataset = loaded_project['df']
                    st.session_state.transformations = loaded_project['transformations']
                    st.session_state.generated_insights = loaded_project['insights']
                    
                    st.success(f"Project '{selected_project}' loaded successfully!")
                    st.rerun()
                else:
                    st.error("Failed to load project.")
            except Exception as e:
                st.error(f"Error loading project: {str(e)}")
    else:
        st.info("No projects saved in session.")

with tab4:
    # Import sharing functionality
    from utils.sharing import create_share_link, generate_share_card, export_visualization_with_branding, add_branding_to_figure, generate_qr_code, generate_report_summary
    
    st.header("Share Reports and Insights")
    st.markdown("""
    Create shareable links to your reports, visualizations, and insights. 
    These links can be shared with colleagues or posted on social media.
    """)
    
    # Check if user has access to sharing features
    can_share = check_access("sharing", None) 
    
    if not can_share:
        st.warning("Sharing reports requires a subscription. Please upgrade your subscription to access this feature.")
        
        # Show a button to upgrade
        if st.button("View Subscription Options", key="upgrade_share"):
            st.switch_page("pages/subscription.py")
    
    # Get the allowed sharing formats for the user's subscription tier
    sharing_formats = []
    if check_access("sharing_format", "pdf"):
        sharing_formats.append("pdf")
    if check_access("sharing_format", "image"):
        sharing_formats.append("image")
    if check_access("sharing_format", "interactive"):
        sharing_formats.append("interactive")
        
    if can_share:
        # Display available sharing formats
        format_labels = {
            "pdf": "PDF Document",
            "image": "Image",
            "interactive": "Interactive Web"
        }
        
        available_formats = []
        for fmt in sharing_formats:
            available_formats.append(format_labels.get(fmt, fmt.capitalize()))
        
        if sharing_formats:
            st.info(f"Your subscription allows sharing in these formats: {', '.join(available_formats)}")
        
        share_type = st.radio(
            "What would you like to share?", 
            ["Complete Report", "Specific Visualization", "Key Insight"]
        )
        
        if share_type == "Complete Report":
            st.subheader("Share Full Analysis Report")
            
            # Options for what to include in the shared report
            include_transformations = st.checkbox("Include transformation history", value=True, key="share_include_trans")
            include_insights = st.checkbox("Include insights", value=True, key="share_include_insights")
            include_visualizations = st.checkbox("Include visualizations", value=True, key="share_include_viz")
            
            # Add a title for the shared report
            report_title = st.text_input("Report Title", value=f"{st.session_state.current_project.get('name', 'Analysis')} Report")
            
            # Check if user has access to PDF sharing format
            can_share_pdf = check_access("sharing_format", "pdf")
            
            if not can_share_pdf:
                st.warning("Sharing reports requires PDF sharing access. Please upgrade your subscription.")
                # Show a button to upgrade
                if st.button("View Subscription Options", key="upgrade_pdf_share"):
                    st.switch_page("pages/subscription.py")
            else:
                # Add a button to generate the shareable link
                if st.button("Generate Shareable Report Link"):
                    with st.spinner("Generating shareable report..."):
                        # Prepare the report data
                        transformations = st.session_state.transformations if 'transformations' in st.session_state and include_transformations else []
                        insights = st.session_state.generated_insights if 'generated_insights' in st.session_state and include_insights else []
                        
                        # Generate the HTML report
                        report_html = export_summary_report(
                            df, 
                            transformations, 
                            insights,
                            add_branding=True
                        )
                        
                        # Prepare the report data for sharing
                        report_data = {
                            "title": report_title,
                            "html": report_html,
                            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "summary": generate_report_summary(df, insights)
                        }
                        
                        # Create a share link
                        share_id = str(uuid.uuid4())
                        share_link = create_share_link("report", share_id, report_data)
                        
                        # Display the sharing card
                        generate_share_card(report_title, "report", share_link, include_social=True)
                        
                        # Option to add QR code
                        if st.checkbox("Include QR code in downloaded reports", value=True):
                            qr_data = generate_qr_code(share_link)
                            st.image(f"data:image/png;base64,{qr_data}", caption="Scan to view report", width=150)
        
        elif share_type == "Specific Visualization":
            st.subheader("Share a Visualization")
            
            # Check if we have visualizations to share
            if 'generated_visualizations' not in st.session_state or not st.session_state.generated_visualizations:
                st.warning("No visualizations available to share. Generate visualizations in the EDA Dashboard first.")
            else:
                viz_options = []
                for i, viz in enumerate(st.session_state.generated_visualizations):
                    if isinstance(viz, dict) and 'title' in viz:
                        viz_options.append(f"{i+1}. {viz['title']}")
                    else:
                        viz_options.append(f"Visualization {i+1}")
                
                selected_viz = st.selectbox("Select visualization to share", viz_options)
                viz_index = int(selected_viz.split('.')[0]) - 1
                
                # Get the selected visualization
                viz = st.session_state.generated_visualizations[viz_index]
                
                # Display the visualization for preview
                if isinstance(viz, dict) and 'figure' in viz:
                    st.subheader("Preview")
                    fig = go.Figure(viz['figure'])
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Add title for sharing
                    viz_title = st.text_input("Visualization Title", value=viz.get('title', f"Visualization {viz_index+1}"))
                    viz_description = st.text_area("Description (optional)", value=viz.get('description', ''))
                    
                    # Check if user has access to image sharing format
                    can_share_image = check_access("sharing_format", "image")
                    
                    if not can_share_image and not check_access("sharing_format", "pdf") and not check_access("sharing_format", "interactive"):
                        st.warning("Sharing visualizations requires appropriate sharing access. Please upgrade your subscription.")
                        # Show a button to upgrade
                        if st.button("View Subscription Options", key="upgrade_viz_share"):
                            st.switch_page("pages/subscription.py")
                    else:
                        # Button to generate shareable link
                        if st.button("Generate Shareable Visualization Link"):
                            with st.spinner("Generating shareable visualization..."):
                                # Prepare the visualization for sharing
                                viz_data = {
                                    "title": viz_title,
                                    "description": viz_description,
                                    "figure": viz['figure'],
                                    "date": datetime.now().strftime("%Y-%m-%d %H:%M")
                                }
                                
                                # Create a share link
                                share_id = str(uuid.uuid4())
                                share_link = create_share_link("visualization", share_id, viz_data)
                                
                                # Display the sharing card
                                generate_share_card(viz_title, "visualization", share_link, include_social=True)
                                
                                # Add export with branding option
                                st.subheader("Export with Branding")
                                
                                export_cols = st.columns(3)
                                with export_cols[0]:
                                    if st.button("Export as PNG", use_container_width=True):
                                        # Add branding to the figure
                                        branded_fig = add_branding_to_figure(fig, viz_title)
                                        img_bytes = export_visualization_with_branding(branded_fig, viz_title, format='png')
                                        
                                        # Create download link
                                        b64 = base64.b64encode(img_bytes).decode()
                                        href = f'<a href="data:image/png;base64,{b64}" download="{viz_title.replace(" ", "_")}.png">Download PNG</a>'
                                        st.markdown(href, unsafe_allow_html=True)
                                
                                with export_cols[1]:
                                    if st.button("Export as SVG", use_container_width=True):
                                        # Add branding to the figure
                                        branded_fig = add_branding_to_figure(fig, viz_title)
                                        img_bytes = export_visualization_with_branding(branded_fig, viz_title, format='svg')
                                        
                                        # Create download link
                                        b64 = base64.b64encode(img_bytes).decode()
                                        href = f'<a href="data:image/svg+xml;base64,{b64}" download="{viz_title.replace(" ", "_")}.svg">Download SVG</a>'
                                        st.markdown(href, unsafe_allow_html=True)
                                
                                with export_cols[2]:
                                    if st.button("Export as PDF", use_container_width=True):
                                        # Add branding to the figure
                                        branded_fig = add_branding_to_figure(fig, viz_title)
                                        pdf_bytes = export_visualization_with_branding(branded_fig, viz_title, format='pdf')
                                        
                                        # Create download link
                                        b64 = base64.b64encode(pdf_bytes).decode()
                                        href = f'<a href="data:application/pdf;base64,{b64}" download="{viz_title.replace(" ", "_")}.pdf">Download PDF</a>'
                                        st.markdown(href, unsafe_allow_html=True)
        
        elif share_type == "Key Insight":
            st.subheader("Share a Key Insight")
            
            # Check if we have insights to share
            if 'generated_insights' not in st.session_state or not st.session_state.generated_insights:
                st.warning("No insights available to share. Generate insights in the Insights Dashboard first.")
            else:
                insight_options = []
                for i, insight in enumerate(st.session_state.generated_insights):
                    if isinstance(insight, dict) and 'title' in insight:
                        insight_options.append(f"{i+1}. {insight['title']}")
                    else:
                        insight_options.append(f"Insight {i+1}")
                
                selected_insight = st.selectbox("Select insight to share", insight_options)
                insight_index = int(selected_insight.split('.')[0]) - 1
                
                # Get the selected insight
                insight = st.session_state.generated_insights[insight_index]
                
                if isinstance(insight, dict):
                    # Display the insight for preview
                    st.subheader("Preview")
                    
                    # Display the insight
                    importance = insight.get('importance', 3)
                    stars = "⭐" * importance
                    st.markdown(f"{stars} **{insight.get('category', 'General')}**")
                    st.markdown(f"### {insight.get('title', 'Insight')}")
                    st.markdown(insight.get('text', ''))
                    
                    # Add title for sharing
                    insight_title = st.text_input("Insight Title", value=insight.get('title', f"Insight {insight_index+1}"))
                    
                    # Check if user has access to PDF sharing format
                    can_share_pdf = check_access("sharing_format", "pdf")
                    
                    if not can_share_pdf:
                        st.warning("Sharing insights requires PDF sharing access. Please upgrade your subscription.")
                        # Show a button to upgrade
                        if st.button("View Subscription Options", key="upgrade_insight_share"):
                            st.switch_page("pages/subscription.py")
                    else:
                        # Button to generate shareable link
                        if st.button("Generate Shareable Insight Link"):
                            with st.spinner("Generating shareable insight..."):
                                # Prepare the insight for sharing
                                insight_data = {
                                    "title": insight_title,
                                    "text": insight.get('text', ''),
                                    "importance": importance,
                                    "category": insight.get('category', 'General'),
                                    "source": "Analytics Assist AI Analysis",
                                    "date": datetime.now().strftime("%Y-%m-%d %H:%M")
                                }
                                
                                # Create a share link
                                share_id = str(uuid.uuid4())
                                share_link = create_share_link("insight", share_id, insight_data)
                                
                                # Display the sharing card
                                generate_share_card(insight_title, "insight", share_link, include_social=True)
        
        st.markdown("""
        ---
        ### Tips for Effective Sharing
        - Use clear and descriptive titles for your shared content
        - Include a brief explanation to provide context for your audience
        - For professional settings, export reports with your organization's branding
        - Share links directly to specific visualizations when discussing particular findings
        """)

# Navigation buttons at the bottom
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("← Insights Dashboard", use_container_width=True):
        st.switch_page("pages/05_Insights_Dashboard.py")
with col2:
    if st.button("Home", use_container_width=True):
        st.switch_page("app.py")
with col3:
    if st.button("Version History →", use_container_width=True):
        st.switch_page("pages/07_Version_History.py")