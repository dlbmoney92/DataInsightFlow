import streamlit as st
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
import base64

st.set_page_config(
    page_title="EDA Dashboard | Analytics Assist",
    page_icon="📊",
    layout="wide"
)

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
    st.button("Go to Upload Page", on_click=lambda: st.switch_page("pages/01_Upload_Data.py"))
    st.stop()

# Header and description
st.title("Exploratory Data Analysis Dashboard")
st.markdown("""
Discover insights from your data with automatic visualizations and statistical analysis.
This dashboard provides a comprehensive overview of your dataset.
""")

# Get data from session state
df = st.session_state.dataset
column_types = st.session_state.column_types
file_name = st.session_state.file_name

# Create tabs for different EDA sections
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Overview", 
    "📈 Distributions", 
    "🔍 Correlations", 
    "🧮 Advanced Analysis",
    "📋 Full Report"
])

# Tab 1: Overview
with tab1:
    st.subheader("Dataset Summary")
    
    # Generate summary statistics
    summary_stats = generate_summary_stats(df)
    
    # Display basic info
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Rows", summary_stats['basic_info']['rows'])
    
    with col2:
        st.metric("Columns", summary_stats['basic_info']['columns'])
    
    with col3:
        missing_vals = sum(info['count'] for info in summary_stats['missing_values'].values())
        total_cells = summary_stats['basic_info']['rows'] * summary_stats['basic_info']['columns']
        missing_pct = round(missing_vals / total_cells * 100, 2) if total_cells > 0 else 0
        st.metric("Missing Values", f"{missing_vals} ({missing_pct}%)")
    
    # Missing values visualization
    st.subheader("Missing Values Heatmap")
    missing_fig = create_missing_values_heatmap(df)
    if missing_fig:
        st.plotly_chart(missing_fig, use_container_width=True, key="missing_values_heatmap")
    else:
        st.info("No missing values to display.")
    
    # Column type breakdown
    st.subheader("Column Types")
    
    # Count column types
    type_counts = {}
    for col_type in column_types.values():
        type_counts[col_type] = type_counts.get(col_type, 0) + 1
    
    # Create pie chart for column types
    type_df = pd.DataFrame({
        'Type': list(type_counts.keys()),
        'Count': list(type_counts.values())
    })
    
    fig = px.pie(
        type_df, 
        values='Count', 
        names='Type', 
        title='Column Types Distribution',
        color_discrete_sequence=px.colors.qualitative.Plotly
    )
    
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True, key="column_types_pie")
    
    # AI-suggested visualizations
    st.subheader("AI-Suggested Visualizations")
    
    if 'visualization_suggestions' not in st.session_state:
        with st.spinner("Generating visualization suggestions..."):
            visualization_suggestions = suggest_visualizations(df)
            st.session_state.visualization_suggestions = visualization_suggestions
    else:
        visualization_suggestions = st.session_state.visualization_suggestions
    
    if visualization_suggestions:
        # Display the top 3 suggestions
        # Convert to list first to ensure we can slice it safely
        suggestions_list = list(visualization_suggestions)
        max_suggestions = min(3, len(suggestions_list))
        
        for i in range(max_suggestions):
            suggestion = suggestions_list[i]
            # Check if suggestion is a dictionary
            if isinstance(suggestion, dict):
                st.markdown(f"### {suggestion.get('title', f'Suggestion {i+1}')}")
                st.markdown(suggestion.get('description', ''))
            else:
                # If it's not a dictionary (e.g., a string), handle it differently
                st.markdown(f"### Suggestion {i+1}")
                st.markdown(str(suggestion) if suggestion else "")
            
            # Create visualization from suggestion only if it's a dictionary
            if isinstance(suggestion, dict):
                from utils.visualization import create_visualization_from_suggestion
                fig = create_visualization_from_suggestion(df, suggestion)
                
                if fig:
                    st.plotly_chart(fig, use_container_width=True, key=f"ai_suggestion_{i}")
                else:
                    st.error("Could not create this visualization. Some columns may be incompatible.")
            else:
                st.warning("Visualization not available for this suggestion format.")
    else:
        st.info("No visualization suggestions available.")

# Tab 2: Distributions
with tab2:
    st.subheader("Column Distributions")
    
    # Create column selectors
    col1, col2 = st.columns(2)
    
    with col1:
        # Numeric columns for distribution plots
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        if numeric_cols:
            selected_num_col = st.selectbox("Select numeric column", numeric_cols)
            dist_plot_type = st.selectbox(
                "Plot type", 
                ["histogram", "box", "violin"],
                format_func=lambda x: x.title()
            )
            
            # Create distribution plot
            num_fig = create_distribution_plot(df, selected_num_col, dist_plot_type)
            if num_fig:
                st.plotly_chart(num_fig, use_container_width=True, key=f"num_dist_{selected_num_col}_{dist_plot_type}")
            
            # Show statistics for the selected column
            if selected_num_col in numeric_cols:
                stats = df[selected_num_col].describe()
                st.markdown(f"**Statistics for {selected_num_col}**")
                st.write(stats)
                
                # Check for skewness
                skew = df[selected_num_col].skew()
                st.markdown(f"**Skewness: {skew:.2f}**")
                if abs(skew) > 1:
                    st.warning(f"This column is highly skewed ({'right' if skew > 0 else 'left'}-skewed)")
                elif abs(skew) > 0.5:
                    st.info(f"This column is moderately skewed ({'right' if skew > 0 else 'left'}-skewed)")
                else:
                    st.success("This column is approximately symmetrically distributed")
        else:
            st.info("No numeric columns found in the dataset.")
    
    with col2:
        # Categorical columns for bar/pie charts
        cat_cols = df.select_dtypes(exclude=['number', 'datetime']).columns.tolist()
        if cat_cols:
            selected_cat_col = st.selectbox("Select categorical column", cat_cols)
            cat_plot_type = st.selectbox(
                "Plot type", 
                ["bar", "pie", "treemap"],
                format_func=lambda x: "Bar Chart" if x == "bar" else "Pie Chart" if x == "pie" else "Treemap"
            )
            
            # Create categorical plot
            cat_fig = create_categorical_plot(df, selected_cat_col, cat_plot_type)
            if cat_fig:
                st.plotly_chart(cat_fig, use_container_width=True, key=f"cat_plot_{selected_cat_col}_{cat_plot_type}")
            
            # Show value counts for the selected column
            if selected_cat_col in cat_cols:
                value_counts = df[selected_cat_col].value_counts().reset_index()
                value_counts.columns = [selected_cat_col, 'Count']
                st.markdown(f"**Value Counts for {selected_cat_col}**")
                
                # Calculate percentages
                value_counts['Percentage'] = (value_counts['Count'] / value_counts['Count'].sum() * 100).round(2)
                
                # Show top 10 values if there are many
                if len(value_counts) > 10:
                    st.write(value_counts.head(10))
                    st.info(f"Showing top 10 out of {len(value_counts)} unique values")
                else:
                    st.write(value_counts)
        else:
            st.info("No categorical columns found in the dataset.")
    
    # Detect and display outliers for numeric columns
    st.subheader("Outlier Detection")
    outliers = detect_outliers(df)
    
    if outliers:
        # Create a summary table of outliers
        outlier_summary = []
        for col, info in outliers.items():
            outlier_summary.append({
                'Column': col,
                'Outlier Count': info['count'],
                'Percentage': f"{info['percent']:.2f}%"
            })
        
        outlier_df = pd.DataFrame(outlier_summary)
        st.write(outlier_df)
        
        # Select a column to view outliers
        if outlier_summary:
            selected_outlier_col = st.selectbox(
                "Select column to view outliers", 
                [row['Column'] for row in outlier_summary]
            )
            
            if selected_outlier_col in outliers:
                # Display a boxplot highlighting outliers
                fig = px.box(
                    df, 
                    y=selected_outlier_col,
                    title=f"Boxplot with Outliers for {selected_outlier_col}",
                    points="outliers",
                    color_discrete_sequence=['#4F8BF9']
                )
                
                st.plotly_chart(fig, use_container_width=True, key=f"outlier_box_{selected_outlier_col}")
                
                # Display the actual outlier values
                outlier_values = outliers[selected_outlier_col]['values']
                st.markdown(f"**Outlier values for {selected_outlier_col}**")
                st.write(outlier_values)
                
                # Recommendation for outliers
                st.info(
                    "Recommendations: Consider applying a transformation such as log transform for skewed data, "
                    "or capping/removing outliers if they are errors."
                )
    else:
        st.info("No significant outliers detected in numeric columns.")

# Tab 3: Correlations
with tab3:
    # Check if there are numeric columns for correlation analysis
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    
    if len(numeric_cols) < 2:
        st.info("Correlation analysis requires at least 2 numeric columns. Your dataset doesn't have enough numeric columns.")
    else:
        st.subheader("Correlation Matrix")
        
        # Create correlation heatmap
        corr_fig = create_correlation_heatmap(df)
        if corr_fig:
            st.plotly_chart(corr_fig, use_container_width=True, key="correlation_heatmap")
        
        # Analyze correlations for strong relationships
        correlation_analysis = analyze_column_correlations(df)
        
        if correlation_analysis and correlation_analysis['strong_correlations']:
            st.subheader("Strong Correlations")
            
            # Create a DataFrame of strong correlations
            strong_corrs = correlation_analysis['strong_correlations']
            strong_corr_df = pd.DataFrame(strong_corrs)
            
            # Format the correlation values
            strong_corr_df['correlation'] = strong_corr_df['correlation'].round(3)
            
            # Sort by absolute correlation value
            strong_corr_df = strong_corr_df.sort_values(
                by='correlation', 
                key=lambda x: x.abs(), 
                ascending=False
            )
            
            st.write(strong_corr_df)
            
            # Option to visualize a specific correlation with scatter plot
            if not strong_corr_df.empty:
                st.subheader("Visualize Correlation")
                
                # Select columns for scatter plot
                col1, col2 = st.columns(2)
                
                with col1:
                    scatter_x = st.selectbox("X-axis", numeric_cols, index=0)
                
                with col2:
                    remaining_cols = [col for col in numeric_cols if col != scatter_x]
                    scatter_y = st.selectbox("Y-axis", remaining_cols, index=0 if remaining_cols else None)
                
                if scatter_x and scatter_y:
                    # Optional color by categorical column
                    cat_cols = df.select_dtypes(exclude=['number', 'datetime']).columns.tolist()
                    color_col = st.selectbox(
                        "Color by (optional)", 
                        ["None"] + cat_cols
                    )
                    
                    color_col = None if color_col == "None" else color_col
                    
                    # Create scatter plot
                    scatter_fig = create_scatter_plot(
                        df, 
                        scatter_x, 
                        scatter_y, 
                        color_col
                    )
                    
                    if scatter_fig:
                        st.plotly_chart(scatter_fig, use_container_width=True, key=f"scatter_{scatter_x}_{scatter_y}")
                        
                        # Calculate and display correlation coefficient
                        corr_val = df[[scatter_x, scatter_y]].corr().iloc[0, 1]
                        st.markdown(f"**Correlation coefficient: {corr_val:.4f}**")
                        
                        # Interpretation of correlation
                        if abs(corr_val) > 0.7:
                            strength = "strong"
                        elif abs(corr_val) > 0.3:
                            strength = "moderate"
                        else:
                            strength = "weak"
                            
                        direction = "positive" if corr_val > 0 else "negative"
                        
                        st.markdown(
                            f"This is a **{strength} {direction}** correlation. "
                            f"{'As one variable increases, the other tends to increase as well.' if corr_val > 0 else 'As one variable increases, the other tends to decrease.'}"
                        )
        else:
            st.info("No strong correlations found in the dataset.")
        
        # Pair Plot for selected variables
        st.subheader("Pair Plot")
        st.markdown("Select up to 4 numeric variables to visualize their relationships")
        
        selected_pair_cols = st.multiselect(
            "Select columns for pair plot",
            numeric_cols,
            default=numeric_cols[:min(4, len(numeric_cols))]
        )
        
        if len(selected_pair_cols) > 1:
            # Optional color by categorical column
            cat_cols = df.select_dtypes(exclude=['number', 'datetime']).columns.tolist()
            pair_color_col = st.selectbox(
                "Color by (optional)", 
                ["None"] + cat_cols,
                key="pair_color"
            )
            
            pair_color_col = None if pair_color_col == "None" else pair_color_col
            
            # Create pair plot
            with st.spinner("Generating pair plot..."):
                pair_fig = create_pair_plot(
                    df, 
                    selected_pair_cols,
                    pair_color_col
                )
                
                if pair_fig:
                    st.plotly_chart(pair_fig, use_container_width=True, key="pair_plot")
        else:
            st.info("Please select at least 2 columns for the pair plot.")

# Tab 4: Advanced Analysis
with tab4:
    st.subheader("Time Series Analysis")
    
    # Check for datetime columns
    date_cols = df.select_dtypes(include=['datetime']).columns.tolist()
    
    # Also check for columns that might be dates but not detected
    for col in df.columns:
        if col not in date_cols:
            try:
                pd.to_datetime(df[col], errors='raise')
                date_cols.append(col)
            except:
                pass
    
    if date_cols:
        # Time series plot
        selected_date_col = st.selectbox("Select date column", date_cols)
        
        # Only show numeric columns for time series values
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        if numeric_cols:
            selected_value_col = st.selectbox("Select value to plot", numeric_cols)
            
            # Optional grouping by categorical column
            cat_cols = df.select_dtypes(exclude=['number', 'datetime']).columns.tolist()
            group_col = st.selectbox(
                "Group by (optional)", 
                ["None"] + cat_cols
            )
            
            group_col = None if group_col == "None" else group_col
            
            # Convert to datetime if not already
            df_copy = df.copy()
            if not pd.api.types.is_datetime64_dtype(df_copy[selected_date_col]):
                try:
                    df_copy[selected_date_col] = pd.to_datetime(df_copy[selected_date_col])
                except:
                    st.error(f"Could not convert {selected_date_col} to datetime.")
                    st.stop()
            
            # Create time series plot
            ts_fig = create_time_series_plot(
                df_copy, 
                selected_date_col, 
                selected_value_col, 
                group_col
            )
            
            if ts_fig:
                st.plotly_chart(ts_fig, use_container_width=True, key=f"timeseries_{selected_date_col}_{selected_value_col}")
                
                # Time trends analysis
                st.subheader("Time Trends Analysis")
                
                if group_col is None:
                    # Calculate rolling mean for trend analysis
                    window_size = st.slider(
                        "Rolling window size", 
                        min_value=2, 
                        max_value=min(50, len(df_copy) // 2),
                        value=min(7, len(df_copy) // 4)
                    )
                    
                    # Sort by date
                    df_time = df_copy.sort_values(by=selected_date_col)
                    
                    # Calculate rolling statistics
                    rolling_mean = df_time[selected_value_col].rolling(window=window_size).mean()
                    
                    # Create trend plot
                    trend_fig = go.Figure()
                    
                    # Add raw data
                    trend_fig.add_trace(
                        go.Scatter(
                            x=df_time[selected_date_col],
                            y=df_time[selected_value_col],
                            mode='lines',
                            name='Raw data',
                            line=dict(color='lightgrey')
                        )
                    )
                    
                    # Add rolling mean
                    trend_fig.add_trace(
                        go.Scatter(
                            x=df_time[selected_date_col],
                            y=rolling_mean,
                            mode='lines',
                            name=f'Rolling mean (window={window_size})',
                            line=dict(color='red', width=2)
                        )
                    )
                    
                    trend_fig.update_layout(
                        title=f"Trend Analysis for {selected_value_col}",
                        xaxis_title=selected_date_col,
                        yaxis_title=selected_value_col,
                        height=400
                    )
                    
                    st.plotly_chart(trend_fig, use_container_width=True, key=f"trend_{selected_value_col}_{window_size}")
                    
                    # Check for seasonality if enough data points
                    if len(df_copy) > 30:
                        st.subheader("Seasonality Check")
                        
                        # Basic seasonality check using autocorrelation
                        # (Simplified approach for demonstration)
                        try:
                            from pandas.plotting import autocorrelation_plot
                            import matplotlib.pyplot as plt
                            
                            # Create matplotlib figure
                            fig, ax = plt.subplots(figsize=(10, 6))
                            autocorrelation_plot(df_time[selected_value_col].dropna(), ax=ax)
                            ax.set_title(f"Autocorrelation Plot for {selected_value_col}")
                            
                            # Convert to Streamlit-compatible format
                            st.pyplot(fig)
                            
                            st.markdown(
                                "**Interpreting the Autocorrelation Plot**: "
                                "Peaks in the plot suggest potential seasonal patterns. "
                                "If there's a recurring pattern of peaks at regular intervals, "
                                "this could indicate seasonality in your data."
                            )
                        except Exception as e:
                            st.error(f"Could not generate autocorrelation plot: {str(e)}")
            else:
                st.error("Could not create time series plot. Please check your data.")
        else:
            st.warning("No numeric columns available for time series analysis.")
    else:
        st.info(
            "No datetime columns detected in your dataset. "
            "Time series analysis requires at least one date/time column."
        )
    
    # Categorical data analysis
    st.subheader("Categorical Data Analysis")
    
    cat_cols = df.select_dtypes(exclude=['number', 'datetime']).columns.tolist()
    
    if cat_cols:
        cat_distributions = analyze_categorical_distributions(df)
        
        if cat_distributions:
            # Select a categorical column to analyze
            selected_cat_col = st.selectbox(
                "Select categorical column to analyze",
                list(cat_distributions.keys())
            )
            
            if selected_cat_col in cat_distributions:
                cat_info = cat_distributions[selected_cat_col]
                
                # Display basic info
                st.markdown(f"**Unique values**: {cat_info['unique_values']}")
                
                # Check if imbalanced
                if cat_info['is_imbalanced']:
                    st.warning(
                        f"This column is imbalanced. The dominant category '{cat_info['dominant_category']}' "
                        f"represents a large portion of the data."
                    )
                
                # Display distribution
                cat_dist_fig = px.bar(
                    x=list(cat_info['top_categories'].keys()),
                    y=list(cat_info['top_categories'].values()),
                    title=f"Top Categories in {selected_cat_col}",
                    labels={'x': selected_cat_col, 'y': 'Count'}
                )
                
                cat_dist_fig.update_layout(height=400)
                st.plotly_chart(cat_dist_fig, use_container_width=True, key=f"cat_dist_{selected_cat_col}")
                
                # Cross-tabulation with another categorical column
                if len(cat_cols) > 1:
                    st.subheader("Cross-Tabulation")
                    
                    other_cat_cols = [col for col in cat_cols if col != selected_cat_col]
                    cross_tab_col = st.selectbox(
                        "Select another categorical column for cross-tabulation",
                        other_cat_cols
                    )
                    
                    if cross_tab_col:
                        # Create cross-tabulation
                        cross_tab = pd.crosstab(
                            df[selected_cat_col], 
                            df[cross_tab_col],
                            normalize='index'  # Row percentages
                        )
                        
                        # Display as heatmap
                        cross_tab_fig = px.imshow(
                            cross_tab,
                            color_continuous_scale='RdBu_r',
                            title=f"Cross-Tabulation: {selected_cat_col} vs {cross_tab_col} (Row %)",
                            labels=dict(x=cross_tab_col, y=selected_cat_col, color="Proportion")
                        )
                        
                        cross_tab_fig.update_layout(height=500)
                        st.plotly_chart(cross_tab_fig, use_container_width=True, key=f"crosstab_{selected_cat_col}_{cross_tab_col}")
                        
                        # Chi-square test for independence
                        from scipy.stats import chi2_contingency
                        
                        contingency_table = pd.crosstab(df[selected_cat_col], df[cross_tab_col])
                        chi2, p, dof, expected = chi2_contingency(contingency_table)
                        
                        st.markdown(f"**Chi-square test for independence**")
                        st.markdown(f"- Chi-square statistic: {chi2:.4f}")
                        st.markdown(f"- p-value: {p:.4f}")
                        
                        if p < 0.05:
                            st.markdown(
                                "**Result**: There appears to be a significant relationship between "
                                f"'{selected_cat_col}' and '{cross_tab_col}' (p < 0.05)"
                            )
                        else:
                            st.markdown(
                                "**Result**: There does not appear to be a significant relationship between "
                                f"'{selected_cat_col}' and '{cross_tab_col}' (p >= 0.05)"
                            )
        else:
            st.info("No categorical data analysis available.")
    else:
        st.info("No categorical columns detected in your dataset.")

# Tab 5: Full Report
with tab5:
    st.subheader("Full EDA Report")
    
    st.markdown("""
    Generate a comprehensive Exploratory Data Analysis (EDA) report for your dataset.
    This may take a few moments depending on the size of your dataset.
    """)
    
    if st.button("Generate Full EDA Report"):
        with st.spinner("Generating full EDA report... This may take a minute."):
            # Generate pandas profiling report
            report_data = generate_quick_eda_report(df)
            
            if report_data:
                # Display report in an iframe
                report_html = base64.b64decode(report_data).decode('utf-8')
                
                # Create an iframe to display the report
                st.components.v1.html(
                    f"""
                    <iframe 
                        srcdoc="{report_html.replace('"', '&quot;')}" 
                        width="100%" 
                        height="800px" 
                        style="border:none;">
                    </iframe>
                    """,
                    height=800
                )
                
                # Download link
                from utils.export import generate_report_download_link
                report_link = generate_report_download_link(report_html, "eda_report.html")
                st.markdown(report_link, unsafe_allow_html=True)
            else:
                st.error("Failed to generate EDA report. Please try again or use individual analysis tabs.")

# Navigation buttons
st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    if st.button("← Back to Data Preview", key="back_to_preview"):
        st.switch_page("pages/02_Data_Preview.py")

with col2:
    if st.button("Continue to Data Transformation →", key="continue_to_transform"):
        st.switch_page("pages/04_Data_Transformation.py")

# Add a sidebar with explanations
with st.sidebar:
    st.header("EDA Explained")
    
    st.markdown("""
    ### What is EDA?
    
    Exploratory Data Analysis (EDA) is the process of analyzing and visualizing data to understand its main characteristics.
    
    ### Why is it important?
    
    - Reveals patterns, anomalies, and relationships
    - Helps identify data quality issues
    - Guides feature selection for modeling
    - Informs data transformation decisions
    
    ### Tips for EDA
    
    1. **Start with distributions** to understand individual variables
    
    2. **Look for correlations** to find relationships between variables
    
    3. **Identify outliers** that might affect your analysis
    
    4. **Check for missing values** and understand their patterns
    
    5. **Explore categorical data** to find imbalances and relationships
    """)
    
    st.markdown("---")
    st.markdown(
        "👉 Use the **AI-Suggested Visualizations** in the Overview tab "
        "for automated insights about your data."
    )
