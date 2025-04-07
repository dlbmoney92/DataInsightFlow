import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import json
import time
import uuid
from typing import List, Dict, Any, Optional, Tuple, Union

def generate_transformation_flow_chart(transformations: List[Dict[str, Any]]) -> go.Figure:
    """
    Generate a flow chart visualization of the transformation pipeline.
    
    Args:
        transformations: List of transformation dictionaries with keys like 
                        'name', 'description', 'transformation_details', etc.
    
    Returns:
        A Plotly figure object with the flow chart
    """
    if not transformations:
        # Create an empty flow chart with message
        fig = go.Figure()
        fig.add_annotation(
            text="No transformations applied yet",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=20)
        )
        fig.update_layout(
            height=300,
            plot_bgcolor='rgba(240, 240, 240, 0.8)',
            paper_bgcolor='rgba(0, 0, 0, 0)',
            margin=dict(l=20, r=20, t=30, b=20),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
        )
        return fig
    
    # Create node information
    nodes = []
    edges = []
    
    # Add the raw data node
    nodes.append({
        'id': 'raw_data',
        'label': 'Raw Data',
        'color': '#2E86C1',
        'shape': 'database',
        'x': 0,
        'y': 0
    })
    
    # Add transformation nodes and edges
    for i, transform in enumerate(transformations):
        transform_id = f"transform_{i}"
        nodes.append({
            'id': transform_id,
            'label': transform['name'],
            'title': transform.get('description', ''),
            'color': '#27AE60',
            'shape': 'box',
            'x': i + 1,
            'y': 0
        })
        
        # Connect from previous node
        if i == 0:
            source_id = 'raw_data'
        else:
            source_id = f"transform_{i-1}"
        
        edges.append({
            'from': source_id,
            'to': transform_id,
            'arrows': 'to'
        })
    
    # Add final output node
    nodes.append({
        'id': 'final_data',
        'label': 'Transformed Data',
        'color': '#8E44AD',
        'shape': 'database',
        'x': len(transformations) + 1,
        'y': 0
    })
    
    # Connect last transformation to final data
    if transformations:
        edges.append({
            'from': f"transform_{len(transformations)-1}",
            'to': 'final_data',
            'arrows': 'to'
        })
    else:
        edges.append({
            'from': 'raw_data',
            'to': 'final_data',
            'arrows': 'to'
        })
    
    # Create a Plotly figure for the flow chart
    fig = go.Figure()
    
    # Add nodes as scatter points
    node_x = [node['x'] for node in nodes]
    node_y = [node['y'] for node in nodes]
    node_text = [node['label'] for node in nodes]
    node_colors = [node['color'] for node in nodes]
    
    fig.add_trace(go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        marker=dict(
            size=30,
            color=node_colors,
            line=dict(width=2, color='DarkSlateGrey')
        ),
        text=node_text,
        textposition="bottom center",
        hoverinfo='text',
        name='Nodes'
    ))
    
    # Add edges as lines
    for edge in edges:
        start_idx = next(i for i, node in enumerate(nodes) if node['id'] == edge['from'])
        end_idx = next(i for i, node in enumerate(nodes) if node['id'] == edge['to'])
        
        fig.add_trace(go.Scatter(
            x=[nodes[start_idx]['x'], nodes[end_idx]['x']],
            y=[nodes[start_idx]['y'], nodes[end_idx]['y']],
            mode='lines+markers',
            line=dict(width=2, color='grey'),
            marker=dict(size=8, color='grey'),
            hoverinfo='none',
            showlegend=False
        ))
    
    # Update layout
    fig.update_layout(
        title='Data Transformation Flow',
        showlegend=False,
        hovermode='closest',
        margin=dict(l=5, r=5, t=50, b=30),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor='rgba(240, 240, 240, 0.8)',
        paper_bgcolor='rgba(0, 0, 0, 0)',
        height=300,
        autosize=True
    )
    
    return fig

def create_before_after_comparison(
    df_original: pd.DataFrame, 
    df_transformed: pd.DataFrame,
    transform_details: Dict[str, Any],
    columns_affected: List[str]
) -> Dict[str, Any]:
    """
    Create a visualization comparing the data before and after a transformation.
    
    Args:
        df_original: Original dataframe before transformation
        df_transformed: Transformed dataframe
        transform_details: Dictionary with transformation details
        columns_affected: List of columns affected by the transformation
    
    Returns:
        Dictionary with visualization data and metadata
    """
    visualizations = {}
    transform_type = transform_details.get('type', 'unknown')
    
    for column in columns_affected:
        if column not in df_original.columns or column not in df_transformed.columns:
            continue
            
        # Get column data
        original_data = df_original[column]
        transformed_data = df_transformed[column]
        
        # Determine column data type
        dtype = str(original_data.dtype)
        
        # Create different visualizations based on data type
        if pd.api.types.is_numeric_dtype(original_data):
            # For numeric data: histograms, boxplots, or scatterplots
            
            # Histogram comparison
            fig_hist = go.Figure()
            fig_hist.add_trace(go.Histogram(
                x=original_data,
                name='Original',
                opacity=0.7,
                marker_color='blue'
            ))
            fig_hist.add_trace(go.Histogram(
                x=transformed_data,
                name='Transformed',
                opacity=0.7,
                marker_color='green'
            ))
            fig_hist.update_layout(
                title_text=f'Distribution Change: {column}',
                xaxis_title=column,
                yaxis_title='Count',
                barmode='overlay'
            )
            
            # Boxplot comparison
            fig_box = go.Figure()
            fig_box.add_trace(go.Box(
                y=original_data,
                name='Original',
                marker_color='blue'
            ))
            fig_box.add_trace(go.Box(
                y=transformed_data,
                name='Transformed',
                marker_color='green'
            ))
            fig_box.update_layout(
                title_text=f'Statistical Change: {column}',
                yaxis_title=column
            )
            
            visualizations[column] = {
                'type': 'numeric',
                'histogram': fig_hist,
                'boxplot': fig_box,
                'summary': {
                    'original': {
                        'mean': original_data.mean(),
                        'median': original_data.median(),
                        'std': original_data.std(),
                        'min': original_data.min(),
                        'max': original_data.max()
                    },
                    'transformed': {
                        'mean': transformed_data.mean(),
                        'median': transformed_data.median(),
                        'std': transformed_data.std(),
                        'min': transformed_data.min(),
                        'max': transformed_data.max()
                    }
                }
            }
            
        elif pd.api.types.is_categorical_dtype(original_data) or pd.api.types.is_object_dtype(original_data):
            # For categorical data: bar charts, pie charts
            
            # Prepare data for visualization
            original_counts = original_data.value_counts().head(10)
            transformed_counts = transformed_data.value_counts().head(10)
            
            # Bar chart comparison
            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(
                x=original_counts.index,
                y=original_counts.values,
                name='Original',
                marker_color='blue'
            ))
            fig_bar.add_trace(go.Bar(
                x=transformed_counts.index,
                y=transformed_counts.values,
                name='Transformed',
                marker_color='green'
            ))
            fig_bar.update_layout(
                title_text=f'Category Distribution Change: {column}',
                xaxis_title=column,
                yaxis_title='Count',
                barmode='group'
            )
            
            visualizations[column] = {
                'type': 'categorical',
                'bar_chart': fig_bar,
                'summary': {
                    'original': {
                        'unique_values': original_data.nunique(),
                        'top_value': original_data.value_counts().index[0] if not original_data.value_counts().empty else None,
                        'top_count': original_data.value_counts().values[0] if not original_data.value_counts().empty else None
                    },
                    'transformed': {
                        'unique_values': transformed_data.nunique(),
                        'top_value': transformed_data.value_counts().index[0] if not transformed_data.value_counts().empty else None,
                        'top_count': transformed_data.value_counts().values[0] if not transformed_data.value_counts().empty else None
                    }
                }
            }
            
        elif pd.api.types.is_datetime64_dtype(original_data):
            # For datetime data: line charts or histograms by time period
            
            # Histogram comparison by month
            fig_time = go.Figure()
            
            try:
                original_month_counts = original_data.dt.month.value_counts().sort_index()
                transformed_month_counts = transformed_data.dt.month.value_counts().sort_index()
                
                fig_time.add_trace(go.Bar(
                    x=original_month_counts.index,
                    y=original_month_counts.values,
                    name='Original',
                    marker_color='blue'
                ))
                fig_time.add_trace(go.Bar(
                    x=transformed_month_counts.index,
                    y=transformed_month_counts.values,
                    name='Transformed',
                    marker_color='green'
                ))
                fig_time.update_layout(
                    title_text=f'Time Distribution Change: {column}',
                    xaxis_title='Month',
                    yaxis_title='Count',
                    barmode='group'
                )
                
                visualizations[column] = {
                    'type': 'datetime',
                    'time_chart': fig_time,
                    'summary': {
                        'original': {
                            'min_date': original_data.min(),
                            'max_date': original_data.max(),
                            'range_days': (original_data.max() - original_data.min()).days if not pd.isna(original_data.max()) and not pd.isna(original_data.min()) else None
                        },
                        'transformed': {
                            'min_date': transformed_data.min(),
                            'max_date': transformed_data.max(),
                            'range_days': (transformed_data.max() - transformed_data.min()).days if not pd.isna(transformed_data.max()) and not pd.isna(transformed_data.min()) else None
                        }
                    }
                }
            except:
                # Fallback for datetime conversion issues
                visualizations[column] = {
                    'type': 'datetime',
                    'error': 'Could not process datetime visualization',
                    'summary': {
                        'original': {
                            'data_type': str(original_data.dtype)
                        },
                        'transformed': {
                            'data_type': str(transformed_data.dtype)
                        }
                    }
                }
        
    return visualizations

def animate_transformation_process(
    df_original: pd.DataFrame, 
    df_final: pd.DataFrame,
    transformation: Dict[str, Any],
    affected_columns: List[str]
) -> None:
    """
    Create an animated visualization of a transformation being applied to the data.
    
    Args:
        df_original: Original dataframe before transformation
        df_final: Final dataframe after transformation
        transformation: Dictionary with transformation details
        affected_columns: List of columns affected by the transformation
    """
    # Generate a unique ID for this animation instance to avoid conflicts
    animation_id = str(uuid.uuid4())
    
    # Display animation title and explanation
    st.subheader("Transformation Animation")
    
    # Animation controls
    with st.expander("Animation Controls", expanded=True):
        col1, col2, col3 = st.columns([2,1,1])
        with col1:
            animation_speed = st.slider("Animation Speed", 
                                      min_value=1, max_value=10, value=5,
                                      key=f"speed_{animation_id}")
        with col2:
            play_button = st.button("Play Animation", key=f"play_{animation_id}")
        with col3:
            reset_button = st.button("Reset", key=f"reset_{animation_id}")
    
    # Animation state
    if f"animation_step_{animation_id}" not in st.session_state:
        st.session_state[f"animation_step_{animation_id}"] = 0
        
    # Create placeholder for the animation
    animation_placeholder = st.empty()
    
    # Reset animation if requested
    if reset_button:
        st.session_state[f"animation_step_{animation_id}"] = 0
    
    # Handle animation playback
    total_steps = 10  # We'll divide the transformation into this many steps
    
    if play_button:
        # Play the animation
        progress_bar = st.progress(0)
        
        for step in range(total_steps + 1):
            # Update session state
            st.session_state[f"animation_step_{animation_id}"] = step
            
            # Calculate the interpolated dataframe for this step
            interpolation_factor = step / total_steps
            df_interpolated = interpolate_dataframes(
                df_original, df_final, interpolation_factor, affected_columns)
            
            # Display the current state
            with animation_placeholder.container():
                display_transformation_frame(
                    df_original, df_interpolated, df_final, 
                    transformation, affected_columns, step, total_steps)
            
            # Update progress bar
            progress_bar.progress(step / total_steps)
            
            # Sleep to control animation speed (slower when speed is 1, faster when 10)
            delay = (11 - animation_speed) * 0.1
            time.sleep(delay)
    
    # Display current frame based on session state
    current_step = st.session_state[f"animation_step_{animation_id}"]
    interpolation_factor = current_step / total_steps if total_steps > 0 else 0
    df_interpolated = interpolate_dataframes(
        df_original, df_final, interpolation_factor, affected_columns)
    
    with animation_placeholder.container():
        display_transformation_frame(
            df_original, df_interpolated, df_final, 
            transformation, affected_columns, current_step, total_steps)

def interpolate_dataframes(
    df_original: pd.DataFrame, 
    df_final: pd.DataFrame, 
    factor: float, 
    columns: List[str]
) -> pd.DataFrame:
    """
    Create an intermediate dataframe that represents a step between original and final.
    
    Args:
        df_original: Original dataframe
        df_final: Final dataframe
        factor: Interpolation factor (0 to 1, where 0 is original and 1 is final)
        columns: Columns to interpolate
    
    Returns:
        Interpolated dataframe
    """
    # Create a copy of the original dataframe
    df_interpolated = df_original.copy()
    
    # For each affected column, calculate interpolated values
    for col in columns:
        if col not in df_original.columns or col not in df_final.columns:
            continue
            
        # Handle different data types
        if pd.api.types.is_numeric_dtype(df_original[col]) and pd.api.types.is_numeric_dtype(df_final[col]):
            # For numeric columns, do linear interpolation
            df_interpolated[col] = df_original[col] + factor * (df_final[col] - df_original[col])
        
        elif pd.api.types.is_categorical_dtype(df_original[col]) or pd.api.types.is_object_dtype(df_original[col]):
            # For categorical columns, gradually replace values
            # We'll randomly replace (factor * 100)% of values from original with values from final
            mask = np.random.random(len(df_original)) < factor
            df_interpolated.loc[mask, col] = df_final.loc[mask, col].values
        
        elif pd.api.types.is_datetime64_dtype(df_original[col]) and pd.api.types.is_datetime64_dtype(df_final[col]):
            # For datetime columns, we need to convert to timestamps for interpolation
            try:
                orig_ts = df_original[col].astype(np.int64)
                final_ts = df_final[col].astype(np.int64)
                interp_ts = orig_ts + factor * (final_ts - orig_ts)
                df_interpolated[col] = pd.to_datetime(interp_ts)
            except:
                # If there's an error, just keep the original values
                pass
    
    return df_interpolated

def display_transformation_frame(
    df_original: pd.DataFrame, 
    df_current: pd.DataFrame, 
    df_final: pd.DataFrame,
    transformation: Dict[str, Any],
    affected_columns: List[str],
    step: int,
    total_steps: int
) -> None:
    """
    Display a single frame of the transformation animation.
    
    Args:
        df_original: Original dataframe
        df_current: Current state of the dataframe during animation
        df_final: Final dataframe after transformation
        transformation: Transformation details
        affected_columns: List of affected columns
        step: Current animation step
        total_steps: Total number of animation steps
    """
    # Display transformation info
    st.markdown(f"**Transformation:** {transformation.get('name', 'Unknown transformation')}")
    st.markdown(f"**Affected Columns:** {', '.join(affected_columns)}")
    st.markdown(f"**Progress:** {int(step/total_steps*100)}% complete")
    
    # For each affected column, create a visualization of the transformation
    for col in affected_columns:
        if col not in df_original.columns or col not in df_final.columns:
            continue
        
        st.markdown(f"#### Column: {col}")
        
        # Determine column data type
        if pd.api.types.is_numeric_dtype(df_original[col]):
            # For numeric columns, show histograms and descriptive stats
            col1, col2 = st.columns(2)
            
            # Histogram comparison
            with col1:
                fig = go.Figure()
                fig.add_trace(go.Histogram(
                    x=df_original[col],
                    name='Original',
                    opacity=0.5,
                    marker_color='blue'
                ))
                fig.add_trace(go.Histogram(
                    x=df_current[col],
                    name='Current',
                    opacity=0.7,
                    marker_color='green'
                ))
                fig.update_layout(
                    title_text=f'Distribution Change',
                    xaxis_title=col,
                    yaxis_title='Count',
                    barmode='overlay',
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Statistics comparison
            with col2:
                stats_df = pd.DataFrame({
                    'Statistic': ['Mean', 'Median', 'Std Dev', 'Min', 'Max'],
                    'Original': [
                        df_original[col].mean(),
                        df_original[col].median(),
                        df_original[col].std(),
                        df_original[col].min(),
                        df_original[col].max()
                    ],
                    'Current': [
                        df_current[col].mean(),
                        df_current[col].median(),
                        df_current[col].std(),
                        df_current[col].min(),
                        df_current[col].max()
                    ],
                    'Final': [
                        df_final[col].mean(),
                        df_final[col].median(),
                        df_final[col].std(),
                        df_final[col].min(),
                        df_final[col].max()
                    ]
                })
                st.dataframe(stats_df, use_container_width=True)
                
                # Show a line chart of how metrics are changing
                metric_df = pd.DataFrame({
                    'Step': list(range(total_steps + 1)),
                    'Mean': [df_original[col].mean() + 
                             (i/total_steps) * (df_final[col].mean() - df_original[col].mean()) 
                             for i in range(total_steps + 1)],
                    'Median': [df_original[col].median() + 
                              (i/total_steps) * (df_final[col].median() - df_original[col].median())
                              for i in range(total_steps + 1)]
                })
                
                fig = px.line(metric_df, x='Step', y=['Mean', 'Median'])
                fig.add_vline(x=step, line_dash="dash", line_color="red")
                fig.update_layout(title_text='Metrics Progression', height=250)
                st.plotly_chart(fig, use_container_width=True)
        
        elif pd.api.types.is_categorical_dtype(df_original[col]) or pd.api.types.is_object_dtype(df_original[col]):
            # For categorical columns, show bar charts
            col1, col2 = st.columns(2)
            
            with col1:
                # Get top categories for visualization
                orig_counts = df_original[col].value_counts().head(7)
                curr_counts = df_current[col].value_counts().head(7)
                
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=orig_counts.index,
                    y=orig_counts.values,
                    name='Original',
                    marker_color='blue'
                ))
                fig.add_trace(go.Bar(
                    x=curr_counts.index,
                    y=curr_counts.values,
                    name='Current',
                    marker_color='green'
                ))
                fig.update_layout(
                    title_text='Category Distribution Change',
                    xaxis_title=col,
                    yaxis_title='Count',
                    barmode='group',
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Stats comparison
                stats_df = pd.DataFrame({
                    'Statistic': ['Unique Values', 'Most Common', 'Most Common Count'],
                    'Original': [
                        df_original[col].nunique(),
                        df_original[col].value_counts().index[0] if not df_original[col].value_counts().empty else 'N/A',
                        df_original[col].value_counts().values[0] if not df_original[col].value_counts().empty else 0
                    ],
                    'Current': [
                        df_current[col].nunique(),
                        df_current[col].value_counts().index[0] if not df_current[col].value_counts().empty else 'N/A',
                        df_current[col].value_counts().values[0] if not df_current[col].value_counts().empty else 0
                    ],
                    'Final': [
                        df_final[col].nunique(),
                        df_final[col].value_counts().index[0] if not df_final[col].value_counts().empty else 'N/A',
                        df_final[col].value_counts().values[0] if not df_final[col].value_counts().empty else 0
                    ]
                })
                st.dataframe(stats_df, use_container_width=True)
                
                # Unique values progression
                uniq_df = pd.DataFrame({
                    'Step': list(range(total_steps + 1)),
                    'Unique Values': [int(df_original[col].nunique() + 
                                     (i/total_steps) * (df_final[col].nunique() - df_original[col].nunique()))
                                     for i in range(total_steps + 1)]
                })
                
                fig = px.line(uniq_df, x='Step', y='Unique Values')
                fig.add_vline(x=step, line_dash="dash", line_color="red")
                fig.update_layout(title_text='Unique Values Progression', height=250)
                st.plotly_chart(fig, use_container_width=True)
    
    # Compare sample rows from original to current
    st.markdown("#### Sample Data Comparison")
    
    # Get a few rows to display (same rows from both dataframes)
    sample_size = min(5, len(df_original))
    sample_indices = np.random.choice(df_original.index, sample_size, replace=False)
    
    # Create a side-by-side view
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Original Data:**")
        st.dataframe(df_original.loc[sample_indices, affected_columns], use_container_width=True)
    
    with col2:
        st.markdown("**Current State:**")
        st.dataframe(df_current.loc[sample_indices, affected_columns], use_container_width=True)

def create_transformation_journey_visualization(
    transformations: List[Dict[str, Any]],
    original_df: pd.DataFrame,
    final_df: pd.DataFrame
) -> None:
    """
    Create a visual journey through all transformations applied to the dataset.
    
    Args:
        transformations: List of transformations
        original_df: Original dataframe
        final_df: Final dataframe
    """
    if not transformations:
        st.info("No transformations have been applied yet.")
        return
    
    st.subheader("Transformation Journey")
    
    # Create a timeline visualization
    timeline_data = []
    
    for i, transform in enumerate(transformations):
        timeline_data.append({
            'Step': i + 1,
            'Transformation': transform.get('name', f'Transformation {i+1}'),
            'Description': transform.get('description', 'No description'),
            'Columns': ", ".join(transform.get('affected_columns', [])),
            'Type': transform.get('transformation_details', {}).get('type', 'Unknown')
        })
    
    timeline_df = pd.DataFrame(timeline_data)
    
    # Display the timeline
    fig = px.timeline(
        timeline_df, 
        x_start='Step', 
        x_end=timeline_df['Step'] + 0.9,
        y='Transformation',
        color='Type',
        hover_data=['Description', 'Columns'],
        height=200 + len(transformations) * 30
    )
    
    fig.update_layout(
        title_text='Transformation Timeline',
        xaxis_title='Step',
        yaxis={
            'categoryarray': timeline_df['Transformation'].tolist(),
            'categoryorder': 'array'
        }
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Display key dataset metrics before and after
    st.markdown("#### Dataset Transformation Impact")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Rows", 
            value=f"{final_df.shape[0]:,}", 
            delta=final_df.shape[0] - original_df.shape[0]
        )
    
    with col2:
        st.metric(
            label="Columns", 
            value=f"{final_df.shape[1]:,}", 
            delta=final_df.shape[1] - original_df.shape[1]
        )
    
    with col3:
        # Calculate missing values percentage
        orig_missing_pct = (original_df.isna().sum().sum() / (original_df.shape[0] * original_df.shape[1])) * 100
        final_missing_pct = (final_df.isna().sum().sum() / (final_df.shape[0] * final_df.shape[1])) * 100
        
        st.metric(
            label="Missing Values", 
            value=f"{final_missing_pct:.2f}%", 
            delta=-(final_missing_pct - orig_missing_pct),
            delta_color="inverse"
        )
    
    # Create a column quality score visualization
    st.markdown("#### Column Quality Changes")
    
    # Calculate quality scores for each column (a simplified metric)
    quality_data = []
    
    # Get common columns between original and final
    common_columns = set(original_df.columns).intersection(set(final_df.columns))
    
    for col in common_columns:
        # Calculate completeness (1 - missing percentage)
        orig_completeness = 1 - (original_df[col].isna().sum() / len(original_df))
        final_completeness = 1 - (final_df[col].isna().sum() / len(final_df))
        
        # Calculate uniqueness (number of unique values / length)
        orig_uniqueness = min(1.0, original_df[col].nunique() / len(original_df)) if len(original_df) > 0 else 0
        final_uniqueness = min(1.0, final_df[col].nunique() / len(final_df)) if len(final_df) > 0 else 0
        
        # Simple quality score (average of completeness and uniqueness)
        orig_quality = (orig_completeness + orig_uniqueness) / 2
        final_quality = (final_completeness + final_uniqueness) / 2
        
        quality_data.append({
            'Column': col,
            'Original Quality': orig_quality * 100,
            'Final Quality': final_quality * 100,
            'Change': (final_quality - orig_quality) * 100
        })
    
    quality_df = pd.DataFrame(quality_data)
    
    # Sort by absolute change magnitude
    quality_df = quality_df.sort_values('Change', key=abs, ascending=False)
    
    # Display top 10 columns with most significant quality changes
    top_changes = quality_df.head(10)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=top_changes['Column'],
        x=top_changes['Original Quality'],
        name='Original Quality',
        orientation='h',
        marker=dict(color='lightblue')
    ))
    
    fig.add_trace(go.Bar(
        y=top_changes['Column'],
        x=top_changes['Final Quality'],
        name='Final Quality',
        orientation='h',
        marker=dict(color='darkblue')
    ))
    
    fig.update_layout(
        title='Top 10 Columns with Quality Changes',
        xaxis_title='Quality Score (%)',
        barmode='group',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)