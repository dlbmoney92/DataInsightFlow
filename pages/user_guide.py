import streamlit as st
import base64
from utils.custom_navigation import render_navigation
from utils.auth_redirect import require_auth
from utils.global_config import apply_global_css

def app():
    # Check authentication
    if not require_auth():
        return
        
    # Apply global CSS
    apply_global_css()
    
    # Hide Streamlit's default multipage navigation menu
    st.markdown("""
        <style>
            [data-testid="stSidebarNav"] {
                display: none !important;
            }
        </style>
    """, unsafe_allow_html=True)

    # Page title and navigation
    st.title("Analytics Assist - User Guide")
    render_navigation()
    
    st.markdown("""
    This step-by-step guide will help you understand how to use Analytics Assist to analyze your data and gain valuable insights.
    """)
    
    # Table of Contents
    with st.expander("Table of Contents", expanded=True):
        st.markdown("""
        1. [Getting Started](#getting-started)
        2. [Uploading Data](#uploading-data)
        3. [Data Preview](#data-preview)
        4. [Exploratory Data Analysis](#exploratory-data-analysis)
        5. [Data Transformation](#data-transformation)
        6. [Insights Dashboard](#insights-dashboard)
        7. [Exporting Reports](#exporting-reports)
        8. [Account Management](#account-management)
        """)
    
    # Getting Started
    st.header("Getting Started", anchor="getting-started")
    st.markdown("""
    Analytics Assist is a powerful data analysis platform designed to help you transform complex datasets into actionable insights. 
    The application is organized into several key sections, all accessible from the left sidebar navigation.
    
    ### Key Features
    
    - **Data Upload**: Support for multiple file formats (CSV, Excel, etc.)
    - **Data Exploration**: Visual and statistical analysis of your data
    - **Data Transformation**: Clean, transform, and prepare data for analysis
    - **AI-Powered Insights**: Automatically generated insights about your data
    - **Report Generation**: Create and export professional reports
    
    ### Navigation
    
    Use the sidebar on the left to navigate between different sections of the application.
    """)
    
    # Upload Data
    st.header("Uploading Data", anchor="uploading-data")
    st.markdown("""
    The first step in using Analytics Assist is to upload your data. You can upload various file formats including CSV, Excel, JSON, and more.
    
    ### Steps to Upload Data:
    
    1. Click on **Upload Data** in the sidebar navigation
    2. Choose your upload method:
       - **Upload a File**: For CSV, Excel, and other file formats
       - **Connect to Database**: For importing data from a database
       - **Use Sample Dataset**: To try the app with pre-loaded data
    3. Follow the prompts to complete the upload
    4. Name your dataset and add any relevant tags or descriptions
    
    ### File Format Support
    
    - **CSV/TSV**: Comma or tab-separated files
    - **Excel**: XLSX and XLS formats
    - **JSON**: Structured JSON data
    - **Text Files**: Plain text with parsing options
    - **Word/PDF**: Document extraction (text and tables)
    """)
    
    # Upload Data screenshot
    st.image("assets/images/upload_data_screenshot.png", 
             caption="Upload Data interface showing file upload options and sample datasets", 
             use_container_width=True)
    
    # Data Preview
    st.header("Data Preview", anchor="data-preview")
    st.markdown("""
    After uploading data, you can preview it to ensure it was imported correctly and explore its basic structure.
    
    ### Preview Features:
    
    - **Tabular View**: See your data in a table format
    - **Data Types**: Automatically detected data types for each column
    - **Summary Statistics**: Quick view of basic statistics (count, mean, etc.)
    - **Missing Values**: Identification of null or missing values
    - **Filtering Options**: Narrow down records based on conditions
    
    ### Using Data Preview:
    
    1. Navigate to **Data Preview** in the sidebar
    2. Browse through your data using pagination controls
    3. Use search functionality to find specific values
    4. Examine column statistics and data quality metrics
    """)
    
    # Data Preview screenshot
    st.image("assets/images/data_preview_screenshot.png", 
             caption="Data Preview interface showing tabular view and data statistics", 
             use_container_width=True)
    
    # EDA Dashboard
    st.header("Exploratory Data Analysis", anchor="exploratory-data-analysis")
    st.markdown("""
    The EDA Dashboard provides tools to understand your data through visualizations and statistical analysis.
    
    ### EDA Features:
    
    - **Data Profiling**: Automated analysis of column distributions
    - **Correlation Analysis**: Identify relationships between variables
    - **Distribution Plots**: Visualize data distributions and detect outliers
    - **Time Series Analysis**: Analyze trends over time (where applicable)
    - **Custom Visualizations**: Create charts based on specific requirements
    
    ### Using the EDA Dashboard:
    
    1. Go to **EDA Dashboard** in the sidebar
    2. Explore the different tabs:
       - **Univariate Analysis**: Examine single variables
       - **Bivariate Analysis**: Explore relationships between pairs of variables
       - **Correlation Matrix**: See correlation coefficients between variables
       - **Custom Charts**: Create your own visualizations
    """)
    
    # EDA screenshot
    st.image("assets/images/eda_dashboard_screenshot.png", 
             caption="EDA Dashboard showing correlation matrix and visualization options", 
             use_container_width=True)
    
    # Data Transformation
    st.header("Data Transformation", anchor="data-transformation")
    st.markdown("""
    Transform your data to prepare it for analysis by cleaning, restructuring, or enhancing it.
    
    ### Transformation Features:
    
    - **Cleaning Operations**: Handle missing values, duplicates, outliers
    - **Feature Engineering**: Create new columns, bin data, extract features
    - **Data Type Conversions**: Convert between data types as needed
    - **Normalization**: Scale or standardize numerical data
    - **Text Processing**: Clean and prepare text data
    
    ### Using Data Transformation:
    
    1. Navigate to **Data Transformation** in the sidebar
    2. Select the type of transformation you want to apply
    3. Choose the columns to transform
    4. Configure transformation parameters
    5. Preview the results before applying
    6. Apply transformations to create a new version of your dataset
    
    All transformations are tracked in the transformation history, allowing you to revert changes if needed.
    """)
    
    # Transformation screenshot
    st.image("assets/images/data_transformation_screenshot.png", 
             caption="Data Transformation interface showing options for cleaning and transforming data", 
             use_container_width=True)
    
    # Insights Dashboard
    st.header("Insights Dashboard", anchor="insights-dashboard")
    st.markdown("""
    The Insights Dashboard uses AI to automatically generate meaningful insights from your data.
    
    ### Insights Features:
    
    - **Automated Data Analysis**: AI examines your data to find patterns and insights
    - **Categorized Insights**: Insights grouped by type (General, Statistical, Patterns, Anomalies)
    - **Interactive Visualizations**: Each insight includes relevant visualizations
    - **Feedback System**: Rate insights to help improve the AI
    - **Natural Language Q&A**: Ask questions about your data in plain English
    
    ### Using the Insights Dashboard:
    
    1. Go to **Insights Dashboard** in the sidebar
    2. Click **Generate Insights** to analyze your data
    3. Explore the insights in expandable sections
    4. Rate the usefulness of insights to help improve recommendations
    5. Use the Q&A feature to ask specific questions about your data
    """)
    
    # Insights screenshot
    st.image("assets/images/insights_dashboard_screenshot.png", 
             caption="AI-powered Insights Dashboard showing automatically generated insights and visualizations", 
             use_container_width=True)
    
    # Export Reports
    st.header("Exporting Reports", anchor="exporting-reports")
    st.markdown("""
    Create professional reports from your analysis to share with others.
    
    ### Export Features:
    
    - **Multiple Formats**: Export as PDF, Excel, CSV, HTML
    - **Customizable Reports**: Choose what to include in your reports
    - **Automated Documentation**: Include data descriptions and methodology
    - **Visualization Export**: Include charts and graphs in your reports
    - **Scheduled Reports**: Set up automatic report generation (Pro/Enterprise)
    
    ### Using Export Reports:
    
    1. Navigate to **Export Reports** in the sidebar
    2. Select the type of report you want to create
    3. Choose what elements to include (tables, charts, insights)
    4. Configure the format and styling options
    5. Generate and download your report
    """)
    
    # Export screenshot
    st.image("assets/images/export_reports_screenshot.png", 
             caption="Export Reports interface showing format options and report configuration", 
             use_container_width=True)
    
    # Account Management
    st.header("Account Management", anchor="account-management")
    st.markdown("""
    Manage your account, subscription, and preferences.
    
    ### Account Features:
    
    - **Profile Management**: Update your personal information
    - **Subscription Plans**: Choose from Free, Basic, Pro, or Enterprise tiers
    - **API Key Management**: Generate and manage API keys for integration
    - **Usage Statistics**: Track your usage of the platform
    - **Team Collaboration**: Share datasets and reports (Pro/Enterprise)
    
    ### Managing Your Account:
    
    1. Click on **Account** or your profile icon in the sidebar
    2. Update your profile information or password
    3. View or change your subscription plan
    4. Manage team access and permissions (Pro/Enterprise)
    """)
    
    # Account Management screenshot
    st.image("assets/images/account_management_screenshot.png", 
             caption="Account Management interface showing profile settings and subscription management", 
             use_container_width=True)
    
    # Tips and Best Practices
    st.header("Tips and Best Practices")
    with st.expander("Tips for Getting the Most Out of Analytics Assist"):
        st.markdown("""
        - **Start with Quality Data**: Clean your data before deep analysis
        - **Explore Before Transforming**: Use EDA to understand data before making changes
        - **Save Versions**: Create version checkpoints before major transformations
        - **Use AI Thoughtfully**: Review AI-generated insights for relevance to your specific context
        - **Combine Approaches**: Use both automated insights and custom analysis
        - **Share Insights**: Export reports to effectively communicate findings
        """)
    
    # Troubleshooting
    with st.expander("Common Issues and Solutions"):
        st.markdown("""
        - **Data Upload Problems**: 
          - Ensure your file is in a supported format
          - Check for encoding issues in CSV files
          - Try splitting very large files
          
        - **Visualization Errors**:
          - Verify that columns contain the expected data types
          - Remove or handle missing values before visualization
          
        - **Performance Issues**:
          - Consider using a sample of very large datasets
          - Close unused browser tabs
          - Clear browser cache if experiencing UI issues
        """)
    
    # Help and Support
    st.header("Help and Support")
    st.markdown("""
    If you need additional help:
    
    - Visit the **Contact Us** page in the sidebar
        """)
    
    # Navigation buttons at the bottom
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Home", use_container_width=True):
            st.switch_page("app.py")
    with col2:
        if st.button("Contact Us →", use_container_width=True):
            st.switch_page("pages/contact_us.py")

if __name__ == "__main__":
    app()