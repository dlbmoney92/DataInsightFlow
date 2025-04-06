import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats
import json
from datetime import datetime
import pandas_profiling
from pandas_profiling import ProfileReport
import io
import base64

def generate_summary_stats(df):
    """Generate summary statistics for the dataset."""
    if df is None or df.empty:
        return None
    
    # Basic info
    n_rows, n_cols = df.shape
    
    # Missing values
    na_counts = df.isna().sum()
    na_percent = (na_counts / n_rows * 100).round(2)
    
    # Column types
    dtypes = df.dtypes.astype(str)
    
    # Numeric column stats
    numeric_cols = df.select_dtypes(include=['number']).columns
    numeric_stats = pd.DataFrame(index=numeric_cols)
    
    if len(numeric_cols) > 0:
        numeric_stats['mean'] = df[numeric_cols].mean()
        numeric_stats['median'] = df[numeric_cols].median()
        numeric_stats['std'] = df[numeric_cols].std()
        numeric_stats['min'] = df[numeric_cols].min()
        numeric_stats['max'] = df[numeric_cols].max()
    
    # Categorical column stats
    cat_cols = df.select_dtypes(exclude=['number', 'datetime']).columns
    cat_stats = {}
    
    for col in cat_cols:
        if df[col].nunique() < 50:  # Only for columns with reasonable number of categories
            value_counts = df[col].value_counts().head(10).to_dict()
            cat_stats[col] = value_counts
    
    # Datetime column stats
    date_cols = df.select_dtypes(include=['datetime']).columns
    date_stats = {}
    
    for col in date_cols:
        date_stats[col] = {
            'min': df[col].min().strftime('%Y-%m-%d %H:%M:%S') if not pd.isna(df[col].min()) else None,
            'max': df[col].max().strftime('%Y-%m-%d %H:%M:%S') if not pd.isna(df[col].max()) else None
        }
    
    # Compile summary
    summary = {
        'basic_info': {
            'rows': n_rows,
            'columns': n_cols,
        },
        'missing_values': {col: {'count': int(count), 'percent': float(percent)} 
                           for col, count, percent in zip(df.columns, na_counts, na_percent)},
        'column_types': {col: str(dtype) for col, dtype in zip(df.columns, dtypes)},
        'numeric_stats': numeric_stats.to_dict() if not numeric_stats.empty else {},
        'categorical_stats': cat_stats,
        'datetime_stats': date_stats
    }
    
    return summary

def analyze_column_correlations(df):
    """Analyze correlations between numeric columns."""
    if df is None or df.empty:
        return None
    
    numeric_df = df.select_dtypes(include=['number'])
    
    if numeric_df.empty or numeric_df.shape[1] < 2:
        return None
    
    # Calculate correlation matrix
    corr_matrix = numeric_df.corr()
    
    # Find strongly correlated columns (positive or negative)
    strong_correlations = []
    for i in range(len(corr_matrix.columns)):
        for j in range(i+1, len(corr_matrix.columns)):
            col1 = corr_matrix.columns[i]
            col2 = corr_matrix.columns[j]
            corr_value = corr_matrix.iloc[i, j]
            
            if abs(corr_value) > 0.7:  # Consider correlations stronger than 0.7
                strong_correlations.append({
                    'column1': col1,
                    'column2': col2,
                    'correlation': float(corr_value),
                    'strength': 'strong positive' if corr_value > 0 else 'strong negative'
                })
    
    return {
        'correlation_matrix': corr_matrix.to_dict(),
        'strong_correlations': strong_correlations
    }

def detect_outliers(df):
    """Detect outliers in numeric columns using Z-score method."""
    if df is None or df.empty:
        return None
    
    numeric_df = df.select_dtypes(include=['number'])
    
    if numeric_df.empty:
        return None
    
    outliers = {}
    
    for column in numeric_df.columns:
        # Skip columns with too many missing values
        if df[column].isna().sum() > 0.5 * len(df):
            continue
        
        # Calculate Z-scores
        z_scores = np.abs(stats.zscore(df[column].dropna()))
        
        # Consider values with Z-score > 3 as outliers
        outlier_indices = np.where(z_scores > 3)[0]
        
        if len(outlier_indices) > 0:
            original_indices = df[column].dropna().index[outlier_indices]
            outlier_values = df.loc[original_indices, column].values
            
            outliers[column] = {
                'count': len(outlier_indices),
                'percent': len(outlier_indices) / len(df) * 100,
                'indices': original_indices.tolist(),
                'values': outlier_values.tolist()
            }
    
    return outliers

def generate_quick_eda_report(df):
    """Generate a quick EDA report using pandas-profiling."""
    if df is None or df.empty:
        return None
    
    try:
        # Create profile report with minimal configuration
        profile = ProfileReport(df, minimal=True, explorative=True, title="Dataset Profile Report")
        
        # Export to HTML
        report_html = profile.to_html()
        
        # Convert to base64 for embedding
        report_base64 = base64.b64encode(report_html.encode()).decode()
        
        return report_base64
    except Exception as e:
        st.error(f"Failed to generate EDA report: {str(e)}")
        return None

def detect_skewness(df):
    """Detect skewed distributions in numeric columns."""
    if df is None or df.empty:
        return None
    
    numeric_df = df.select_dtypes(include=['number'])
    
    if numeric_df.empty:
        return None
    
    skewness = {}
    
    for column in numeric_df.columns:
        # Skip columns with too many missing values
        if df[column].isna().sum() > 0.5 * len(df):
            continue
        
        # Calculate skewness
        skew_value = df[column].skew()
        
        if abs(skew_value) > 0.5:  # Consider values with abs(skew) > 0.5 as skewed
            skewness[column] = {
                'skewness': float(skew_value),
                'direction': 'right' if skew_value > 0 else 'left',
                'severity': 'high' if abs(skew_value) > 1 else 'moderate'
            }
    
    return skewness

def analyze_categorical_distributions(df):
    """Analyze the distribution of categorical columns."""
    if df is None or df.empty:
        return None
    
    # Consider both categorical and object types
    cat_columns = df.select_dtypes(include=['category', 'object']).columns
    
    if len(cat_columns) == 0:
        return None
    
    cat_distributions = {}
    
    for column in cat_columns:
        # Skip if too many unique values
        if df[column].nunique() > 50:
            continue
        
        # Get value counts and calculate percentages
        value_counts = df[column].value_counts()
        total_count = value_counts.sum()
        percentages = (value_counts / total_count * 100).round(2)
        
        # Check for imbalanced categories (if one category is much more frequent)
        is_imbalanced = False
        dominant_category = None
        
        if not percentages.empty:
            max_percentage = percentages.max()
            if max_percentage > 75:  # If one category represents more than 75% of the data
                is_imbalanced = True
                dominant_category = percentages.idxmax()
        
        cat_distributions[column] = {
            'unique_values': int(df[column].nunique()),
            'top_categories': dict(zip(value_counts.index[:10].astype(str), value_counts.values[:10])),
            'top_percentages': dict(zip(percentages.index[:10].astype(str), percentages.values[:10])),
            'is_imbalanced': is_imbalanced,
            'dominant_category': str(dominant_category) if dominant_category is not None else None
        }
    
    return cat_distributions
