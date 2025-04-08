import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import json
import re
from utils.database import save_transformation

def register_transformation(df, name, description, function, columns, params=None):
    """Register a transformation in the session state and database."""
    if 'transformations' not in st.session_state:
        st.session_state.transformations = []
    
    if 'transformation_history' not in st.session_state:
        st.session_state.transformation_history = []
    
    # Determine transformation type category for visualization
    function_to_type = {
        'impute_missing_mean': 'missing_value_handling',
        'impute_missing_median': 'missing_value_handling',
        'impute_missing_mode': 'missing_value_handling',
        'impute_missing_constant': 'missing_value_handling',
        'remove_outliers': 'outlier_removal',
        'normalize_columns': 'normalization',
        'standardize_data': 'normalization',
        'encode_categorical': 'encoding',
        'format_dates': 'date_formatting',
        'drop_columns': 'column_removal',
        'rename_columns': 'column_renaming',
        'create_bins': 'binning',
        'log_transform': 'transformation',
        'sqrt_transform': 'transformation',
        'boxcox_transform': 'transformation',
        'convert_numeric_to_datetime': 'type_conversion',
        'round_off': 'rounding',
        'standardize_category_names': 'standardization'
    }
    
    transformation_type = function_to_type.get(function, 'other')
    
    # Add to transformations list
    transformation = {
        'name': name,
        'description': description,
        'function': function,
        'type': transformation_type,
        'columns': columns,
        'params': params,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    st.session_state.transformations.append(transformation)
    
    # Add to history with additional metadata for visualization
    history_entry = {
        'action': f"Applied {name} to {', '.join(columns)}",
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'details': description,
        'type': transformation_type,
        'columns': columns,
        'function': function
    }
    
    st.session_state.transformation_history.append(history_entry)
    
    # Save to database if dataset_id is available
    if 'dataset_id' in st.session_state and st.session_state.dataset_id:
        transformation_details = {
            'function': function,
            'params': params,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        save_transformation(
            dataset_id=st.session_state.dataset_id,
            name=name,
            description=description,
            transformation_details=transformation_details,
            affected_columns=columns
        )
    
    return transformation

def apply_transformations(df, transformations=None):
    """Apply a list of transformations to the DataFrame."""
    if df is None or df.empty:
        return df
    
    if transformations is None:
        transformations = st.session_state.transformations if 'transformations' in st.session_state else []
    
    df_transformed = df.copy()
    
    for transform in transformations:
        function_name = transform['function']
        columns = transform['columns']
        params = transform['params'] if 'params' in transform else {}
        
        try:
            # Apply the transformation function and handle different return patterns
            result = None
            
            if function_name == 'impute_missing_mean':
                result = impute_missing_mean(df_transformed, columns)
            elif function_name == 'impute_missing_median':
                result = impute_missing_median(df_transformed, columns)
            elif function_name == 'impute_missing_mode':
                result = impute_missing_mode(df_transformed, columns)
            elif function_name == 'impute_missing_constant':
                result = impute_missing_constant(df_transformed, columns, params.get('value'))
            elif function_name == 'remove_outliers':
                result = remove_outliers(df_transformed, columns, method=params.get('method', 'zscore'))
            elif function_name == 'normalize':
                result = normalize_columns(df_transformed, columns, method=params.get('method', 'minmax'))
            elif function_name == 'standardize_data':
                result = standardize_data(df_transformed, columns, 
                                       method=params.get('method', 'zscore'),
                                       custom_mapping=params.get('custom_mapping'))
            elif function_name == 'encode_categorical':
                result = encode_categorical(df_transformed, columns, method=params.get('method', 'onehot'))
            elif function_name == 'format_dates':
                result = format_dates(df_transformed, columns[0], output_format=params.get('output_format'))
            elif function_name == 'to_datetime':
                result = to_datetime(df_transformed, columns[0], format=params.get('format'))
            elif function_name == 'drop_columns':
                result = drop_columns(df_transformed, columns)
            elif function_name == 'rename_columns':
                result = rename_columns(df_transformed, params.get('mapping', {}))
            elif function_name == 'create_bins':
                result = create_bins(
                    df_transformed, 
                    columns[0], 
                    num_bins=params.get('num_bins', 5), 
                    new_column_name=params.get('new_column_name'),
                    method=params.get('method', 'equal_width'),
                    bin_edges=params.get('bin_edges'),
                    labels=params.get('labels')
                )
            elif function_name == 'log_transform':
                result = log_transform(
                    df_transformed, 
                    columns,
                    base=params.get('base'),
                    handle_zeros=params.get('handle_zeros', True)
                )
            elif function_name == 'convert_numeric_to_datetime':
                result = convert_numeric_to_datetime(
                    df_transformed, 
                    columns[0],
                    component=params.get('component')
                )
            elif function_name == 'round_off':
                result = round_off(df_transformed, columns, decimals=params.get('decimals', 2))
            elif function_name == 'standardize_category_names':
                result = standardize_category_names(
                    df_transformed, 
                    columns, 
                    method=params.get('method', 'upper'),
                    custom_mapping=params.get('custom_mapping')
                )
                
            # Handle different return types (some functions now return (df, stats) tuple)
            if result is not None:
                if isinstance(result, tuple) and len(result) > 0:
                    df_transformed = result[0]  # Extract the DataFrame from the tuple
                else:
                    df_transformed = result
                    
        except Exception as e:
            st.error(f"Error applying transformation {function_name}: {str(e)}")
            # Continue with other transformations
            continue
    
    return df_transformed

def impute_missing_mean(df, columns):
    """Impute missing values with the mean of each column."""
    df_out = df.copy()
    
    for column in columns:
        if column in df.columns and pd.api.types.is_numeric_dtype(df[column]):
            mean_value = df[column].mean()
            df_out[column] = df[column].fillna(mean_value)
    
    return df_out

def impute_missing_median(df, columns):
    """Impute missing values with the median of each column."""
    df_out = df.copy()
    
    for column in columns:
        if column in df.columns and pd.api.types.is_numeric_dtype(df[column]):
            median_value = df[column].median()
            df_out[column] = df[column].fillna(median_value)
    
    return df_out

def impute_missing_mode(df, columns):
    """Impute missing values with the mode of each column."""
    df_out = df.copy()
    
    for column in columns:
        if column in df.columns:
            # Get the mode (most frequent value)
            mode_value = df[column].mode().iloc[0] if not df[column].mode().empty else None
            if mode_value is not None:
                df_out[column] = df[column].fillna(mode_value)
    
    return df_out

def impute_missing_constant(df, columns, value):
    """Impute missing values with a constant value."""
    df_out = df.copy()
    
    for column in columns:
        if column in df.columns:
            df_out[column] = df[column].fillna(value)
    
    return df_out

def remove_outliers(df, columns, method='zscore', threshold=3):
    """Remove outliers from specified columns."""
    df_out = df.copy()
    
    for column in columns:
        if column in df.columns and pd.api.types.is_numeric_dtype(df[column]):
            if method == 'zscore':
                # Z-score method
                z_scores = np.abs((df[column] - df[column].mean()) / df[column].std())
                df_out = df_out[z_scores < threshold]
            elif method == 'iqr':
                # IQR method
                Q1 = df[column].quantile(0.25)
                Q3 = df[column].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                df_out = df_out[(df[column] >= lower_bound) & (df[column] <= upper_bound)]
    
    return df_out

def normalize_columns(df, columns, method='minmax'):
    """Normalize specified columns."""
    df_out = df.copy()
    
    for column in columns:
        if column in df.columns and pd.api.types.is_numeric_dtype(df[column]):
            if method == 'minmax':
                # Min-max normalization
                min_val = df[column].min()
                max_val = df[column].max()
                if max_val > min_val:  # Avoid division by zero
                    df_out[column] = (df[column] - min_val) / (max_val - min_val)
            elif method == 'zscore':
                # Z-score normalization
                mean = df[column].mean()
                std = df[column].std()
                if std > 0:  # Avoid division by zero
                    df_out[column] = (df[column] - mean) / std
    
    return df_out

def encode_categorical(df, columns, method='onehot'):
    """Encode categorical columns."""
    df_out = df.copy()
    
    for column in columns:
        if column in df.columns:
            if method == 'onehot':
                # One-hot encoding
                dummies = pd.get_dummies(df[column], prefix=column)
                df_out = pd.concat([df_out.drop(column, axis=1), dummies], axis=1)
            elif method == 'label':
                # Label encoding
                categories = df[column].astype('category').cat.categories
                df_out[column] = df[column].astype('category').cat.codes
                # Store category mapping for reference
                df_out[f'{column}_mapping'] = pd.Series(
                    {i: category for i, category in enumerate(categories)}
                )
    
    return df_out

def format_dates(df, column, output_format=None):
    """Format datetime columns.
    
    Args:
        df: DataFrame
        column: Column name to format
        output_format: Output date format string
    
    Returns:
        Tuple of (transformed DataFrame, stats)
    """
    df_out = df.copy()
    stats = {"success": 0, "failed": 0}
    
    if column in df.columns:
        # Try to convert to datetime first if not already datetime
        try:
            if not pd.api.types.is_datetime64_any_dtype(df[column]):
                df_out[column] = pd.to_datetime(df[column])
            
            # Then format to the desired output
            if output_format:
                df_out[column] = df_out[column].dt.strftime(output_format)
                
            # Count successful conversions
            stats["success"] = df_out[column].notna().sum()
            stats["failed"] = df_out[column].isna().sum()
        except Exception as e:
            stats["error"] = str(e)
    else:
        stats["error"] = f"Column {column} not found in dataframe"
    
    return df_out, stats

def drop_columns(df, columns):
    """Drop specified columns from the DataFrame.
    
    Args:
        df: DataFrame
        columns: List of column names to drop
    
    Returns:
        Tuple of (transformed DataFrame, stats)
    """
    df_out = df.copy()
    
    # Get columns that actually exist in the dataframe
    valid_columns = [col for col in columns if col in df.columns]
    
    # Drop columns
    df_out = df_out.drop(columns=valid_columns, errors='ignore')
    
    stats = {
        "columns_before": len(df.columns),
        "columns_after": len(df_out.columns),
        "columns_dropped": len(valid_columns),
        "dropped_columns": valid_columns
    }
    
    return df_out, stats

def rename_columns(df, mapping):
    """Rename columns according to the provided mapping.
    
    Args:
        df: DataFrame
        mapping: Dictionary of current_name -> new_name mappings
    
    Returns:
        Tuple of (transformed DataFrame, stats)
    """
    df_out = df.copy()
    
    # Apply the renaming
    df_out = df_out.rename(columns=mapping)
    
    stats = {
        "columns_renamed": len(mapping),
        "mapping": mapping
    }
    
    return df_out, stats

def create_bins(df, column, num_bins=5, new_column_name=None, method="equal_width", bin_edges=None, labels=None):
    """
    Create bins from a numeric column.
    
    Parameters:
    - df: DataFrame containing the data
    - column: Column to bin
    - num_bins: Number of bins to create (default=5)
    - new_column_name: Name for the new binned column (default=None, will use column_bins)
    - method: Binning method ('equal_width', 'equal_frequency', or 'custom')
    - bin_edges: Custom bin edges if method='custom'
    - labels: Custom labels for the bins
    
    Returns:
    - df_out: DataFrame with binned column added
    - stats: Dictionary with binning statistics
    """
    stats = {"success": 0, "failed": 0, "error": None}
    
    if column not in df.columns:
        stats["error"] = f"Column {column} not found in dataframe"
        return df, stats
    
    if not pd.api.types.is_numeric_dtype(df[column]):
        stats["error"] = f"Column {column} is not numeric"
        return df, stats
    
    df_out = df.copy()
    
    # Determine bin name if not provided
    if new_column_name is None:
        new_column_name = f"{column}_bins"
    
    try:
        # Create bins based on the method
        if method == "equal_width":
            # Equal width binning (default pd.cut behavior)
            df_out[new_column_name] = pd.cut(df[column], bins=num_bins, labels=labels)
        
        elif method == "equal_frequency":
            # Equal frequency binning (quantile-based)
            df_out[new_column_name] = pd.qcut(df[column], q=num_bins, labels=labels, duplicates='drop')
        
        elif method == "custom" and bin_edges is not None:
            # Custom binning with user-defined edges
            df_out[new_column_name] = pd.cut(df[column], bins=bin_edges, labels=labels)
        
        else:
            # Default to equal width binning
            df_out[new_column_name] = pd.cut(df[column], bins=num_bins, labels=labels)
        
        # Count successful binning
        stats["success"] = df_out[new_column_name].notna().sum()
        stats["failed"] = df_out[new_column_name].isna().sum()
        
    except Exception as e:
        stats["error"] = str(e)
    
    return df_out, stats

def log_transform(df, columns, base=None, handle_zeros=True):
    """Apply log transformation to specified columns.
    
    Args:
        df: DataFrame containing the data
        columns: List of column names to transform
        base: The logarithm base to use (None for natural log, 10 for log10, 2 for log2)
        handle_zeros: Whether to handle zeros and negative values by adding a constant
        
    Returns:
        Tuple of (transformed DataFrame, stats)
    """
    df_out = df.copy()
    stats = {"success": 0, "failed": 0, "error": None}
    
    for column in columns:
        if column in df.columns and pd.api.types.is_numeric_dtype(df[column]):
            try:
                # Handle zeros and negative values if requested
                constant = 0
                if handle_zeros:
                    min_val = df[column].min()
                    if min_val <= 0:  # Handle zeros and negative values
                        constant = abs(min_val) + 1
                
                # Apply log transformation with the specified base
                if base == 10:
                    df_out[f"{column}_log"] = np.log10(df[column] + constant)
                elif base == 2:
                    df_out[f"{column}_log"] = np.log2(df[column] + constant)
                else:  # Default to natural log
                    df_out[f"{column}_log"] = np.log(df[column] + constant)
                
                # Count successful transformations
                stats["success"] += df_out[f"{column}_log"].notna().sum()
                stats["failed"] += df_out[f"{column}_log"].isna().sum()
                
            except Exception as e:
                stats["error"] = f"Error transforming column {column}: {str(e)}"
        else:
            stats["error"] = f"Column {column} not found or not numeric"
    
    return df_out, stats

def convert_numeric_to_datetime(df, column, component=None):
    """Convert numeric values (e.g., Unix timestamps) to datetime or extract components.
    
    Args:
        df: DataFrame
        column: Column name to convert
        component: Optional datetime component to extract (year, month, etc.)
    
    Returns:
        Tuple of (transformed DataFrame, stats)
    """
    df_out = df.copy()
    stats = {"success": 0, "failed": 0}
    
    if column in df.columns:
        try:
            # Try to detect the format
            first_valid = df[column].iloc[df[column].first_valid_index()] if not df[column].isna().all() else None
            
            if first_valid is not None:
                # First convert to datetime if needed
                if not pd.api.types.is_datetime64_any_dtype(df[column]):
                    if pd.api.types.is_numeric_dtype(df[column]):
                        # If it's numeric, assume it's a Unix timestamp
                        # Try both seconds and milliseconds
                        if df[column].max() > 2e10:  # likely milliseconds
                            df_out[column] = pd.to_datetime(df[column], unit='ms')
                        else:  # likely seconds
                            df_out[column] = pd.to_datetime(df[column], unit='s')
                    else:
                        # Otherwise just try standard conversion
                        df_out[column] = pd.to_datetime(df[column])
                
                # If a component is specified, extract it
                if component:
                    new_col = f"{column}_{component}"
                    
                    if component == 'year':
                        df_out[new_col] = df_out[column].dt.year
                    elif component == 'month':
                        df_out[new_col] = df_out[column].dt.month
                    elif component == 'day':
                        df_out[new_col] = df_out[column].dt.day
                    elif component == 'hour':
                        df_out[new_col] = df_out[column].dt.hour
                    elif component == 'minute':
                        df_out[new_col] = df_out[column].dt.minute
                    elif component == 'second':
                        df_out[new_col] = df_out[column].dt.second
                    elif component == 'day_of_week':
                        df_out[new_col] = df_out[column].dt.dayofweek
                    elif component == 'week_of_year':
                        df_out[new_col] = df_out[column].dt.isocalendar().week
                    elif component == 'quarter':
                        df_out[new_col] = df_out[column].dt.quarter
                
                # Count successful conversions
                stats["success"] = df_out[column].notna().sum()
                stats["failed"] = df_out[column].isna().sum()
        except Exception as e:
            stats["error"] = str(e)
    else:
        stats["error"] = f"Column {column} not found in dataframe"
    
    return df_out, stats

def standardize_data(df, columns, method="zscore", custom_mapping=None):
    """Standardize data using various methods.
    
    Args:
        df: DataFrame
        columns: List of columns to standardize
        method: Standardization method ('zscore', 'minmax', 'robust', 'quantile', 'custom')
        custom_mapping: Custom mapping for the 'custom' method
        
    Returns:
        Tuple of (transformed DataFrame, stats)
    """
    df_out = df.copy()
    stats = {"success": 0, "failed": 0, "error": None}
    
    for column in columns:
        if column in df.columns and pd.api.types.is_numeric_dtype(df[column]):
            try:
                if method == "zscore":
                    # Z-score normalization
                    mean = df[column].mean()
                    std = df[column].std()
                    if std > 0:  # Avoid division by zero
                        df_out[column] = (df[column] - mean) / std
                    else:
                        stats["error"] = f"Cannot standardize column {column}: Standard deviation is zero"
                
                elif method == "minmax":
                    # Min-max scaling to [0, 1]
                    min_val = df[column].min()
                    max_val = df[column].max()
                    if max_val > min_val:  # Avoid division by zero
                        df_out[column] = (df[column] - min_val) / (max_val - min_val)
                    else:
                        stats["error"] = f"Cannot standardize column {column}: All values are identical"
                
                elif method == "robust":
                    # Robust scaling using median and IQR
                    median = df[column].median()
                    q1 = df[column].quantile(0.25)
                    q3 = df[column].quantile(0.75)
                    iqr = q3 - q1
                    if iqr > 0:  # Avoid division by zero
                        df_out[column] = (df[column] - median) / iqr
                    else:
                        stats["error"] = f"Cannot standardize column {column}: IQR is zero"
                
                elif method == "quantile":
                    # Quantile transformation (uniform distribution)
                    from sklearn.preprocessing import QuantileTransformer
                    qt = QuantileTransformer(output_distribution='uniform')
                    df_out[column] = qt.fit_transform(df[[column]])
                
                elif method == "custom" and custom_mapping is not None:
                    # Custom mapping
                    df_out[column] = df[column].map(custom_mapping)
                
                # Count successful transformations
                stats["success"] += df_out[column].notna().sum()
                stats["failed"] += df_out[column].isna().sum()
                
            except Exception as e:
                stats["error"] = f"Error standardizing column {column}: {str(e)}"
        else:
            stats["error"] = f"Column {column} not found or not numeric"
    
    return df_out, stats

def round_off(df, columns, decimals=2):
    """Round numeric values to specified number of decimal places.
    
    Args:
        df: DataFrame containing the data
        columns: List of column names to round
        decimals: Number of decimal places to round to (default=2)
        
    Returns:
        Tuple of (transformed DataFrame, stats)
    """
    df_out = df.copy()
    stats = {"success": 0, "failed": 0, "error": None}
    
    if not isinstance(columns, list):
        columns = [columns]  # Convert single column to list
    
    for column in columns:
        if column in df.columns and pd.api.types.is_numeric_dtype(df[column]):
            try:
                df_out[column] = df[column].round(decimals)
                
                # Count successful transformations
                stats["success"] += df_out[column].notna().sum()
                stats["failed"] += df_out[column].isna().sum()
            except Exception as e:
                stats["error"] = f"Error rounding column {column}: {str(e)}"
        else:
            stats["error"] = f"Column {column} not found or not numeric"
    
    return df_out, stats

def standardize_category_names(df, columns, method='upper', custom_mapping=None):
    """Standardize category names by converting to specified case, removing extra spaces, or applying custom mappings.
    
    Args:
        df: DataFrame
        columns: List of columns to standardize
        method: Standardization method ('upper', 'lower', 'title', 'strip', 'custom')
        custom_mapping: Custom mapping dictionary for the 'custom' method
        
    Returns:
        Tuple of (transformed DataFrame, stats)
    """
    df_out = df.copy()
    stats = {"success": 0, "failed": 0, "error": None}
    
    if not isinstance(columns, list):
        columns = [columns]  # Convert single column to list
    
    for column in columns:
        if column in df.columns:
            try:
                # Handle string columns
                if pd.api.types.is_string_dtype(df[column]) or df[column].dtype == 'object':
                    # Apply the appropriate transformation
                    if method.lower() == 'upper':
                        df_out[column] = df[column].str.upper()
                        df_out[column] = df[column].str.strip()
                        df_out[column] = df[column].str.replace(r'\s+', ' ', regex=True)
                    
                    elif method.lower() == 'lower':
                        df_out[column] = df[column].str.lower()
                        df_out[column] = df[column].str.strip()
                        df_out[column] = df[column].str.replace(r'\s+', ' ', regex=True)
                    
                    elif method.lower() == 'title':
                        df_out[column] = df[column].str.title()
                        df_out[column] = df[column].str.strip()
                        df_out[column] = df[column].str.replace(r'\s+', ' ', regex=True)
                    
                    elif method.lower() == 'strip':
                        # Just remove extra spaces
                        df_out[column] = df[column].str.strip()
                        df_out[column] = df[column].str.replace(r'\s+', ' ', regex=True)
                    
                    elif method.lower() == 'custom' and custom_mapping is not None:
                        # Apply custom mapping
                        df_out[column] = df[column].map(custom_mapping)
                    
                    # Count successful transformations
                    stats["success"] += df_out[column].notna().sum()
                    stats["failed"] += df_out[column].isna().sum()
                    
                else:
                    stats["error"] = f"Column {column} is not a string/object column"
                    
            except Exception as e:
                stats["error"] = f"Error standardizing column {column}: {str(e)}"
        else:
            stats["error"] = f"Column {column} not found in dataframe"
    
    return df_out, stats

def to_datetime(df, column, format=None):
    """Convert a column to datetime format.
    
    Args:
        df: DataFrame
        column: Column name to convert
        format: Optional datetime format string
    
    Returns:
        Tuple of (transformed DataFrame, stats)
    """
    df_out = df.copy()
    stats = {"success": 0, "failed": 0}
    
    if column in df.columns:
        try:
            if format:
                df_out[column] = pd.to_datetime(df[column], format=format)
            else:
                df_out[column] = pd.to_datetime(df[column])
                
            # Count successful conversions
            stats["success"] = df_out[column].notna().sum()
            stats["failed"] = df_out[column].isna().sum()
        except Exception as e:
            stats["error"] = str(e)
    else:
        stats["error"] = f"Column {column} not found in dataframe"
    
    return df_out, stats

def get_column_stats_before_after(original_df, transformed_df, column):
    """Get statistics for a column before and after transformation."""
    if column not in original_df.columns or column not in transformed_df.columns:
        return None
    
    stats = {}
    
    if pd.api.types.is_numeric_dtype(original_df[column]):
        # Numeric column stats
        stats['before'] = {
            'mean': float(original_df[column].mean()),
            'median': float(original_df[column].median()),
            'std': float(original_df[column].std()),
            'min': float(original_df[column].min()),
            'max': float(original_df[column].max()),
            'missing': int(original_df[column].isna().sum()),
            'missing_percent': float(original_df[column].isna().mean() * 100)
        }
        
        stats['after'] = {
            'mean': float(transformed_df[column].mean()),
            'median': float(transformed_df[column].median()),
            'std': float(transformed_df[column].std()),
            'min': float(transformed_df[column].min()),
            'max': float(transformed_df[column].max()),
            'missing': int(transformed_df[column].isna().sum()),
            'missing_percent': float(transformed_df[column].isna().mean() * 100)
        }
    else:
        # Categorical column stats
        stats['before'] = {
            'unique_values': int(original_df[column].nunique()),
            'missing': int(original_df[column].isna().sum()),
            'missing_percent': float(original_df[column].isna().mean() * 100)
        }
        
        stats['after'] = {
            'unique_values': int(transformed_df[column].nunique()),
            'missing': int(transformed_df[column].isna().sum()),
            'missing_percent': float(transformed_df[column].isna().mean() * 100)
        }
    
    return stats
