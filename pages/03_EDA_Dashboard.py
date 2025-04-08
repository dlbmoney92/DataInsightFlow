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
import base64

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

# Check authentication first
if not require_auth():
    st.stop()  # Stop if not authenticated

# Show user info if authenticated
if "user" in st.session_state:
    st.sidebar.success(f"Logged in as: {st.session_state.user.get('email', 'User')}")
    st.sidebar.info(f"Subscription: {st.session_state.subscription_tier.capitalize()}")

st.title("Exploratory Data Analysis Dashboard")
st.markdown("""
Use this interactive dashboard to explore and visualize your data. 
Generate statistical summaries, create visualizations, and identify patterns and outliers.
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
    df = st.session_state.dataset
    
    # Display basic dataset info in sidebar
    st.sidebar.subheader("Dataset Info")
    st.sidebar.info(f"""
    - **Rows**: {df.shape[0]}
    - **Columns**: {df.shape[1]}
    - **Project**: {st.session_state.current_project.get('name', 'Unnamed project')}
    """)
    
    # Create tabs for different EDA features
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Summary Stats", 
        "📈 Visualizations", 
        "🔍 Correlations", 
        "⚠️ Outliers", 
        "📑 Full Report"
    ])
    
    with tab1:
        st.header("Summary Statistics")
        
        # Summary statistics section
        summary_stats = generate_summary_stats(df)
        
        # Create columns based on data types
        numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        temporal_cols = [col for col in df.columns if pd.api.types.is_datetime64_any_dtype(df[col])]
        
        # Choose analysis type
        analysis_type = st.radio(
            "Choose analysis type:",
            ["Numeric Columns", "Categorical Columns", "Temporal Columns", "Missing Values"],
            horizontal=True
        )
        
        if analysis_type == "Numeric Columns" and numeric_cols:
            st.subheader("Numeric Columns")
            
            # Display numeric statistics
            st.dataframe(summary_stats["numeric_summary"])
            
            # Skewness analysis
            skew_results = detect_skewness(df)
            if skew_results and len(skew_results) > 0:
                st.subheader("Distribution Skewness")
                skew_df = pd.DataFrame(skew_results)
                st.dataframe(skew_df)
            
            # Histogram with custom column selection
            st.subheader("Distribution Plot")
            selected_num_col = st.selectbox("Select a numeric column", numeric_cols)
            fig = create_distribution_plot(df, selected_num_col)
            st.plotly_chart(fig, use_container_width=True)
            
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
                    st.plotly_chart(fig, use_container_width=True)
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
                st.plotly_chart(fig, use_container_width=True)
        
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
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.success("No missing values found in the dataset!")
    
    with tab2:
        st.header("Data Visualizations")
        
        # Create an AI suggestion section
        with st.expander("🤖 AI-Suggested Visualizations", expanded=True):
            visualizations = suggest_visualizations(df)
            st.write(visualizations)
        
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
            st.plotly_chart(fig, use_container_width=True)
            
        elif viz_type == "Categorical Plot":
            if categorical_cols:
                # Column selection for categorical plot
                col = st.selectbox("Select categorical column", categorical_cols)
                
                # Create categorical plot
                fig = create_categorical_plot(df, col)
                st.plotly_chart(fig, use_container_width=True)
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
            st.plotly_chart(fig, use_container_width=True)
            
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
                st.plotly_chart(fig, use_container_width=True)
                
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
                
            st.plotly_chart(fig, use_container_width=True)
            
        elif viz_type == "Time Series" and temporal_cols:
            # Column selection for time series
            time_col = st.selectbox("Select time column", temporal_cols)
            value_col = st.selectbox("Select value column", numeric_cols)
            
            # Create time series plot
            fig = create_time_series_plot(df, time_col, value_col)
            st.plotly_chart(fig, use_container_width=True)
            
        elif viz_type == "Time Series" and not temporal_cols:
            st.info("No temporal columns found in the dataset for time series visualization.")
            
    with tab3:
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
            st.plotly_chart(fig, use_container_width=True)
            
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
            fig = px.scatter(df, x=x_col, y=y_col, trendline="ols", 
                           title=f"Correlation between {x_col} and {y_col}")
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Display the correlation coefficient
            corr_value = df[x_col].corr(df[y_col], method=corr_method)
            st.info(f"Correlation coefficient ({corr_method}): {corr_value:.4f}")
        else:
            st.info("At least 2 numeric columns are required for correlation analysis.")
    
    with tab4:
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
                values = stats['values']
                outlier_summary.append({
                    "Column": col,
                    "Outlier Count": outlier_count,
                    "% Outliers": f"{pct_outliers:.2f}%",
                    "Min Outlier": min(values) if values else None,
                    "Max Outlier": max(values) if values else None
                })
            
        if outlier_summary:
            outlier_df = pd.DataFrame(outlier_summary)
            st.dataframe(outlier_df)
            
            # Visualize outliers for a selected column
            st.subheader("Visualize Outliers")
            selected_col = st.selectbox("Select column to visualize outliers", list(outliers.keys()))
            
            if selected_col in outliers:
                # Create a box plot to show outliers
                fig = px.box(df, y=selected_col, title=f"Box Plot with Outliers: {selected_col}")
                
                # Highlight the outliers
                if outliers[selected_col] and outliers[selected_col]['count'] > 0:
                    outlier_indices = outliers[selected_col]['indices']
                    
                    # Get outlier values
                    if isinstance(outlier_indices, list) and outlier_indices:
                        outlier_values = df.loc[outlier_indices, selected_col]
                        
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
                
                st.plotly_chart(fig, use_container_width=True)
                
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
    
    with tab5:
        st.header("Complete EDA Report")
        
        # Generate a comprehensive EDA report
        with st.spinner("Generating EDA report..."):
            report_html = generate_quick_eda_report(df)
            
            # Display the report
            st.components.v1.html(report_html, height=600, scrolling=True)
            
            # Provide a download link for the report
            st.download_button(
                label="Download EDA Report",
                data=report_html,
                file_name="eda_report.html",
                mime="text/html"
            )
            
    # Add navigation buttons
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("← Data Preview", use_container_width=True):
            st.switch_page("pages/02_Data_Preview.py")
    with col2:
        if st.button("Home", use_container_width=True):
            st.switch_page("app.py")
    with col3:
        if st.button("Data Transformation →", use_container_width=True):
            st.switch_page("pages/04_Data_Transformation.py")