import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import altair as alt
import json

def create_distribution_plot(df, column, plot_type='histogram'):
    """Create a distribution plot for a numeric column."""
    if df is None or df.empty or column not in df.columns:
        return None
    
    # Check if column is numeric
    if not pd.api.types.is_numeric_dtype(df[column]):
        return None
    
    if plot_type == 'histogram':
        fig = px.histogram(
            df, 
            x=column,
            title=f'Distribution of {column}',
            color_discrete_sequence=['#4F8BF9'],
            marginal='box'  # Add a box plot at the margins
        )
    elif plot_type == 'box':
        fig = px.box(
            df,
            y=column,
            title=f'Box Plot of {column}',
            color_discrete_sequence=['#4F8BF9']
        )
    elif plot_type == 'violin':
        fig = px.violin(
            df,
            y=column,
            title=f'Violin Plot of {column}',
            color_discrete_sequence=['#4F8BF9'],
            box=True  # Add a box plot inside the violin
        )
    else:
        return None
    
    # Add mean and median lines
    mean_val = df[column].mean()
    median_val = df[column].median()
    
    fig.add_vline(x=mean_val, line_dash='dash', line_color='red', annotation_text=f'Mean: {mean_val:.2f}')
    fig.add_vline(x=median_val, line_dash='dash', line_color='green', annotation_text=f'Median: {median_val:.2f}')
    
    fig.update_layout(
        height=400,
        margin=dict(l=10, r=10, t=30, b=10),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#262730')
    )
    
    return fig

def create_categorical_plot(df, column, plot_type='bar'):
    """Create a plot for a categorical column."""
    if df is None or df.empty or column not in df.columns:
        return None
    
    # Get value counts
    value_counts = df[column].value_counts().reset_index()
    value_counts.columns = [column, 'count']
    
    # Limit to top 20 categories if there are too many
    if len(value_counts) > 20:
        value_counts = value_counts.head(20)
        title_suffix = " (Top 20)"
    else:
        title_suffix = ""
    
    if plot_type == 'bar':
        fig = px.bar(
            value_counts,
            x=column,
            y='count',
            title=f'Counts of {column}{title_suffix}',
            color_discrete_sequence=['#4F8BF9'],
            text='count'  # Show count values on bars
        )
    elif plot_type == 'pie':
        fig = px.pie(
            value_counts,
            names=column,
            values='count',
            title=f'Proportion of {column}{title_suffix}',
            color_discrete_sequence=px.colors.qualitative.Plotly
        )
    elif plot_type == 'treemap':
        fig = px.treemap(
            value_counts,
            names=column,
            values='count',
            title=f'Treemap of {column}{title_suffix}',
            color='count',
            color_continuous_scale='Blues'
        )
    else:
        return None
    
    fig.update_layout(
        height=400,
        margin=dict(l=10, r=10, t=30, b=10),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#262730')
    )
    
    return fig

def create_correlation_heatmap(df):
    """Create a correlation heatmap for numeric columns."""
    if df is None or df.empty:
        return None
    
    # Select only numeric columns
    numeric_df = df.select_dtypes(include=['number'])
    
    if numeric_df.empty or numeric_df.shape[1] < 2:
        return None
    
    # Calculate correlation matrix
    corr_matrix = numeric_df.corr()
    
    # Create heatmap
    fig = px.imshow(
        corr_matrix,
        title='Correlation Matrix',
        color_continuous_scale='RdBu_r',
        zmin=-1,
        zmax=1,
        aspect='auto'
    )
    
    # Add correlation values as text
    annotations = []
    for i, row in enumerate(corr_matrix.values):
        for j, value in enumerate(row):
            if abs(value) > 0.5:  # Only annotate strong correlations
                annotations.append(
                    dict(
                        x=j,
                        y=i,
                        text=f'{value:.2f}',
                        showarrow=False,
                        font=dict(color='white' if abs(value) > 0.7 else 'black')
                    )
                )
    
    fig.update_layout(annotations=annotations)
    
    fig.update_layout(
        height=500,
        margin=dict(l=10, r=10, t=30, b=10),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#262730')
    )
    
    return fig

def create_scatter_plot(df, x_column, y_column, color_column=None, size_column=None):
    """Create a scatter plot between two numeric columns."""
    if (df is None or df.empty or 
        x_column not in df.columns or 
        y_column not in df.columns or
        not pd.api.types.is_numeric_dtype(df[x_column]) or
        not pd.api.types.is_numeric_dtype(df[y_column])):
        return None
    
    # Create scatter plot
    fig = px.scatter(
        df,
        x=x_column,
        y=y_column,
        color=color_column if color_column in df.columns else None,
        size=size_column if size_column in df.columns else None,
        title=f'{y_column} vs {x_column}',
        color_discrete_sequence=px.colors.qualitative.Plotly,
        opacity=0.7,
        hover_data=df.columns[:5]  # Include some columns in hover data
    )
    
    # Add trendline
    if color_column is None or color_column not in df.columns:
        fig.update_layout(
            height=500,
            margin=dict(l=10, r=10, t=30, b=10),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#262730')
        )
        
        # Calculate correlation
        correlation = df[[x_column, y_column]].corr().iloc[0, 1]
        fig.add_annotation(
            text=f'Correlation: {correlation:.2f}',
            x=0.95,
            y=0.05,
            xref='paper',
            yref='paper',
            showarrow=False,
            align='right',
            bgcolor='rgba(255, 255, 255, 0.8)'
        )
    
    return fig

def create_time_series_plot(df, date_column, value_column, group_column=None):
    """Create a time series plot."""
    if (df is None or df.empty or 
        date_column not in df.columns or 
        value_column not in df.columns or
        not pd.api.types.is_numeric_dtype(df[value_column])):
        return None
    
    # Convert to datetime if not already
    if not pd.api.types.is_datetime64_dtype(df[date_column]):
        try:
            df = df.copy()
            df[date_column] = pd.to_datetime(df[date_column])
        except:
            return None
    
    # Group by date and category if provided
    if group_column is not None and group_column in df.columns:
        # Create line plot with color by group
        fig = px.line(
            df,
            x=date_column,
            y=value_column,
            color=group_column,
            title=f'{value_column} over time by {group_column}',
            color_discrete_sequence=px.colors.qualitative.Plotly
        )
    else:
        # Create simple line plot
        fig = px.line(
            df,
            x=date_column,
            y=value_column,
            title=f'{value_column} over time',
            color_discrete_sequence=['#4F8BF9']
        )
    
    fig.update_layout(
        height=400,
        margin=dict(l=10, r=10, t=30, b=10),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#262730')
    )
    
    return fig

def create_pair_plot(df, columns=None, color_column=None):
    """Create a pair plot (scatter plot matrix) for selected columns."""
    if df is None or df.empty:
        return None
    
    # Select only numeric columns if not specified
    if columns is None:
        numeric_df = df.select_dtypes(include=['number'])
        if numeric_df.shape[1] < 2:
            return None
        columns = numeric_df.columns[:4]  # Limit to first 4 numeric columns
    else:
        # Verify all columns exist and are numeric
        valid_columns = []
        for col in columns:
            if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
                valid_columns.append(col)
        
        if len(valid_columns) < 2:
            return None
        columns = valid_columns
    
    # Create pair plot
    fig = px.scatter_matrix(
        df,
        dimensions=columns,
        color=color_column if color_column in df.columns else None,
        title='Pair Plot',
        color_discrete_sequence=px.colors.qualitative.Plotly,
        opacity=0.7
    )
    
    fig.update_layout(
        height=700,
        margin=dict(l=10, r=10, t=30, b=10),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#262730')
    )
    
    return fig

def create_missing_values_heatmap(df):
    """Create a heatmap showing missing values in the dataset."""
    if df is None or df.empty:
        return None
    
    # Create a boolean mask for missing values
    missing_mask = df.isna().T
    
    # Create heatmap
    fig = px.imshow(
        missing_mask,
        color_continuous_scale=[[0, 'white'], [1, 'red']],
        title='Missing Values Heatmap',
        labels=dict(x='Row Index', y='Column', color='Missing'),
        aspect='auto'
    )
    
    # Add summary statistics
    missing_counts = df.isna().sum()
    missing_pcts = (missing_counts / len(df) * 100).round(2)
    
    annotations = []
    for i, (col, pct) in enumerate(zip(missing_counts.index, missing_pcts)):
        if pct > 0:  # Only annotate columns with missing values
            annotations.append(
                dict(
                    x=len(df) - 1,  # Far right
                    y=i,
                    text=f'{pct:.1f}%',
                    xanchor='right',
                    yanchor='middle',
                    showarrow=False,
                    font=dict(color='black', size=10),
                    bgcolor='rgba(255, 255, 255, 0.8)'
                )
            )
    
    fig.update_layout(annotations=annotations)
    
    fig.update_layout(
        height=500,
        margin=dict(l=10, r=10, t=30, b=10),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#262730'),
        xaxis=dict(showticklabels=False)  # Hide row indices
    )
    
    return fig

def create_visualization_from_suggestion(df, suggestion):
    """Create a visualization based on an AI suggestion."""
    if df is None or df.empty or not suggestion:
        return None
    
    chart_type = suggestion.get('chart_type', '').lower()
    columns = suggestion.get('columns', [])
    title = suggestion.get('title', 'Visualization')
    
    # Verify that all columns exist
    for col in columns:
        if col not in df.columns:
            return None
    
    # Create visualization based on chart type
    if chart_type == 'histogram' and len(columns) >= 1:
        return create_distribution_plot(df, columns[0], 'histogram')
    
    elif chart_type == 'bar_chart' and len(columns) >= 1:
        return create_categorical_plot(df, columns[0], 'bar')
    
    elif chart_type == 'pie_chart' and len(columns) >= 1:
        return create_categorical_plot(df, columns[0], 'pie')
    
    elif chart_type == 'scatter_plot' and len(columns) >= 2:
        color_col = columns[2] if len(columns) > 2 else None
        size_col = columns[3] if len(columns) > 3 else None
        return create_scatter_plot(df, columns[0], columns[1], color_col, size_col)
    
    elif chart_type == 'line_chart' and len(columns) >= 2:
        group_col = columns[2] if len(columns) > 2 else None
        return create_time_series_plot(df, columns[0], columns[1], group_col)
    
    elif chart_type == 'correlation_heatmap':
        return create_correlation_heatmap(df)
    
    elif chart_type == 'missing_values_heatmap':
        return create_missing_values_heatmap(df)
    
    elif chart_type == 'pair_plot' and len(columns) >= 2:
        color_col = columns[-1] if len(columns) > 4 else None
        return create_pair_plot(df, columns[:4], color_col)
    
    elif chart_type == 'box_plot' and len(columns) >= 1:
        return create_distribution_plot(df, columns[0], 'box')
    
    else:
        return None
