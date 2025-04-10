import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats
import json
from datetime import datetime
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
    
    # Create a formatted numeric summary dataframe for display
    numeric_summary = None
    if not numeric_stats.empty:
        # Create a descriptive stats dataframe
        numeric_summary = df[numeric_cols].describe().T
        # Add additional stats
        if not numeric_summary.empty:
            numeric_summary['missing'] = df[numeric_cols].isna().sum()
            numeric_summary['missing_pct'] = (df[numeric_cols].isna().sum() / len(df) * 100).round(2)
    
    # Categorical column stats
    cat_cols = df.select_dtypes(exclude=['number', 'datetime']).columns
    cat_stats = {}
    
    for col in cat_cols:
        if df[col].nunique() < 50:  # Only for columns with reasonable number of categories
            value_counts = df[col].value_counts().head(10).to_dict()
            cat_stats[col] = {
                'count': int(df[col].nunique()),
                'value_counts': value_counts
            }
    
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
        'numeric_summary': numeric_summary,
        'categorical_stats': cat_stats,
        'datetime_stats': date_stats
    }
    
    return summary

def analyze_column_correlations(df, method='pearson'):
    """Analyze correlations between numeric columns.
    
    Args:
        df: The DataFrame to analyze
        method: Correlation method ('pearson', 'spearman', or 'kendall')
    """
    if df is None or df.empty:
        return None
    
    numeric_df = df.select_dtypes(include=['number'])
    
    if numeric_df.empty or numeric_df.shape[1] < 2:
        return None
    
    # Calculate correlation matrix
    corr_matrix = numeric_df.corr(method=method)
    
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
    
    # Format top correlations as a DataFrame for easy display
    top_correlations = pd.DataFrame(strong_correlations)
    
    return {
        'correlation_matrix': corr_matrix,
        'strong_correlations': strong_correlations,
        'top_correlations': top_correlations if not top_correlations.empty else pd.DataFrame(columns=['column1', 'column2', 'correlation', 'strength'])
    }

def detect_outliers(df, method='zscore', threshold=3.0):
    """Detect outliers in numeric columns.
    
    Args:
        df: The DataFrame to analyze
        method: The method to use for outlier detection ('zscore', 'iqr', or 'modified_zscore')
        threshold: The threshold value for identifying outliers
    """
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
        
        # Get non-missing values
        values = df[column].dropna()
        
        # Skip if too few values
        if len(values) < 5:
            continue
        
        # Detect outliers based on selected method
        outlier_indices = []
        
        if method == 'zscore':
            # Calculate Z-scores
            z_scores = np.abs(stats.zscore(values))
            outlier_indices = np.where(z_scores > threshold)[0]
            
        elif method == 'iqr':
            # Use Interquartile Range method
            q1 = values.quantile(0.25)
            q3 = values.quantile(0.75)
            iqr = q3 - q1
            lower_bound = q1 - (threshold * iqr)
            upper_bound = q3 + (threshold * iqr)
            outlier_indices = values[(values < lower_bound) | (values > upper_bound)].index
            
        elif method == 'modified_zscore':
            # Modified Z-score using median
            median = values.median()
            mad = np.median(np.abs(values - median))
            if mad > 0:  # Avoid division by zero
                modified_z_scores = 0.6745 * np.abs(values - median) / mad
                outlier_indices = values[modified_z_scores > threshold].index
        
        # Store outliers if any were found
        if len(outlier_indices) > 0:
            # For 'zscore' method, we need to map back to the original indices
            if method == 'zscore':
                original_indices = values.index[outlier_indices]
                outlier_values = values.iloc[outlier_indices].values
            else:
                original_indices = outlier_indices
                outlier_values = values.loc[outlier_indices].values
            
            outliers[column] = {
                'count': len(outlier_indices),
                'percent': len(outlier_indices) / len(df) * 100,
                'indices': original_indices.tolist(),
                'values': outlier_values.tolist()
            }
    
    return outliers

def generate_quick_eda_report(df):
    """Generate a quick EDA report with custom HTML."""
    if df is None or df.empty:
        return None
    
    try:
        # Generate summary statistics
        summary_stats = generate_summary_stats(df)
        
        # Get correlation information
        correlations = analyze_column_correlations(df)
        
        # Get outlier information
        outliers = detect_outliers(df)
        
        # Get skewness information
        skewness = detect_skewness(df)
        
        # Get categorical distributions
        cat_distributions = analyze_categorical_distributions(df)
        
        # Create HTML report with double quotes for CSS properties
        html = f"""
        <html>
        <head>
            <title>Dataset Profile Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1, h2, h3 {{ color: #2c3e50; }}
                .section {{ margin-bottom: 30px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ text-align: left; padding: 8px; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #f2f2f2; }}
                tr:hover {{ background-color: #f5f5f5; }}
                .stat-card {{ 
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    padding: 15px;
                    margin-bottom: 15px;
                    background-color: #f9f9f9;
                }}
            </style>
        </head>
        <body>
            <h1>Dataset Profile Report</h1>
            
            <div class="section">
                <h2>Dataset Overview</h2>
                <div class="stat-card">
                    <p><strong>Rows:</strong> {summary_stats['basic_info']['rows']}</p>
                    <p><strong>Columns:</strong> {summary_stats['basic_info']['columns']}</p>
                </div>
            </div>
            
            <div class="section">
                <h2>Column Types</h2>
                <table>
                    <tr>
                        <th>Column</th>
                        <th>Type</th>
                        <th>Missing Values</th>
                        <th>Missing %</th>
                    </tr>
        """
        
        # Add column type information
        for col, dtype in summary_stats['column_types'].items():
            missing_count = summary_stats['missing_values'][col]['count']
            missing_percent = summary_stats['missing_values'][col]['percent']
            html += f"""
                    <tr>
                        <td>{col}</td>
                        <td>{dtype}</td>
                        <td>{missing_count}</td>
                        <td>{missing_percent:.2f}%</td>
                    </tr>
            """
        
        html += """
                </table>
            </div>
        """
        
        # Add numeric statistics if available
        if summary_stats['numeric_stats']:
            html += """
            <div class="section">
                <h2>Numeric Columns Statistics</h2>
                <table>
                    <tr>
                        <th>Column</th>
                        <th>Mean</th>
                        <th>Median</th>
                        <th>Std</th>
                        <th>Min</th>
                        <th>Max</th>
                    </tr>
            """
            
            for col in summary_stats['numeric_stats'].get('mean', {}).keys():
                mean = summary_stats['numeric_stats']['mean'].get(col, 'N/A')
                median = summary_stats['numeric_stats']['median'].get(col, 'N/A')
                std = summary_stats['numeric_stats']['std'].get(col, 'N/A')
                min_val = summary_stats['numeric_stats']['min'].get(col, 'N/A')
                max_val = summary_stats['numeric_stats']['max'].get(col, 'N/A')
                
                html += f"""
                        <tr>
                            <td>{col}</td>
                            <td>{f"{mean:.2f}" if isinstance(mean, (int, float)) else mean}</td>
                            <td>{f"{median:.2f}" if isinstance(median, (int, float)) else median}</td>
                            <td>{f"{std:.2f}" if isinstance(std, (int, float)) else std}</td>
                            <td>{f"{min_val:.2f}" if isinstance(min_val, (int, float)) else min_val}</td>
                            <td>{f"{max_val:.2f}" if isinstance(max_val, (int, float)) else max_val}</td>
                        </tr>
                """
            
            html += """
                </table>
            </div>
            """
        
        # Add correlation information if available
        if correlations and correlations.get('strong_correlations'):
            html += """
            <div class="section">
                <h2>Strong Correlations</h2>
                <table>
                    <tr>
                        <th>Column 1</th>
                        <th>Column 2</th>
                        <th>Correlation</th>
                        <th>Strength</th>
                    </tr>
            """
            
            for corr in correlations['strong_correlations']:
                html += f"""
                        <tr>
                            <td>{corr['column1']}</td>
                            <td>{corr['column2']}</td>
                            <td>{corr['correlation']:.3f}</td>
                            <td>{corr['strength']}</td>
                        </tr>
                """
            
            html += """
                </table>
            </div>
            """
        
        # Add outlier information if available
        if outliers:
            html += """
            <div class="section">
                <h2>Outliers</h2>
                <table>
                    <tr>
                        <th>Column</th>
                        <th>Count</th>
                        <th>Percentage</th>
                    </tr>
            """
            
            for col, details in outliers.items():
                html += f"""
                        <tr>
                            <td>{col}</td>
                            <td>{details['count']}</td>
                            <td>{details['percent']:.2f}%</td>
                        </tr>
                """
            
            html += """
                </table>
            </div>
            """
        
        # Add skewness information if available
        if skewness:
            html += """
            <div class="section">
                <h2>Skewed Distributions</h2>
                <table>
                    <tr>
                        <th>Column</th>
                        <th>Skewness Value</th>
                        <th>Direction</th>
                        <th>Severity</th>
                    </tr>
            """
            
            for col, details in skewness.items():
                html += f"""
                        <tr>
                            <td>{col}</td>
                            <td>{details['skewness']:.3f}</td>
                            <td>{details['direction']}</td>
                            <td>{details['severity']}</td>
                        </tr>
                """
            
            html += """
                </table>
            </div>
            """
        
        # Close the HTML document
        html += """
        </body>
        </html>
        """
        
        # Convert to base64 for embedding
        report_base64 = base64.b64encode(html.encode()).decode()
        
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
