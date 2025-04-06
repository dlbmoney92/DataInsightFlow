import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import io
import base64
import json
import os
from datetime import datetime
import csv

def generate_excel_download_link(df, filename="data.xlsx", sheet_name="Data"):
    """Generate a download link for an Excel file."""
    buffer = io.BytesIO()
    
    # Create a writer for Excel
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    buffer.seek(0)
    b64 = base64.b64encode(buffer.read()).decode()
    
    # Create download link
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}">Download Excel File</a>'
    
    return href

def generate_csv_download_link(df, filename="data.csv"):
    """Generate a download link for a CSV file."""
    csv_string = df.to_csv(index=False)
    b64 = base64.b64encode(csv_string.encode()).decode()
    
    # Create download link
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">Download CSV File</a>'
    
    return href

def generate_json_download_link(df, filename="data.json"):
    """Generate a download link for a JSON file."""
    json_string = df.to_json(orient='records', date_format='iso')
    b64 = base64.b64encode(json_string.encode()).decode()
    
    # Create download link
    href = f'<a href="data:file/json;base64,{b64}" download="{filename}">Download JSON File</a>'
    
    return href

def generate_report_download_link(report_html, filename="report.html"):
    """Generate a download link for an HTML report."""
    b64 = base64.b64encode(report_html.encode()).decode()
    
    # Create download link
    href = f'<a href="data:text/html;base64,{b64}" download="{filename}">Download HTML Report</a>'
    
    return href

def generate_transformation_log(transformations, filename="transformation_log.json"):
    """Generate a download link for the transformation log."""
    # Create a copy of the transformations list with function names as strings
    clean_transformations = []
    
    for t in transformations:
        clean_t = {
            'name': t['name'],
            'description': t['description'],
            'function': t['function'],
            'columns': t['columns'],
            'params': t['params'] if 'params' in t else {},
            'timestamp': t['timestamp']
        }
        clean_transformations.append(clean_t)
    
    # Convert to JSON
    json_string = json.dumps(clean_transformations, indent=2)
    b64 = base64.b64encode(json_string.encode()).decode()
    
    # Create download link
    href = f'<a href="data:file/json;base64,{b64}" download="{filename}">Download Transformation Log</a>'
    
    return href

def generate_insights_download_link(insights, filename="insights.json"):
    """Generate a download link for the insights."""
    # Convert to JSON
    json_string = json.dumps(insights, indent=2)
    b64 = base64.b64encode(json_string.encode()).decode()
    
    # Create download link
    href = f'<a href="data:file/json;base64,{b64}" download="{filename}">Download Insights</a>'
    
    return href

def export_summary_report(df, transformations, insights, visualizations=None):
    """Generate a summary report in HTML format."""
    # Create HTML content
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Analytics Assist - Data Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1, h2, h3 {{ color: #4F8BF9; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background-color: #f2f2f2; }}
            .section {{ margin-bottom: 30px; }}
            .insight {{ background-color: #f9f9f9; padding: 10px; margin-bottom: 10px; border-left: 4px solid #4F8BF9; }}
            .transformation {{ background-color: #f0f8ff; padding: 10px; margin-bottom: 10px; }}
        </style>
    </head>
    <body>
        <h1>Analytics Assist - Data Analysis Report</h1>
        <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <div class="section">
            <h2>Dataset Summary</h2>
            <p>Rows: {len(df)}</p>
            <p>Columns: {len(df.columns)}</p>
            <p>Column names: {', '.join(df.columns.tolist())}</p>
        </div>
        
        <div class="section">
            <h2>Data Sample</h2>
            <table>
                <tr>
                    {' '.join([f'<th>{col}</th>' for col in df.columns])}
                </tr>
                {''.join([f"<tr>{' '.join([f'<td>{str(val)}</td>' for val in row])}</tr>" for _, row in df.head(10).iterrows()])}
            </table>
        </div>
    """
    
    # Add insights section
    if insights:
        html_content += """
        <div class="section">
            <h2>Key Insights</h2>
        """
        
        for insight in insights:
            html_content += f"""
            <div class="insight">
                <h3>{insight.get('title', 'Insight')}</h3>
                <p>{insight.get('description', '')}</p>
                <p><strong>Importance:</strong> {insight.get('importance', '-')}/5</p>
                <p><strong>Recommended Action:</strong> {insight.get('recommended_action', '-')}</p>
            </div>
            """
        
        html_content += "</div>"
    
    # Add transformations section
    if transformations:
        html_content += """
        <div class="section">
            <h2>Applied Transformations</h2>
        """
        
        for transform in transformations:
            html_content += f"""
            <div class="transformation">
                <h3>{transform.get('name', 'Transformation')}</h3>
                <p>{transform.get('description', '')}</p>
                <p><strong>Applied to:</strong> {', '.join(transform.get('columns', []))}</p>
                <p><strong>Applied at:</strong> {transform.get('timestamp', '-')}</p>
            </div>
            """
        
        html_content += "</div>"
    
    # Add numeric column statistics
    numeric_cols = df.select_dtypes(include=['number']).columns
    if not numeric_cols.empty:
        html_content += """
        <div class="section">
            <h2>Numeric Column Statistics</h2>
            <table>
                <tr>
                    <th>Column</th>
                    <th>Mean</th>
                    <th>Median</th>
                    <th>Std Dev</th>
                    <th>Min</th>
                    <th>Max</th>
                    <th>Missing</th>
                </tr>
        """
        
        for col in numeric_cols:
            html_content += f"""
                <tr>
                    <td>{col}</td>
                    <td>{df[col].mean():.2f}</td>
                    <td>{df[col].median():.2f}</td>
                    <td>{df[col].std():.2f}</td>
                    <td>{df[col].min():.2f}</td>
                    <td>{df[col].max():.2f}</td>
                    <td>{df[col].isna().sum()} ({df[col].isna().mean()*100:.1f}%)</td>
                </tr>
            """
        
        html_content += """
            </table>
        </div>
        """
    
    # Close HTML content
    html_content += """
    </body>
    </html>
    """
    
    return html_content

def save_project(name, df, transformations, insights):
    """Save the current project to session state."""
    if 'projects' not in st.session_state:
        st.session_state.projects = []
    
    # Create project data
    project = {
        'name': name,
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'dataset': df.to_dict() if df is not None else None,
        'transformations': transformations,
        'insights': insights
    }
    
    # Check if project already exists
    for i, p in enumerate(st.session_state.projects):
        if p['name'] == name:
            st.session_state.projects[i] = project
            return True
    
    # Add new project
    st.session_state.projects.append(project)
    return True

def load_project(name):
    """Load a project from session state."""
    if 'projects' not in st.session_state:
        return False
    
    for project in st.session_state.projects:
        if project['name'] == name:
            # Load project data
            if project['dataset']:
                st.session_state.dataset = pd.DataFrame.from_dict(project['dataset'])
            else:
                st.session_state.dataset = None
            
            st.session_state.transformations = project['transformations']
            st.session_state.insights = project['insights']
            st.session_state.current_project = project
            return True
    
    return False
