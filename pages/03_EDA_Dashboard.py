import streamlit as st

# Set page configuration - must be the first Streamlit command
st.set_page_config(
    page_title="EDA Dashboard | Analytics Assist",
    page_icon="📊",
    layout="wide"
)

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from utils.data_analyzer import (
    generate_summary_stats,
    analyze_column_correlations,
    detect_outliers,
    generate_quick_eda_report,
    detect_skewness,
    analyze_categorical_distributions
)
from utils.visualization import (
    create_distribution_plot,
    create_categorical_plot,
    create_correlation_heatmap,
    create_scatter_plot,
    create_time_series_plot,
    create_pair_plot,
    create_missing_values_heatmap
)
from utils.ai_suggestions import suggest_visualizations
from utils.auth_redirect import require_auth
from utils.custom_navigation import render_navigation, initialize_navigation
from utils.global_config import apply_global_css
from utils.access_control import check_access
import base64

def format_outlier_value(value):
    """Format outlier values depending on their type."""
    if isinstance(value, (int, np.integer)):
        return str(value)
    elif isinstance(value, (float, np.floating)):
        return f"{value:.4f}"
    else:
        return str(value)

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

# Sidebar content - render custom navigation
render_navigation()

# Main content
st.title("EDA Dashboard")

# Check if user is authenticated, redirect if not
if not require_auth():
    st.stop()

# Check if a dataset is loaded
if "dataset" not in st.session_state or st.session_state.dataset is None or st.session_state.dataset.empty:
    st.info("Please upload a dataset or load an existing one from the Upload Data page.")
    st.stop()

# Get the dataset
df = st.session_state.dataset
dataset_name = st.session_state.get("dataset_name", "Unnamed Dataset")

st.header(f"Exploratory Data Analysis: {dataset_name}")

# Determine column types
numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
temporal_cols = []

# Check for datetime columns - they may be stored as objects
for col in df.columns:
    if pd.api.types.is_datetime64_any_dtype(df[col]):
        temporal_cols.append(col)
    elif col in categorical_cols:  # Check if we can convert object columns to datetime
        try:
            pd.to_datetime(df[col], errors='raise')
            temporal_cols.append(col)
            categorical_cols.remove(col)  # Remove from categorical list if it's actually a date
        except:
            pass  # Not a datetime column, keep as categorical

# Determine which tabs are available based on subscription
tabs_available = {
    "Summary": True,  # Always available
    "Visualizations": check_access("visualization", "basic"),
    "Correlations": True,  # Always available
    "Outliers": check_access("visualization", "outlier_detection"),
    "Full Report": check_access("visualization", "full_eda_report")
}

# Create tab info with available and ordered tabs
tab_info = {}
tab_index = 0

for tab_name, available in tabs_available.items():
    tab_info[tab_name] = {
        "available": available,
        "index": tab_index if available else None
    }
    if available:
        tab_index += 1

# Create tabs
tabs = st.tabs([name for name, info in tab_info.items() if info["available"]])

# Summary tab (always available)
with tabs[tab_info["Summary"]["index"]]:
    st.header("Dataset Summary")
    
    # Basic info
    st.subheader("Basic Information")
    num_rows, num_cols = df.shape
    st.write(f"**Rows:** {num_rows}  |  **Columns:** {num_cols}")
    st.write(f"**Numeric Columns:** {len(numeric_cols)}  |  **Categorical Columns:** {len(categorical_cols)}  |  **Temporal Columns:** {len(temporal_cols)}")
    
    # Memory usage
    memory_usage = df.memory_usage(deep=True).sum()
    st.write(f"**Memory Usage:** {memory_usage / 1024 / 1024:.2f} MB")
    
    # Data types table
    st.subheader("Data Types")
    
    # Create a more informative data types table
    data_types = []
    for col in df.columns:
        dtype = df[col].dtype
        null_count = df[col].isna().sum()
        null_pct = (null_count / len(df)) * 100
        unique_count = df[col].nunique()
        unique_pct = (unique_count / len(df)) * 100
        
        data_types.append({
            "Column": col,
            "Type": str(dtype),
            "Null Count": null_count,
            "Null %": f"{null_pct:.2f}%",
            "Unique Values": unique_count,
            "Unique %": f"{unique_pct:.2f}%"
        })
    
    st.dataframe(pd.DataFrame(data_types))
    
    # Choose which type of analysis to display
    st.subheader("Column Analysis")
    
    analysis_options = ["Numeric Columns", "Categorical Columns", "Temporal Columns", "Missing Values"]
    available_options = []
    
    if numeric_cols:
        available_options.append("Numeric Columns")
    if categorical_cols:
        available_options.append("Categorical Columns")
    if temporal_cols:
        available_options.append("Temporal Columns")
    available_options.append("Missing Values")
    
    analysis_type = st.selectbox("Select analysis type", available_options)
    
    if analysis_type == "Numeric Columns" and numeric_cols:
        st.subheader("Numeric Columns")
        
        # Descriptive statistics
        numeric_stats = df[numeric_cols].describe().T
        numeric_stats['missing'] = df[numeric_cols].isnull().sum().values
        numeric_stats['missing_pct'] = (df[numeric_cols].isnull().sum().values / len(df)) * 100
        numeric_stats = numeric_stats.round(2)
        st.dataframe(numeric_stats)
        
        # Skewness analysis
        st.subheader("Skewness Analysis")
        
        skew_results = []
        for col in numeric_cols:
            skew = df[col].skew()
            skew_type = "Highly Skewed (Right)" if skew > 1 else "Moderately Skewed (Right)" if skew > 0.5 else "Fairly Symmetric" if skew > -0.5 else "Moderately Skewed (Left)" if skew > -1 else "Highly Skewed (Left)"
            skew_results.append({
                "Column": col,
                "Skewness": f"{skew:.4f}",
                "Interpretation": skew_type
            })
        
        skew_df = pd.DataFrame(skew_results)
        st.dataframe(skew_df)
    
        # Histogram with custom column selection
        st.subheader("Distribution Plot")
        selected_num_col = st.selectbox("Select a numeric column", numeric_cols)
        fig = create_distribution_plot(df, selected_num_col)
        st.plotly_chart(fig, use_container_width=True, key="summary_distribution_plot")
        
    elif analysis_type == "Categorical Columns" and categorical_cols:
        st.subheader("Categorical Columns")
        
        # Display categorical statistics
        cat_stats = analyze_categorical_distributions(df)
        if cat_stats:
            for col, stats in cat_stats.items():
                st.write(f"**{col}** - {stats['unique_values']} unique values")
                st.dataframe(pd.DataFrame({
                    'Value': stats['top_categories'].keys(),
                    'Count': stats['top_categories'].values(),
                    'Percentage': stats['top_percentages'].values()
                }))
                
                # Bar chart for categorical column
                fig = create_categorical_plot(df, col)
                st.plotly_chart(fig, use_container_width=True, key=f"cat_plot_{col}")
        else:
            st.info("No categorical columns found in the dataset.")
        
    elif analysis_type == "Temporal Columns" and temporal_cols:
        st.subheader("Temporal Columns")
        
        # Display temporal statistics
        for col in temporal_cols:
            st.write(f"**{col}**")
            st.write(f"- Min date: {df[col].min()}")
            st.write(f"- Max date: {df[col].max()}")
            st.write(f"- Range: {(df[col].max() - df[col].min()).days} days")
            
            # Time series plot
            st.subheader(f"Time Series Plot - {col}")
            
            # Choose a numeric column for the y-axis
            y_col = st.selectbox(f"Select y-axis for {col}", numeric_cols)
            
            # Create time series plot
            fig = create_time_series_plot(df, col, y_col)
            st.plotly_chart(fig, use_container_width=True, key=f"time_series_{col}")
    
    elif analysis_type == "Missing Values":
        st.subheader("Missing Values Analysis")
        
        # Calculate missing values
        missing_data = df.isnull().sum().reset_index()
        missing_data.columns = ['Column', 'Missing Values']
        missing_data['Percentage'] = (missing_data['Missing Values'] / len(df)) * 100
        missing_data = missing_data.sort_values('Missing Values', ascending=False)
        
        # Display missing values table
        st.dataframe(missing_data)
        
        # Create missing values heatmap
        if df.isnull().values.any():  # Only create if there are missing values
            st.subheader("Missing Values Heatmap")
            fig = create_missing_values_heatmap(df)
            st.plotly_chart(fig, use_container_width=True, key="missing_vals_heatmap")
        else:
            st.success("No missing values found in the dataset!")

# Visualizations tab (conditional based on subscription)
if tab_info["Visualizations"]["available"]:
    with tabs[tab_info["Visualizations"]["index"]]:
        st.header("Data Visualizations")
        
        # Create an AI suggestion section
        with st.expander("🤖 AI-Suggested Visualizations", expanded=True):
            visualizations = suggest_visualizations(df)
            if visualizations:
                # Display suggestions in a user-friendly format
                for i, viz in enumerate(visualizations):
                    with st.container():
                        st.markdown(f"### {i+1}. {viz.get('title', 'Visualization Suggestion')}")
                        st.markdown(f"**Chart Type:** {viz.get('chart_type', 'Not specified')}")
                        st.markdown(f"**Description:** {viz.get('description', 'No description available')}")
                        st.markdown(f"**Columns:** {', '.join(viz.get('columns', []))}")
                        st.markdown("---")
            else:
                st.info("No visualization suggestions available for this dataset.")
        
        # Choose a visualization type
        viz_type = st.selectbox(
            "Select visualization type",
            ["Distribution Plot", "Categorical Plot", "Scatter Plot", "Pair Plot", "Box Plot", "Time Series"]
        )
    
        if viz_type == "Distribution Plot":
            # Column selection for distribution plot
            col = st.selectbox("Select column for distribution plot", numeric_cols)
            
            # Create distribution plot
            fig = create_distribution_plot(df, col)
            st.plotly_chart(fig, use_container_width=True, key="viz_distribution_plot")
            
        elif viz_type == "Categorical Plot":
            if categorical_cols:
                # Column selection for categorical plot
                col = st.selectbox("Select categorical column", categorical_cols)
                
                # Create categorical plot
                fig = create_categorical_plot(df, col)
                st.plotly_chart(fig, use_container_width=True, key="viz_categorical_plot")
            else:
                st.info("No categorical columns found in the dataset.")
                
        elif viz_type == "Scatter Plot":
            # Column selection for scatter plot
            col1 = st.selectbox("Select X-axis column", numeric_cols, key="scatter_x")
            col2 = st.selectbox("Select Y-axis column", numeric_cols, key="scatter_y")
            
            # Optional color by column
            color_col = st.selectbox("Color by (optional)", ["None"] + categorical_cols)
            color_col = None if color_col == "None" else color_col
            
            # Create scatter plot
            fig = create_scatter_plot(df, col1, col2, color_column=color_col)
            st.plotly_chart(fig, use_container_width=True, key="viz_scatter_plot")
            
        elif viz_type == "Pair Plot":
            # Column selection for pair plot (limit to 5 columns for performance)
            if len(numeric_cols) > 5:
                selected_cols = st.multiselect(
                    "Select columns for pair plot (max 5 recommended)", 
                    numeric_cols,
                    default=numeric_cols[:3]
                )
                
                if len(selected_cols) > 5:
                    st.warning("Too many columns selected. This might make the visualization slow. Consider selecting fewer columns.")
            else:
                selected_cols = numeric_cols
                
            # Optional color by column
            color_col = st.selectbox("Color by (optional)", ["None"] + categorical_cols)
            color_col = None if color_col == "None" else color_col
            
            if selected_cols:
                # Create pair plot
                fig = create_pair_plot(df, selected_cols, color_column=color_col)
                st.plotly_chart(fig, use_container_width=True, key="viz_pair_plot")
                
        elif viz_type == "Box Plot":
            # Column selection for box plot
            numeric_col = st.selectbox("Select numeric column", numeric_cols)
            
            # Optional grouping column
            group_col = st.selectbox("Group by (optional)", ["None"] + categorical_cols)
            group_col = None if group_col == "None" else group_col
            
            # Create box plot
            if group_col:
                fig = px.box(df, x=group_col, y=numeric_col, color=group_col,
                           title=f"Box Plot of {numeric_col} by {group_col}")
            else:
                fig = px.box(df, y=numeric_col, title=f"Box Plot of {numeric_col}")
                
            st.plotly_chart(fig, use_container_width=True, key="viz_box_plot")
            
        elif viz_type == "Time Series" and temporal_cols:
            # Column selection for time series
            time_col = st.selectbox("Select time column", temporal_cols)
            value_col = st.selectbox("Select value column", numeric_cols)
            
            # Create time series plot
            fig = create_time_series_plot(df, time_col, value_col)
            st.plotly_chart(fig, use_container_width=True, key="viz_time_series")
            
        elif viz_type == "Time Series" and not temporal_cols:
            st.info("No temporal columns found in the dataset for time series visualization.")
        
# Correlations tab (always available)
with tabs[tab_info["Correlations"]["index"]]:
    st.header("Correlation Analysis")
    
    # Only perform correlation analysis if there are at least 2 numeric columns
    if len(numeric_cols) >= 2:
        # Correlation coefficient type
        corr_method = st.radio(
            "Correlation method:",
            ["pearson", "spearman", "kendall"],
            index=0,
            horizontal=True,
            help=("Pearson: linear correlation, "
                  "Spearman: rank correlation, "
                  "Kendall: ordinal correlation")
        )
        
        # Compute the correlation matrix
        corr_results = analyze_column_correlations(df, method=corr_method)
        
        # Display correlation matrix as a table
        st.subheader("Correlation Matrix")
        st.dataframe(corr_results["correlation_matrix"])
        
        # Display correlation heatmap
        st.subheader("Correlation Heatmap")
        fig = create_correlation_heatmap(df, method=corr_method)
        st.plotly_chart(fig, use_container_width=True, key="corr_heatmap")
        
        # Display top correlated pairs
        st.subheader("Top Correlated Pairs")
        st.dataframe(corr_results["top_correlations"])
        
        # Option to visualize a specific correlation
        st.subheader("Visualize Correlation")
        
        col1, col2 = st.columns(2)
        with col1:
            x_col = st.selectbox("Select X-axis column", numeric_cols, key="corr_x")
        with col2:
            y_col = st.selectbox("Select Y-axis column", numeric_cols, key="corr_y")
            
        # Create scatter plot for the selected correlation
        # Handle duplicate column names by creating a pandas DataFrame with fixed column names
        # This approach avoids the narwhals.exceptions.DuplicateError
        
        # Create a completely new pandas DataFrame with only the needed columns
        import pandas as pd
        plot_data = pd.DataFrame()
        plot_data['x_values'] = df[x_col].values
        plot_data['y_values'] = df[y_col].values
        
        # Use the new DataFrame with guaranteed unique column names for plotting
        fig = px.scatter(plot_data, x='x_values', y='y_values', trendline="ols", 
                       title=f"Correlation between {x_col} and {y_col}")
        
        # Update axis labels to show the original column names
        fig.update_layout(
            xaxis_title=x_col,
            yaxis_title=y_col
        )
        
        st.plotly_chart(fig, use_container_width=True, key="corr_scatter")
        
        # Display the correlation coefficient
        corr_value = df[x_col].corr(df[y_col], method=corr_method)
        st.info(f"Correlation coefficient ({corr_method}): {corr_value:.4f}")
    else:
        st.info("At least 2 numeric columns are required for correlation analysis.")

# Outliers tab (conditional based on subscription)
if tab_info["Outliers"]["available"]:
    with tabs[tab_info["Outliers"]["index"]]:
        st.header("Outlier Detection")
        
        # Choose outlier detection method
        outlier_method = st.radio(
            "Outlier detection method:",
            ["Z-Score", "IQR (Interquartile Range)", "Modified Z-Score"],
            horizontal=True
        )
        
        # Set threshold based on method
        if outlier_method == "Z-Score":
            threshold = st.slider("Z-Score threshold", 1.0, 5.0, 3.0, 0.1)
            method = "zscore"
        elif outlier_method == "IQR (Interquartile Range)":
            threshold = st.slider("IQR multiplier", 1.0, 3.0, 1.5, 0.1)
            method = "iqr"
        else:  # Modified Z-Score
            threshold = st.slider("Modified Z-Score threshold", 1.0, 5.0, 3.5, 0.1)
            method = "modified_zscore"
            
        # Detect outliers
        outliers = detect_outliers(df, method=method, threshold=threshold)
        
        # Display outlier summary
        st.subheader("Outlier Summary")
        
        # Create a summary table of outliers by column
        outlier_summary = []
        if outliers:
            for col, stats in outliers.items():
                outlier_count = stats['count']
                pct_outliers = stats['percent']
                values = stats.get('values', [])
                outlier_summary.append({
                    "Column": col,
                    "Outlier Count": outlier_count,
                    "% Outliers": f"{pct_outliers:.2f}%",
                    "Min Outlier": format_outlier_value(min(values)) if values and len(values) > 0 else "N/A", 
                    "Max Outlier": format_outlier_value(max(values)) if values and len(values) > 0 else "N/A"
                })
            
        if outlier_summary:
            outlier_df = pd.DataFrame(outlier_summary)
            # Format the percentage for better display
            if "% Outliers" in outlier_df.columns:
                outlier_df["% Outliers"] = outlier_df["% Outliers"].apply(lambda x: f"{float(x.strip('%')):.2f}%" if isinstance(x, str) else f"{float(x):.2f}%")
            st.dataframe(outlier_df)
            
            # Visualize outliers for a selected column
            st.subheader("Visualize Outliers")
            selected_col = st.selectbox("Select column to visualize outliers", list(outliers.keys()))
            
            if selected_col in outliers:
                # Create a box plot to show outliers
                # Create a simplified DataFrame with only the selected column to avoid duplicate column issues
                import pandas as pd
                box_data = pd.DataFrame()
                box_data['value'] = df[selected_col].values
                
                fig = px.box(box_data, y='value', title=f"Box Plot with Outliers: {selected_col}")
                
                # Update y-axis label to show the original column name
                fig.update_layout(yaxis_title=selected_col)
                
                # Highlight the outliers
                if outliers[selected_col] and outliers[selected_col]['count'] > 0:
                    outlier_indices = outliers[selected_col]['indices']
                    
                    # Get outlier values
                    if isinstance(outlier_indices, list) and outlier_indices:
                        outlier_values = df.loc[outlier_indices, selected_col].values
                        
                        # Add scatter points for outliers
                        fig.add_trace(
                            go.Scatter(
                                x=[0] * len(outlier_values),
                                y=outlier_values,
                                mode="markers",
                                marker=dict(color="red", size=8, symbol="circle"),
                                name="Outliers"
                            )
                        )
                
                st.plotly_chart(fig, use_container_width=True, key="outlier_box_plot")
                
                # Option to show the actual outlier values
                with st.expander("Show outlier records"):
                    if outliers[selected_col] and outliers[selected_col]['count'] > 0:
                        outlier_indices = outliers[selected_col]['indices']
                        if isinstance(outlier_indices, list) and outlier_indices:
                            st.dataframe(df.loc[outlier_indices])
                        else:
                            st.info(f"No outlier indices available for {selected_col}.")
                    else:
                        st.info(f"No outliers detected in {selected_col} with the current settings.")
        else:
            st.info("No outliers detected with the current settings.")

# Full Report tab (conditional based on subscription)
if tab_info["Full Report"]["available"]:
    with tabs[tab_info["Full Report"]["index"]]:
        st.header("Complete EDA Report")
        
        # Generate a comprehensive EDA report
        with st.spinner("Generating EDA report..."):
            try:
                # Create a copy of the dataframe with fixed column names for the report
                report_df = df.copy()
                
                # Generate HTML report
                report_html = generate_quick_eda_report(report_df)
                
                # Display the report
                st.components.v1.html(report_html, height=600, scrolling=True)
                
                # Option to download the report as PDF
                from utils.export import convert_html_to_pdf
                
                # First offer HTML download option
                b64_html = base64.b64encode(report_html.encode()).decode()
                href_html = f'<a href="data:text/html;base64,{b64_html}" download="eda_report_{dataset_name}.html">Download as HTML</a>'
                
                # Create columns for download options
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(href_html, unsafe_allow_html=True)
                
                with col2:
                    if st.button("Download as PDF"):
                        with st.spinner("Generating PDF..."):
                            try:
                                pdf_bytes = convert_html_to_pdf(report_html)
                                b64_pdf = base64.b64encode(pdf_bytes).decode()
                                href_pdf = f'<a href="data:application/pdf;base64,{b64_pdf}" download="eda_report_{dataset_name}.pdf">Click here to download PDF</a>'
                                st.markdown(href_pdf, unsafe_allow_html=True)
                                st.success("PDF generated successfully!")
                            except Exception as e:
                                st.error(f"Error generating PDF: {str(e)}")
                                st.info("Please try the HTML download option instead.")
                
            except Exception as e:
                st.error(f"Error generating EDA report: {str(e)}")
                st.info("Try with a smaller dataset or fewer columns for better performance.")