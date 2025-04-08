import streamlit as st

# Set page configuration - must be the first Streamlit command
st.set_page_config(
    page_title="Data Transformation | Analytics Assist",
    page_icon="🧹",
    layout="wide"
)

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json
import time
import uuid
from utils.transformations import (
    apply_transformations,
    register_transformation,
    get_column_stats_before_after,
    impute_missing_mean,
    impute_missing_median,
    impute_missing_mode,
    impute_missing_constant,
    remove_outliers,
    normalize_columns,
    encode_categorical,
    format_dates,
    drop_columns,
    rename_columns,
    create_bins,
    log_transform,
    convert_numeric_to_datetime,
    standardize_data,
    round_off,
    standardize_category_names,
    to_datetime
)
from utils.ai_suggestions import generate_column_cleaning_suggestions
from utils.visualization import create_distribution_plot, create_categorical_plot
from utils.auth_redirect import require_auth
from utils.transformation_visualizer import (
    generate_transformation_flow_chart,
    create_before_after_comparison,
    animate_transformation_process,
    create_transformation_journey_visualization
)
from utils.custom_navigation import render_navigation, initialize_navigation
from utils.global_config import apply_global_css

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

def local_register_transformation(transformations, transformation_history, transformation_name, transformation_details, original_df, df, columns_affected):
    """
    Register a transformation in the session state and save to transformation history.
    """
    # Get timestamp for the transformation
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Create a unique ID for the transformation
    transformation_id = str(uuid.uuid4())
    
    # Create transformation record
    transformation = {
        "id": transformation_id,
        "name": transformation_name,
        "timestamp": timestamp,
        "details": transformation_details,
        "columns_affected": columns_affected if isinstance(columns_affected, list) else [columns_affected]
    }
    
    # Add to transformations list
    transformations.append(transformation)
    
    # Add to transformation history
    transformation_history.append({
        "id": transformation_id,
        "name": transformation_name,
        "timestamp": timestamp
    })
    
    # Also save to database if dataset_id is available
    if "dataset_id" in st.session_state:
        try:
            from utils.database import save_transformation
            
            # Extract function name from transformation details, or use a default
            function_name = transformation_details.get("type", "custom_transformation")
            
            # Save the transformation to the database
            save_transformation(
                dataset_id=st.session_state.get("dataset_id"),
                name=transformation_name,
                description=json.dumps(transformation_details),
                transformation_details={
                    "function": function_name,
                    "params": transformation_details
                },
                affected_columns=columns_affected if isinstance(columns_affected, list) else [columns_affected]
            )
        except Exception as e:
            st.warning(f"Could not save transformation to database: {str(e)}")
    
    return True

def local_local_register_transformation(transformation_name, transformation_details, original_df, df, columns_affected):
    """Local version of register_transformation that can handle the current call signature."""
    # This is a wrapper function to maintain backward compatibility
    
    # Ensure session state lists exist
    if "transformations" not in st.session_state:
        st.session_state.transformations = []
    
    if "transformation_history" not in st.session_state:
        st.session_state.transformation_history = []
    
    # Call the actual register_transformation with the correct parameters
    return local_register_transformation(
        st.session_state.transformations,
        st.session_state.transformation_history,
        transformation_name,
        transformation_details,
        original_df,
        df,
        columns_affected
    )

# Check authentication
if not require_auth():
    st.stop()

# Show user info if authenticated
if "user" in st.session_state:
    st.sidebar.success(f"Logged in as: {st.session_state.user.get('email', 'User')}")
    st.sidebar.info(f"Subscription: {st.session_state.subscription_tier.capitalize()}")

st.title("Data Transformation")
st.markdown("""
This page allows you to clean, transform, and prepare your data for analysis. 
Apply various transformations to handle missing values, outliers, and other data quality issues.
""")

# Check if dataset is loaded
if "dataset" not in st.session_state or st.session_state.dataset is None:
    st.warning("No dataset loaded. Please upload or select a dataset first.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Upload Data", use_container_width=True):
            st.switch_page("pages/01_Upload_Data.py")
    with col2:
        if st.button("Data Preview", use_container_width=True):
            st.switch_page("pages/02_Data_Preview.py")
else:
    # Get the dataset from session state
    df = st.session_state.dataset.copy()
    original_df = df.copy()  # Keep a copy of the original dataframe
    
    # Initialize transformations list if it doesn't exist
    if "transformations" not in st.session_state:
        st.session_state.transformations = []
    
    if "transformation_history" not in st.session_state:
        st.session_state.transformation_history = []
    
    # Display dataset info
    st.sidebar.subheader("Dataset Info")
    st.sidebar.info(f"""
    - **Rows**: {df.shape[0]}
    - **Columns**: {df.shape[1]}
    - **Project**: {st.session_state.current_project.get('name', 'Unnamed project')}
    """)
    
    # Main section - Transformation Operations
    transformation_tab, history_tab, code_tab = st.tabs([
        "🧹 Apply Transformations", 
        "📜 Transformation History", 
        "💻 Generated Code"
    ])
    
    with transformation_tab:
        # Split into two columns
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("Transformation Operations")
            
            # Create a form for transformation selection
            transformation_type = st.selectbox(
                "Select transformation type",
                [
                    "Impute Missing Values",
                    "Handle Outliers",
                    "Normalize/Scale Data",
                    "Encode Categorical Variables",
                    "Transform Date/Time",
                    "Filter/Drop Data",
                    "Rename Columns",
                    "Bin/Discretize Data",
                    "Mathematical Transformations",
                    "Advanced Transformations"
                ]
            )
            
            # Based on the selected transformation type, show appropriate options
            if transformation_type == "Impute Missing Values":
                columns_with_missing = [col for col in df.columns if df[col].isnull().any()]
                
                if not columns_with_missing:
                    st.info("No columns with missing values found in the dataset.")
                    selected_column = st.selectbox("Select column (no missing values)", df.columns)
                    impute_method = st.selectbox(
                        "Select imputation method",
                        ["Mean", "Median", "Mode", "Constant value"],
                        disabled=True
                    )
                    constant_value = st.text_input("Constant value (if applicable)", value="0", disabled=True)
                    execute_button = st.button("Apply Transformation", disabled=True)
                else:
                    selected_column = st.selectbox("Select column with missing values", columns_with_missing)
                    
                    # Get column data type
                    col_dtype = df[selected_column].dtype
                    
                    # Different imputation methods based on data type
                    if np.issubdtype(col_dtype, np.number):
                        impute_method = st.selectbox(
                            "Select imputation method",
                            ["Mean", "Median", "Mode", "Constant value"]
                        )
                    else:
                        impute_method = st.selectbox(
                            "Select imputation method",
                            ["Mode", "Constant value"]
                        )
                    
                    # If constant value is selected, allow user to enter the value
                    if impute_method == "Constant value":
                        constant_value = st.text_input("Constant value", value="0")
                    else:
                        constant_value = None
                    
                    # Button to execute the transformation
                    execute_button = st.button("Apply Transformation")
                    
                    if execute_button:
                        # Perform the imputation based on the selected method
                        if impute_method == "Mean":
                            transformed_df, stats = impute_missing_mean(df, selected_column)
                            transformation_name = f"Impute missing values in {selected_column} with mean"
                        elif impute_method == "Median":
                            transformed_df, stats = impute_missing_median(df, selected_column)
                            transformation_name = f"Impute missing values in {selected_column} with median"
                        elif impute_method == "Mode":
                            transformed_df, stats = impute_missing_mode(df, selected_column)
                            transformation_name = f"Impute missing values in {selected_column} with mode"
                        elif impute_method == "Constant value":
                            # Convert the constant value to the appropriate type
                            if np.issubdtype(col_dtype, np.number):
                                try:
                                    constant = float(constant_value)
                                except ValueError:
                                    st.error("Please enter a valid number for constant value.")
                                    st.stop()
                            else:
                                constant = constant_value
                                
                            transformed_df, stats = impute_missing_constant(df, selected_column, constant)
                            transformation_name = f"Impute missing values in {selected_column} with constant {constant}"
                            
                        # Update the dataframe and register the transformation
                        df = transformed_df
                        
                        # Generate transformation details
                        transformation_details = {
                            "type": "impute_missing",
                            "method": impute_method.lower(),
                            "column": selected_column,
                            "constant_value": constant_value if impute_method == "Constant value" else None,
                            "stats": stats
                        }
                        
                        # Register transformation
                        local_register_transformation(
                            st.session_state.transformations,
                            st.session_state.transformation_history,
                            transformation_name,
                            transformation_details,
                            original_df,
                            df,
                            selected_column
                        )
                        
                        # Update the session state
                        st.session_state.dataset = df
                        
                        # Show success message
                        st.success(f"Successfully imputed missing values in {selected_column}.")
                        st.rerun()
                
            elif transformation_type == "Handle Outliers":
                numeric_columns = df.select_dtypes(include=np.number).columns.tolist()
                
                if not numeric_columns:
                    st.info("No numeric columns found in the dataset.")
                    selected_column = st.selectbox("Select column (no numeric columns)", df.columns)
                    outlier_method = st.selectbox(
                        "Select outlier handling method",
                        ["Z-score", "IQR", "Percentile"],
                        disabled=True
                    )
                    threshold = st.slider("Threshold", 1.0, 5.0, 3.0, disabled=True)
                    handle_method = st.selectbox(
                        "How to handle outliers",
                        ["Remove", "Cap", "Replace with mean", "Replace with median"],
                        disabled=True
                    )
                    execute_button = st.button("Apply Transformation", disabled=True)
                else:
                    selected_column = st.selectbox("Select numeric column", numeric_columns)
                    
                    # Outlier detection method
                    outlier_method = st.selectbox(
                        "Select outlier detection method",
                        ["Z-score", "IQR", "Percentile"]
                    )
                    
                    # Threshold for outlier detection
                    if outlier_method == "Z-score":
                        threshold = st.slider("Z-score threshold", 1.0, 5.0, 3.0, 0.1)
                    elif outlier_method == "IQR":
                        threshold = st.slider("IQR multiplier", 1.0, 3.0, 1.5, 0.1)
                    else:  # Percentile
                        lower_pct = st.slider("Lower percentile", 0.0, 20.0, 5.0, 0.5)
                        upper_pct = st.slider("Upper percentile", 80.0, 100.0, 95.0, 0.5)
                        threshold = (lower_pct, upper_pct)
                    
                    # How to handle outliers
                    handle_method = st.selectbox(
                        "How to handle outliers",
                        ["Remove", "Cap", "Replace with mean", "Replace with median"]
                    )
                    
                    # Button to execute the transformation
                    execute_button = st.button("Apply Transformation")
                    
                    if execute_button:
                        # Perform outlier handling
                        # Create a list with the selected column
                        columns_to_check = [selected_column]
                        
                        # Call remove_outliers with the correct parameters
                        transformed_df = remove_outliers(
                            df, 
                            columns=columns_to_check, 
                            method=outlier_method.lower(), 
                            threshold=threshold
                        )
                        
                        # Calculate basic stats for reporting
                        stats = {
                            'original_rows': len(df),
                            'transformed_rows': len(transformed_df),
                            'rows_removed': len(df) - len(transformed_df)
                        }
                        
                        # Generate transformation name
                        if outlier_method == "Percentile":
                            transformation_name = f"Handle outliers in {selected_column} using {outlier_method} ({threshold[0]}-{threshold[1]}) with {handle_method}"
                        else:
                            transformation_name = f"Handle outliers in {selected_column} using {outlier_method} (threshold={threshold}) with {handle_method}"
                        
                        # Update the dataframe
                        df = transformed_df
                        
                        # Generate transformation details
                        transformation_details = {
                            "type": "handle_outliers",
                            "method": outlier_method.lower(),
                            "threshold": threshold,
                            "handle_method": handle_method.lower(),
                            "column": selected_column,
                            "stats": stats
                        }
                        
                        # Register transformation
                        local_register_transformation(
                            st.session_state.transformations,
                            st.session_state.transformation_history,
                            transformation_name,
                            transformation_details,
                            original_df,
                            df,
                            selected_column
                        )
                        
                        # Update the session state
                        st.session_state.dataset = df
                        
                        # Show success message
                        st.success(f"Successfully handled outliers in {selected_column}.")
                        st.rerun()
                
            elif transformation_type == "Normalize/Scale Data":
                numeric_columns = df.select_dtypes(include=np.number).columns.tolist()
                
                if not numeric_columns:
                    st.info("No numeric columns found in the dataset.")
                    selected_columns = st.multiselect("Select columns (no numeric columns)", df.columns)
                    normalize_method = st.selectbox(
                        "Select normalization method",
                        ["Min-Max scaling", "Z-score standardization", "Robust scaling"],
                        disabled=True
                    )
                    execute_button = st.button("Apply Transformation", disabled=True)
                else:
                    selected_columns = st.multiselect("Select numeric columns", numeric_columns)
                    
                    # Normalization method
                    normalize_method = st.selectbox(
                        "Select normalization method",
                        ["Min-Max scaling", "Z-score standardization", "Robust scaling"]
                    )
                    
                    # Button to execute the transformation
                    execute_button = st.button("Apply Transformation")
                    
                    if execute_button and selected_columns:
                        # Perform normalization
                        transformed_df, stats = normalize_columns(
                            df, 
                            selected_columns, 
                            method=normalize_method.lower().replace(" ", "_").replace("-", "_")
                        )
                        
                        # Generate transformation name
                        transformation_name = f"Normalize {', '.join(selected_columns)} using {normalize_method}"
                        
                        # Update the dataframe
                        df = transformed_df
                        
                        # Generate transformation details
                        transformation_details = {
                            "type": "normalize",
                            "method": normalize_method.lower().replace(" ", "_").replace("-", "_"),
                            "columns": selected_columns,
                            "stats": stats
                        }
                        
                        # Register transformation
                        local_register_transformation(
                            st.session_state.transformations,
                            st.session_state.transformation_history,
                            transformation_name,
                            transformation_details,
                            original_df,
                            df,
                            selected_columns
                        )
                        
                        # Update the session state
                        st.session_state.dataset = df
                        
                        # Show success message
                        st.success(f"Successfully normalized {len(selected_columns)} columns.")
                        st.rerun()
                    elif execute_button and not selected_columns:
                        st.warning("Please select at least one column to normalize.")
                
            elif transformation_type == "Encode Categorical Variables":
                categorical_columns = df.select_dtypes(include=['object', 'category']).columns.tolist()
                
                if not categorical_columns:
                    st.info("No categorical columns found in the dataset.")
                    selected_column = st.selectbox("Select column (no categorical columns)", df.columns)
                    encode_method = st.selectbox(
                        "Select encoding method",
                        ["One-hot encoding", "Label encoding", "Frequency encoding"],
                        disabled=True
                    )
                    execute_button = st.button("Apply Transformation", disabled=True)
                else:
                    selected_column = st.selectbox("Select categorical column", categorical_columns)
                    
                    # Encoding method
                    encode_method = st.selectbox(
                        "Select encoding method",
                        ["One-hot encoding", "Label encoding", "Frequency encoding"]
                    )
                    
                    # Button to execute the transformation
                    execute_button = st.button("Apply Transformation")
                    
                    if execute_button:
                        # Perform encoding
                        transformed_df, stats = encode_categorical(
                            df, 
                            selected_column, 
                            method=encode_method.lower().replace(" ", "_").replace("-", "_")
                        )
                        
                        # Generate transformation name
                        transformation_name = f"Encode {selected_column} using {encode_method}"
                        
                        # Update the dataframe
                        df = transformed_df
                        
                        # Generate transformation details
                        transformation_details = {
                            "type": "encode_categorical",
                            "method": encode_method.lower().replace(" ", "_").replace("-", "_"),
                            "column": selected_column,
                            "stats": stats
                        }
                        
                        # Register transformation
                        local_register_transformation(
                            st.session_state.transformations,
                            st.session_state.transformation_history,
                            transformation_name,
                            transformation_details,
                            original_df,
                            df,
                            selected_column
                        )
                        
                        # Update the session state
                        st.session_state.dataset = df
                        
                        # Show success message
                        st.success(f"Successfully encoded {selected_column}.")
                        st.rerun()
                
            elif transformation_type == "Transform Date/Time":
                # Identify datetime columns or columns that could be converted to datetime
                date_columns = [col for col in df.columns if pd.api.types.is_datetime64_any_dtype(df[col])]
                potential_date_columns = []
                
                for col in df.columns:
                    if col not in date_columns:
                        # Try to convert a sample of non-null values to datetime
                        sample = df[col].dropna().head(10)
                        try:
                            pd.to_datetime(sample)
                            potential_date_columns.append(col)
                        except:
                            pass
                
                all_date_columns = date_columns + potential_date_columns
                
                if not all_date_columns:
                    st.info("No date/time columns found in the dataset.")
                    selected_column = st.selectbox("Select column (no date columns)", df.columns)
                    date_operation = st.selectbox(
                        "Select date operation",
                        ["Format date", "Extract components", "Convert to datetime"],
                        disabled=True
                    )
                    execute_button = st.button("Apply Transformation", disabled=True)
                else:
                    selected_column = st.selectbox("Select date/time column", all_date_columns)
                    
                    # Date operation
                    if selected_column in date_columns:
                        date_operation = st.selectbox(
                            "Select date operation",
                            ["Format date", "Extract components"]
                        )
                    else:
                        date_operation = st.selectbox(
                            "Select date operation",
                            ["Convert to datetime", "Format date", "Extract components"]
                        )
                    
                    # Additional options based on operation
                    if date_operation == "Format date":
                        date_format = st.text_input("Date format", value="%Y-%m-%d")
                        st.info("Common formats: %Y-%m-%d, %m/%d/%Y, %d-%b-%Y")
                    elif date_operation == "Extract components":
                        component = st.selectbox(
                            "Select component to extract",
                            ["Year", "Month", "Day", "Hour", "Minute", "Second", "Day of week", "Week of year", "Quarter"]
                        )
                    elif date_operation == "Convert to datetime":
                        date_format = st.text_input("Input date format (if known)", value="")
                        st.info("Leave blank for automatic format detection.")
                    
                    # Button to execute the transformation
                    execute_button = st.button("Apply Transformation")
                    
                    if execute_button:
                        if date_operation == "Convert to datetime":
                            # Convert to datetime
                            if date_format:
                                transformed_df, stats = to_datetime(df, selected_column, format=date_format)
                            else:
                                transformed_df, stats = to_datetime(df, selected_column)
                                
                            transformation_name = f"Convert {selected_column} to datetime"
                            
                            transformation_details = {
                                "type": "to_datetime",
                                "column": selected_column,
                                "format": date_format if date_format else "auto",
                                "stats": stats
                            }
                        elif date_operation == "Format date":
                            # Format date
                            transformed_df, stats = format_dates(df, selected_column, output_format=date_format)
                            
                            transformation_name = f"Format {selected_column} to {date_format}"
                            
                            transformation_details = {
                                "type": "format_date",
                                "column": selected_column,
                                "output_format": date_format,
                                "stats": stats
                            }
                        elif date_operation == "Extract components":
                            # Extract component
                            component_func = component.lower().replace(" ", "_")
                            
                            transformed_df, stats = convert_numeric_to_datetime(df, selected_column, component_func)
                            
                            transformation_name = f"Extract {component} from {selected_column}"
                            
                            transformation_details = {
                                "type": "extract_date_component",
                                "column": selected_column,
                                "component": component_func,
                                "stats": stats
                            }
                        
                        # Update the dataframe
                        df = transformed_df
                        
                        # Register transformation
                        local_register_transformation(
                            st.session_state.transformations,
                            st.session_state.transformation_history,
                            transformation_name,
                            transformation_details,
                            original_df,
                            df,
                            selected_column
                        )
                        
                        # Update the session state
                        st.session_state.dataset = df
                        
                        # Show success message
                        st.success(f"Successfully transformed {selected_column}.")
                        st.rerun()
                
            elif transformation_type == "Filter/Drop Data":
                operation = st.selectbox(
                    "Select operation",
                    ["Drop columns", "Drop rows with missing values", "Filter rows by condition"]
                )
                
                if operation == "Drop columns":
                    selected_columns = st.multiselect("Select columns to drop", df.columns)
                    
                    execute_button = st.button("Apply Transformation")
                    
                    if execute_button and selected_columns:
                        # Perform drop columns
                        transformed_df, stats = drop_columns(df, selected_columns)
                        
                        # Generate transformation name
                        transformation_name = f"Drop columns: {', '.join(selected_columns)}"
                        
                        # Update the dataframe
                        df = transformed_df
                        
                        # Generate transformation details
                        transformation_details = {
                            "type": "drop_columns",
                            "columns": selected_columns,
                            "stats": stats
                        }
                        
                        # Register transformation
                        local_register_transformation(
                            st.session_state.transformations,
                            st.session_state.transformation_history,
                            transformation_name,
                            transformation_details,
                            original_df,
                            df,
                            selected_columns
                        )
                        
                        # Update the session state
                        st.session_state.dataset = df
                        
                        # Show success message
                        st.success(f"Successfully dropped {len(selected_columns)} columns.")
                        st.rerun()
                    elif execute_button and not selected_columns:
                        st.warning("Please select at least one column to drop.")
                
                elif operation == "Drop rows with missing values":
                    # Options for dropping rows with missing values
                    drop_option = st.radio(
                        "How to drop rows with missing values",
                        ["Drop rows with any missing values", "Drop rows with all missing values", "Drop rows with missing values in specific columns"]
                    )
                    
                    if drop_option == "Drop rows with missing values in specific columns":
                        selected_columns = st.multiselect("Select columns to check for missing values", df.columns)
                    else:
                        selected_columns = None
                    
                    # Show preview of how many rows will be dropped
                    if drop_option == "Drop rows with any missing values":
                        rows_to_drop = df.dropna().shape[0] - df.shape[0]
                    elif drop_option == "Drop rows with all missing values":
                        rows_to_drop = df.dropna(how='all').shape[0] - df.shape[0]
                    elif selected_columns:
                        rows_to_drop = df.dropna(subset=selected_columns).shape[0] - df.shape[0]
                    else:
                        rows_to_drop = 0
                        
                    st.info(f"This operation will drop {abs(rows_to_drop)} rows ({abs(rows_to_drop)/df.shape[0]:.2%} of data).")
                    
                    execute_button = st.button("Apply Transformation")
                    
                    if execute_button:
                        # Perform drop rows
                        if drop_option == "Drop rows with any missing values":
                            transformed_df = df.dropna()
                            how = "any"
                            subset = None
                        elif drop_option == "Drop rows with all missing values":
                            transformed_df = df.dropna(how='all')
                            how = "all"
                            subset = None
                        else:
                            transformed_df = df.dropna(subset=selected_columns)
                            how = "any"
                            subset = selected_columns
                        
                        # Generate stats
                        stats = {
                            "rows_before": df.shape[0],
                            "rows_after": transformed_df.shape[0],
                            "rows_dropped": df.shape[0] - transformed_df.shape[0]
                        }
                        
                        # Generate transformation name
                        if subset:
                            transformation_name = f"Drop rows with missing values in columns: {', '.join(subset)}"
                        else:
                            transformation_name = f"Drop rows with {how} missing values"
                        
                        # Update the dataframe
                        df = transformed_df
                        
                        # Generate transformation details
                        transformation_details = {
                            "type": "drop_rows_with_missing",
                            "how": how,
                            "subset": subset,
                            "stats": stats
                        }
                        
                        # Register transformation
                        local_register_transformation(
                            st.session_state.transformations,
                            st.session_state.transformation_history,
                            transformation_name,
                            transformation_details,
                            original_df,
                            df,
                            None
                        )
                        
                        # Update the session state
                        st.session_state.dataset = df
                        
                        # Show success message
                        st.success(f"Successfully dropped {stats['rows_dropped']} rows with missing values.")
                        st.rerun()
                
                elif operation == "Filter rows by condition":
                    column = st.selectbox("Select column to filter", df.columns)
                    
                    # Get column type to determine appropriate filter options
                    col_dtype = df[column].dtype
                    
                    if np.issubdtype(col_dtype, np.number):
                        # Numeric column
                        filter_type = st.selectbox(
                            "Filter type",
                            ["Greater than", "Less than", "Equal to", "Between"]
                        )
                        
                        if filter_type == "Between":
                            min_val = st.number_input("Minimum value", value=float(df[column].min()))
                            max_val = st.number_input("Maximum value", value=float(df[column].max()))
                            condition_str = f"{column} between {min_val} and {max_val}"
                        else:
                            threshold = st.number_input("Threshold value", value=float(df[column].mean()))
                            condition_str = f"{column} {filter_type.lower()} {threshold}"
                    else:
                        # Non-numeric column
                        unique_values = df[column].dropna().unique()
                        if len(unique_values) <= 10:
                            # For categorical with few values
                            filter_type = "Equal to"
                            selected_value = st.selectbox("Select value", [""] + list(unique_values))
                            condition_str = f"{column} equals '{selected_value}'"
                        else:
                            # For categorical with many values
                            filter_type = st.selectbox(
                                "Filter type",
                                ["Equal to", "Contains", "Starts with", "Ends with"]
                            )
                            text_value = st.text_input("Filter text")
                            condition_str = f"{column} {filter_type.lower()} '{text_value}'"
                    
                    execute_button = st.button("Apply Transformation")
                    
                    if execute_button:
                        # Perform row filtering
                        if np.issubdtype(col_dtype, np.number):
                            if filter_type == "Greater than":
                                mask = df[column] > threshold
                            elif filter_type == "Less than":
                                mask = df[column] < threshold
                            elif filter_type == "Equal to":
                                mask = df[column] == threshold
                            elif filter_type == "Between":
                                mask = (df[column] >= min_val) & (df[column] <= max_val)
                        else:
                            if filter_type == "Equal to":
                                mask = df[column] == selected_value
                            elif filter_type == "Contains":
                                mask = df[column].astype(str).str.contains(text_value, na=False)
                            elif filter_type == "Starts with":
                                mask = df[column].astype(str).str.startswith(text_value, na=False)
                            elif filter_type == "Ends with":
                                mask = df[column].astype(str).str.endswith(text_value, na=False)
                        
                        transformed_df = df[mask]
                        
                        # Generate stats
                        stats = {
                            "rows_before": df.shape[0],
                            "rows_after": transformed_df.shape[0],
                            "rows_filtered": df.shape[0] - transformed_df.shape[0]
                        }
                        
                        # Generate transformation name
                        transformation_name = f"Filter rows where {condition_str}"
                        
                        # Update the dataframe
                        df = transformed_df
                        
                        # Generate transformation details
                        transformation_details = {
                            "type": "filter_rows",
                            "column": column,
                            "filter_type": filter_type,
                            "condition": condition_str,
                            "stats": stats
                        }
                        
                        # Register transformation
                        local_register_transformation(
                            st.session_state.transformations,
                            st.session_state.transformation_history,
                            transformation_name,
                            transformation_details,
                            original_df,
                            df,
                            column
                        )
                        
                        # Update the session state
                        st.session_state.dataset = df
                        
                        # Show success message
                        st.success(f"Successfully filtered rows. {transformed_df.shape[0]} rows remaining.")
                        st.rerun()
                
            elif transformation_type == "Rename Columns":
                # Create a dataframe for renaming columns
                rename_df = pd.DataFrame({
                    'Original Column Name': df.columns,
                    'New Column Name': df.columns
                })
                
                renamed = {}
                for i, row in enumerate(rename_df.itertuples()):
                    original_name = row._1
                    new_name = st.text_input(f"Rename {original_name}", value=original_name, key=f"rename_{i}")
                    if new_name != original_name:
                        renamed[original_name] = new_name
                
                execute_button = st.button("Apply Transformation")
                
                if execute_button and renamed:
                    # Perform column renaming
                    transformed_df, stats = rename_columns(df, renamed)
                    
                    # Generate transformation name
                    transformation_name = f"Rename columns: {', '.join([f'{old} → {new}' for old, new in renamed.items()])}"
                    
                    # Update the dataframe
                    df = transformed_df
                    
                    # Generate transformation details
                    transformation_details = {
                        "type": "rename_columns",
                        "rename_map": renamed,
                        "stats": stats
                    }
                    
                    # Register transformation
                    local_register_transformation(
                        st.session_state.transformations,
                        st.session_state.transformation_history,
                        transformation_name,
                        transformation_details,
                        original_df,
                        df,
                        list(renamed.keys())
                    )
                    
                    # Update the session state
                    st.session_state.dataset = df
                    
                    # Show success message
                    st.success(f"Successfully renamed {len(renamed)} columns.")
                    st.rerun()
                elif execute_button and not renamed:
                    st.info("No columns were renamed. Please change at least one column name.")
                
            elif transformation_type == "Bin/Discretize Data":
                numeric_columns = df.select_dtypes(include=np.number).columns.tolist()
                
                if not numeric_columns:
                    st.info("No numeric columns found in the dataset.")
                    selected_column = st.selectbox("Select column (no numeric columns)", df.columns)
                    num_bins = st.slider("Number of bins", 2, 20, 5, disabled=True)
                    execute_button = st.button("Apply Transformation", disabled=True)
                else:
                    selected_column = st.selectbox("Select numeric column", numeric_columns)
                    
                    # Binning options
                    binning_method = st.selectbox(
                        "Binning method",
                        ["Equal width", "Equal frequency", "Custom"]
                    )
                    
                    if binning_method == "Custom":
                        bin_edges_input = st.text_input(
                            "Bin edges (comma-separated)",
                            value=f"{df[selected_column].min()}, {df[selected_column].max()}"
                        )
                        try:
                            bin_edges = [float(x.strip()) for x in bin_edges_input.split(",")]
                            num_bins = len(bin_edges) - 1
                        except:
                            st.error("Please enter valid numeric values for bin edges.")
                            bin_edges = None
                    else:
                        num_bins = st.slider("Number of bins", 2, 20, 5)
                        bin_edges = None
                    
                    # Labels
                    use_custom_labels = st.checkbox("Use custom labels")
                    if use_custom_labels:
                        if binning_method == "Custom" and bin_edges:
                            expected_labels = num_bins
                        else:
                            expected_labels = num_bins
                            
                        labels_input = st.text_input(
                            f"Labels (comma-separated, {expected_labels} needed)",
                            value=", ".join([f"Bin {i+1}" for i in range(expected_labels)])
                        )
                        try:
                            labels = [label.strip() for label in labels_input.split(",")]
                            if len(labels) != expected_labels:
                                st.warning(f"Number of labels ({len(labels)}) doesn't match number of bins ({expected_labels}).")
                        except:
                            st.error("Please enter valid labels.")
                            labels = None
                    else:
                        labels = None
                    
                    # Button to execute the transformation
                    execute_button = st.button("Apply Transformation")
                    
                    if execute_button:
                        # Perform binning
                        if binning_method == "Equal width":
                            method = "equal_width"
                        elif binning_method == "Equal frequency":
                            method = "equal_frequency"
                        else:
                            method = "custom"
                            
                        transformed_df, stats = create_bins(
                            df, 
                            selected_column, 
                            num_bins=num_bins, 
                            method=method,
                            bin_edges=bin_edges,
                            labels=labels
                        )
                        
                        # Generate transformation name
                        transformation_name = f"Bin {selected_column} into {num_bins} bins using {binning_method}"
                        
                        # Update the dataframe
                        df = transformed_df
                        
                        # Generate transformation details
                        transformation_details = {
                            "type": "create_bins",
                            "column": selected_column,
                            "num_bins": num_bins,
                            "method": method,
                            "bin_edges": bin_edges,
                            "labels": labels,
                            "stats": stats
                        }
                        
                        # Register transformation
                        local_register_transformation(
                            st.session_state.transformations,
                            st.session_state.transformation_history,
                            transformation_name,
                            transformation_details,
                            original_df,
                            df,
                            selected_column
                        )
                        
                        # Update the session state
                        st.session_state.dataset = df
                        
                        # Show success message
                        st.success(f"Successfully binned {selected_column} into {num_bins} bins.")
                        st.rerun()
                
            elif transformation_type == "Mathematical Transformations":
                numeric_columns = df.select_dtypes(include=np.number).columns.tolist()
                
                if not numeric_columns:
                    st.info("No numeric columns found in the dataset.")
                    selected_column = st.selectbox("Select column (no numeric columns)", df.columns)
                    math_operation = st.selectbox(
                        "Select mathematical operation",
                        ["Log transform", "Square root", "Square", "Cube", "Absolute value", "Round"],
                        disabled=True
                    )
                    execute_button = st.button("Apply Transformation", disabled=True)
                else:
                    selected_column = st.selectbox("Select numeric column", numeric_columns)
                    
                    # Mathematical operation
                    math_operation = st.selectbox(
                        "Select mathematical operation",
                        ["Log transform", "Square root", "Square", "Cube", "Absolute value", "Round"]
                    )
                    
                    # Additional parameters for specific operations
                    if math_operation == "Log transform":
                        log_base = st.selectbox("Log base", ["Natural (e)", "10", "2"])
                        handle_zeros = st.checkbox("Add small constant to handle zeros/negatives", value=True)
                    elif math_operation == "Round":
                        decimals = st.slider("Decimal places", 0, 5, 2)
                    
                    # Button to execute the transformation
                    execute_button = st.button("Apply Transformation")
                    
                    if execute_button:
                        # Perform mathematical transformation
                        if math_operation == "Log transform":
                            if log_base == "Natural (e)":
                                base = "e"
                            elif log_base == "10":
                                base = 10
                            else:
                                base = 2
                                
                            transformed_df, stats = log_transform(
                                df, 
                                selected_column, 
                                base=base, 
                                handle_zeros=handle_zeros
                            )
                            
                            if handle_zeros:
                                transformation_name = f"Log transform ({base}) with small constant on {selected_column}"
                            else:
                                transformation_name = f"Log transform ({base}) on {selected_column}"
                                
                            transformation_details = {
                                "type": "log_transform",
                                "column": selected_column,
                                "base": base,
                                "handle_zeros": handle_zeros,
                                "stats": stats
                            }
                            
                        elif math_operation == "Square root":
                            def transform_func(x):
                                # Handle negative values by returning NaN
                                return np.sqrt(x) if x >= 0 else np.nan
                            
                            transformed_df = df.copy()
                            transformed_df[selected_column] = df[selected_column].apply(transform_func)
                            
                            stats = {
                                "mean_before": df[selected_column].mean(),
                                "mean_after": transformed_df[selected_column].mean(),
                                "min_before": df[selected_column].min(),
                                "min_after": transformed_df[selected_column].min(),
                                "max_before": df[selected_column].max(),
                                "max_after": transformed_df[selected_column].max()
                            }
                            
                            transformation_name = f"Square root transform on {selected_column}"
                            
                            transformation_details = {
                                "type": "power_transform",
                                "column": selected_column,
                                "power": 0.5,
                                "stats": stats
                            }
                            
                        elif math_operation == "Square":
                            transformed_df = df.copy()
                            transformed_df[selected_column] = df[selected_column] ** 2
                            
                            stats = {
                                "mean_before": df[selected_column].mean(),
                                "mean_after": transformed_df[selected_column].mean(),
                                "min_before": df[selected_column].min(),
                                "min_after": transformed_df[selected_column].min(),
                                "max_before": df[selected_column].max(),
                                "max_after": transformed_df[selected_column].max()
                            }
                            
                            transformation_name = f"Square transform on {selected_column}"
                            
                            transformation_details = {
                                "type": "power_transform",
                                "column": selected_column,
                                "power": 2,
                                "stats": stats
                            }
                            
                        elif math_operation == "Cube":
                            transformed_df = df.copy()
                            transformed_df[selected_column] = df[selected_column] ** 3
                            
                            stats = {
                                "mean_before": df[selected_column].mean(),
                                "mean_after": transformed_df[selected_column].mean(),
                                "min_before": df[selected_column].min(),
                                "min_after": transformed_df[selected_column].min(),
                                "max_before": df[selected_column].max(),
                                "max_after": transformed_df[selected_column].max()
                            }
                            
                            transformation_name = f"Cube transform on {selected_column}"
                            
                            transformation_details = {
                                "type": "power_transform",
                                "column": selected_column,
                                "power": 3,
                                "stats": stats
                            }
                            
                        elif math_operation == "Absolute value":
                            transformed_df = df.copy()
                            transformed_df[selected_column] = df[selected_column].abs()
                            
                            stats = {
                                "mean_before": df[selected_column].mean(),
                                "mean_after": transformed_df[selected_column].mean(),
                                "min_before": df[selected_column].min(),
                                "min_after": transformed_df[selected_column].min(),
                                "max_before": df[selected_column].max(),
                                "max_after": transformed_df[selected_column].max(),
                                "negative_values_before": (df[selected_column] < 0).sum()
                            }
                            
                            transformation_name = f"Absolute value transform on {selected_column}"
                            
                            transformation_details = {
                                "type": "abs_transform",
                                "column": selected_column,
                                "stats": stats
                            }
                            
                        elif math_operation == "Round":
                            transformed_df, stats = round_off(df, selected_column, decimals=decimals)
                            
                            transformation_name = f"Round {selected_column} to {decimals} decimal places"
                            
                            transformation_details = {
                                "type": "round",
                                "column": selected_column,
                                "decimals": decimals,
                                "stats": stats
                            }
                        
                        # Update the dataframe
                        df = transformed_df
                        
                        # Register transformation
                        local_register_transformation(
                            st.session_state.transformations,
                            st.session_state.transformation_history,
                            transformation_name,
                            transformation_details,
                            original_df,
                            df,
                            selected_column
                        )
                        
                        # Update the session state
                        st.session_state.dataset = df
                        
                        # Show success message
                        st.success(f"Successfully applied {math_operation} to {selected_column}.")
                        st.rerun()
                
            elif transformation_type == "Advanced Transformations":
                operation = st.selectbox(
                    "Select advanced operation",
                    ["Create custom column", "Standardize category names", "Custom Python expression"]
                )
                
                if operation == "Create custom column":
                    new_column_name = st.text_input("New column name")
                    
                    # Simple expression builder
                    use_expr_builder = st.checkbox("Use expression builder", value=True)
                    
                    if use_expr_builder:
                        operation_type = st.selectbox(
                            "Operation type",
                            ["Arithmetic", "String", "Conditional"]
                        )
                        
                        if operation_type == "Arithmetic":
                            numeric_columns = df.select_dtypes(include=np.number).columns.tolist()
                            
                            if len(numeric_columns) < 2:
                                st.info("Need at least two numeric columns for arithmetic operations.")
                                execute_button = st.button("Apply Transformation", disabled=True)
                            else:
                                col1 = st.selectbox("First column", numeric_columns, key="arith_col1")
                                operator = st.selectbox("Operator", ["+", "-", "*", "/", "**"])
                                col2 = st.selectbox("Second column", numeric_columns, key="arith_col2")
                                
                                expression = f"{col1} {operator} {col2}"
                                
                                st.info(f"Expression: {expression}")
                                
                                execute_button = st.button("Apply Transformation")
                                
                                if execute_button and new_column_name:
                                    # Apply arithmetic expression
                                    transformed_df = df.copy()
                                    
                                    if operator == "+":
                                        transformed_df[new_column_name] = df[col1] + df[col2]
                                    elif operator == "-":
                                        transformed_df[new_column_name] = df[col1] - df[col2]
                                    elif operator == "*":
                                        transformed_df[new_column_name] = df[col1] * df[col2]
                                    elif operator == "/":
                                        # Handle division by zero
                                        transformed_df[new_column_name] = df[col1] / df[col2].replace(0, np.nan)
                                    elif operator == "**":
                                        transformed_df[new_column_name] = df[col1] ** df[col2]
                                    
                                    # Generate stats
                                    stats = {
                                        "new_column": new_column_name,
                                        "expression": expression,
                                        "mean": transformed_df[new_column_name].mean(),
                                        "min": transformed_df[new_column_name].min(),
                                        "max": transformed_df[new_column_name].max()
                                    }
                                    
                                    # Generate transformation name
                                    transformation_name = f"Create new column '{new_column_name}' using {expression}"
                                    
                                    # Update the dataframe
                                    df = transformed_df
                                    
                                    # Generate transformation details
                                    transformation_details = {
                                        "type": "create_custom_column",
                                        "new_column": new_column_name,
                                        "expression": expression,
                                        "stats": stats
                                    }
                                    
                                    # Register transformation
                                    local_register_transformation(
                                        st.session_state.transformations,
                                        st.session_state.transformation_history,
                                        transformation_name,
                                        transformation_details,
                                        original_df,
                                        df,
                                        None
                                    )
                                    
                                    # Update the session state
                                    st.session_state.dataset = df
                                    
                                    # Show success message
                                    st.success(f"Successfully created new column '{new_column_name}'.")
                                    st.rerun()
                                elif execute_button and not new_column_name:
                                    st.warning("Please enter a name for the new column.")
                        
                        elif operation_type == "String":
                            string_columns = df.select_dtypes(include=['object']).columns.tolist()
                            
                            if not string_columns:
                                st.info("No string columns found in the dataset.")
                                execute_button = st.button("Apply Transformation", disabled=True)
                            else:
                                string_op = st.selectbox(
                                    "String operation",
                                    ["Concatenate", "Extract", "Length", "Uppercase", "Lowercase", "Replace"]
                                )
                                
                                if string_op == "Concatenate":
                                    cols_to_concat = st.multiselect("Columns to concatenate", df.columns)
                                    separator = st.text_input("Separator", value=" ")
                                    
                                    if cols_to_concat:
                                        expression = f"Concatenate {', '.join(cols_to_concat)} with separator '{separator}'"
                                    else:
                                        expression = ""
                                        
                                elif string_op == "Extract":
                                    col = st.selectbox("Column to extract from", string_columns)
                                    extract_type = st.selectbox("Extract type", ["First N characters", "Last N characters", "Range"])
                                    
                                    if extract_type == "First N characters":
                                        n_chars = st.number_input("Number of characters", min_value=1, value=3)
                                        expression = f"First {n_chars} characters of {col}"
                                    elif extract_type == "Last N characters":
                                        n_chars = st.number_input("Number of characters", min_value=1, value=3)
                                        expression = f"Last {n_chars} characters of {col}"
                                    else:  # Range
                                        start_pos = st.number_input("Start position", min_value=0, value=0)
                                        end_pos = st.number_input("End position", min_value=0, value=5)
                                        expression = f"Characters {start_pos} to {end_pos} of {col}"
                                        
                                elif string_op in ["Length", "Uppercase", "Lowercase"]:
                                    col = st.selectbox(f"Column for {string_op}", string_columns)
                                    expression = f"{string_op} of {col}"
                                    
                                elif string_op == "Replace":
                                    col = st.selectbox("Column for replacement", string_columns)
                                    find_text = st.text_input("Find text")
                                    replace_text = st.text_input("Replace with")
                                    expression = f"Replace '{find_text}' with '{replace_text}' in {col}"
                                
                                st.info(f"Operation: {expression}")
                                
                                execute_button = st.button("Apply Transformation")
                                
                                if execute_button and new_column_name and expression:
                                    # Apply string operation
                                    transformed_df = df.copy()
                                    
                                    if string_op == "Concatenate":
                                        # Convert all columns to string and concatenate
                                        transformed_df[new_column_name] = df[cols_to_concat].astype(str).agg(separator.join, axis=1)
                                        
                                    elif string_op == "Extract":
                                        if extract_type == "First N characters":
                                            transformed_df[new_column_name] = df[col].astype(str).str[:n_chars]
                                        elif extract_type == "Last N characters":
                                            transformed_df[new_column_name] = df[col].astype(str).str[-n_chars:]
                                        else:  # Range
                                            transformed_df[new_column_name] = df[col].astype(str).str[start_pos:end_pos]
                                            
                                    elif string_op == "Length":
                                        transformed_df[new_column_name] = df[col].astype(str).str.len()
                                        
                                    elif string_op == "Uppercase":
                                        transformed_df[new_column_name] = df[col].astype(str).str.upper()
                                        
                                    elif string_op == "Lowercase":
                                        transformed_df[new_column_name] = df[col].astype(str).str.lower()
                                        
                                    elif string_op == "Replace":
                                        transformed_df[new_column_name] = df[col].astype(str).str.replace(find_text, replace_text)
                                    
                                    # Generate stats
                                    if transformed_df[new_column_name].dtype.kind in 'ifc':  # If numeric
                                        stats = {
                                            "new_column": new_column_name,
                                            "expression": expression,
                                            "mean": transformed_df[new_column_name].mean(),
                                            "min": transformed_df[new_column_name].min(),
                                            "max": transformed_df[new_column_name].max()
                                        }
                                    else:
                                        stats = {
                                            "new_column": new_column_name,
                                            "expression": expression,
                                            "unique_values": transformed_df[new_column_name].nunique()
                                        }
                                    
                                    # Generate transformation name
                                    transformation_name = f"Create string column '{new_column_name}' using {expression}"
                                    
                                    # Update the dataframe
                                    df = transformed_df
                                    
                                    # Generate transformation details
                                    transformation_details = {
                                        "type": "create_string_column",
                                        "new_column": new_column_name,
                                        "operation": string_op,
                                        "expression": expression,
                                        "stats": stats
                                    }
                                    
                                    # Register transformation
                                    local_register_transformation(
                                        st.session_state.transformations,
                                        st.session_state.transformation_history,
                                        transformation_name,
                                        transformation_details,
                                        original_df,
                                        df,
                                        None
                                    )
                                    
                                    # Update the session state
                                    st.session_state.dataset = df
                                    
                                    # Show success message
                                    st.success(f"Successfully created new column '{new_column_name}'.")
                                    st.rerun()
                                elif execute_button and not new_column_name:
                                    st.warning("Please enter a name for the new column.")
                        
                        elif operation_type == "Conditional":
                            condition_column = st.selectbox("Condition based on column", df.columns)
                            
                            # Get column type to determine condition options
                            col_dtype = df[condition_column].dtype
                            
                            if np.issubdtype(col_dtype, np.number):
                                # Numeric condition
                                condition_type = st.selectbox(
                                    "Condition type",
                                    ["Greater than", "Less than", "Equal to", "Between"]
                                )
                                
                                if condition_type == "Between":
                                    min_val = st.number_input("Minimum value", value=float(df[condition_column].min()))
                                    max_val = st.number_input("Maximum value", value=float(df[condition_column].max()))
                                    
                                    condition_expr = f"({condition_column} >= {min_val}) & ({condition_column} <= {max_val})"
                                else:
                                    threshold = st.number_input("Threshold value", value=float(df[condition_column].mean()))
                                    
                                    if condition_type == "Greater than":
                                        condition_expr = f"{condition_column} > {threshold}"
                                    elif condition_type == "Less than":
                                        condition_expr = f"{condition_column} < {threshold}"
                                    else:  # Equal to
                                        condition_expr = f"{condition_column} == {threshold}"
                            else:
                                # Categorical condition
                                unique_values = df[condition_column].dropna().unique()
                                
                                if len(unique_values) <= 10:
                                    # For categorical with few values
                                    selected_value = st.selectbox("Equal to value", unique_values)
                                    condition_expr = f"{condition_column} == '{selected_value}'"
                                else:
                                    # For categorical with many values
                                    condition_type = st.selectbox(
                                        "Condition type",
                                        ["Equal to", "Contains", "Starts with", "Ends with"]
                                    )
                                    
                                    text_value = st.text_input("Condition text")
                                    
                                    if condition_type == "Equal to":
                                        condition_expr = f"{condition_column} == '{text_value}'"
                                    elif condition_type == "Contains":
                                        condition_expr = f"{condition_column}.str.contains('{text_value}')"
                                    elif condition_type == "Starts with":
                                        condition_expr = f"{condition_column}.str.startswith('{text_value}')"
                                    else:  # Ends with
                                        condition_expr = f"{condition_column}.str.endswith('{text_value}')"
                            
                            # Result values
                            true_value = st.text_input("Value if condition is true", value="1")
                            false_value = st.text_input("Value if condition is false", value="0")
                            
                            # Try to convert to numeric if both values appear to be numeric
                            try:
                                true_val = float(true_value)
                                false_val = float(false_value)
                                is_numeric_result = True
                            except:
                                true_val = true_value
                                false_val = false_value
                                is_numeric_result = False
                            
                            expression = f"If {condition_expr} then {true_value} else {false_value}"
                            
                            st.info(f"Expression: {expression}")
                            
                            execute_button = st.button("Apply Transformation")
                            
                            if execute_button and new_column_name:
                                # Apply conditional operation
                                transformed_df = df.copy()
                                
                                # Evaluate the condition
                                if np.issubdtype(col_dtype, np.number):
                                    if condition_type == "Between":
                                        mask = (df[condition_column] >= min_val) & (df[condition_column] <= max_val)
                                    elif condition_type == "Greater than":
                                        mask = df[condition_column] > threshold
                                    elif condition_type == "Less than":
                                        mask = df[condition_column] < threshold
                                    else:  # Equal to
                                        mask = df[condition_column] == threshold
                                else:
                                    if len(unique_values) <= 10:
                                        mask = df[condition_column] == selected_value
                                    else:
                                        if condition_type == "Equal to":
                                            mask = df[condition_column] == text_value
                                        elif condition_type == "Contains":
                                            mask = df[condition_column].astype(str).str.contains(text_value, na=False)
                                        elif condition_type == "Starts with":
                                            mask = df[condition_column].astype(str).str.startswith(text_value, na=False)
                                        else:  # Ends with
                                            mask = df[condition_column].astype(str).str.endswith(text_value, na=False)
                                
                                # Apply the condition result
                                transformed_df[new_column_name] = np.where(mask, true_val, false_val)
                                
                                # Generate stats
                                if is_numeric_result:
                                    stats = {
                                        "new_column": new_column_name,
                                        "expression": expression,
                                        "mean": transformed_df[new_column_name].mean(),
                                        "true_count": mask.sum(),
                                        "false_count": (~mask).sum()
                                    }
                                else:
                                    stats = {
                                        "new_column": new_column_name,
                                        "expression": expression,
                                        "true_count": mask.sum(),
                                        "false_count": (~mask).sum()
                                    }
                                
                                # Generate transformation name
                                transformation_name = f"Create conditional column '{new_column_name}'"
                                
                                # Update the dataframe
                                df = transformed_df
                                
                                # Generate transformation details
                                transformation_details = {
                                    "type": "create_conditional_column",
                                    "new_column": new_column_name,
                                    "condition": condition_expr,
                                    "true_value": true_val,
                                    "false_value": false_val,
                                    "expression": expression,
                                    "stats": stats
                                }
                                
                                # Register transformation
                                local_register_transformation(
                                    st.session_state.transformations,
                                    st.session_state.transformation_history,
                                    transformation_name,
                                    transformation_details,
                                    original_df,
                                    df,
                                    None
                                )
                                
                                # Update the session state
                                st.session_state.dataset = df
                                
                                # Show success message
                                st.success(f"Successfully created conditional column '{new_column_name}'.")
                                st.rerun()
                            elif execute_button and not new_column_name:
                                st.warning("Please enter a name for the new column.")
                    else:
                        # Custom expression
                        st.markdown("""
                        Enter a custom expression using pandas syntax. Use `df` to refer to the dataframe.
                        
                        Examples:
                        - `df['A'] + df['B']`
                        - `df['A'].str.upper()`
                        - `np.where(df['A'] > 0, 'Positive', 'Negative')`
                        """)
                        
                        expression = st.text_area("Expression", height=100)
                        
                        execute_button = st.button("Apply Transformation")
                        
                        if execute_button and new_column_name and expression:
                            try:
                                # Apply the custom expression
                                transformed_df = df.copy()
                                
                                # Evaluate the expression (local variables don't work with st.text_area)
                                # We need to use pandas and numpy functions
                                local_vars = {'df': df, 'np': np, 'pd': pd}
                                result = eval(expression, globals(), local_vars)
                                
                                transformed_df[new_column_name] = result
                                
                                # Generate stats based on result type
                                if np.issubdtype(transformed_df[new_column_name].dtype, np.number):
                                    stats = {
                                        "new_column": new_column_name,
                                        "expression": expression,
                                        "mean": transformed_df[new_column_name].mean(),
                                        "min": transformed_df[new_column_name].min(),
                                        "max": transformed_df[new_column_name].max()
                                    }
                                else:
                                    stats = {
                                        "new_column": new_column_name,
                                        "expression": expression,
                                        "unique_values": transformed_df[new_column_name].nunique()
                                    }
                                
                                # Generate transformation name
                                transformation_name = f"Create custom column '{new_column_name}'"
                                
                                # Update the dataframe
                                df = transformed_df
                                
                                # Generate transformation details
                                transformation_details = {
                                    "type": "create_custom_column",
                                    "new_column": new_column_name,
                                    "expression": expression,
                                    "stats": stats
                                }
                                
                                # Register transformation
                                local_register_transformation(
                                    st.session_state.transformations,
                                    st.session_state.transformation_history,
                                    transformation_name,
                                    transformation_details,
                                    original_df,
                                    df,
                                    None
                                )
                                
                                # Update the session state
                                st.session_state.dataset = df
                                
                                # Show success message
                                st.success(f"Successfully created custom column '{new_column_name}'.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error in expression: {str(e)}")
                        elif execute_button and not new_column_name:
                            st.warning("Please enter a name for the new column.")
                        elif execute_button and not expression:
                            st.warning("Please enter an expression.")
                
                elif operation == "Standardize category names":
                    categorical_columns = df.select_dtypes(include=['object', 'category']).columns.tolist()
                    
                    if not categorical_columns:
                        st.info("No categorical columns found in the dataset.")
                        execute_button = st.button("Apply Transformation", disabled=True)
                    else:
                        selected_column = st.selectbox("Select categorical column", categorical_columns)
                        
                        # Display unique values
                        unique_values = df[selected_column].dropna().unique()
                        st.write("Unique values:")
                        st.write(", ".join([str(val) for val in unique_values]))
                        
                        # Standardization options
                        standard_option = st.selectbox(
                            "Standardization option",
                            ["Lowercase", "Uppercase", "Title Case", "Remove extra spaces", "Custom mappings"]
                        )
                        
                        if standard_option == "Custom mappings":
                            # Create mappings for each unique value
                            mapping = {}
                            for val in unique_values:
                                mapping[val] = st.text_input(f"Map '{val}' to", value=str(val))
                                
                            std_option = "custom"
                        else:
                            if standard_option == "Lowercase":
                                std_option = "lower"
                            elif standard_option == "Uppercase":
                                std_option = "upper"
                            elif standard_option == "Title Case":
                                std_option = "title"
                            elif standard_option == "Remove extra spaces":
                                std_option = "strip"
                                
                            mapping = None
                        
                        execute_button = st.button("Apply Transformation")
                        
                        if execute_button:
                            # Perform standardization
                            transformed_df, stats = standardize_category_names(
                                df, 
                                selected_column, 
                                method=std_option,
                                custom_mapping=mapping
                            )
                            
                            # Generate transformation name
                            if std_option == "custom":
                                transformation_name = f"Custom standardization of {selected_column}"
                            else:
                                transformation_name = f"Standardize {selected_column} using {standard_option}"
                            
                            # Update the dataframe
                            df = transformed_df
                            
                            # Generate transformation details
                            transformation_details = {
                                "type": "standardize_category",
                                "column": selected_column,
                                "method": std_option,
                                "custom_mapping": mapping,
                                "stats": stats
                            }
                            
                            # Register transformation
                            local_register_transformation(
                                st.session_state.transformations,
                                st.session_state.transformation_history,
                                transformation_name,
                                transformation_details,
                                original_df,
                                df,
                                selected_column
                            )
                            
                            # Update the session state
                            st.session_state.dataset = df
                            
                            # Show success message
                            st.success(f"Successfully standardized {selected_column}.")
                            st.rerun()
                
                elif operation == "Custom Python expression":
                    st.markdown("""
                    Enter a custom Python expression to transform the dataframe. Use `df` to refer to the dataframe.
                    
                    Examples:
                    - `df.fillna(0)`
                    - `df.drop_duplicates()`
                    - `df[df['A'] > 0]`
                    """)
                    
                    expression = st.text_area("Python expression", height=100)
                    
                    execute_button = st.button("Apply Transformation")
                    
                    if execute_button and expression:
                        try:
                            # Apply the custom expression
                            transformed_df = eval(expression, {"df": df.copy(), "np": np, "pd": pd})
                            
                            # Check if the result is a DataFrame
                            if not isinstance(transformed_df, pd.DataFrame):
                                st.error("The expression must return a DataFrame.")
                            else:
                                # Generate stats
                                stats = {
                                    "rows_before": df.shape[0],
                                    "rows_after": transformed_df.shape[0],
                                    "columns_before": df.shape[1],
                                    "columns_after": transformed_df.shape[1]
                                }
                                
                                # Generate transformation name
                                transformation_name = f"Custom Python: {expression[:50]}{'...' if len(expression) > 50 else ''}"
                                
                                # Update the dataframe
                                df = transformed_df
                                
                                # Generate transformation details
                                transformation_details = {
                                    "type": "custom_python",
                                    "expression": expression,
                                    "stats": stats
                                }
                                
                                # Register transformation
                                local_register_transformation(
                                    st.session_state.transformations,
                                    st.session_state.transformation_history,
                                    transformation_name,
                                    transformation_details,
                                    original_df,
                                    df,
                                    None
                                )
                                
                                # Update the session state
                                st.session_state.dataset = df
                                
                                # Show success message
                                st.success("Successfully applied custom Python expression.")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Error in expression: {str(e)}")
                    elif execute_button and not expression:
                        st.warning("Please enter a Python expression.")
        
        with col2:
            # Create AI suggestion section based on column data types
            st.subheader("AI-Powered Suggestions")
            
            # Select column for AI suggestions
            selected_col_for_ai = st.selectbox("Select column for AI suggestions", df.columns)
            
            if selected_col_for_ai:
                # Get column type
                col_dtype = df[selected_col_for_ai].dtype
                if np.issubdtype(col_dtype, np.number):
                    col_type = "numeric"
                elif pd.api.types.is_datetime64_any_dtype(df[selected_col_for_ai]):
                    col_type = "datetime"
                else:
                    col_type = "categorical"
                
                # Get AI suggestions
                with st.spinner("Generating AI suggestions..."):
                    suggestions = generate_column_cleaning_suggestions(df, selected_col_for_ai, col_type)
                    
                    # Display suggestions in a better format
                    st.markdown(f"### Suggestions for '{selected_col_for_ai}'")
                    
                    # Check if we got suggestions back
                    if suggestions and isinstance(suggestions, list):
                        for i, suggestion in enumerate(suggestions):
                            with st.expander(f"{i+1}. {suggestion.get('operation', 'Suggestion')}", expanded=True):
                                st.markdown(f"**Description:** {suggestion.get('description', 'N/A')}")
                                st.markdown(f"**Rationale:** {suggestion.get('rationale', 'N/A')}")
                                st.markdown(f"**Code Action:** `{suggestion.get('code_action', 'N/A')}`")
                                st.divider()
                    else:
                        st.info("No suggestions available for this column.")
            
            # Data preview section
            st.subheader("Data Preview")
            
            # Show original and transformed data
            before_after_tabs = st.tabs(["Current Data", "Original Data", "Column Statistics"])
            
            with before_after_tabs[0]:
                st.dataframe(df.head(10))
                
                # Show data shape and memory usage
                st.info(f"Shape: {df.shape[0]} rows × {df.shape[1]} columns")
                
                # Show datatypes summary
                dtype_summary = df.dtypes.value_counts().reset_index()
                dtype_summary.columns = ['Data Type', 'Count']
                st.table(dtype_summary)
            
            with before_after_tabs[1]:
                st.dataframe(original_df.head(10))
                
                # Show the original data shape
                st.info(f"Original shape: {original_df.shape[0]} rows × {original_df.shape[1]} columns")
                
                # Show changes in data shape if any
                if df.shape != original_df.shape:
                    row_diff = df.shape[0] - original_df.shape[0]
                    col_diff = df.shape[1] - original_df.shape[1]
                    
                    row_change = f"+{row_diff}" if row_diff > 0 else str(row_diff)
                    col_change = f"+{col_diff}" if col_diff > 0 else str(col_diff)
                    
                    st.info(f"Changes: {row_change} rows, {col_change} columns")
            
            with before_after_tabs[2]:
                # Show column statistics
                if st.session_state.transformations:
                    # Get the latest transformation
                    latest_transformation = st.session_state.transformations[-1]
                    
                    # Check if a specific column was affected
                    affected_columns = latest_transformation.get("affected_columns", [])
                    
                    if affected_columns and not isinstance(affected_columns, list):
                        affected_columns = [affected_columns]
                        
                    if affected_columns:
                        for col in affected_columns:
                            if col in df.columns:
                                # Get the stats before and after
                                stats = get_column_stats_before_after(original_df, df, col)
                                
                                st.markdown(f"### Statistics for '{col}'")
                                
                                if stats["is_numeric"]:
                                    # Create a DataFrame for numeric stats
                                    stats_df = pd.DataFrame({
                                        "Statistic": ["Mean", "Median", "Min", "Max", "Std Dev", "Missing"],
                                        "Before": [
                                            stats["before"]["mean"],
                                            stats["before"]["median"],
                                            stats["before"]["min"],
                                            stats["before"]["max"],
                                            stats["before"]["std"],
                                            stats["before"]["missing"]
                                        ],
                                        "After": [
                                            stats["after"]["mean"],
                                            stats["after"]["median"],
                                            stats["after"]["min"],
                                            stats["after"]["max"],
                                            stats["after"]["std"],
                                            stats["after"]["missing"]
                                        ]
                                    })
                                    
                                    st.table(stats_df)
                                    
                                    # Show distribution before and after
                                    st.markdown("#### Distribution Before vs. After")
                                    
                                    # Combine before and after for plotting
                                    before_df = original_df[[col]].copy()
                                    before_df['Version'] = 'Before'
                                    
                                    after_df = df[[col]].copy()
                                    after_df['Version'] = 'After'
                                    
                                    combined_df = pd.concat([before_df, after_df])
                                    
                                    # Create a histogram
                                    fig = px.histogram(
                                        combined_df, 
                                        x=col, 
                                        color='Version',
                                        barmode='overlay',
                                        opacity=0.7,
                                        marginal="box"
                                    )
                                    
                                    st.plotly_chart(fig, use_container_width=True)
                                else:
                                    # Create a DataFrame for non-numeric stats
                                    stats_df = pd.DataFrame({
                                        "Statistic": ["Unique Values", "Missing", "Most Common"],
                                        "Before": [
                                            stats["before"]["unique"],
                                            stats["before"]["missing"],
                                            stats["before"]["most_common"]
                                        ],
                                        "After": [
                                            stats["after"]["unique"],
                                            stats["after"]["missing"],
                                            stats["after"]["most_common"]
                                        ]
                                    })
                                    
                                    st.table(stats_df)
                                    
                                    # Show bar chart of top categories before and after
                                    st.markdown("#### Top Categories Before vs. After")
                                    
                                    top_before = original_df[col].value_counts().head(10).reset_index()
                                    top_before.columns = ['Value', 'Count']
                                    top_before['Version'] = 'Before'
                                    
                                    top_after = df[col].value_counts().head(10).reset_index()
                                    top_after.columns = ['Value', 'Count']
                                    top_after['Version'] = 'After'
                                    
                                    combined_top = pd.concat([top_before, top_after])
                                    
                                    fig = px.bar(
                                        combined_top,
                                        x='Value',
                                        y='Count',
                                        color='Version',
                                        barmode='group'
                                    )
                                    
                                    st.plotly_chart(fig, use_container_width=True)
                    else:
                        # Show general dataframe stats
                        st.markdown("### Overall DataFrame Statistics")
                        
                        stats_df = pd.DataFrame({
                            "Statistic": ["Rows", "Columns", "Missing Values", "Memory Usage"],
                            "Before": [
                                original_df.shape[0],
                                original_df.shape[1],
                                original_df.isnull().sum().sum(),
                                f"{original_df.memory_usage(deep=True).sum() / (1024 * 1024):.2f} MB"
                            ],
                            "After": [
                                df.shape[0],
                                df.shape[1],
                                df.isnull().sum().sum(),
                                f"{df.memory_usage(deep=True).sum() / (1024 * 1024):.2f} MB"
                            ]
                        })
                        
                        st.table(stats_df)
                else:
                    st.info("Apply a transformation to see column statistics.")
                    
            # Visualization of transformations
            st.subheader("Transformation Visualization")
            
            if st.session_state.transformations:
                # Create a visual flow chart of transformations
                st.markdown("### Transformation Flow")
                flow_chart = generate_transformation_flow_chart(st.session_state.transformations)
                st.graphviz_chart(flow_chart)
                
                # Before and after comparison for selected column
                st.markdown("### Before and After Comparison")
                comparison_col = st.selectbox("Select column for comparison", df.columns, key="compare_col")
                
                if comparison_col:
                    comparison_viz = create_before_after_comparison(original_df, df, comparison_col)
                    st.plotly_chart(comparison_viz, use_container_width=True)
            else:
                st.info("Apply transformations to see visualizations.")
    
    with history_tab:
        st.header("Transformation History")
        
        if not st.session_state.transformations:
            st.info("No transformations have been applied yet.")
        else:
            # Create columns for the transformation history
            history_cols = st.columns([3, 1, 1])
            with history_cols[0]:
                st.markdown("**Transformation**")
            with history_cols[1]:
                st.markdown("**Applied At**")
            with history_cols[2]:
                st.markdown("**Actions**")
                
            # Create a separator
            st.markdown("---")
            
            # Display the transformations
            for i, t in enumerate(st.session_state.transformations):
                cols = st.columns([3, 1, 1])
                
                with cols[0]:
                    st.markdown(f"**{i+1}. {t['name']}**")
                    
                    # Show additional details as expandable
                    with st.expander("Details"):
                        st.json(t["details"])
                
                with cols[1]:
                    st.markdown(t["timestamp"])
                
                with cols[2]:
                    # Button to remove this transformation
                    if st.button("Remove", key=f"remove_{i}"):
                        # Store a copy of the current transformations
                        current_transformations = st.session_state.transformations.copy()
                        
                        # Remove this transformation and all that follow
                        st.session_state.transformations = current_transformations[:i]
                        
                        # Reapply the remaining transformations
                        if i == 0:
                            # If removing the first transformation, reset to original data
                            st.session_state.dataset = original_df.copy()
                        else:
                            # Get the dataframe at the previous step
                            prev_transformation = current_transformations[i-1]
                            if "result_df" in prev_transformation:
                                st.session_state.dataset = prev_transformation["result_df"].copy()
                            else:
                                # If the result_df is not available, reapply all transformations
                                result_df = original_df.copy()
                                for j in range(i):
                                    t_details = current_transformations[j]["details"]
                                    # Reapply transformation using the stored details
                                    # (This would require implementing logic to reapply each type of transformation)
                                    # For simplicity, we'll just update the session state
                                    result_df = apply_transformations(result_df, [t_details])
                                
                                st.session_state.dataset = result_df
                        
                        # Add to transformation history
                        st.session_state.transformation_history.append({
                            "action": "removed",
                            "transformation": current_transformations[i]["name"],
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
                        
                        st.success(f"Removed transformation: {current_transformations[i]['name']}")
                        st.rerun()
                
                # Add a separator between transformations
                st.markdown("---")
            
            # Add a button to undo all transformations
            if st.button("Reset All Transformations"):
                st.session_state.transformations = []
                st.session_state.dataset = original_df.copy()
                
                # Add to transformation history
                st.session_state.transformation_history.append({
                    "action": "reset_all",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                
                st.success("Reset all transformations. Data reverted to original state.")
                st.rerun()
            
            # Display transformation journey visualization
            st.subheader("Transformation Journey")
            if len(st.session_state.transformations) > 0:
                journey_viz = create_transformation_journey_visualization(
                    original_df, 
                    st.session_state.transformations
                )
                st.pyplot(journey_viz)
            
            # Display transformation history log
            st.subheader("Activity Log")
            if st.session_state.transformation_history:
                history_df = pd.DataFrame(st.session_state.transformation_history)
                st.dataframe(history_df, use_container_width=True)
    
    with code_tab:
        st.header("Generated Python Code")
        
        if not st.session_state.transformations:
            st.info("No transformations have been applied yet.")
        else:
            # Generate Python code for the transformations
            code = "import pandas as pd\nimport numpy as np\n\n"
            code += "# Load the dataset\n"
            code += "df = pd.read_csv('your_data.csv')  # Update with your file path\n\n"
            code += "# Apply transformations\n"
            
            for i, t in enumerate(st.session_state.transformations):
                details = t["details"]
                t_type = details.get("type")
                
                code += f"# Step {i+1}: {t['name']}\n"
                
                if t_type == "impute_missing":
                    method = details.get("method")
                    column = details.get("column")
                    
                    if method == "mean":
                        code += f"df['{column}'] = df['{column}'].fillna(df['{column}'].mean())\n"
                    elif method == "median":
                        code += f"df['{column}'] = df['{column}'].fillna(df['{column}'].median())\n"
                    elif method == "mode":
                        code += f"df['{column}'] = df['{column}'].fillna(df['{column}'].mode()[0])\n"
                    elif method == "constant value":
                        constant = details.get("constant_value")
                        code += f"df['{column}'] = df['{column}'].fillna({constant})\n"
                
                elif t_type == "handle_outliers":
                    method = details.get("method")
                    column = details.get("column")
                    threshold = details.get("threshold")
                    handle_method = details.get("handle_method")
                    
                    if method == "zscore":
                        code += f"# Z-score method with threshold {threshold}\n"
                        code += f"from scipy import stats\n"
                        code += f"z_scores = stats.zscore(df['{column}'])\n"
                        code += f"outlier_indices = np.where(np.abs(z_scores) > {threshold})[0]\n"
                    elif method == "iqr":
                        code += f"# IQR method with multiplier {threshold}\n"
                        code += f"q1 = df['{column}'].quantile(0.25)\n"
                        code += f"q3 = df['{column}'].quantile(0.75)\n"
                        code += f"iqr = q3 - q1\n"
                        code += f"lower_bound = q1 - {threshold} * iqr\n"
                        code += f"upper_bound = q3 + {threshold} * iqr\n"
                        code += f"outlier_indices = df[(df['{column}'] < lower_bound) | (df['{column}'] > upper_bound)].index\n"
                    elif method == "percentile":
                        lower, upper = threshold
                        code += f"# Percentile method with range {lower}-{upper}\n"
                        code += f"lower_bound = df['{column}'].quantile({lower/100})\n"
                        code += f"upper_bound = df['{column}'].quantile({upper/100})\n"
                        code += f"outlier_indices = df[(df['{column}'] < lower_bound) | (df['{column}'] > upper_bound)].index\n"
                    
                    if handle_method == "remove":
                        code += f"# Remove outliers\n"
                        code += f"df = df.drop(outlier_indices)\n"
                    elif handle_method == "cap":
                        code += f"# Cap outliers\n"
                        code += f"df.loc[df['{column}'] < lower_bound, '{column}'] = lower_bound\n"
                        code += f"df.loc[df['{column}'] > upper_bound, '{column}'] = upper_bound\n"
                    elif handle_method == "replace with mean":
                        code += f"# Replace outliers with mean\n"
                        code += f"mean_value = df['{column}'].mean()\n"
                        code += f"df.loc[outlier_indices, '{column}'] = mean_value\n"
                    elif handle_method == "replace with median":
                        code += f"# Replace outliers with median\n"
                        code += f"median_value = df['{column}'].median()\n"
                        code += f"df.loc[outlier_indices, '{column}'] = median_value\n"
                
                elif t_type == "normalize":
                    method = details.get("method")
                    columns = details.get("columns")
                    
                    column_list = ", ".join([f"'{col}'" for col in columns])
                    
                    if method == "min_max_scaling":
                        code += f"# Min-Max scaling\n"
                        code += f"from sklearn.preprocessing import MinMaxScaler\n"
                        code += f"scaler = MinMaxScaler()\n"
                        code += f"df[[{column_list}]] = scaler.fit_transform(df[[{column_list}]])\n"
                    elif method == "z_score_standardization":
                        code += f"# Z-score standardization\n"
                        code += f"from sklearn.preprocessing import StandardScaler\n"
                        code += f"scaler = StandardScaler()\n"
                        code += f"df[[{column_list}]] = scaler.fit_transform(df[[{column_list}]])\n"
                    elif method == "robust_scaling":
                        code += f"# Robust scaling\n"
                        code += f"from sklearn.preprocessing import RobustScaler\n"
                        code += f"scaler = RobustScaler()\n"
                        code += f"df[[{column_list}]] = scaler.fit_transform(df[[{column_list}]])\n"
                
                elif t_type == "encode_categorical":
                    method = details.get("method")
                    column = details.get("column")
                    
                    if method == "one_hot_encoding":
                        code += f"# One-hot encoding\n"
                        code += f"df = pd.get_dummies(df, columns=['{column}'], prefix=['{column}'])\n"
                    elif method == "label_encoding":
                        code += f"# Label encoding\n"
                        code += f"from sklearn.preprocessing import LabelEncoder\n"
                        code += f"le = LabelEncoder()\n"
                        code += f"df['{column}'] = le.fit_transform(df['{column}'])\n"
                    elif method == "frequency_encoding":
                        code += f"# Frequency encoding\n"
                        code += f"freq_encoding = df['{column}'].value_counts(normalize=True).to_dict()\n"
                        code += f"df['{column}_freq'] = df['{column}'].map(freq_encoding)\n"
                
                elif t_type == "to_datetime":
                    column = details.get("column")
                    format_str = details.get("format")
                    
                    if format_str and format_str != "auto":
                        code += f"# Convert to datetime with format\n"
                        code += f"df['{column}'] = pd.to_datetime(df['{column}'], format='{format_str}')\n"
                    else:
                        code += f"# Convert to datetime\n"
                        code += f"df['{column}'] = pd.to_datetime(df['{column}'])\n"
                
                elif t_type == "format_date":
                    column = details.get("column")
                    output_format = details.get("output_format")
                    
                    code += f"# Format date\n"
                    code += f"df['{column}'] = df['{column}'].dt.strftime('{output_format}')\n"
                
                elif t_type == "extract_date_component":
                    column = details.get("column")
                    component = details.get("component")
                    
                    new_col = f"{column}_{component}"
                    
                    code += f"# Extract date component\n"
                    if component == "year":
                        code += f"df['{new_col}'] = df['{column}'].dt.year\n"
                    elif component == "month":
                        code += f"df['{new_col}'] = df['{column}'].dt.month\n"
                    elif component == "day":
                        code += f"df['{new_col}'] = df['{column}'].dt.day\n"
                    elif component == "hour":
                        code += f"df['{new_col}'] = df['{column}'].dt.hour\n"
                    elif component == "minute":
                        code += f"df['{new_col}'] = df['{column}'].dt.minute\n"
                    elif component == "second":
                        code += f"df['{new_col}'] = df['{column}'].dt.second\n"
                    elif component == "day_of_week":
                        code += f"df['{new_col}'] = df['{column}'].dt.day_name()\n"
                    elif component == "week_of_year":
                        code += f"df['{new_col}'] = df['{column}'].dt.isocalendar().week\n"
                    elif component == "quarter":
                        code += f"df['{new_col}'] = df['{column}'].dt.quarter\n"
                
                elif t_type == "drop_columns":
                    columns = details.get("columns")
                    
                    column_list = ", ".join([f"'{col}'" for col in columns])
                    
                    code += f"# Drop columns\n"
                    code += f"df = df.drop(columns=[{column_list}])\n"
                
                elif t_type == "drop_rows_with_missing":
                    how = details.get("how")
                    subset = details.get("subset")
                    
                    code += f"# Drop rows with missing values\n"
                    if subset:
                        subset_list = ", ".join([f"'{col}'" for col in subset])
                        code += f"df = df.dropna(subset=[{subset_list}], how='{how}')\n"
                    else:
                        code += f"df = df.dropna(how='{how}')\n"
                
                elif t_type == "filter_rows":
                    column = details.get("column")
                    condition = details.get("condition")
                    
                    code += f"# Filter rows\n"
                    code += f"# Condition: {condition}\n"
                    code += f"# You may need to adjust this code based on the specific condition\n"
                    
                    if "between" in condition.lower():
                        # Extract min and max values from condition string
                        parts = condition.split("between")[1].strip().split("and")
                        min_val = parts[0].strip()
                        max_val = parts[1].strip()
                        
                        code += f"df = df[(df['{column}'] >= {min_val}) & (df['{column}'] <= {max_val})]\n"
                    elif "greater than" in condition.lower():
                        threshold = condition.split("greater than")[1].strip()
                        code += f"df = df[df['{column}'] > {threshold}]\n"
                    elif "less than" in condition.lower():
                        threshold = condition.split("less than")[1].strip()
                        code += f"df = df[df['{column}'] < {threshold}]\n"
                    elif "equal" in condition.lower():
                        value = condition.split("equal")[1].strip()
                        # Check if it's a string (has quotes)
                        if "'" in value:
                            code += f"df = df[df['{column}'] == {value}]\n"
                        else:
                            code += f"df = df[df['{column}'] == {value}]\n"
                    else:
                        code += f"# Custom condition - replace with appropriate filter\n"
                        code += f"# df = df[...]\n"
                
                elif t_type == "rename_columns":
                    rename_map = details.get("rename_map")
                    
                    rename_dict = ", ".join([f"'{old}': '{new}'" for old, new in rename_map.items()])
                    
                    code += f"# Rename columns\n"
                    code += f"df = df.rename(columns={{{rename_dict}}})\n"
                
                elif t_type == "create_bins":
                    column = details.get("column")
                    num_bins = details.get("num_bins")
                    method = details.get("method")
                    bin_edges = details.get("bin_edges")
                    labels = details.get("labels")
                    
                    bin_column = f"{column}_bins"
                    
                    code += f"# Create bins\n"
                    
                    if method == "equal_width":
                        if labels:
                            labels_list = ", ".join([f"'{label}'" for label in labels])
                            code += f"labels = [{labels_list}]\n"
                            code += f"df['{bin_column}'] = pd.cut(df['{column}'], bins={num_bins}, labels=labels)\n"
                        else:
                            code += f"df['{bin_column}'] = pd.cut(df['{column}'], bins={num_bins})\n"
                    elif method == "equal_frequency":
                        if labels:
                            labels_list = ", ".join([f"'{label}'" for label in labels])
                            code += f"labels = [{labels_list}]\n"
                            code += f"df['{bin_column}'] = pd.qcut(df['{column}'], q={num_bins}, labels=labels)\n"
                        else:
                            code += f"df['{bin_column}'] = pd.qcut(df['{column}'], q={num_bins})\n"
                    elif method == "custom":
                        bin_edges_list = ", ".join([str(edge) for edge in bin_edges])
                        
                        if labels:
                            labels_list = ", ".join([f"'{label}'" for label in labels])
                            code += f"bins = [{bin_edges_list}]\n"
                            code += f"labels = [{labels_list}]\n"
                            code += f"df['{bin_column}'] = pd.cut(df['{column}'], bins=bins, labels=labels)\n"
                        else:
                            code += f"bins = [{bin_edges_list}]\n"
                            code += f"df['{bin_column}'] = pd.cut(df['{column}'], bins=bins)\n"
                
                elif t_type == "log_transform":
                    column = details.get("column")
                    base = details.get("base")
                    handle_zeros = details.get("handle_zeros")
                    
                    code += f"# Log transform\n"
                    
                    if handle_zeros:
                        code += f"# Add small constant to handle zeros/negatives\n"
                        code += f"small_const = 1e-8  # Adjust as needed\n"
                        
                        if base == "e":
                            code += f"df['{column}'] = np.log(df['{column}'] + small_const)\n"
                        else:
                            code += f"df['{column}'] = np.log{base}(df['{column}'] + small_const)\n"
                    else:
                        if base == "e":
                            code += f"df['{column}'] = np.log(df['{column}'])\n"
                        else:
                            code += f"df['{column}'] = np.log{base}(df['{column}'])\n"
                
                elif t_type == "round":
                    column = details.get("column")
                    decimals = details.get("decimals")
                    
                    code += f"# Round values\n"
                    code += f"df['{column}'] = df['{column}'].round({decimals})\n"
                
                elif t_type in ["create_custom_column", "create_string_column", "create_conditional_column"]:
                    new_column = details.get("new_column")
                    expression = details.get("expression")
                    
                    code += f"# Create custom column\n"
                    code += f"# Expression: {expression}\n"
                    code += f"# You may need to adjust this code based on the specific expression\n"
                    
                    # Try to infer a simple pandas expression
                    if "+" in expression or "-" in expression or "*" in expression or "/" in expression:
                        # Likely a simple arithmetic expression
                        code += f"df['{new_column}'] = {expression}\n"
                    else:
                        code += f"# Custom expression - replace with appropriate implementation\n"
                        code += f"# df['{new_column}'] = ...\n"
                
                elif t_type == "standardize_category":
                    column = details.get("column")
                    method = details.get("method")
                    custom_mapping = details.get("custom_mapping")
                    
                    code += f"# Standardize category names\n"
                    
                    if method == "lower":
                        code += f"df['{column}'] = df['{column}'].str.lower()\n"
                    elif method == "upper":
                        code += f"df['{column}'] = df['{column}'].str.upper()\n"
                    elif method == "title":
                        code += f"df['{column}'] = df['{column}'].str.title()\n"
                    elif method == "strip":
                        code += f"df['{column}'] = df['{column}'].str.strip()\n"
                    elif method == "custom":
                        code += f"# Custom mapping\n"
                        code += f"mapping = {{\n"
                        for old, new in custom_mapping.items():
                            code += f"    '{old}': '{new}',\n"
                        code += f"}}\n"
                        code += f"df['{column}'] = df['{column}'].map(mapping)\n"
                
                elif t_type == "custom_python":
                    expression = details.get("expression")
                    
                    code += f"# Custom Python expression\n"
                    code += f"# {expression}\n"
                    code += f"# You may need to adjust this code based on the specific expression\n"
                    
                    # Try to infer if it's a simple expression
                    if expression.strip().startswith("df."):
                        code += f"df = {expression}\n"
                    else:
                        code += f"# Custom expression - replace with appropriate implementation\n"
                        code += f"# df = ...\n"
                
                code += "\n"
            
            # Add export code
            code += "# Export the transformed dataset\n"
            code += "df.to_csv('transformed_data.csv', index=False)\n"
            
            # Display the code
            st.code(code, language="python")
            
            # Copy button
            if st.button("Copy Code to Clipboard"):
                st.success("Code copied to clipboard! You can paste it into your Python editor.")
                
            # Download button
            st.download_button(
                label="Download as Python script",
                data=code,
                file_name="data_transformation_script.py",
                mime="text/plain"
            )
    
    # Navigation section
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("← EDA Dashboard", use_container_width=True):
            st.switch_page("pages/03_EDA_Dashboard.py")
    with col2:
        if st.button("Home", use_container_width=True):
            st.switch_page("app.py")
    with col3:
        if st.button("Insights Dashboard →", use_container_width=True):
            st.switch_page("pages/05_Insights_Dashboard.py")