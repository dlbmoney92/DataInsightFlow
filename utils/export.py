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
import tempfile
import subprocess
from pathlib import Path

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

def export_summary_report(df, transformations, insights, visualizations=None, add_branding=True):
    """
    Generate a summary report in HTML format.
    
    Parameters:
    - df: DataFrame to include in the report
    - transformations: List of transformations applied to the data
    - insights: List of insights generated from the data
    - visualizations: Optional list of visualizations to include
    - add_branding: Whether to add branding to the report (default: True)
    """
    # Create HTML content with improved styling
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Analytics Assist - Data Report</title>
        <style>
            body {{ 
                font-family: 'Segoe UI', Arial, sans-serif; 
                margin: 0; 
                padding: 0;
                color: #333;
                line-height: 1.6;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background: white;
            }}
            .header {{
                background: linear-gradient(to right, #1e3c72, #2a5298);
                color: white;
                padding: 20px;
                display: flex;
                align-items: center;
                justify-content: space-between;
                border-radius: 8px 8px 0 0;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }}
            .header-content {{
                flex: 1;
            }}
            .header-logo {{
                margin-left: 20px;
            }}
            h1, h2, h3 {{ 
                color: #1e3c72; 
                margin-top: 1.5em;
                margin-bottom: 0.5em;
            }}
            h1 {{
                margin-top: 0;
                color: white;
            }}
            table {{ 
                border-collapse: collapse; 
                width: 100%; 
                margin: 20px 0;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                border-radius: 5px;
                overflow: hidden;
            }}
            th, td {{ 
                padding: 12px; 
                text-align: left; 
                border-bottom: 1px solid #ddd; 
            }}
            th {{ 
                background-color: #f8f9fa; 
                font-weight: 600;
                color: #1e3c72;
            }}
            tr:nth-child(even) {{ background-color: #f2f2f2; }}
            tr:hover {{ background-color: #e9f0ff; }}
            .section {{ 
                margin-bottom: 30px; 
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }}
            .insight {{ 
                background-color: #f9f9f9; 
                padding: 15px; 
                margin-bottom: 15px; 
                border-left: 4px solid #4F8BF9; 
                border-radius: 0 8px 8px 0;
            }}
            .transformation {{ 
                background-color: #f0f8ff; 
                padding: 15px; 
                margin-bottom: 15px; 
                border-radius: 8px;
            }}
            .footer {{
                margin-top: 50px;
                padding: 20px;
                text-align: center;
                background: linear-gradient(to right, #f5f7fa, #c3cfe2);
                border-radius: 0 0 8px 8px;
                color: #666;
            }}
            .timestamp {{
                display: inline-block;
                padding: 5px 10px;
                background: rgba(255,255,255,0.3);
                border-radius: 20px;
                font-size: 0.8em;
                margin-top: 5px;
            }}
            .summary-stat {{
                display: inline-block;
                background: #f0f8ff;
                padding: 10px 15px;
                margin: 5px;
                border-radius: 8px;
                border-left: 3px solid #4F8BF9;
                min-width: 150px;
            }}
            .stat-label {{
                font-size: 0.8em;
                color: #666;
                display: block;
            }}
            .stat-value {{
                font-size: 1.2em;
                font-weight: bold;
                color: #1e3c72;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="header-content">
                    <h1>Analytics Assist - Data Analysis Report</h1>
                    <div class="timestamp">Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</div>
                </div>
                <div class="header-logo">
                    <!-- Logo will be inserted here via code later if available -->
                </div>
            </div>
            
            <div class="section">
                <h2>Dataset Summary</h2>
                <div style="display: flex; flex-wrap: wrap; gap: 10px; justify-content: space-between;">
                    <div class="summary-stat">
                        <span class="stat-label">Rows</span>
                        <span class="stat-value">{len(df):,}</span>
                    </div>
                    <div class="summary-stat">
                        <span class="stat-label">Columns</span>
                        <span class="stat-value">{len(df.columns)}</span>
                    </div>
                    <div class="summary-stat">
                        <span class="stat-label">Numeric Columns</span>
                        <span class="stat-value">{len(df.select_dtypes(include='number').columns)}</span>
                    </div>
                    <div class="summary-stat">
                        <span class="stat-label">Text/Categorical</span>
                        <span class="stat-value">{len(df.select_dtypes(include=['object','category']).columns)}</span>
                    </div>
                </div>
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
    
    # Add branding footer if requested
    if add_branding:
        # Add logo to the header first
        # Use embedded base64 logo
        logo_path = "assets/logo.png"
        logo_base64 = None
        try:
            import base64
            with open(logo_path, "rb") as img_file:
                logo_base64 = base64.b64encode(img_file.read()).decode()
        except Exception as e:
            print(f"Could not load logo for header: {e}")
            
        # Add logo to the header if available
        if logo_base64:
            # Find the header-logo div and replace its content
            html_content = html_content.replace('<!-- Logo will be inserted here via code later if available -->', 
                        f'<img src="data:image/png;base64,{logo_base64}" alt="Analytics Assist Logo" style="height: 50px; width: auto;">')
        
        # Create HTML for the logo in footer
        if logo_base64:
            logo_html = f'<img src="data:image/png;base64,{logo_base64}" alt="Analytics Assist Logo" style="height: 60px; margin-bottom: 10px;">'
        else:
            # Fallback if logo can't be loaded
            logo_html = '<div style="font-weight: bold; font-size: 1.6em; margin-bottom: 10px; color: #1e3c72;">Analytics Assist</div>'
        
        # Create a professional footer
        html_content += f"""
        <div class="footer">
            {logo_html}
            <p><strong>Report Generated with Analytics Assist</strong></p>
            <p>Transform Your Data Into Powerful Insights</p>
            <p><a href="https://analyticsassist.replit.app" style="color: #1e3c72; text-decoration: none; font-weight: bold;">analyticsassist.replit.app</a></p>
            <div style="font-size: 0.8em; margin-top: 15px; color: #777;">© {datetime.now().year} Analytics Assist. All Rights Reserved.</div>
        </div>
        </div> <!-- Close container -->
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

def convert_html_to_pdf(html_content):
    """
    Convert HTML content to PDF using WeasyPrint.
    
    Args:
        html_content (str): The HTML content to convert
        
    Returns:
        bytes: The PDF file as bytes
    """
    try:
        # Use WeasyPrint to convert HTML to PDF
        from weasyprint import HTML
        
        # Create a BytesIO buffer to store the PDF
        pdf_buffer = io.BytesIO()
        
        # Make sure HTML content is properly formatted with DOCTYPE and HTML structure
        # This ensures the content is properly rendered in the PDF
        if not html_content.strip().startswith('<!DOCTYPE html>') and not html_content.strip().startswith('<html'):
            html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Analytics Assist Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1, h2, h3 {{ color: #2c3e50; }}
        table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
{html_content}
</body>
</html>"""
        
        # Convert HTML to PDF
        HTML(string=html_content).write_pdf(pdf_buffer)
        
        # Get the PDF content
        pdf_buffer.seek(0)
        pdf_bytes = pdf_buffer.getvalue()
        
        return pdf_bytes
        
    except Exception as e:
        st.error(f"Error converting HTML to PDF: {str(e)}")
        raise Exception(f"Failed to convert HTML to PDF: {str(e)}")

def generate_pdf_download_link(html_content, filename="report.pdf"):
    """Generate a download link for a PDF report."""
    try:
        pdf_bytes = convert_html_to_pdf(html_content)
        b64 = base64.b64encode(pdf_bytes).decode()
        
        # Create download link
        href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}">Download PDF Report</a>'
        
        return href
    except Exception as e:
        st.error(f"Error generating PDF download link: {str(e)}")
        return None
