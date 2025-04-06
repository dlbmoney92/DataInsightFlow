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
    
    # Add to transformations list
    transformation = {
        'name': name,
        'description': description,
        'function': function,
        'columns': columns,
        'params': params,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    st.session_state.transformations.append(transformation)
    
    # Add to history
    history_entry = {
        'action': f"Applied {name} to {', '.join(columns)}",
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'details': description
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
        
        # Apply the transformation function
        if function_name == 'impute_missing_mean':
            df_transformed = impute_missing_mean(df_transformed, columns)
        elif function_name == 'impute_missing_median':
            df_transformed = impute_missing_median(df_transformed, columns)
        elif function_name == 'impute_missing_mode':
            df_transformed = impute_missing_mode(df_transformed, columns)
        elif function_name == 'impute_missing_constant':
            df_transformed = impute_missing_constant(df_transformed, columns, params.get('value'))
        elif function_name == 'remove_outliers':
            df_transformed = remove_outliers(df_transformed, columns, method=params.get('method', 'zscore'))
        elif function_name == 'normalize':
            df_transformed = normalize_columns(df_transformed, columns, method=params.get('method', 'minmax'))
        elif function_name == 'encode_categorical':
            df_transformed = encode_categorical(df_transformed, columns, method=params.get('method', 'onehot'))
        elif function_name == 'format_dates':
            df_transformed = format_dates(df_transformed, columns, format=params.get('format'))
        elif function_name == 'drop_columns':
            df_transformed = drop_columns(df_transformed, columns)
        elif function_name == 'rename_columns':
            df_transformed = rename_columns(df_transformed, params.get('mapping', {}))
        elif function_name == 'create_bins':
            df_transformed = create_bins(df_transformed, columns[0], params.get('num_bins', 5), params.get('new_column_name'))
        elif function_name == 'log_transform':
            df_transformed = log_transform(df_transformed, columns)
        elif function_name == 'convert_numeric_to_datetime':
            df_transformed = convert_numeric_to_datetime(df_transformed, columns)
    
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

def format_dates(df, columns, format=None):
    """Format datetime columns."""
    df_out = df.copy()
    
    for column in columns:
        if column in df.columns:
            # Try to convert to datetime
            try:
                if format:
                    df_out[column] = pd.to_datetime(df[column], format=format)
                else:
                    df_out[column] = pd.to_datetime(df[column])
            except:
                pass
    
    return df_out

def drop_columns(df, columns):
    """Drop specified columns from the DataFrame."""
    return df.drop(columns=columns, errors='ignore')

def rename_columns(df, mapping):
    """Rename columns according to the provided mapping."""
    return df.rename(columns=mapping)

def create_bins(df, column, num_bins=5, new_column_name=None):
    """Create bins from a numeric column."""
    if column not in df.columns or not pd.api.types.is_numeric_dtype(df[column]):
        return df
    
    df_out = df.copy()
    
    # Determine bin name if not provided
    if new_column_name is None:
        new_column_name = f"{column}_bins"
    
    # Create bins
    df_out[new_column_name] = pd.cut(df[column], bins=num_bins)
    
    return df_out

def log_transform(df, columns):
    """Apply log transformation to specified columns."""
    df_out = df.copy()
    
    for column in columns:
        if column in df.columns and pd.api.types.is_numeric_dtype(df[column]):
            # Handle zeros and negative values by adding a small constant
            min_val = df[column].min()
            constant = 1 if min_val >= 0 else abs(min_val) + 1
            
            # Apply log transformation
            df_out[f"{column}_log"] = np.log(df[column] + constant)
    
    return df_out

def convert_numeric_to_datetime(df, columns):
    """Convert numeric values (e.g., Unix timestamps) to datetime."""
    df_out = df.copy()
    
    for column in columns:
        if column in df.columns:
            try:
                # Try to detect the format
                first_valid = df[column].iloc[df[column].first_valid_index()] if not df[column].isna().all() else None
                
                if first_valid is not None:
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
            except Exception as e:
                # If conversion fails, keep the original
                pass
    
    return df_out

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
