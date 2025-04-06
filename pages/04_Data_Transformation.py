import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json
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

st.set_page_config(
    page_title="Data Transformation | Analytics Assist",
    page_icon="🧹",
    layout="wide"
)

# Check if dataset exists in session state
if 'dataset' not in st.session_state or st.session_state.dataset is None:
    st.warning("Please upload a dataset first.")
    st.button("Go to Upload Page", on_click=lambda: st.switch_page("pages/01_Upload_Data.py"))
    st.stop()

# Header and description
st.title("Data Transformation & Cleaning")
st.markdown("""
Transform and clean your data with AI-powered suggestions. All transformations require 
your confirmation before being applied, giving you full control over the process.
""")

# Get data from session state
df = st.session_state.dataset
column_types = st.session_state.column_types
file_name = st.session_state.file_name

# Initialize transformation history if not exists
if 'transformations' not in st.session_state:
    st.session_state.transformations = []
if 'transformation_history' not in st.session_state:
    st.session_state.transformation_history = []

# Create tabs for different transformation approaches
tab1, tab2, tab3 = st.tabs([
    "🧠 AI Suggestions", 
    "🛠️ Manual Transformations", 
    "📋 Transformation History"
])

# Tab 1: AI Suggestions
with tab1:
    st.subheader("AI-Suggested Data Cleaning")
    st.markdown("""
    Our AI analyzes your data and suggests appropriate cleaning operations. 
    Review each suggestion and apply the ones you find useful.
    """)
    
    # Column selection for AI suggestions
    all_columns = df.columns.tolist()
    
    # Let user select columns or analyze all
    analysis_option = st.radio(
        "Select columns for analysis:",
        ["Analyze all columns", "Select specific columns"]
    )
    
    if analysis_option == "Select specific columns":
        selected_columns = st.multiselect(
            "Choose columns to analyze",
            options=all_columns,
            default=all_columns[:min(3, len(all_columns))]
        )
    else:
        selected_columns = all_columns
    
    # Generate suggestions button
    if st.button("Generate AI Suggestions"):
        if not selected_columns:
            st.warning("Please select at least one column for analysis.")
        else:
            with st.spinner("Analyzing data and generating suggestions..."):
                # Store AI suggestions in session state
                st.session_state.ai_suggestions = []
                
                # Process each selected column
                for column in selected_columns:
                    # Get column type from session state
                    column_type = column_types.get(column, "unknown")
                    
                    # Generate suggestions
                    column_suggestions = generate_column_cleaning_suggestions(df, column, column_type)
                    
                    if column_suggestions:
                        # Make sure we have a list of dictionaries, not strings
                        valid_suggestions = []
                        for suggestion in column_suggestions:
                            # If suggestion is already a dictionary
                            if isinstance(suggestion, dict):
                                # Add column name to the suggestion
                                suggestion_copy = suggestion.copy()  # Create a copy to avoid modifying the original
                                suggestion_copy['column'] = column
                                valid_suggestions.append(suggestion_copy)
                            # If suggestion is a string (unexpected format)
                            elif isinstance(suggestion, str):
                                # Create a basic suggestion dictionary
                                valid_suggestions.append({
                                    'operation': 'unknown',
                                    'description': suggestion,
                                    'rationale': 'No rationale provided',
                                    'code_action': '',
                                    'column': column
                                })
                        
                        st.session_state.ai_suggestions.extend(valid_suggestions)
    
    # Display AI suggestions
    if 'ai_suggestions' in st.session_state and st.session_state.ai_suggestions:
        st.subheader("Suggested Transformations")
        
        # Group suggestions by column
        suggestions_by_column = {}
        for suggestion in st.session_state.ai_suggestions:
            column = suggestion.get('column', 'Unknown')
            if column not in suggestions_by_column:
                suggestions_by_column[column] = []
            suggestions_by_column[column].append(suggestion)
        
        # Display suggestions by column with collapsible sections
        for column, suggestions in suggestions_by_column.items():
            with st.expander(f"Suggestions for '{column}' ({len(suggestions)})", expanded=True):
                for i, suggestion in enumerate(suggestions):
                    # Create a card-like display for each suggestion
                    st.markdown(f"### {suggestion.get('operation', 'Transformation')}")
                    st.markdown(f"**Description**: {suggestion.get('description', 'No description provided')}")
                    st.markdown(f"**Rationale**: {suggestion.get('rationale', 'No rationale provided')}")
                    
                    # Preview before/after with a sample
                    with st.container():
                        if st.button(f"Preview Effect", key=f"preview_{column}_{i}"):
                            # Apply the transformation to a temporary dataframe
                            df_before = df.copy()
                            
                            # Get the code action
                            code_action = suggestion.get('code_action', '')
                            
                            # Apply transformation based on code action
                            if 'impute_missing_mean' in code_action:
                                df_after = impute_missing_mean(df, [column])
                            elif 'impute_missing_median' in code_action:
                                df_after = impute_missing_median(df, [column])
                            elif 'impute_missing_mode' in code_action:
                                df_after = impute_missing_mode(df, [column])
                            elif 'impute_missing_constant' in code_action:
                                # Extract value from code action if possible, default to 0
                                value = 0
                                if 'value=' in code_action:
                                    try:
                                        value = float(code_action.split('value=')[1].split(')')[0])
                                    except:
                                        pass
                                df_after = impute_missing_constant(df, [column], value)
                            elif 'remove_outliers' in code_action:
                                method = 'zscore'
                                if 'method=' in code_action:
                                    method = code_action.split('method=')[1].split(')')[0].replace("'", "")
                                df_after = remove_outliers(df, [column], method=method)
                            elif 'normalize' in code_action:
                                method = 'minmax'
                                if 'method=' in code_action:
                                    method = code_action.split('method=')[1].split(')')[0].replace("'", "")
                                df_after = normalize_columns(df, [column], method=method)
                            elif 'encode_categorical' in code_action:
                                method = 'onehot'
                                if 'method=' in code_action:
                                    method = code_action.split('method=')[1].split(')')[0].replace("'", "")
                                df_after = encode_categorical(df, [column], method=method)
                            elif 'format_dates' in code_action:
                                format = None
                                if 'format=' in code_action:
                                    format = code_action.split('format=')[1].split(')')[0].replace("'", "")
                                df_after = format_dates(df, [column], format=format)
                            elif 'drop_columns' in code_action:
                                df_after = drop_columns(df, [column])
                            elif 'log_transform' in code_action:
                                df_after = log_transform(df, [column])
                            elif 'convert_numeric_to_datetime' in code_action:
                                df_after = convert_numeric_to_datetime(df, [column])
                            elif 'standardize_data' in code_action:
                                df_after = standardize_data(df, [column])
                            elif 'round_off' in code_action:
                                decimals = 2
                                if 'decimals=' in code_action:
                                    try:
                                        decimals = int(code_action.split('decimals=')[1].split(')')[0])
                                    except:
                                        pass
                                df_after = round_off(df, [column], decimals)
                            elif 'standardize_category_names' in code_action:
                                case = 'upper'
                                if 'case=' in code_action:
                                    case = code_action.split('case=')[1].split(')')[0].replace("'", "").replace('"', '')
                                df_after = standardize_category_names(df, [column], case)
                            elif "pd.to_datetime" in code_action:
                                df_after = to_datetime(df, [column])
                            elif 'create_bins' in code_action:
                                num_bins = 5
                                if 'num_bins=' in code_action:
                                    try:
                                        num_bins = int(code_action.split('num_bins=')[1].split(',')[0])
                                    except:
                                        pass
                                new_col = f"{column}_bins"
                                if 'new_column_name=' in code_action:
                                    new_col = code_action.split('new_column_name=')[1].split(')')[0].replace("'", "")
                                df_after = create_bins(df, column, num_bins, new_col)
                            # Handle special case for date component extraction
                            elif 'df[' in code_action and '.dt.' in code_action:
                                # This is likely a date extraction operation like: 
                                # df['Year'] = df['Date'].dt.year; df['Month'] = df['Date'].dt.month; df['Day'] = df['Date'].dt.day
                                
                                try:
                                    # Find the source date column
                                    parts = code_action.split('.dt.')
                                    if len(parts) > 0:
                                        source_col = parts[0].split("df['")[1].split("']")[0]
                                        
                                        # Make a copy to avoid SettingWithCopyWarning
                                        df_after = df.copy()
                                        
                                        # Split by semicolon to process each operation
                                        operations = code_action.split(';')
                                        affected_columns = []
                                        
                                        for op in operations:
                                            if '=' in op and '.dt.' in op:
                                                # Extract target column and date component
                                                target_col = op.split("df['")[1].split("']")[0]
                                                date_component = op.split('.dt.')[1].strip()
                                                
                                                # Apply transformation based on the date component
                                                if 'year' in date_component:
                                                    df_after[target_col] = pd.to_datetime(df_after[source_col]).dt.year
                                                elif 'month' in date_component:
                                                    df_after[target_col] = pd.to_datetime(df_after[source_col]).dt.month
                                                elif 'day' in date_component:
                                                    df_after[target_col] = pd.to_datetime(df_after[source_col]).dt.day
                                                elif 'quarter' in date_component:
                                                    df_after[target_col] = pd.to_datetime(df_after[source_col]).dt.quarter
                                                elif 'weekday' in date_component:
                                                    df_after[target_col] = pd.to_datetime(df_after[source_col]).dt.weekday
                                                elif 'week' in date_component:
                                                    df_after[target_col] = pd.to_datetime(df_after[source_col]).dt.isocalendar().week
                                                
                                                affected_columns.append(target_col)
                                        
                                        # If we didn't process any operations successfully
                                        if not affected_columns:
                                            st.warning(f"Couldn't identify date components to extract in: {code_action}")
                                            df_after = df.copy()  # Just use original dataframe
                                    else:
                                        st.warning(f"Couldn't identify source date column in: {code_action}")
                                        df_after = df.copy()  # Just use original dataframe
                                except Exception as e:
                                    st.warning(f"Error processing date extraction: {str(e)}")
                                    df_after = df.copy()  # Just use original dataframe
                            
                            elif 'convert_numeric_to_datetime' in code_action:
                                # Extract column name from the code
                                try:
                                    col_name = code_action.split('(')[1].split(')')[0].strip("'\"")
                                    df_after = convert_numeric_to_datetime(df, [col_name])
                                except Exception as e:
                                    st.warning(f"Error in convert_numeric_to_datetime: {str(e)}")
                                    df_after = df.copy()
                                    
                            elif 'convert_numeric_to_date' in code_action or 'convert_to_date' in code_action:
                                try:
                                    # This is likely a date conversion - let's use to_datetime
                                    df_after = to_datetime(df, [column])
                                except Exception as e:
                                    st.warning(f"Error converting to date: {str(e)}")
                                    df_after = df.copy()
                                
                            elif 'check_date_range' in code_action:
                                try:
                                    # This is a date validation - we'll convert to datetime first
                                    df_after = to_datetime(df, [column])
                                except Exception as e:
                                    st.warning(f"Error validating date range: {str(e)}")
                                    df_after = df.copy()
                                
                            elif 'find_and_remove_duplicates' in code_action or 'drop_duplicates' in code_action:
                                try:
                                    # Handle duplicate removal
                                    df_after = df.drop_duplicates(subset=[column] if column else None)
                                except Exception as e:
                                    st.warning(f"Error removing duplicates: {str(e)}")
                                    df_after = df.copy()
                                
                            elif '.str.upper()' in code_action:
                                try:
                                    # Apply upper case transformation
                                    df_after = standardize_category_names(df, [column], case='upper')
                                except Exception as e:
                                    st.warning(f"Error converting to uppercase: {str(e)}")
                                    df_after = df.copy()
                                
                            elif '.str.lower()' in code_action:
                                try:
                                    # Apply lower case transformation
                                    df_after = standardize_category_names(df, [column], case='lower')
                                except Exception as e:
                                    st.warning(f"Error converting to lowercase: {str(e)}")
                                    df_after = df.copy()
                                
                            elif 'extract_date_components' in code_action:
                                try:
                                    # Make a copy to avoid SettingWithCopyWarning
                                    df_after = df.copy()
                                    
                                    # Convert to datetime first
                                    df_after[column] = pd.to_datetime(df_after[column], errors='coerce')
                                    
                                    # Extract date components
                                    df_after[f"{column}_year"] = df_after[column].dt.year
                                    df_after[f"{column}_month"] = df_after[column].dt.month
                                    df_after[f"{column}_day"] = df_after[column].dt.day
                                except Exception as e:
                                    st.warning(f"Error extracting date components: {str(e)}")
                                    df_after = df.copy()
                            
                            else:
                                # Try to extract string transformation from code
                                if "df['" in code_action and "'] = " in code_action:
                                    try:
                                        # For custom string operations that follow pattern: df['column'] = ...
                                        target_col = code_action.split("df['")[1].split("']")[0]
                                        # Make a copy to avoid SettingWithCopyWarning
                                        df_after = df.copy()
                                        
                                        # Simple string transformations
                                        if ".str.upper()" in code_action:
                                            df_after[target_col] = df_after[target_col].str.upper()
                                        elif ".str.lower()" in code_action:
                                            df_after[target_col] = df_after[target_col].str.lower()
                                        elif ".str.strip()" in code_action:
                                            df_after[target_col] = df_after[target_col].str.strip()
                                        elif ".str.replace(" in code_action:
                                            # This is more complex, let's at least try a basic version
                                            df_after[target_col] = df_after[target_col].str.replace(" ", "")
                                        else:
                                            # If we can't determine the specific operation, just notify the user
                                            st.warning(f"Couldn't interpret custom string operation: {code_action}")
                                            df_after = df.copy()
                                    except Exception as e:
                                        st.warning(f"Error in custom string operation: {str(e)}")
                                        df_after = df.copy()
                                else:
                                    st.warning(f"Unknown transformation: {code_action}")
                                    continue
                            
                            # Display before/after comparison
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown("**Before Transformation:**")
                                if column in df_before.columns:
                                    if pd.api.types.is_numeric_dtype(df_before[column]):
                                        # For numeric columns, show distribution and stats
                                        fig_before = create_distribution_plot(df_before, column, 'histogram')
                                        if fig_before:
                                            st.plotly_chart(fig_before, use_container_width=True, key=f"before_dist_{column}_{i}")
                                        
                                        # Show statistics
                                        stats_before = df_before[column].describe()
                                        st.write(stats_before)
                                    else:
                                        # For categorical columns, show value counts
                                        fig_before = create_categorical_plot(df_before, column, 'bar')
                                        if fig_before:
                                            st.plotly_chart(fig_before, use_container_width=True, key=f"before_cat_{column}_{i}")
                                        
                                        # Show top values
                                        st.write(df_before[column].value_counts().head(5))
                            
                            with col2:
                                st.markdown("**After Transformation:**")
                                
                                # Check if column was removed or renamed
                                if 'drop_columns' in code_action:
                                    st.info(f"Column '{column}' would be removed from the dataset.")
                                elif column not in df_after.columns:
                                    # Check if we've created new columns (like one-hot encoding)
                                    new_cols = [col for col in df_after.columns if col not in df_before.columns]
                                    if new_cols:
                                        st.success(f"New columns created: {', '.join(new_cols)}")
                                        # Show one of the new columns
                                        if pd.api.types.is_numeric_dtype(df_after[new_cols[0]]):
                                            fig_after = create_distribution_plot(df_after, new_cols[0], 'histogram')
                                            if fig_after:
                                                st.plotly_chart(fig_after, use_container_width=True, key=f"after_dist_{new_cols[0]}_{i}")
                                        else:
                                            fig_after = create_categorical_plot(df_after, new_cols[0], 'bar')
                                            if fig_after:
                                                st.plotly_chart(fig_after, use_container_width=True, key=f"after_cat_{new_cols[0]}_{i}")
                                    else:
                                        st.warning("The column structure has changed significantly after transformation.")
                                else:
                                    # Show the transformed column
                                    if pd.api.types.is_numeric_dtype(df_after[column]):
                                        # For numeric columns, show distribution and stats
                                        fig_after = create_distribution_plot(df_after, column, 'histogram')
                                        if fig_after:
                                            st.plotly_chart(fig_after, use_container_width=True, key=f"after_dist_{column}_{i}")
                                        
                                        # Show statistics
                                        stats_after = df_after[column].describe()
                                        st.write(stats_after)
                                    else:
                                        # For categorical columns, show value counts
                                        fig_after = create_categorical_plot(df_after, column, 'bar')
                                        if fig_after:
                                            st.plotly_chart(fig_after, use_container_width=True, key=f"after_cat_{column}_{i}")
                                        
                                        # Show top values
                                        st.write(df_after[column].value_counts().head(5))
                            
                            # Summary of changes
                            st.markdown("**Summary of Changes:**")
                            
                            # Get column stats before and after
                            if column in df_before.columns and column in df_after.columns:
                                stats = get_column_stats_before_after(df_before, df_after, column)
                                
                                if stats and pd.api.types.is_numeric_dtype(df_before[column]):
                                    # For numeric columns
                                    st.markdown(f"- Missing values: {stats['before']['missing']} → {stats['after']['missing']}")
                                    st.markdown(f"- Mean: {stats['before']['mean']:.2f} → {stats['after']['mean']:.2f}")
                                    st.markdown(f"- Standard Deviation: {stats['before']['std']:.2f} → {stats['after']['std']:.2f}")
                                elif stats:
                                    # For categorical columns
                                    st.markdown(f"- Missing values: {stats['before']['missing']} → {stats['after']['missing']}")
                                    st.markdown(f"- Unique values: {stats['before']['unique_values']} → {stats['after']['unique_values']}")
                            elif 'drop_columns' in code_action:
                                st.markdown(f"- Column '{column}' would be removed from the dataset.")
                            else:
                                # New columns created
                                new_cols = [col for col in df_after.columns if col not in df_before.columns]
                                if new_cols:
                                    st.markdown(f"- New columns created: {', '.join(new_cols)}")
                                else:
                                    st.markdown("- The column structure has changed significantly.")
                    
                    # Apply transformation button
                    if st.button(f"Apply Transformation", key=f"apply_{column}_{i}"):
                        # Get the code action
                        code_action = suggestion.get('code_action', '')
                        
                        # Extract function and parameters
                        if 'impute_missing_mean' in code_action:
                            # Apply transformation
                            df_transformed = impute_missing_mean(df, [column])
                            # Register the transformation
                            register_transformation(
                                df,
                                name="Impute Missing Values with Mean",
                                description=f"Fill missing values in '{column}' with the mean value.",
                                function="impute_missing_mean",
                                columns=[column]
                            )
                            
                        elif 'impute_missing_median' in code_action:
                            # Apply transformation
                            df_transformed = impute_missing_median(df, [column])
                            # Register the transformation
                            register_transformation(
                                df,
                                name="Impute Missing Values with Median",
                                description=f"Fill missing values in '{column}' with the median value.",
                                function="impute_missing_median",
                                columns=[column]
                            )
                            
                        elif 'impute_missing_mode' in code_action:
                            # Apply transformation
                            df_transformed = impute_missing_mode(df, [column])
                            # Register the transformation
                            register_transformation(
                                df,
                                name="Impute Missing Values with Mode",
                                description=f"Fill missing values in '{column}' with the most frequent value.",
                                function="impute_missing_mode",
                                columns=[column]
                            )
                            
                        elif 'impute_missing_constant' in code_action:
                            # Extract value from code action if possible, default to 0
                            value = 0
                            if 'value=' in code_action:
                                try:
                                    value = float(code_action.split('value=')[1].split(')')[0])
                                except:
                                    pass
                            
                            # Apply transformation
                            df_transformed = impute_missing_constant(df, [column], value)
                            # Register the transformation
                            register_transformation(
                                df,
                                name="Impute Missing Values with Constant",
                                description=f"Fill missing values in '{column}' with the constant value: {value}.",
                                function="impute_missing_constant",
                                columns=[column],
                                params={"value": value}
                            )
                            
                        elif 'remove_outliers' in code_action:
                            method = 'zscore'
                            if 'method=' in code_action:
                                method = code_action.split('method=')[1].split(')')[0].replace("'", "")
                            
                            # Apply transformation
                            df_transformed = remove_outliers(df, [column], method=method)
                            # Register the transformation
                            register_transformation(
                                df,
                                name="Remove Outliers",
                                description=f"Remove outliers from '{column}' using {method} method.",
                                function="remove_outliers",
                                columns=[column],
                                params={"method": method}
                            )
                            
                        elif 'normalize' in code_action:
                            method = 'minmax'
                            if 'method=' in code_action:
                                method = code_action.split('method=')[1].split(')')[0].replace("'", "")
                            
                            # Apply transformation
                            df_transformed = normalize_columns(df, [column], method=method)
                            # Register the transformation
                            register_transformation(
                                df,
                                name="Normalize Column",
                                description=f"Normalize '{column}' using {method} method.",
                                function="normalize_columns",
                                columns=[column],
                                params={"method": method}
                            )
                            
                        elif 'encode_categorical' in code_action:
                            method = 'onehot'
                            if 'method=' in code_action:
                                method = code_action.split('method=')[1].split(')')[0].replace("'", "")
                            
                            # Apply transformation
                            df_transformed = encode_categorical(df, [column], method=method)
                            # Register the transformation
                            register_transformation(
                                df,
                                name="Encode Categorical Variable",
                                description=f"Encode categorical column '{column}' using {method} encoding.",
                                function="encode_categorical",
                                columns=[column],
                                params={"method": method}
                            )
                            
                        elif 'format_dates' in code_action:
                            format = None
                            if 'format=' in code_action:
                                format = code_action.split('format=')[1].split(')')[0].replace("'", "")
                            
                            # Apply transformation
                            df_transformed = format_dates(df, [column], format=format)
                            # Register the transformation
                            register_transformation(
                                df,
                                name="Format Date Column",
                                description=f"Convert '{column}' to datetime format.",
                                function="format_dates",
                                columns=[column],
                                params={"format": format}
                            )
                            
                        elif 'drop_columns' in code_action:
                            # Apply transformation
                            df_transformed = drop_columns(df, [column])
                            # Register the transformation
                            register_transformation(
                                df,
                                name="Drop Column",
                                description=f"Remove column '{column}' from the dataset.",
                                function="drop_columns",
                                columns=[column]
                            )
                            
                        elif 'log_transform' in code_action:
                            # Apply transformation
                            df_transformed = log_transform(df, [column])
                            # Register the transformation
                            register_transformation(
                                df,
                                name="Log Transform",
                                description=f"Apply logarithmic transformation to '{column}'.",
                                function="log_transform",
                                columns=[column]
                            )
                            
                        elif 'convert_numeric_to_datetime' in code_action:
                            # Extract column name from the code
                            try:
                                col_name = code_action.split('(')[1].split(')')[0].strip("'\"")
                                # Apply transformation
                                df_transformed = convert_numeric_to_datetime(df, [column])
                                # Register the transformation
                                register_transformation(
                                    df,
                                    name="Convert to DateTime",
                                    description=f"Convert numeric timestamps in '{column}' to datetime format.",
                                    function="convert_numeric_to_datetime",
                                    columns=[column]
                                )
                            except Exception as e:
                                st.error(f"Error in convert_numeric_to_datetime: {str(e)}")
                                continue
                                
                        elif 'standardize_data' in code_action:
                            # Apply transformation
                            df_transformed = standardize_data(df, [column])
                            # Register the transformation
                            register_transformation(
                                df,
                                name="Standardize Data",
                                description=f"Apply z-score standardization to '{column}'.",
                                function="standardize_data",
                                columns=[column]
                            )
                            
                        elif 'round_off' in code_action:
                            # Extract decimals parameter if present
                            decimals = 2
                            if 'decimals=' in code_action:
                                try:
                                    decimals = int(code_action.split('decimals=')[1].split(')')[0])
                                except:
                                    pass
                            
                            # Apply transformation
                            df_transformed = round_off(df, [column], decimals)
                            # Register the transformation
                            register_transformation(
                                df,
                                name="Round Values",
                                description=f"Round values in '{column}' to {decimals} decimal places.",
                                function="round_off",
                                columns=[column],
                                params={"decimals": decimals}
                            )
                            
                        elif 'standardize_category_names' in code_action:
                            # Extract case parameter if present
                            case = 'upper'
                            if 'case=' in code_action:
                                case = code_action.split('case=')[1].split(')')[0].replace("'", "").replace('"', '')
                            
                            # Apply transformation
                            df_transformed = standardize_category_names(df, [column], case)
                            # Register the transformation
                            register_transformation(
                                df,
                                name="Standardize Category Names",
                                description=f"Standardize category names in '{column}' to {case} case.",
                                function="standardize_category_names",
                                columns=[column],
                                params={"case": case}
                            )
                            
                        elif 'pd.to_datetime' in code_action:
                            # Apply transformation
                            df_transformed = to_datetime(df, [column])
                            # Register the transformation
                            register_transformation(
                                df,
                                name="Convert to DateTime",
                                description=f"Convert '{column}' to datetime format.",
                                function="to_datetime",
                                columns=[column]
                            )
                            
                        elif 'create_bins' in code_action:
                            num_bins = 5
                            if 'num_bins=' in code_action:
                                try:
                                    num_bins = int(code_action.split('num_bins=')[1].split(',')[0])
                                except:
                                    pass
                            
                            new_col = f"{column}_bins"
                            if 'new_column_name=' in code_action:
                                new_col = code_action.split('new_column_name=')[1].split(')')[0].replace("'", "")
                            
                            # Apply transformation
                            df_transformed = create_bins(df, column, num_bins, new_col)
                            # Register the transformation
                            register_transformation(
                                df,
                                name="Create Bins",
                                description=f"Create {num_bins} bins from '{column}' into new column '{new_col}'.",
                                function="create_bins",
                                columns=[column],
                                params={"num_bins": num_bins, "new_column_name": new_col}
                            )
                            
                        # Handle special case for date component extraction
                        elif 'df[' in code_action and '.dt.' in code_action:
                            try:
                                # Find the source date column
                                parts = code_action.split('.dt.')
                                if len(parts) > 0:
                                    source_col = parts[0].split("df['")[1].split("']")[0]
                                    
                                    # Make a copy to avoid SettingWithCopyWarning
                                    df_transformed = df.copy()
                                    
                                    # Split by semicolon to process each operation
                                    operations = code_action.split(';')
                                    affected_columns = []
                                    operations_desc = []
                                    
                                    for op in operations:
                                        if '=' in op and '.dt.' in op:
                                            # Extract target column and date component
                                            target_col = op.split("df['")[1].split("']")[0]
                                            date_component = op.split('.dt.')[1].strip()
                                            
                                            component_desc = None
                                            # Apply transformation based on the date component
                                            if 'year' in date_component:
                                                df_transformed[target_col] = pd.to_datetime(df_transformed[source_col]).dt.year
                                                component_desc = "year"
                                            elif 'month' in date_component:
                                                df_transformed[target_col] = pd.to_datetime(df_transformed[source_col]).dt.month
                                                component_desc = "month"
                                            elif 'day' in date_component:
                                                df_transformed[target_col] = pd.to_datetime(df_transformed[source_col]).dt.day
                                                component_desc = "day"
                                            elif 'quarter' in date_component:
                                                df_transformed[target_col] = pd.to_datetime(df_transformed[source_col]).dt.quarter
                                                component_desc = "quarter"
                                            elif 'weekday' in date_component:
                                                df_transformed[target_col] = pd.to_datetime(df_transformed[source_col]).dt.weekday
                                                component_desc = "weekday"
                                            elif 'week' in date_component:
                                                df_transformed[target_col] = pd.to_datetime(df_transformed[source_col]).dt.isocalendar().week
                                                component_desc = "week number"
                                            
                                            if component_desc:
                                                affected_columns.append(target_col)
                                                operations_desc.append(f"Extract {component_desc} to '{target_col}'")
                                    
                                    # If we successfully processed at least one operation
                                    if affected_columns:
                                        # Register the transformation
                                        register_transformation(
                                            df,
                                            name="Extract Date Components",
                                            description=f"Extract date components from '{source_col}': {', '.join(operations_desc)}",
                                            function="extract_date_components",
                                            columns=[source_col],
                                            params={"operations": operations_desc}
                                        )
                                    else:
                                        st.error(f"Could not identify date components to extract in: {code_action}")
                                        continue
                                else:
                                    st.error(f"Could not identify source date column in: {code_action}")
                                    continue
                            except Exception as e:
                                st.error(f"Error processing date extraction: {str(e)}")
                                continue
                            

                                
                        elif 'convert_numeric_to_date' in code_action or 'convert_to_date' in code_action:
                            try:
                                # This is likely a date conversion - let's use to_datetime
                                df_transformed = to_datetime(df, [column])
                                # Register the transformation
                                register_transformation(
                                    df,
                                    name="Convert to Date",
                                    description=f"Convert '{column}' to date format",
                                    function="to_datetime",
                                    columns=[column]
                                )
                            except Exception as e:
                                st.error(f"Error converting to date: {str(e)}")
                                continue
                                
                        elif 'check_date_range' in code_action:
                            try:
                                # This is a date validation - we'll convert to datetime first
                                df_transformed = to_datetime(df, [column])
                                # Register the transformation
                                register_transformation(
                                    df,
                                    name="Validate Date Range",
                                    description=f"Convert '{column}' to proper date format for validation",
                                    function="to_datetime",
                                    columns=[column]
                                )
                            except Exception as e:
                                st.error(f"Error validating date range: {str(e)}")
                                continue
                                
                        elif 'find_and_remove_duplicates' in code_action or 'drop_duplicates' in code_action:
                            try:
                                # Handle duplicate removal
                                df_transformed = df.drop_duplicates(subset=[column] if column else None)
                                # Register the transformation
                                register_transformation(
                                    df,
                                    name="Remove Duplicates",
                                    description=f"Remove duplicate rows based on '{column}'" if column else "Remove duplicate rows",
                                    function="drop_duplicates",
                                    columns=[column] if column else []
                                )
                            except Exception as e:
                                st.error(f"Error removing duplicates: {str(e)}")
                                continue
                                
                        elif '.str.upper()' in code_action:
                            try:
                                # Apply upper case transformation
                                df_transformed = standardize_category_names(df, [column], case='upper')
                                # Register the transformation
                                register_transformation(
                                    df,
                                    name="Convert to Uppercase",
                                    description=f"Convert text in '{column}' to uppercase",
                                    function="standardize_category_names",
                                    columns=[column],
                                    params={"case": "upper"}
                                )
                            except Exception as e:
                                st.error(f"Error converting to uppercase: {str(e)}")
                                continue
                                
                        elif '.str.lower()' in code_action:
                            try:
                                # Apply lower case transformation
                                df_transformed = standardize_category_names(df, [column], case='lower')
                                # Register the transformation
                                register_transformation(
                                    df,
                                    name="Convert to Lowercase",
                                    description=f"Convert text in '{column}' to lowercase",
                                    function="standardize_category_names",
                                    columns=[column],
                                    params={"case": "lower"}
                                )
                            except Exception as e:
                                st.error(f"Error converting to lowercase: {str(e)}")
                                continue
                                
                        elif 'extract_date_components' in code_action:
                            try:
                                # Make a copy to avoid SettingWithCopyWarning
                                df_transformed = df.copy()
                                
                                # Convert to datetime first
                                df_transformed[column] = pd.to_datetime(df_transformed[column], errors='coerce')
                                
                                # Extract date components
                                df_transformed[f"{column}_year"] = df_transformed[column].dt.year
                                df_transformed[f"{column}_month"] = df_transformed[column].dt.month
                                df_transformed[f"{column}_day"] = df_transformed[column].dt.day
                                
                                # Register the transformation
                                register_transformation(
                                    df,
                                    name="Extract Date Components",
                                    description=f"Extract year, month, and day from '{column}'",
                                    function="extract_date_components",
                                    columns=[column],
                                    params={"components": ["year", "month", "day"]}
                                )
                            except Exception as e:
                                st.error(f"Error extracting date components: {str(e)}")
                                continue
                                
                        else:
                            # Try to extract string transformation from code
                            if "df['" in code_action and "'] = " in code_action:
                                try:
                                    # For custom string operations that follow pattern: df['column'] = ...
                                    target_col = code_action.split("df['")[1].split("']")[0]
                                    # Make a copy to avoid SettingWithCopyWarning
                                    df_transformed = df.copy()
                                    
                                    # Simple string transformations
                                    if ".str.upper()" in code_action:
                                        df_transformed[target_col] = df_transformed[target_col].str.upper()
                                        operation = "Convert to Uppercase"
                                    elif ".str.lower()" in code_action:
                                        df_transformed[target_col] = df_transformed[target_col].str.lower()
                                        operation = "Convert to Lowercase"
                                    elif ".str.strip()" in code_action:
                                        df_transformed[target_col] = df_transformed[target_col].str.strip()
                                        operation = "Remove Whitespace"
                                    elif ".str.replace(" in code_action:
                                        # This is more complex, let's at least try a basic version
                                        df_transformed[target_col] = df_transformed[target_col].str.replace(" ", "")
                                        operation = "Replace Spaces"
                                    else:
                                        # If we can't determine the specific operation, just notify the user
                                        st.warning(f"Couldn't interpret custom string operation: {code_action}")
                                        continue
                                        
                                    # Register the transformation
                                    register_transformation(
                                        df,
                                        name=operation,
                                        description=f"Apply {operation.lower()} to '{target_col}'",
                                        function="custom_string_operation",
                                        columns=[target_col]
                                    )
                                except Exception as e:
                                    st.error(f"Error in custom string operation: {str(e)}")
                                    continue
                            else:
                                st.warning(f"Unknown transformation: {code_action}")
                                continue
                        
                        # Update the dataset in session state
                        st.session_state.dataset = df_transformed
                        
                        # Success message
                        st.success(f"Successfully applied transformation to '{column}'!")
                        
                        # Remove this suggestion from the list
                        st.session_state.ai_suggestions.remove(suggestion)
                        
                        # Rerun to refresh the UI
                        st.rerun()
    else:
        st.info("Click 'Generate AI Suggestions' to get automatic recommendations for data cleaning.")

# Tab 2: Manual Transformations
with tab2:
    st.subheader("Manual Data Transformations")
    st.markdown("""
    Apply custom transformations to your data. Select the type of transformation
    and the columns you want to transform.
    """)
    
    # Create sections for different types of transformations
    transform_type = st.selectbox(
        "Select Transformation Type",
        [
            "Missing Value Imputation",
            "Outlier Handling",
            "Normalization/Scaling",
            "Categorical Encoding",
            "Date Formatting",
            "Column Operations",
            "Variable Transformation"
        ]
    )
    
    # Missing Value Imputation
    if transform_type == "Missing Value Imputation":
        st.markdown("### Missing Value Imputation")
        
        # Show columns with missing values
        missing_vals = df.isna().sum()
        cols_with_missing = missing_vals[missing_vals > 0].index.tolist()
        
        if not cols_with_missing:
            st.info("No columns with missing values found in the dataset.")
        else:
            # Create a dataframe showing missing values
            missing_df = pd.DataFrame({
                'Column': missing_vals.index,
                'Missing Values': missing_vals.values,
                'Percentage': (missing_vals / len(df) * 100).round(2).values
            })
            missing_df = missing_df[missing_df['Missing Values'] > 0].sort_values(by='Missing Values', ascending=False)
            
            st.write(missing_df)
            
            # Let user select columns for imputation
            selected_cols = st.multiselect(
                "Select columns for imputation",
                options=cols_with_missing
            )
            
            if selected_cols:
                # Choose imputation method
                imputation_method = st.selectbox(
                    "Select imputation method",
                    [
                        "Mean (for numeric columns)",
                        "Median (for numeric columns)",
                        "Mode (most frequent value)",
                        "Constant value",
                        "Forward fill (use previous value)",
                        "Backward fill (use next value)"
                    ]
                )
                
                # For constant imputation, get the value
                constant_value = None
                if imputation_method == "Constant value":
                    constant_value = st.text_input("Enter constant value")
                
                # Apply transformation button
                if st.button("Apply Imputation"):
                    # Apply the selected imputation method
                    if imputation_method == "Mean (for numeric columns)":
                        # Filter to only include numeric columns
                        numeric_cols = [col for col in selected_cols if pd.api.types.is_numeric_dtype(df[col])]
                        
                        if not numeric_cols:
                            st.error("None of the selected columns are numeric. Please select numeric columns for mean imputation.")
                        else:
                            # Apply transformation
                            df_transformed = impute_missing_mean(df, numeric_cols)
                            
                            # Register the transformation
                            register_transformation(
                                df,
                                name="Impute Missing Values with Mean",
                                description=f"Fill missing values in {', '.join(numeric_cols)} with their respective mean values.",
                                function="impute_missing_mean",
                                columns=numeric_cols
                            )
                            
                            # Update session state
                            st.session_state.dataset = df_transformed
                            st.success(f"Successfully imputed missing values in {len(numeric_cols)} columns with mean values.")
                            st.rerun()
                    
                    elif imputation_method == "Median (for numeric columns)":
                        # Filter to only include numeric columns
                        numeric_cols = [col for col in selected_cols if pd.api.types.is_numeric_dtype(df[col])]
                        
                        if not numeric_cols:
                            st.error("None of the selected columns are numeric. Please select numeric columns for median imputation.")
                        else:
                            # Apply transformation
                            df_transformed = impute_missing_median(df, numeric_cols)
                            
                            # Register the transformation
                            register_transformation(
                                df,
                                name="Impute Missing Values with Median",
                                description=f"Fill missing values in {', '.join(numeric_cols)} with their respective median values.",
                                function="impute_missing_median",
                                columns=numeric_cols
                            )
                            
                            # Update session state
                            st.session_state.dataset = df_transformed
                            st.success(f"Successfully imputed missing values in {len(numeric_cols)} columns with median values.")
                            st.rerun()
                    
                    elif imputation_method == "Mode (most frequent value)":
                        # Apply transformation
                        df_transformed = impute_missing_mode(df, selected_cols)
                        
                        # Register the transformation
                        register_transformation(
                            df,
                            name="Impute Missing Values with Mode",
                            description=f"Fill missing values in {', '.join(selected_cols)} with their respective most frequent values.",
                            function="impute_missing_mode",
                            columns=selected_cols
                        )
                        
                        # Update session state
                        st.session_state.dataset = df_transformed
                        st.success(f"Successfully imputed missing values in {len(selected_cols)} columns with mode values.")
                        st.rerun()
                    
                    elif imputation_method == "Constant value":
                        if not constant_value:
                            st.error("Please enter a constant value for imputation.")
                        else:
                            try:
                                # Try to convert to numeric if possible
                                constant = float(constant_value)
                            except:
                                # Otherwise use as string
                                constant = constant_value
                            
                            # Apply transformation
                            df_transformed = impute_missing_constant(df, selected_cols, constant)
                            
                            # Register the transformation
                            register_transformation(
                                df,
                                name="Impute Missing Values with Constant",
                                description=f"Fill missing values in {', '.join(selected_cols)} with the constant value: {constant}.",
                                function="impute_missing_constant",
                                columns=selected_cols,
                                params={"value": constant}
                            )
                            
                            # Update session state
                            st.session_state.dataset = df_transformed
                            st.success(f"Successfully imputed missing values in {len(selected_cols)} columns with the constant value: {constant}.")
                            st.rerun()
                    
                    elif imputation_method == "Forward fill (use previous value)":
                        # Apply transformation (forward fill)
                        df_transformed = df.copy()
                        df_transformed[selected_cols] = df_transformed[selected_cols].ffill()
                        
                        # Register the transformation
                        register_transformation(
                            df,
                            name="Forward Fill Missing Values",
                            description=f"Fill missing values in {', '.join(selected_cols)} with the previous value in each column.",
                            function="impute_missing_ffill",
                            columns=selected_cols
                        )
                        
                        # Update session state
                        st.session_state.dataset = df_transformed
                        st.success(f"Successfully forward-filled missing values in {len(selected_cols)} columns.")
                        st.rerun()
                    
                    elif imputation_method == "Backward fill (use next value)":
                        # Apply transformation (backward fill)
                        df_transformed = df.copy()
                        df_transformed[selected_cols] = df_transformed[selected_cols].bfill()
                        
                        # Register the transformation
                        register_transformation(
                            df,
                            name="Backward Fill Missing Values",
                            description=f"Fill missing values in {', '.join(selected_cols)} with the next value in each column.",
                            function="impute_missing_bfill",
                            columns=selected_cols
                        )
                        
                        # Update session state
                        st.session_state.dataset = df_transformed
                        st.success(f"Successfully backward-filled missing values in {len(selected_cols)} columns.")
                        st.rerun()
    
    # Outlier Handling
    elif transform_type == "Outlier Handling":
        st.markdown("### Outlier Detection & Handling")
        
        # Select only numeric columns
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        if not numeric_cols:
            st.info("No numeric columns found in the dataset for outlier detection.")
        else:
            # Let user select columns for outlier handling
            selected_cols = st.multiselect(
                "Select numeric columns for outlier handling",
                options=numeric_cols
            )
            
            if selected_cols:
                # Choose outlier detection method
                outlier_method = st.selectbox(
                    "Select outlier detection method",
                    ["Z-score (standard deviations from mean)", "IQR (interquartile range)"]
                )
                
                # Choose handling strategy
                handling_strategy = st.selectbox(
                    "Select outlier handling strategy",
                    ["Remove outliers", "Cap outliers (winsorization)", "Replace with NaN"]
                )
                
                # For z-score, get threshold
                z_threshold = 3.0
                if outlier_method == "Z-score (standard deviations from mean)":
                    z_threshold = st.slider(
                        "Z-score threshold (higher = fewer outliers detected)", 
                        min_value=1.0, 
                        max_value=5.0, 
                        value=3.0,
                        step=0.1
                    )
                
                # For IQR, get multiple
                iqr_multiple = 1.5
                if outlier_method == "IQR (interquartile range)":
                    iqr_multiple = st.slider(
                        "IQR multiple (higher = fewer outliers detected)", 
                        min_value=1.0, 
                        max_value=3.0, 
                        value=1.5,
                        step=0.1
                    )
                
                # Analyze button
                if st.button("Analyze Outliers"):
                    # Create plots to show outliers for each selected column
                    for column in selected_cols:
                        st.markdown(f"#### Outliers in '{column}'")
                        
                        # Create box plot
                        fig = px.box(
                            df, 
                            y=column,
                            title=f"Box Plot with Outliers for {column}",
                            points="outliers",
                            color_discrete_sequence=['#4F8BF9']
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Calculate outliers
                        if outlier_method == "Z-score (standard deviations from mean)":
                            z_scores = np.abs((df[column] - df[column].mean()) / df[column].std())
                            outliers = df[z_scores > z_threshold]
                            
                            # Show stats
                            outlier_count = len(outliers)
                            outlier_pct = outlier_count / len(df) * 100
                            
                            st.markdown(f"**Z-score > {z_threshold}:** {outlier_count} outliers ({outlier_pct:.2f}% of data)")
                            
                            if outlier_count > 0:
                                st.write(f"Outlier values (sample of up to 10):")
                                st.write(outliers[column].sample(min(10, outlier_count)))
                        
                        else:  # IQR method
                            Q1 = df[column].quantile(0.25)
                            Q3 = df[column].quantile(0.75)
                            IQR = Q3 - Q1
                            lower_bound = Q1 - iqr_multiple * IQR
                            upper_bound = Q3 + iqr_multiple * IQR
                            
                            outliers = df[(df[column] < lower_bound) | (df[column] > upper_bound)]
                            
                            # Show stats
                            outlier_count = len(outliers)
                            outlier_pct = outlier_count / len(df) * 100
                            
                            st.markdown(f"**IQR method (multiple={iqr_multiple}):** {outlier_count} outliers ({outlier_pct:.2f}% of data)")
                            st.markdown(f"- Lower bound: {lower_bound:.2f}")
                            st.markdown(f"- Upper bound: {upper_bound:.2f}")
                            
                            if outlier_count > 0:
                                st.write(f"Outlier values (sample of up to 10):")
                                st.write(outliers[column].sample(min(10, outlier_count)))
                
                # Apply transformation button
                if st.button("Apply Outlier Handling"):
                    if handling_strategy == "Remove outliers":
                        # Apply transformation
                        method = 'zscore' if outlier_method == "Z-score (standard deviations from mean)" else 'iqr'
                        df_transformed = remove_outliers(df, selected_cols, method=method)
                        
                        # Create params based on method
                        params = {"method": method}
                        if method == 'zscore':
                            params["threshold"] = z_threshold
                        else:
                            params["iqr_multiple"] = iqr_multiple
                        
                        # Register the transformation
                        register_transformation(
                            df,
                            name="Remove Outliers",
                            description=f"Remove outliers from {', '.join(selected_cols)} using {method} method.",
                            function="remove_outliers",
                            columns=selected_cols,
                            params=params
                        )
                        
                        # Update session state
                        st.session_state.dataset = df_transformed
                        
                        # Calculate rows removed
                        rows_removed = len(df) - len(df_transformed)
                        
                        st.success(f"Successfully removed {rows_removed} outlier rows from the dataset.")
                        st.rerun()
                    
                    elif handling_strategy == "Cap outliers (winsorization)":
                        # Apply transformation (cap outliers at bounds)
                        df_transformed = df.copy()
                        
                        for column in selected_cols:
                            if outlier_method == "Z-score (standard deviations from mean)":
                                z_scores = np.abs((df[column] - df[column].mean()) / df[column].std())
                                mean = df[column].mean()
                                std = df[column].std()
                                
                                # Cap outliers
                                df_transformed.loc[z_scores > z_threshold, column] = np.where(
                                    df.loc[z_scores > z_threshold, column] > mean,
                                    mean + z_threshold * std,
                                    mean - z_threshold * std
                                )
                            else:  # IQR method
                                Q1 = df[column].quantile(0.25)
                                Q3 = df[column].quantile(0.75)
                                IQR = Q3 - Q1
                                lower_bound = Q1 - iqr_multiple * IQR
                                upper_bound = Q3 + iqr_multiple * IQR
                                
                                # Cap outliers
                                df_transformed[column] = df_transformed[column].clip(lower=lower_bound, upper=upper_bound)
                        
                        # Create params based on method
                        method = 'zscore' if outlier_method == "Z-score (standard deviations from mean)" else 'iqr'
                        params = {"method": method, "strategy": "cap"}
                        if method == 'zscore':
                            params["threshold"] = z_threshold
                        else:
                            params["iqr_multiple"] = iqr_multiple
                        
                        # Register the transformation
                        register_transformation(
                            df,
                            name="Cap Outliers",
                            description=f"Cap outliers in {', '.join(selected_cols)} using {method} method.",
                            function="cap_outliers",
                            columns=selected_cols,
                            params=params
                        )
                        
                        # Update session state
                        st.session_state.dataset = df_transformed
                        st.success(f"Successfully capped outliers in {len(selected_cols)} columns.")
                        st.rerun()
                    
                    elif handling_strategy == "Replace with NaN":
                        # Apply transformation (replace outliers with NaN)
                        df_transformed = df.copy()
                        
                        for column in selected_cols:
                            if outlier_method == "Z-score (standard deviations from mean)":
                                z_scores = np.abs((df[column] - df[column].mean()) / df[column].std())
                                df_transformed.loc[z_scores > z_threshold, column] = np.nan
                            else:  # IQR method
                                Q1 = df[column].quantile(0.25)
                                Q3 = df[column].quantile(0.75)
                                IQR = Q3 - Q1
                                lower_bound = Q1 - iqr_multiple * IQR
                                upper_bound = Q3 + iqr_multiple * IQR
                                
                                # Replace outliers with NaN
                                df_transformed.loc[(df_transformed[column] < lower_bound) | 
                                                   (df_transformed[column] > upper_bound), column] = np.nan
                        
                        # Create params based on method
                        method = 'zscore' if outlier_method == "Z-score (standard deviations from mean)" else 'iqr'
                        params = {"method": method, "strategy": "replace_nan"}
                        if method == 'zscore':
                            params["threshold"] = z_threshold
                        else:
                            params["iqr_multiple"] = iqr_multiple
                        
                        # Register the transformation
                        register_transformation(
                            df,
                            name="Replace Outliers with NaN",
                            description=f"Replace outliers in {', '.join(selected_cols)} with NaN using {method} method.",
                            function="replace_outliers_nan",
                            columns=selected_cols,
                            params=params
                        )
                        
                        # Update session state
                        st.session_state.dataset = df_transformed
                        st.success(f"Successfully replaced outliers with NaN in {len(selected_cols)} columns.")
                        st.rerun()
    
    # Normalization/Scaling
    elif transform_type == "Normalization/Scaling":
        st.markdown("### Normalization & Scaling")
        
        # Select only numeric columns
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        if not numeric_cols:
            st.info("No numeric columns found in the dataset for normalization.")
        else:
            # Let user select columns for normalization
            selected_cols = st.multiselect(
                "Select numeric columns to normalize",
                options=numeric_cols
            )
            
            if selected_cols:
                # Choose normalization method
                norm_method = st.selectbox(
                    "Select normalization method",
                    [
                        "Min-Max Scaling (0 to 1)",
                        "Z-score Standardization (mean=0, std=1)"
                    ]
                )
                
                # Preview transformation
                if st.button("Preview Normalization"):
                    # Apply normalization to a temporary dataframe
                    method = 'minmax' if norm_method == "Min-Max Scaling (0 to 1)" else 'zscore'
                    df_preview = normalize_columns(df, selected_cols, method=method)
                    
                    # Show before/after comparison for the first few selected columns
                    for i, column in enumerate(selected_cols[:3]):  # Limit to first 3 columns for clarity
                        st.markdown(f"#### Normalization Preview for '{column}'")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("**Before Normalization:**")
                            # Show distribution
                            fig_before = create_distribution_plot(df, column, 'histogram')
                            if fig_before:
                                st.plotly_chart(fig_before, use_container_width=True)
                            
                            # Show statistics
                            stats_before = df[column].describe()
                            st.write(stats_before)
                        
                        with col2:
                            st.markdown("**After Normalization:**")
                            # Show distribution
                            fig_after = create_distribution_plot(df_preview, column, 'histogram')
                            if fig_after:
                                st.plotly_chart(fig_after, use_container_width=True)
                            
                            # Show statistics
                            stats_after = df_preview[column].describe()
                            st.write(stats_after)
                
                # Apply transformation button
                if st.button("Apply Normalization"):
                    method = 'minmax' if norm_method == "Min-Max Scaling (0 to 1)" else 'zscore'
                    
                    # Apply transformation
                    df_transformed = normalize_columns(df, selected_cols, method=method)
                    
                    # Register the transformation
                    register_transformation(
                        df,
                        name=f"{norm_method} Normalization",
                        description=f"Apply {norm_method} to {', '.join(selected_cols)}.",
                        function="normalize_columns",
                        columns=selected_cols,
                        params={"method": method}
                    )
                    
                    # Update session state
                    st.session_state.dataset = df_transformed
                    st.success(f"Successfully normalized {len(selected_cols)} columns using {norm_method}.")
                    st.rerun()
    
    # Categorical Encoding
    elif transform_type == "Categorical Encoding":
        st.markdown("### Categorical Variable Encoding")
        
        # Select categorical columns (excluding datetime)
        cat_cols = df.select_dtypes(exclude=['number', 'datetime']).columns.tolist()
        
        if not cat_cols:
            st.info("No categorical columns found in the dataset for encoding.")
        else:
            # Let user select columns for encoding
            selected_cols = st.multiselect(
                "Select categorical columns to encode",
                options=cat_cols
            )
            
            if selected_cols:
                # Show value counts for selected columns
                for column in selected_cols:
                    st.markdown(f"**Value counts for '{column}':**")
                    value_counts = df[column].value_counts().head(10)
                    st.write(value_counts)
                    
                    if len(df[column].unique()) > 10:
                        st.info(f"Showing top 10 out of {len(df[column].unique())} unique values.")
                
                # Choose encoding method
                encoding_method = st.selectbox(
                    "Select encoding method",
                    [
                        "One-Hot Encoding (dummy variables)",
                        "Label Encoding (integer labels)"
                    ]
                )
                
                # Apply transformation button
                if st.button("Apply Encoding"):
                    method = 'onehot' if encoding_method == "One-Hot Encoding (dummy variables)" else 'label'
                    
                    # Apply transformation
                    df_transformed = encode_categorical(df, selected_cols, method=method)
                    
                    # Register the transformation
                    register_transformation(
                        df,
                        name=f"{encoding_method}",
                        description=f"Apply {encoding_method} to {', '.join(selected_cols)}.",
                        function="encode_categorical",
                        columns=selected_cols,
                        params={"method": method}
                    )
                    
                    # Update session state
                    st.session_state.dataset = df_transformed
                    
                    # For one-hot encoding, calculate how many new columns were created
                    if method == 'onehot':
                        new_cols = [col for col in df_transformed.columns if col not in df.columns]
                        st.success(f"Successfully encoded {len(selected_cols)} columns, creating {len(new_cols)} new columns.")
                    else:
                        st.success(f"Successfully encoded {len(selected_cols)} columns using Label Encoding.")
                    
                    st.rerun()
    
    # Date Formatting
    elif transform_type == "Date Formatting":
        st.markdown("### Date & Time Formatting")
        
        # Try to identify potential date columns (both actual datetime and string columns that might be dates)
        datetime_cols = df.select_dtypes(include=['datetime']).columns.tolist()
        
        # Also check for columns that might be dates but not detected
        potential_date_cols = []
        for col in df.columns:
            if col not in datetime_cols:
                # Check if column has string data
                if df[col].dtype == 'object':
                    # Take a sample and try to convert to datetime
                    sample = df[col].dropna().head(5)
                    try:
                        pd.to_datetime(sample, errors='raise')
                        potential_date_cols.append(col)
                    except:
                        pass
        
        # Combine both lists
        all_date_cols = datetime_cols + potential_date_cols
        
        if not all_date_cols:
            st.info("No datetime columns or potential date columns found in the dataset.")
        else:
            # Let user select columns for date formatting
            selected_cols = st.multiselect(
                "Select columns to format as dates",
                options=all_date_cols
            )
            
            if selected_cols:
                # For each selected column, show a sample
                for column in selected_cols:
                    st.markdown(f"**Sample values from '{column}':**")
                    sample_values = df[column].dropna().head(3).tolist()
                    st.write(sample_values)
                
                # Offer datetime format
                date_format = st.text_input(
                    "Enter date format (optional, leave blank for auto-detection)",
                    placeholder="%Y-%m-%d"
                )
                
                date_format = date_format if date_format else None
                
                # Apply transformation button
                if st.button("Format as DateTime"):
                    # Apply transformation
                    df_transformed = format_dates(df, selected_cols, format=date_format)
                    
                    # Register the transformation
                    register_transformation(
                        df,
                        name="Format as DateTime",
                        description=f"Convert {', '.join(selected_cols)} to datetime format.",
                        function="format_dates",
                        columns=selected_cols,
                        params={"format": date_format}
                    )
                    
                    # Update session state
                    st.session_state.dataset = df_transformed
                    st.success(f"Successfully formatted {len(selected_cols)} columns as datetime.")
                    st.rerun()
    
    # Column Operations
    elif transform_type == "Column Operations":
        st.markdown("### Column Operations")
        
        # Create subtabs for different column operations
        col_op = st.selectbox(
            "Select Column Operation",
            [
                "Drop Columns",
                "Rename Columns",
                "Create New Column",
                "Combine Columns"
            ]
        )
        
        # Drop Columns
        if col_op == "Drop Columns":
            st.markdown("#### Drop Columns")
            
            # Let user select columns to drop
            cols_to_drop = st.multiselect(
                "Select columns to drop",
                options=df.columns.tolist()
            )
            
            if cols_to_drop:
                # Apply transformation button
                if st.button("Drop Selected Columns"):
                    # Apply transformation
                    df_transformed = drop_columns(df, cols_to_drop)
                    
                    # Register the transformation
                    register_transformation(
                        df,
                        name="Drop Columns",
                        description=f"Remove columns: {', '.join(cols_to_drop)}.",
                        function="drop_columns",
                        columns=cols_to_drop
                    )
                    
                    # Update session state
                    st.session_state.dataset = df_transformed
                    st.success(f"Successfully dropped {len(cols_to_drop)} columns.")
                    st.rerun()
        
        # Rename Columns
        elif col_op == "Rename Columns":
            st.markdown("#### Rename Columns")
            
            # Create a dataframe for renaming
            rename_data = []
            for col in df.columns:
                rename_data.append({"Original": col, "New Name": col})
            
            rename_df = pd.DataFrame(rename_data)
            
            # Let user edit the new names
            edited_df = st.data_editor(
                rename_df,
                hide_index=True,
                use_container_width=True,
                column_config={
                    "Original": st.column_config.TextColumn(
                        "Original Column Name",
                        disabled=True
                    ),
                    "New Name": st.column_config.TextColumn(
                        "New Column Name",
                        help="Edit to rename"
                    )
                }
            )
            
            # Apply transformation button
            if st.button("Apply Column Renaming"):
                # Create mapping of old to new names
                rename_mapping = {}
                for _, row in edited_df.iterrows():
                    if row["Original"] != row["New Name"]:
                        rename_mapping[row["Original"]] = row["New Name"]
                
                if not rename_mapping:
                    st.info("No columns were renamed. Please edit the New Name column to rename columns.")
                else:
                    # Apply transformation
                    df_transformed = rename_columns(df, rename_mapping)
                    
                    # Register the transformation
                    register_transformation(
                        df,
                        name="Rename Columns",
                        description=f"Rename columns: {', '.join([f'{old} → {new}' for old, new in rename_mapping.items()])}.",
                        function="rename_columns",
                        columns=list(rename_mapping.keys()),
                        params={"mapping": rename_mapping}
                    )
                    
                    # Update session state
                    st.session_state.dataset = df_transformed
                    st.success(f"Successfully renamed {len(rename_mapping)} columns.")
                    st.rerun()
        
        # Create New Column
        elif col_op == "Create New Column":
            st.markdown("#### Create New Column")
            
            # Options for new column creation
            creation_method = st.selectbox(
                "Creation method",
                [
                    "Mathematical expression",
                    "Text combination",
                    "Binning numeric column"
                ]
            )
            
            if creation_method == "Mathematical expression":
                numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                
                if not numeric_cols:
                    st.info("No numeric columns found for mathematical expressions.")
                else:
                    new_col_name = st.text_input("New column name", value="new_column")
                    
                    # Let user select expression type
                    expr_type = st.selectbox(
                        "Expression type",
                        [
                            "Simple arithmetic (A + B, A - B, etc.)",
                            "Custom formula"
                        ]
                    )
                    
                    if expr_type == "Simple arithmetic (A + B, A - B, etc.)":
                        col1 = st.selectbox("First column", numeric_cols)
                        
                        operation = st.selectbox(
                            "Operation",
                            ["+", "-", "*", "/"]
                        )
                        
                        # Second operand can be column or constant
                        operand_type = st.selectbox(
                            "Second operand type",
                            ["Column", "Constant"]
                        )
                        
                        if operand_type == "Column":
                            col2 = st.selectbox("Second column", numeric_cols)
                            
                            # Apply button
                            if st.button("Create New Column"):
                                # Create new column based on operation
                                df_transformed = df.copy()
                                
                                if operation == "+":
                                    df_transformed[new_col_name] = df[col1] + df[col2]
                                elif operation == "-":
                                    df_transformed[new_col_name] = df[col1] - df[col2]
                                elif operation == "*":
                                    df_transformed[new_col_name] = df[col1] * df[col2]
                                elif operation == "/":
                                    # Handle division by zero
                                    df_transformed[new_col_name] = df[col1] / df[col2].replace(0, np.nan)
                                
                                # Register the transformation
                                register_transformation(
                                    df,
                                    name="Create Column from Arithmetic",
                                    description=f"Create new column '{new_col_name}' using {col1} {operation} {col2}.",
                                    function="create_column_arithmetic",
                                    columns=[col1, col2],
                                    params={"new_column": new_col_name, "operation": operation}
                                )
                                
                                # Update session state
                                st.session_state.dataset = df_transformed
                                st.success(f"Successfully created new column '{new_col_name}'.")
                                st.rerun()
                        else:  # Constant
                            constant_value = st.number_input("Constant value", value=0.0)
                            
                            # Apply button
                            if st.button("Create New Column"):
                                # Create new column based on operation
                                df_transformed = df.copy()
                                
                                if operation == "+":
                                    df_transformed[new_col_name] = df[col1] + constant_value
                                elif operation == "-":
                                    df_transformed[new_col_name] = df[col1] - constant_value
                                elif operation == "*":
                                    df_transformed[new_col_name] = df[col1] * constant_value
                                elif operation == "/":
                                    # Handle division by zero
                                    if constant_value == 0:
                                        st.error("Cannot divide by zero.")
                                    else:
                                        df_transformed[new_col_name] = df[col1] / constant_value
                                
                                # Register the transformation
                                register_transformation(
                                    df,
                                    name="Create Column from Arithmetic",
                                    description=f"Create new column '{new_col_name}' using {col1} {operation} {constant_value}.",
                                    function="create_column_arithmetic",
                                    columns=[col1],
                                    params={"new_column": new_col_name, "operation": operation, "constant": constant_value}
                                )
                                
                                # Update session state
                                st.session_state.dataset = df_transformed
                                st.success(f"Successfully created new column '{new_col_name}'.")
                                st.rerun()
                    
                    else:  # Custom formula
                        st.markdown(
                            "Enter a custom formula using column names and operations. "
                            "Example: `col1 * 2 + col2 / 3`"
                        )
                        
                        # Show available columns
                        st.markdown("**Available columns:**")
                        st.write(", ".join(numeric_cols))
                        
                        # Formula input
                        formula = st.text_area("Formula", placeholder="column1 * column2 + 5")
                        
                        # Apply button
                        if st.button("Create New Column"):
                            if not formula:
                                st.error("Please enter a formula.")
                            else:
                                try:
                                    # Replace column names with df['column_name']
                                    modified_formula = formula
                                    for col in numeric_cols:
                                        modified_formula = modified_formula.replace(col, f"df['{col}']")
                                    
                                    # Create new column using eval (with security precautions)
                                    df_transformed = df.copy()
                                    df_transformed[new_col_name] = eval(modified_formula)
                                    
                                    # Register the transformation
                                    register_transformation(
                                        df,
                                        name="Create Column from Custom Formula",
                                        description=f"Create new column '{new_col_name}' using formula: {formula}.",
                                        function="create_column_formula",
                                        columns=numeric_cols,
                                        params={"new_column": new_col_name, "formula": formula}
                                    )
                                    
                                    # Update session state
                                    st.session_state.dataset = df_transformed
                                    st.success(f"Successfully created new column '{new_col_name}'.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error in formula: {str(e)}")
            
            elif creation_method == "Text combination":
                # Get string columns
                text_cols = df.select_dtypes(include=['object']).columns.tolist()
                
                if not text_cols:
                    st.info("No text columns found for combination.")
                else:
                    new_col_name = st.text_input("New column name", value="combined_text")
                    
                    # Let user select columns to combine
                    columns_to_combine = st.multiselect(
                        "Select columns to combine",
                        options=text_cols
                    )
                    
                    # Separator
                    separator = st.text_input("Separator", value=" ")
                    
                    # Apply button
                    if st.button("Create Combined Column"):
                        if not columns_to_combine:
                            st.error("Please select at least one column to combine.")
                        else:
                            # Create combined column
                            df_transformed = df.copy()
                            
                            # Start with first column
                            df_transformed[new_col_name] = df[columns_to_combine[0]].astype(str)
                            
                            # Add remaining columns with separator
                            for col in columns_to_combine[1:]:
                                df_transformed[new_col_name] = df_transformed[new_col_name] + separator + df[col].astype(str)
                            
                            # Register the transformation
                            register_transformation(
                                df,
                                name="Create Combined Text Column",
                                description=f"Create new column '{new_col_name}' by combining {', '.join(columns_to_combine)}.",
                                function="create_combined_text",
                                columns=columns_to_combine,
                                params={"new_column": new_col_name, "separator": separator}
                            )
                            
                            # Update session state
                            st.session_state.dataset = df_transformed
                            st.success(f"Successfully created new column '{new_col_name}'.")
                            st.rerun()
            
            elif creation_method == "Binning numeric column":
                # Get numeric columns
                numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                
                if not numeric_cols:
                    st.info("No numeric columns found for binning.")
                else:
                    column_to_bin = st.selectbox("Select column to bin", numeric_cols)
                    
                    # New column name
                    new_col_name = st.text_input("New column name", value=f"{column_to_bin}_bins")
                    
                    # Number of bins
                    num_bins = st.slider("Number of bins", min_value=2, max_value=20, value=5)
                    
                    # Preview button
                    if st.button("Preview Bins"):
                        # Calculate bin edges
                        bin_edges = np.linspace(
                            df[column_to_bin].min(),
                            df[column_to_bin].max(),
                            num_bins + 1
                        )
                        
                        st.markdown("**Bin edges:**")
                        for i in range(len(bin_edges) - 1):
                            st.write(f"Bin {i+1}: {bin_edges[i]:.2f} to {bin_edges[i+1]:.2f}")
                        
                        # Create temporary binned column
                        df_temp = df.copy()
                        df_temp[new_col_name] = pd.cut(
                            df_temp[column_to_bin],
                            bins=num_bins
                        )
                        
                        # Show distribution
                        st.markdown("**Distribution of bins:**")
                        bin_counts = df_temp[new_col_name].value_counts().sort_index()
                        
                        # Create bar chart
                        fig = px.bar(
                            x=bin_counts.index.astype(str),
                            y=bin_counts.values,
                            labels={'x': 'Bins', 'y': 'Count'},
                            title=f"Distribution of {new_col_name}"
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Apply button
                    if st.button("Create Bins"):
                        # Apply transformation
                        df_transformed = create_bins(df, column_to_bin, num_bins, new_col_name)
                        
                        # Register the transformation
                        register_transformation(
                            df,
                            name="Create Bins",
                            description=f"Create {num_bins} bins from '{column_to_bin}' into new column '{new_col_name}'.",
                            function="create_bins",
                            columns=[column_to_bin],
                            params={"num_bins": num_bins, "new_column_name": new_col_name}
                        )
                        
                        # Update session state
                        st.session_state.dataset = df_transformed
                        st.success(f"Successfully created new binned column '{new_col_name}'.")
                        st.rerun()
        
        # Combine Columns
        elif col_op == "Combine Columns":
            st.markdown("#### Combine Columns")
            
            # Let user select columns to combine
            columns_to_combine = st.multiselect(
                "Select columns to combine",
                options=df.columns.tolist()
            )
            
            if columns_to_combine:
                # New column name
                new_col_name = st.text_input("New column name", value="combined_column")
                
                # Combine method
                combine_method = st.selectbox(
                    "Combine method",
                    ["Concatenate text", "Sum numeric values", "Average numeric values"]
                )
                
                # Apply button
                if st.button("Combine Columns"):
                    df_transformed = df.copy()
                    
                    if combine_method == "Concatenate text":
                        # Separator
                        separator = st.text_input("Separator", value=" ")
                        
                        # Concatenate columns as text
                        df_transformed[new_col_name] = df[columns_to_combine[0]].astype(str)
                        for col in columns_to_combine[1:]:
                            df_transformed[new_col_name] = df_transformed[new_col_name] + separator + df[col].astype(str)
                        
                        # Register the transformation
                        register_transformation(
                            df,
                            name="Concatenate Columns",
                            description=f"Create '{new_col_name}' by concatenating {', '.join(columns_to_combine)}.",
                            function="concatenate_columns",
                            columns=columns_to_combine,
                            params={"new_column": new_col_name, "separator": separator}
                        )
                    
                    elif combine_method == "Sum numeric values":
                        # Check if all selected columns are numeric
                        numeric_cols = [col for col in columns_to_combine if pd.api.types.is_numeric_dtype(df[col])]
                        
                        if len(numeric_cols) != len(columns_to_combine):
                            st.error("All selected columns must be numeric for sum operation.")
                            st.stop()
                        
                        # Sum the columns
                        df_transformed[new_col_name] = df[columns_to_combine].sum(axis=1)
                        
                        # Register the transformation
                        register_transformation(
                            df,
                            name="Sum Columns",
                            description=f"Create '{new_col_name}' by summing {', '.join(columns_to_combine)}.",
                            function="sum_columns",
                            columns=columns_to_combine,
                            params={"new_column": new_col_name}
                        )
                    
                    elif combine_method == "Average numeric values":
                        # Check if all selected columns are numeric
                        numeric_cols = [col for col in columns_to_combine if pd.api.types.is_numeric_dtype(df[col])]
                        
                        if len(numeric_cols) != len(columns_to_combine):
                            st.error("All selected columns must be numeric for average operation.")
                            st.stop()
                        
                        # Average the columns
                        df_transformed[new_col_name] = df[columns_to_combine].mean(axis=1)
                        
                        # Register the transformation
                        register_transformation(
                            df,
                            name="Average Columns",
                            description=f"Create '{new_col_name}' by averaging {', '.join(columns_to_combine)}.",
                            function="average_columns",
                            columns=columns_to_combine,
                            params={"new_column": new_col_name}
                        )
                    
                    # Update session state
                    st.session_state.dataset = df_transformed
                    st.success(f"Successfully created new column '{new_col_name}'.")
                    st.rerun()
    
    # Variable Transformation
    elif transform_type == "Variable Transformation":
        st.markdown("### Variable Transformations")
        
        # Get numeric columns
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        if not numeric_cols:
            st.info("No numeric columns found for transformation.")
        else:
            # Transform method
            transform_method = st.selectbox(
                "Select transformation method",
                [
                    "Log transformation",
                    "Square root transformation",
                    "Box-Cox transformation"
                ]
            )
            
            # Let user select columns to transform
            selected_cols = st.multiselect(
                "Select columns to transform",
                options=numeric_cols
            )
            
            if selected_cols:
                # Check data suitability for transformation
                if transform_method == "Log transformation":
                    # Check for non-positive values
                    has_zero_or_negative = False
                    for col in selected_cols:
                        if (df[col] <= 0).any():
                            has_zero_or_negative = True
                            st.warning(f"Column '{col}' contains zeros or negative values which are problematic for log transformation.")
                    
                    if has_zero_or_negative:
                        st.info("Log transformation options for non-positive values:")
                        handling_method = st.selectbox(
                            "How to handle zeros and negative values",
                            ["Add constant to make all values positive", "Skip negative/zero values (convert to NaN)"]
                        )
                
                # Preview transformation
                if st.button("Preview Transformation"):
                    # Apply transformation to a temporary dataframe
                    if transform_method == "Log transformation":
                        df_preview = df.copy()
                        
                        for col in selected_cols:
                            # Handle zeros and negative values if present
                            if (df[col] <= 0).any():
                                if handling_method == "Add constant to make all values positive":
                                    min_val = df[col].min()
                                    constant = abs(min_val) + 1 if min_val <= 0 else 0
                                    df_preview[f"{col}_log"] = np.log(df[col] + constant)
                                else:
                                    df_preview[f"{col}_log"] = np.log(df[col].clip(lower=0.000001))
                            else:
                                df_preview[f"{col}_log"] = np.log(df[col])
                    
                    elif transform_method == "Square root transformation":
                        df_preview = df.copy()
                        
                        for col in selected_cols:
                            # Handle negative values if present
                            if (df[col] < 0).any():
                                st.warning(f"Column '{col}' contains negative values which are not suitable for square root transformation.")
                                df_preview[f"{col}_sqrt"] = np.sqrt(df[col].clip(lower=0))
                            else:
                                df_preview[f"{col}_sqrt"] = np.sqrt(df[col])
                    
                    elif transform_method == "Box-Cox transformation":
                        # Box-Cox requires all positive values
                        from scipy import stats
                        
                        df_preview = df.copy()
                        
                        for col in selected_cols:
                            # Check if all values are positive
                            if (df[col] <= 0).any():
                                min_val = df[col].min()
                                constant = abs(min_val) + 1
                                st.info(f"Adding {constant} to all values in '{col}' to make them positive for Box-Cox.")
                                
                                # Apply Box-Cox with constant
                                transformed_data, lambda_value = stats.boxcox(df[col] + constant)
                                df_preview[f"{col}_boxcox"] = transformed_data
                                st.info(f"Optimal lambda for '{col}': {lambda_value:.4f}")
                            else:
                                # Apply Box-Cox
                                transformed_data, lambda_value = stats.boxcox(df[col])
                                df_preview[f"{col}_boxcox"] = transformed_data
                                st.info(f"Optimal lambda for '{col}': {lambda_value:.4f}")
                    
                    # Show before/after comparison for the first selected column
                    if selected_cols:
                        col = selected_cols[0]
                        transformed_col = f"{col}_log" if transform_method == "Log transformation" else \
                                        f"{col}_sqrt" if transform_method == "Square root transformation" else \
                                        f"{col}_boxcox"
                        
                        st.markdown(f"#### Transformation Preview for '{col}'")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("**Before Transformation:**")
                            # Check for skewness
                            skew = df[col].skew()
                            st.write(f"Skewness: {skew:.4f}")
                            
                            # Show distribution
                            fig_before = create_distribution_plot(df, col, 'histogram')
                            if fig_before:
                                st.plotly_chart(fig_before, use_container_width=True)
                        
                        with col2:
                            st.markdown("**After Transformation:**")
                            # Check skewness of transformed data
                            skew_after = df_preview[transformed_col].skew()
                            st.write(f"Skewness: {skew_after:.4f}")
                            
                            # Show distribution
                            fig_after = create_distribution_plot(df_preview, transformed_col, 'histogram')
                            if fig_after:
                                st.plotly_chart(fig_after, use_container_width=True)
                
                # Apply transformation button
                if st.button("Apply Transformation"):
                    if transform_method == "Log transformation":
                        # Apply log transformation
                        df_transformed = log_transform(df, selected_cols)
                        
                        # Register the transformation
                        register_transformation(
                            df,
                            name="Log Transformation",
                            description=f"Apply logarithmic transformation to {', '.join(selected_cols)}.",
                            function="log_transform",
                            columns=selected_cols
                        )
                    
                    elif transform_method == "Square root transformation":
                        # Apply square root transformation
                        df_transformed = df.copy()
                        
                        for col in selected_cols:
                            # Handle negative values if present
                            if (df[col] < 0).any():
                                df_transformed[f"{col}_sqrt"] = np.sqrt(df[col].clip(lower=0))
                            else:
                                df_transformed[f"{col}_sqrt"] = np.sqrt(df[col])
                        
                        # Register the transformation
                        register_transformation(
                            df,
                            name="Square Root Transformation",
                            description=f"Apply square root transformation to {', '.join(selected_cols)}.",
                            function="sqrt_transform",
                            columns=selected_cols
                        )
                    
                    elif transform_method == "Box-Cox transformation":
                        # Apply Box-Cox transformation
                        from scipy import stats
                        
                        df_transformed = df.copy()
                        lambda_values = {}
                        
                        for col in selected_cols:
                            # Check if all values are positive
                            if (df[col] <= 0).any():
                                min_val = df[col].min()
                                constant = abs(min_val) + 1
                                
                                # Apply Box-Cox with constant
                                transformed_data, lambda_value = stats.boxcox(df[col] + constant)
                                df_transformed[f"{col}_boxcox"] = transformed_data
                                lambda_values[col] = lambda_value
                            else:
                                # Apply Box-Cox
                                transformed_data, lambda_value = stats.boxcox(df[col])
                                df_transformed[f"{col}_boxcox"] = transformed_data
                                lambda_values[col] = lambda_value
                        
                        # Register the transformation
                        register_transformation(
                            df,
                            name="Box-Cox Transformation",
                            description=f"Apply Box-Cox transformation to {', '.join(selected_cols)}.",
                            function="boxcox_transform",
                            columns=selected_cols,
                            params={"lambda_values": lambda_values}
                        )
                    
                    # Update session state
                    st.session_state.dataset = df_transformed
                    st.success(f"Successfully applied {transform_method} to {len(selected_cols)} columns.")
                    st.rerun()

# Tab 3: Transformation History
with tab3:
    st.subheader("Transformation History & Management")
    
    # Display the transformation history
    if st.session_state.transformation_history:
        st.markdown("### Applied Transformations")
        
        # Create a dataframe from transformation history
        history_data = []
        for i, history in enumerate(st.session_state.transformation_history):
            history_data.append({
                "ID": i+1,
                "Timestamp": history.get('timestamp', ''),
                "Action": history.get('action', ''),
                "Details": history.get('details', '')
            })
        
        history_df = pd.DataFrame(history_data)
        
        # Display the history
        st.dataframe(history_df, use_container_width=True)
        
        # Undo last transformation
        if st.button("Undo Last Transformation"):
            if st.session_state.transformations:
                # Remove the last transformation
                st.session_state.transformations.pop()
                st.session_state.transformation_history.pop()
                
                # Re-apply all transformations from the original data
                original_df = pd.read_csv(st.session_state.file_name) if st.session_state.file_name.endswith('.csv') else pd.read_excel(st.session_state.file_name)
                
                if st.session_state.transformations:
                    # Apply all remaining transformations
                    df_transformed = apply_transformations(original_df, st.session_state.transformations)
                    st.session_state.dataset = df_transformed
                else:
                    # If no transformations left, revert to original
                    st.session_state.dataset = original_df
                
                st.success("Successfully undid the last transformation.")
                st.rerun()
    else:
        st.info("No transformations have been applied yet.")
    
    # Display the current data
    st.subheader("Current Dataset Preview")
    st.dataframe(df.head(10), use_container_width=True)
    
    # Dataset statistics
    st.markdown("### Current Dataset Statistics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Rows", df.shape[0])
    
    with col2:
        st.metric("Columns", df.shape[1])
    
    with col3:
        missing_vals = df.isna().sum().sum()
        missing_pct = round(missing_vals / (df.shape[0] * df.shape[1]) * 100, 2)
        st.metric("Missing Values", f"{missing_vals} ({missing_pct}%)")

# Navigation buttons
st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    if st.button("← Back to EDA Dashboard", key="back_to_eda"):
        st.switch_page("pages/03_EDA_Dashboard.py")

with col2:
    if st.button("Continue to Insights →", key="continue_to_insights"):
        st.switch_page("pages/05_Insights_Dashboard.py")

# Add a sidebar with tips
with st.sidebar:
    st.header("Data Transformation Guide")
    
    st.markdown("""
    ### Why Transform Your Data?
    
    - **Better Analysis**: Properly transformed data leads to more accurate insights
    
    - **Improved Visualizations**: Many charts require specific data formats
    
    - **Machine Learning Ready**: ML algorithms generally work better with clean, transformed data
    
    ### Tips for Transformation
    
    1. **Start with missing values** - They can affect other transformations
    
    2. **Handle outliers early** - Extreme values can distort analyses
    
    3. **Use AI suggestions** - Let our AI help identify potential transformations
    
    4. **Check the effect** - Always preview transformations before applying them
    
    5. **Track your changes** - Use the history tab to manage transformations
    """)
    
    st.markdown("---")
    
    st.markdown("""
    **Human-in-the-loop** means you're always in control - 
    our AI makes suggestions, but you decide which transformations to apply.
    """)
