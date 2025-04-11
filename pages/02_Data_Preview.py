import streamlit as st
import pandas as pd
import numpy as np
from utils.file_processor import apply_column_types
from utils.auth_redirect import require_auth
from utils.custom_navigation import render_navigation, render_developer_login, logout_developer, initialize_navigation
from utils.quick_start import show_tour_bubble

st.set_page_config(
    page_title="Data Preview | Analytics Assist",
    page_icon="🔍",
    layout="wide"
)

# Initialize navigation
initialize_navigation()

# Check if a rerun is needed (from a previous action)
if "need_rerun" in st.session_state and st.session_state.need_rerun:
    # Clear the flag
    st.session_state.need_rerun = False
    # Execute rerun - this will be the last statement executed on this run
    st.rerun()

# Hide Streamlit’s default multipage navigation menu
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {
            display: none !important;
        }
    </style>
""", unsafe_allow_html=True)
# Render custom navigation bar
render_navigation()

# Sidebar extras
with st.sidebar:
    # Developer login form
    render_developer_login()
    
    # Logout from developer mode if active
    logout_developer()

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
    if st.button("Go to Upload Page"):
        st.switch_page("pages/01_Upload_Data.py")
    st.stop()

# Header and description
st.title("Data Preview & Column Types")
st.markdown("""
Review your data and verify the automatically detected column types. You can make adjustments 
if needed before proceeding to analysis.
""")

# Get data from session state
df = st.session_state.dataset
column_types = st.session_state.column_types
file_name = st.session_state.file_name

# Display dataset info
st.subheader(f"Dataset: {file_name}")
st.markdown(f"**Rows:** {df.shape[0]} • **Columns:** {df.shape[1]}")

# Data preview with pagination
data_preview_container = st.container()
with data_preview_container:
    page_size = st.slider("Rows per page", min_value=5, max_value=50, value=10, step=5)
    total_pages = max(1, (len(df) + page_size - 1) // page_size)
    page_number = st.number_input("Page", min_value=1, max_value=total_pages, value=1, step=1)
    
    start_idx = (page_number - 1) * page_size
    end_idx = min(start_idx + page_size, len(df))
    
    st.dataframe(df.iloc[start_idx:end_idx], height=400)

# Add tour bubble for data preview section
show_tour_bubble(
    element_id="div[data-testid='stDataFrame']", 
    title="Data Preview", 
    content="This section displays the first few rows of your dataset. You can use the pagination controls to navigate through the data and get a better understanding of its structure.",
    step=5,
    position="bottom",
    page_key="data_preview_page"
)

# Missing values summary
missing_values_container = st.container()
with missing_values_container:
    st.subheader("Missing Values Summary")
    missing_values = df.isna().sum()
    missing_percent = (missing_values / len(df) * 100).round(2)
    
    missing_df = pd.DataFrame({
        'Column': missing_values.index,
        'Missing Values': missing_values.values,
        'Percentage': missing_percent.values
    })
    
    # Only show columns with missing values
    missing_df = missing_df[missing_df['Missing Values'] > 0].sort_values(by='Missing Values', ascending=False)
    
    if not missing_df.empty:
        st.dataframe(missing_df, height=200)
    else:
        st.success("No missing values found in the dataset!")

# Add tour bubble for missing values section
show_tour_bubble(
    element_id="h3:contains('Missing Values Summary')", 
    title="Missing Values", 
    content="This section helps you identify missing data in your dataset. Missing values can affect your analysis and should be addressed through imputation or filtering, which you can do in the Data Transformation page.",
    step=7,
    position="left",
    page_key="data_preview_page"
)

# Duplicate rows check
duplicates = df.duplicated().sum()
if duplicates > 0:
    st.warning(f"Found {duplicates} duplicate rows ({(duplicates/len(df)*100):.2f}% of data)")
    if st.button("Remove Duplicates"):
        df = df.drop_duplicates()
        st.session_state.dataset = df
        st.session_state.need_rerun = True
        st.success(f"Removed {duplicates} duplicate rows. Page will refresh.")
else:
    st.success("No duplicate rows found in the dataset!")

# Column Types Editor
column_types_container = st.container()
with column_types_container:
    st.subheader("Column Types")
    st.markdown("""
    Verify the detected column types below. You can change them if needed.
    - **numeric**: Numbers that can be used in calculations
    - **datetime**: Dates and times
    - **categorical**: Values from a fixed set of options
    - **text**: Free-form text data
    - **boolean**: True/False values
    """)

# Add tour bubble for column types section
show_tour_bubble(
    element_id="h3:contains('Column Types')", 
    title="Column Types", 
    content="Setting the right data types is crucial for analysis. Here you can review and adjust the automatically detected column types to ensure your data is interpreted correctly.",
    step=6,
    position="right",
    page_key="data_preview_page"
)

# Allow editing column types
edited_column_types = {}

# Create columns for display
col1, col2 = st.columns(2)

with col1:
    for i, (column, col_type) in enumerate(list(column_types.items())[:len(column_types)//2 + len(column_types)%2]):
        # Show a sample of the data
        sample_values = df[column].dropna().head(3).tolist()
        sample_str = ", ".join([str(val) for val in sample_values])
        
        st.markdown(f"**{column}**")
        st.text(f"Sample: {sample_str[:50] + '...' if len(sample_str) > 50 else sample_str}")
        
        edited_column_types[column] = st.selectbox(
            f"Type for {column}",
            options=["numeric", "datetime", "categorical", "text", "boolean"],
            index=["numeric", "datetime", "categorical", "text", "boolean"].index(col_type) 
                  if col_type in ["numeric", "datetime", "categorical", "text", "boolean"] else 3,
            key=f"col_type_{i}"
        )
        st.write("")

with col2:
    for i, (column, col_type) in enumerate(list(column_types.items())[len(column_types)//2 + len(column_types)%2:]):
        # Show a sample of the data
        sample_values = df[column].dropna().head(3).tolist()
        sample_str = ", ".join([str(val) for val in sample_values])
        
        st.markdown(f"**{column}**")
        st.text(f"Sample: {sample_str[:50] + '...' if len(sample_str) > 50 else sample_str}")
        
        edited_column_types[column] = st.selectbox(
            f"Type for {column}",
            options=["numeric", "datetime", "categorical", "text", "boolean"],
            index=["numeric", "datetime", "categorical", "text", "boolean"].index(col_type) 
                  if col_type in ["numeric", "datetime", "categorical", "text", "boolean"] else 3,
            key=f"col_type_{i + len(column_types)//2 + len(column_types)%2}"
        )
        st.write("")

# Apply column types button
st.markdown("---")
if st.button("Apply Column Types"):
    # Update session state with edited column types
    st.session_state.column_types = edited_column_types
    
    # Apply column types to the DataFrame
    updated_df = apply_column_types(df, edited_column_types)
    st.session_state.dataset = updated_df
    st.session_state.need_rerun = True
    
    st.success("Column types updated successfully! Page will refresh.")

# Navigation buttons
st.markdown("---")
nav_container = st.container()
with nav_container:
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("← Back to Upload", key="back_to_upload"):
            st.switch_page("pages/01_Upload_Data.py")
    
    with col2:
        if st.button("Continue to EDA Dashboard →", key="continue_to_eda"):
            st.switch_page("pages/03_EDA_Dashboard.py")

# Add tour bubble for navigation
show_tour_bubble(
    element_id="div:contains('Continue to EDA Dashboard')", 
    title="Continue Your Journey", 
    content="Once you've reviewed your data and made any necessary adjustments to column types, click here to explore your dataset with interactive visualizations in the EDA Dashboard.",
    step=8,
    position="bottom",
    page_key="data_preview_page"
)

# Add a sidebar with tips
with st.sidebar:
    tips_container = st.container()
    with tips_container:
        st.header("Understanding Data Types")
        
        st.markdown("""
        ### Why Data Types Matter:
        
        Correct data types ensure:
        
        1. **Proper analysis**: Calculations work as expected
        
        2. **Efficient storage**: Data is stored optimally
        
        3. **Better visualizations**: Charts are appropriate for the data
        
        4. **Accurate insights**: AI suggestions are more relevant
        
        ### Common Type Issues:
        
        - **Numbers stored as text**: Can't be used in calculations
        
        - **Dates stored as text**: Can't be used for time analysis
        
        - **Categories with too many values**: May need to be treated as text
        
        - **Boolean values as text**: Can't be used for logical operations
        """)
    
    # Add tour bubble for the sidebar tips
    show_tour_bubble(
        element_id="h2:contains('Understanding Data Types')", 
        title="Helpful Tips", 
        content="The sidebar contains useful information about data types and why they matter for your analysis. Be sure to reference these tips when deciding how to categorize your columns.",
        step=9,
        position="left",
        page_key="data_preview_page"
    )
