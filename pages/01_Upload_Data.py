import streamlit as st
import pandas as pd
import numpy as np
import os
import json
from datetime import datetime
from utils.file_processor import (
    process_uploaded_file, 
    is_valid_file_type, 
    infer_column_types,
    supported_file_types
)
from utils.database import save_dataset, list_datasets, get_dataset
from utils.access_control import check_access
from utils.custom_navigation import render_navigation, render_developer_login, logout_developer, initialize_navigation

st.set_page_config(
    page_title="Upload Data | Analytics Assist",
    page_icon="📁",
    layout="wide"
)

# Initialize navigation
initialize_navigation()

# Render custom navigation bar
render_navigation()

# Sidebar extras
with st.sidebar:
    # Developer login form
    render_developer_login()
    
    # Logout from developer mode if active
    logout_developer()

# Authentication check
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("⚠️ You need to log in to upload and analyze data.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Log In", use_container_width=True):
            st.switch_page("pages/login.py")
    with col2:
        if st.button("Sign Up", use_container_width=True):
            st.switch_page("pages/signup.py")
            
    # Display feature preview even if not logged in
    st.markdown("---")
    st.subheader("Upload Data Feature Preview")
    st.markdown("""
    Once logged in, you'll be able to:
    - Upload various file formats (CSV, Excel, JSON, etc.)
    - Automatically detect data types and structure
    - Save datasets to your account for analysis
    - Transform and visualize your data
    
    Sign up for a free account to get started!
    """)
else:
    # Show user info if authenticated
    if "user" in st.session_state:
        st.sidebar.success(f"Logged in as: {st.session_state.user.get('email', 'User')}")
        st.sidebar.info(f"Subscription: {st.session_state.subscription_tier.capitalize()}")
    
    # Display supported file formats in preview
    st.markdown("**Supported file formats:**")
    file_format_cols = st.columns(3)
    for i, file_type in enumerate(supported_file_types):
        with file_format_cols[i % 3]:
            st.markdown(f"- {file_type}")
            
    # Continue execution for logged-in users

# If user is logged in, continue with the normal upload functionality
# Header and description
st.title("Upload Your Data")
st.markdown("""
Use this page to upload your dataset. Analytics Assist supports various file formats 
and will automatically detect the structure of your data.
""")

# Uploader section
st.subheader("Choose a file to upload")

# Display supported file types
col1, col2 = st.columns(2)
with col1:
    st.markdown("**Supported file formats:**")
    for file_type in supported_file_types:
        st.markdown(f"- {file_type}")

# File uploader
with col2:
    # Check if user can upload based on their subscription tier
    can_upload = check_access("upload", "new_dataset")
    
    if can_upload:
        uploaded_file = st.file_uploader("", type=[ext[1:] for ext in supported_file_types])
    else:
        st.warning("Your current subscription plan doesn't allow uploading more datasets. Please upgrade your plan.")
        if st.button("Upgrade Subscription"):
            st.switch_page("pages/subscription.py")
        uploaded_file = None

# Name the project
if uploaded_file is not None:
    project_name = st.text_input("Project Name", value="My Data Analysis Project")

# Process the uploaded file
if uploaded_file is not None:
    # Check if file type is valid
    if is_valid_file_type(uploaded_file.name):
        with st.spinner("Processing your file..."):
            # Process the file
            df = process_uploaded_file(uploaded_file)
            
            if df is not None and not df.empty:
                # Store in session state
                st.session_state.dataset = df
                st.session_state.file_name = uploaded_file.name
                
                # Infer column types
                column_types = infer_column_types(df)
                st.session_state.column_types = column_types
                
                # Reset transformations
                st.session_state.transformations = []
                st.session_state.transformation_history = []
                
                # Save to database
                with st.spinner("Saving to database..."):
                    description = f"Uploaded on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    file_type = uploaded_file.name.split('.')[-1].lower()
                    dataset_id = save_dataset(
                        name=project_name,
                        description=description,
                        file_name=uploaded_file.name,
                        file_type=file_type,
                        df=df,
                        column_types=column_types
                    )
                    if dataset_id:
                        st.session_state.dataset_id = dataset_id
                
                # Create a new project
                st.session_state.current_project = {
                    'name': project_name,
                    'file_name': uploaded_file.name,
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'dataset_id': st.session_state.dataset_id
                }
                
                # Success message
                st.success(f"Successfully loaded {uploaded_file.name} with {df.shape[0]} rows and {df.shape[1]} columns.")
                
                # Preview the data
                st.subheader("Data Preview")
                st.dataframe(df.head(10))
                
                # Display inferred column types
                st.subheader("Detected Column Types")
                
                # Create a DataFrame to display column types
                column_type_df = pd.DataFrame({
                    'Column': list(column_types.keys()),
                    'Detected Type': list(column_types.values())
                })
                
                st.dataframe(column_type_df)
                
                # Next step button
                st.markdown("---")
                if st.button("Continue to Data Preview", key="continue_to_preview"):
                    st.switch_page("pages/02_Data_Preview.py")
            else:
                st.error("Could not process the uploaded file. Please make sure it contains valid data.")
    else:
        st.error(f"Unsupported file type. Please upload one of the supported file types: {', '.join(supported_file_types)}")

# Display examples and instructions if no file is uploaded
if uploaded_file is None:
    st.markdown("---")
    st.subheader("Getting Started")
    
    st.markdown("""
    ### How to prepare your data
    
    For the best experience, make sure your data follows these guidelines:
    
    1. **Headers**: Include column headers in your data file
    2. **Formatting**: Avoid merged cells or complex formatting (for Excel files)
    3. **Size**: For the free version, files should be under 100MB
    
    ### Sample Datasets
    
    Don't have a dataset ready? Here are some options:
    
    1. Use our sample datasets
    2. Create a simple CSV or Excel file with your own data
    3. Export data from another system into a supported format
    """)
    
    # Sample datasets
    st.subheader("Sample Datasets")
    
    sample_datasets = {
        "Sales Data": "Sample sales dataset with transactions, products, and customer information",
        "Customer Survey": "Sample customer satisfaction survey results with ratings and feedback",
        "Stock Prices": "Historical stock price data for major companies",
        "Health Metrics": "Sample health and fitness tracker data with various metrics"
    }
    
    selected_sample = st.selectbox("Select a sample dataset", list(sample_datasets.keys()))
    
    st.info(f"Description: {sample_datasets[selected_sample]}")
    
    if st.button("Use Sample Dataset"):
        # Load the selected sample dataset
        if selected_sample == "Sales Data":
            # Create a sample sales dataset
            np.random.seed(42)
            dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
            products = ['Product A', 'Product B', 'Product C', 'Product D']
            regions = ['North', 'South', 'East', 'West']
            
            data = {
                'Date': np.random.choice(dates, 1000),
                'Product': np.random.choice(products, 1000),
                'Region': np.random.choice(regions, 1000),
                'Units': np.random.randint(1, 50, 1000),
                'Price': np.random.uniform(10, 100, 1000).round(2),
                'CustomerID': np.random.randint(1000, 9999, 1000)
            }
            
            data['Revenue'] = data['Units'] * data['Price']
            df = pd.DataFrame(data)
            
        elif selected_sample == "Customer Survey":
            # Create a sample customer survey dataset
            np.random.seed(42)
            n_samples = 500
            
            data = {
                'CustomerID': np.random.randint(1000, 9999, n_samples),
                'Age': np.random.randint(18, 80, n_samples),
                'Gender': np.random.choice(['Male', 'Female', 'Non-binary'], n_samples),
                'ProductRating': np.random.randint(1, 6, n_samples),
                'ServiceRating': np.random.randint(1, 6, n_samples),
                'LikelyToRecommend': np.random.randint(1, 11, n_samples),
                'Feedback': np.random.choice([
                    'Great product, highly satisfied',
                    'Average experience, could be better',
                    'Not satisfied with service',
                    'Will definitely recommend',
                    'Need more features',
                    'Excellent customer support',
                    np.nan
                ], n_samples)
            }
            
            data['OverallSatisfaction'] = (data['ProductRating'] + data['ServiceRating']) / 2
            df = pd.DataFrame(data)
            
        elif selected_sample == "Stock Prices":
            # Create a sample stock price dataset
            np.random.seed(42)
            companies = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'META']
            dates = pd.date_range(start='2022-01-01', end='2022-12-31', freq='B')
            
            all_data = []
            for company in companies:
                start_price = np.random.uniform(100, 500)
                price = start_price
                
                for date in dates:
                    change = np.random.normal(0, 0.02)  # 2% standard deviation
                    price = price * (1 + change)
                    volume = np.random.randint(100000, 10000000)
                    
                    all_data.append({
                        'Date': date,
                        'Symbol': company,
                        'Open': price * (1 - np.random.uniform(0, 0.01)),
                        'High': price * (1 + np.random.uniform(0, 0.02)),
                        'Low': price * (1 - np.random.uniform(0, 0.02)),
                        'Close': price,
                        'Volume': volume
                    })
            
            df = pd.DataFrame(all_data)
            
        elif selected_sample == "Health Metrics":
            # Create a sample health metrics dataset
            np.random.seed(42)
            n_samples = 500
            
            dates = pd.date_range(start='2023-01-01', end='2023-06-30', freq='D')
            user_ids = [f'User{i:03d}' for i in range(1, 6)]  # 5 users
            
            all_data = []
            for user_id in user_ids:
                for date in dates:
                    # Simulate some missing data
                    if np.random.random() < 0.1:  # 10% chance of missing data
                        continue
                        
                    steps = np.random.randint(2000, 15000)
                    heart_rate = np.random.randint(60, 100)
                    sleep_hours = round(np.random.uniform(4, 10), 1)
                    calories = np.random.randint(1500, 3000)
                    weight = round(np.random.uniform(60, 90), 1)
                    
                    all_data.append({
                        'Date': date,
                        'UserID': user_id,
                        'Steps': steps,
                        'HeartRate': heart_rate,
                        'SleepHours': sleep_hours,
                        'Calories': calories,
                        'Weight': weight
                    })
            
            df = pd.DataFrame(all_data)
        
        # Store in session state
        st.session_state.dataset = df
        st.session_state.file_name = f"{selected_sample}.csv"
        
        # Infer column types
        column_types = infer_column_types(df)
        st.session_state.column_types = column_types
        
        # Reset transformations
        st.session_state.transformations = []
        st.session_state.transformation_history = []
        
        # Save to database
        with st.spinner("Saving to database..."):
            project_name = f"Sample - {selected_sample}"
            description = f"Sample dataset created on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            file_name = f"{selected_sample}.csv"
            file_type = "csv"
            dataset_id = save_dataset(
                name=project_name,
                description=description,
                file_name=file_name,
                file_type=file_type,
                df=df,
                column_types=column_types
            )
            if dataset_id:
                st.session_state.dataset_id = dataset_id
        
        # Create a new project
        st.session_state.current_project = {
            'name': f"Sample - {selected_sample}",
            'file_name': f"{selected_sample}.csv",
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'dataset_id': st.session_state.dataset_id
        }
        
        # Success message and redirect
        st.success(f"Successfully loaded sample dataset with {df.shape[0]} rows and {df.shape[1]} columns.")
        st.rerun()

# Add a section to load existing datasets
st.markdown("---")
st.subheader("Load Existing Dataset")

# Get list of existing datasets
datasets_list = list_datasets()

if datasets_list:
    # Create a DataFrame for displaying the datasets
    datasets_df = pd.DataFrame([
        {'ID': ds['id'], 'Name': ds['name'], 'Rows': ds['row_count'], 
         'Columns': ds['column_count'], 'Created': ds['created_at'].strftime('%Y-%m-%d %H:%M')}
        for ds in datasets_list
    ])
    
    st.dataframe(datasets_df)
    
    # Select a dataset to load
    selected_dataset_id = st.selectbox("Select a dataset to load", 
                                      options=[ds['id'] for ds in datasets_list],
                                      format_func=lambda x: next((ds['name'] for ds in datasets_list if ds['id'] == x), ''))
    
    if st.button("Load Selected Dataset"):
        with st.spinner("Loading dataset from database..."):
            dataset_data = get_dataset(selected_dataset_id)
            
            if dataset_data:
                # Store in session state
                st.session_state.dataset = dataset_data['dataset']
                st.session_state.file_name = dataset_data['file_name']
                st.session_state.column_types = dataset_data['column_types']
                st.session_state.dataset_id = dataset_data['id']
                
                # Reset transformations
                st.session_state.transformations = []
                st.session_state.transformation_history = []
                
                # Create a new project
                st.session_state.current_project = {
                    'name': dataset_data['name'],
                    'file_name': dataset_data['file_name'],
                    'created_at': dataset_data['created_at'].strftime('%Y-%m-%d %H:%M:%S'),
                    'dataset_id': dataset_data['id']
                }
                
                st.success(f"Successfully loaded dataset '{dataset_data['name']}' with {dataset_data['row_count']} rows and {dataset_data['column_count']} columns.")
                st.rerun()
else:
    st.info("No existing datasets found. Upload a new dataset or use a sample dataset.")


# Add a sidebar with tips
with st.sidebar:
    st.header("Tips for Data Upload")
    
    st.markdown("""
    ### Best Practices:
    
    1. **Clean headers**: Make sure column names are clear and have no special characters
    
    2. **Check for errors**: Pre-clean your data if it has obvious errors
    
    3. **File size**: Large files may take longer to process
    
    4. **Data types**: The system will attempt to auto-detect data types, but you can adjust them in the next step
    
    5. **Missing values**: The system will handle missing values, but it's good to be aware of them
    """)
    
    st.markdown("---")
    
    st.markdown("""
    ### What happens next?
    
    After uploading, you'll be able to:
    1. Review and confirm data types
    2. Get automatic data insights
    3. Apply transformations
    4. Visualize your data
    5. Export your findings
    """)
