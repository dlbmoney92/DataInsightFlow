import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import datetime
import io
import calendar
from utils.custom_navigation import render_navigation, initialize_navigation
from utils.auth_redirect import require_auth
from utils.database import get_db_connection

# Set the page configuration
st.set_page_config(
    page_title="Site Analytics | Analytics Assist",
    page_icon="📊",
    layout="wide"
)

# Authentication check
require_auth()

def check_admin_status():
    """Check if the current user has admin privileges."""
    if not st.session_state.get("logged_in", False):
        return False
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    user_id = st.session_state.get("user_id")
    
    # Check if user is an admin (subscription tier = enterprise)
    cursor.execute("""
    SELECT subscription_tier FROM users WHERE id = %s
    """, (user_id,))
    
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if result and result[0] == "enterprise":
        return True
    return False

def get_user_signup_data():
    """Get user signup data for analytics."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT 
        id, 
        email, 
        subscription_tier, 
        created_at, 
        last_login,
        is_trial,
        trial_start_date,
        trial_end_date
    FROM 
        users
    ORDER BY 
        created_at DESC
    """)
    
    columns = [desc[0] for desc in cursor.description]
    results = []
    
    for row in cursor.fetchall():
        user_data = dict(zip(columns, row))
        results.append(user_data)
    
    cursor.close()
    conn.close()
    
    return results

def get_dataset_upload_data():
    """Get dataset upload statistics."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT 
        id,
        user_id,
        name,
        file_type,
        created_at,
        row_count,
        column_count
    FROM 
        datasets
    ORDER BY 
        created_at DESC
    """)
    
    columns = [desc[0] for desc in cursor.description]
    results = []
    
    for row in cursor.fetchall():
        dataset_data = dict(zip(columns, row))
        results.append(dataset_data)
    
    cursor.close()
    conn.close()
    
    return results

def get_feature_usage_data():
    """Get feature usage data (from user_feedback or other tables)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # This is a simplified query - in a real system, you'd have more detailed usage tracking
    cursor.execute("""
    SELECT 
        feature, 
        page, 
        COUNT(*) as usage_count
    FROM 
        user_feedback
    GROUP BY 
        feature, page
    ORDER BY 
        usage_count DESC
    """)
    
    columns = [desc[0] for desc in cursor.description]
    results = []
    
    for row in cursor.fetchall():
        feature_data = dict(zip(columns, row))
        results.append(feature_data)
    
    cursor.close()
    conn.close()
    
    return results

def app():
    st.title("Site Analytics Dashboard")
    
    # Check if user has admin privileges
    is_admin = check_admin_status()
    
    if not is_admin:
        st.error("You don't have permission to access this page. Please contact an administrator if you believe this is a mistake.")
        st.stop()
    
    # Get analytics data
    user_data = get_user_signup_data()
    dataset_data = get_dataset_upload_data()
    feature_usage_data = get_feature_usage_data()
    
    # Convert to DataFrames
    users_df = pd.DataFrame(user_data) if user_data else pd.DataFrame()
    datasets_df = pd.DataFrame(dataset_data) if dataset_data else pd.DataFrame()
    features_df = pd.DataFrame(feature_usage_data) if feature_usage_data else pd.DataFrame()
    
    # Dashboard header
    st.markdown("""
    <div style="background: linear-gradient(to right, #1e3c72, #2a5298); padding: 20px; border-radius: 10px; margin-bottom: 20px;">
        <h2 style="color: white; margin-bottom: 10px;">Analytics Assist - Site Analytics</h2>
        <p style="color: white; font-size: 1.1em;">
            Track usage patterns, user growth, and feature adoption to make data-driven decisions.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_users = len(users_df) if not users_df.empty else 0
        st.metric("Total Users", total_users)
    
    with col2:
        active_users = len(users_df[users_df['last_login'] >= (datetime.datetime.now() - datetime.timedelta(days=30))]) if not users_df.empty and 'last_login' in users_df.columns else 0
        st.metric("Active Users (30d)", active_users)
    
    with col3:
        total_datasets = len(datasets_df) if not datasets_df.empty else 0
        st.metric("Total Datasets", total_datasets)
    
    with col4:
        avg_dataset_size = int(datasets_df['row_count'].mean()) if not datasets_df.empty and 'row_count' in datasets_df.columns else 0
        st.metric("Avg Dataset Size", f"{avg_dataset_size:,} rows")
    
    # Create tabs for different analysis
    tab1, tab2, tab3, tab4 = st.tabs(["User Analytics", "Dataset Analytics", "Feature Usage", "Google Analytics"])
    
    with tab1:
        st.header("User Analytics")
        
        if users_df.empty:
            st.info("No user data available.")
        else:
            # Format datetime columns
            for col in ['created_at', 'last_login', 'trial_start_date', 'trial_end_date']:
                if col in users_df.columns:
                    users_df[col] = pd.to_datetime(users_df[col])
            
            # User growth over time
            if 'created_at' in users_df.columns:
                users_df['signup_month'] = users_df['created_at'].dt.to_period('M')
                user_growth = users_df.groupby('signup_month').size().reset_index()
                user_growth.columns = ['Month', 'New Users']
                user_growth['Month'] = user_growth['Month'].dt.to_timestamp()
                user_growth['Cumulative Users'] = user_growth['New Users'].cumsum()
                
                # Create chart
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=user_growth['Month'],
                    y=user_growth['New Users'],
                    name='New Users',
                    marker_color='rgb(55, 83, 109)'
                ))
                fig.add_trace(go.Scatter(
                    x=user_growth['Month'],
                    y=user_growth['Cumulative Users'],
                    name='Cumulative Users',
                    marker_color='rgb(26, 118, 255)',
                    mode='lines+markers'
                ))
                fig.update_layout(
                    title='User Growth Over Time',
                    xaxis_title='Month',
                    yaxis_title='Number of Users',
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    )
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Subscription tier distribution
            if 'subscription_tier' in users_df.columns:
                tier_counts = users_df['subscription_tier'].value_counts().reset_index()
                tier_counts.columns = ['Tier', 'Count']
                
                # Capitalize tiers
                tier_counts['Tier'] = tier_counts['Tier'].str.capitalize()
                
                fig = px.pie(
                    tier_counts, 
                    values='Count', 
                    names='Tier',
                    title='Users by Subscription Tier',
                    color_discrete_sequence=px.colors.sequential.Blues_r
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Trial conversion analysis
            col1, col2 = st.columns(2)
            
            with col1:
                if 'is_trial' in users_df.columns and 'trial_end_date' in users_df.columns:
                    # Calculate trials and conversions
                    total_trials = users_df['is_trial'].sum() if 'is_trial' in users_df.columns else 0
                    converted_trials = len(users_df[
                        (users_df['is_trial'] == 1) & 
                        (users_df['subscription_tier'] != 'free') & 
                        (users_df['trial_end_date'] < datetime.datetime.now())
                    ]) if 'is_trial' in users_df.columns and 'subscription_tier' in users_df.columns and 'trial_end_date' in users_df.columns else 0
                    
                    conversion_rate = (converted_trials / total_trials * 100) if total_trials > 0 else 0
                    
                    # Create gauge chart
                    fig = go.Figure(go.Indicator(
                        mode = "gauge+number",
                        value = conversion_rate,
                        title = {'text': "Trial Conversion Rate"},
                        gauge = {
                            'axis': {'range': [0, 100], 'ticksuffix': "%"},
                            'bar': {'color': "royalblue"},
                            'steps': [
                                {'range': [0, 30], 'color': "lightgray"},
                                {'range': [30, 70], 'color': "gray"},
                                {'range': [70, 100], 'color': "darkgray"}
                            ],
                        }
                    ))
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                if 'last_login' in users_df.columns:
                    # Calculate recency
                    now = datetime.datetime.now()
                    users_df['days_since_login'] = (now - users_df['last_login']).dt.days
                    
                    # Create bins
                    recency_bins = [0, 7, 30, 90, float('inf')]
                    recency_labels = ['Last 7 days', '8-30 days', '31-90 days', '90+ days']
                    
                    users_df['recency_group'] = pd.cut(
                        users_df['days_since_login'], 
                        bins=recency_bins, 
                        labels=recency_labels,
                        right=False
                    )
                    
                    recency_counts = users_df['recency_group'].value_counts().reset_index()
                    recency_counts.columns = ['Recency', 'Count']
                    recency_counts = recency_counts.sort_values(by='Recency')
                    
                    fig = px.bar(
                        recency_counts,
                        x='Recency',
                        y='Count',
                        title='User Recency Distribution',
                        color='Count',
                        color_continuous_scale='Blues'
                    )
                    st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.header("Dataset Analytics")
        
        if datasets_df.empty:
            st.info("No dataset data available.")
        else:
            # Format datetime columns
            if 'created_at' in datasets_df.columns:
                datasets_df['created_at'] = pd.to_datetime(datasets_df['created_at'])
            
            # Datasets created over time
            if 'created_at' in datasets_df.columns:
                datasets_df['upload_month'] = datasets_df['created_at'].dt.to_period('M')
                dataset_growth = datasets_df.groupby('upload_month').size().reset_index()
                dataset_growth.columns = ['Month', 'Datasets Uploaded']
                dataset_growth['Month'] = dataset_growth['Month'].dt.to_timestamp()
                
                fig = px.bar(
                    dataset_growth,
                    x='Month',
                    y='Datasets Uploaded',
                    title='Dataset Uploads Over Time',
                    color='Datasets Uploaded',
                    color_continuous_scale='Blues'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # File type distribution
            if 'file_type' in datasets_df.columns:
                filetype_counts = datasets_df['file_type'].value_counts().reset_index()
                filetype_counts.columns = ['File Type', 'Count']
                
                fig = px.pie(
                    filetype_counts, 
                    values='Count', 
                    names='File Type',
                    title='Dataset File Types',
                    color_discrete_sequence=px.colors.sequential.Viridis
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Dataset size distribution
            col1, col2 = st.columns(2)
            
            with col1:
                if 'row_count' in datasets_df.columns:
                    # Create bins for dataset sizes
                    size_bins = [0, 100, 1000, 10000, 100000, float('inf')]
                    size_labels = ['<100 rows', '100-1K rows', '1K-10K rows', '10K-100K rows', '100K+ rows']
                    
                    datasets_df['size_group'] = pd.cut(
                        datasets_df['row_count'], 
                        bins=size_bins, 
                        labels=size_labels,
                        right=False
                    )
                    
                    size_counts = datasets_df['size_group'].value_counts().reset_index()
                    size_counts.columns = ['Size', 'Count']
                    size_counts = size_counts.sort_values(by='Size')
                    
                    fig = px.bar(
                        size_counts,
                        x='Size',
                        y='Count',
                        title='Dataset Size Distribution',
                        color='Count',
                        color_continuous_scale='Blues'
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                if 'column_count' in datasets_df.columns:
                    # Create bins for column counts
                    column_bins = [0, 5, 10, 20, 50, float('inf')]
                    column_labels = ['<5 cols', '5-10 cols', '10-20 cols', '20-50 cols', '50+ cols']
                    
                    datasets_df['column_group'] = pd.cut(
                        datasets_df['column_count'], 
                        bins=column_bins, 
                        labels=column_labels,
                        right=False
                    )
                    
                    column_counts = datasets_df['column_group'].value_counts().reset_index()
                    column_counts.columns = ['Columns', 'Count']
                    column_counts = column_counts.sort_values(by='Columns')
                    
                    fig = px.bar(
                        column_counts,
                        x='Columns',
                        y='Count',
                        title='Dataset Column Distribution',
                        color='Count',
                        color_continuous_scale='Blues'
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            # Dataset uploads per user
            if 'user_id' in datasets_df.columns:
                datasets_per_user = datasets_df.groupby('user_id').size().reset_index()
                datasets_per_user.columns = ['User ID', 'Dataset Count']
                
                # Create bins
                count_bins = [0, 1, 2, 5, 10, float('inf')]
                count_labels = ['1 dataset', '2 datasets', '3-5 datasets', '6-10 datasets', '10+ datasets']
                
                count_distribution = pd.cut(
                    datasets_per_user['Dataset Count'], 
                    bins=count_bins, 
                    labels=count_labels,
                    right=False
                ).value_counts().reset_index()
                
                count_distribution.columns = ['Dataset Count', 'Number of Users']
                count_distribution = count_distribution.sort_values(by='Dataset Count')
                
                fig = px.bar(
                    count_distribution,
                    x='Dataset Count',
                    y='Number of Users',
                    title='Datasets per User Distribution',
                    color='Number of Users',
                    color_continuous_scale='Blues'
                )
                st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.header("Feature Usage")
        
        if features_df.empty:
            st.info("No feature usage data available.")
        else:
            # Top features by usage
            if 'feature' in features_df.columns and 'usage_count' in features_df.columns:
                top_features = features_df.sort_values('usage_count', ascending=False).head(10)
                
                fig = px.bar(
                    top_features,
                    x='feature',
                    y='usage_count',
                    title='Top 10 Features by Usage',
                    color='usage_count',
                    color_continuous_scale='Blues'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Usage by page
            if 'page' in features_df.columns:
                page_usage = features_df.groupby('page')['usage_count'].sum().reset_index()
                page_usage = page_usage.sort_values('usage_count', ascending=False)
                
                fig = px.pie(
                    page_usage, 
                    values='usage_count', 
                    names='page',
                    title='Feature Usage by Page',
                    color_discrete_sequence=px.colors.sequential.Blues_r
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Display raw feature usage data
            with st.expander("View Raw Feature Usage Data"):
                st.dataframe(features_df, use_container_width=True)
    
    with tab4:
        st.header("Google Analytics Integration")
        
        st.markdown("""
        The Google Analytics tracking code (ID: G-HGSH7TS3LX) has been integrated into the site.
        For detailed analytics, please visit the Google Analytics dashboard directly.
        """)
        
        # Display GA tracking info
        st.info("To view detailed analytics, visit [Google Analytics](https://analytics.google.com) and sign in with your Google account.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Analytics Reference")
            st.markdown("""
            **Tracking ID:** G-HGSH7TS3LX
            
            **Implementation:** The tracking code is integrated directly in the application's main template to track all page views and events.
            
            **Key Metrics Available in GA:**
            - User acquisition
            - Page views
            - Session duration
            - Bounce rate
            - Geographic distribution
            - Device usage
            - User journey/flow
            """)
        
        with col2:
            # Simulated GA widget (for presentation purposes)
            st.subheader("Quick GA Stats Preview")
            
            # This would be replaced with actual GA API data in a production implementation
            # For now, we'll use simulated data
            current_month = datetime.datetime.now().month
            previous_month = current_month - 1 if current_month > 1 else 12
            
            current_month_name = calendar.month_name[current_month]
            previous_month_name = calendar.month_name[previous_month]
            
            # Simulated metrics
            metrics = {
                'Users': {
                    'current': 152,
                    'previous': 128
                },
                'Sessions': {
                    'current': 304,
                    'previous': 267
                },
                'Pageviews': {
                    'current': 1876,
                    'previous': 1543
                },
                'Bounce Rate': {
                    'current': 32.4,
                    'previous': 35.8
                }
            }
            
            # Display simulated metrics with delta
            for metric, values in metrics.items():
                current = values['current']
                previous = values['previous']
                delta = ((current - previous) / previous * 100) if previous > 0 else 0
                
                suffix = '%' if metric == 'Bounce Rate' else ''
                delta_color = 'normal' if metric != 'Bounce Rate' else 'inverse'
                
                st.metric(
                    f"{metric} ({current_month_name})", 
                    f"{current}{suffix}",
                    f"{delta:.1f}% vs {previous_month_name}",
                    delta_color=delta_color
                )
        
        st.markdown("""
        **Note:** This dashboard provides basic analytics information. For more comprehensive analysis, 
        please access the full Google Analytics dashboard where you can create custom reports, 
        segment users, and analyze conversion funnels.
        """)
        
        st.warning("The above Google Analytics preview contains simulated data and is for illustration purposes only.")

# Run the app
if __name__ == "__main__":
    # Initialize navigation
    initialize_navigation()
    
    # Hide Streamlit's default menu
    st.markdown("""
        <style>
            [data-testid="stSidebarNav"] {
                display: none !important;
            }
        </style>
    """, unsafe_allow_html=True)
    
    # Render custom navigation bar
    render_navigation()
    
    # Run the app
    app()