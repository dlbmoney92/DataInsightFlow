import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from utils.auth_redirect import require_auth
from utils.feedback import get_feedback_stats
from utils.database import get_db_connection
import json

def check_admin_status():
    """Check if the current user has admin privileges."""
    if not st.session_state.get("logged_in", False):
        return False
    
    user_id = st.session_state.get("user_id")
    if not user_id:
        return False
    
    # Check if the user is an admin
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT is_admin FROM users WHERE id = %s
            """,
            (user_id,)
        )
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        return result and result[0]
    except Exception as e:
        st.error(f"Error checking admin status: {e}")
        return False

def get_detailed_feedback_data():
    """Get detailed feedback data for analysis."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all feedback with user info
        cursor.execute(
            """
            SELECT 
                f.id, f.feedback_id, f.feedback_type, f.rating, 
                f.comments, f.feature, f.page, f.metadata,
                f.created_at, u.email
            FROM 
                user_feedback f
            LEFT JOIN 
                users u ON f.user_id = u.id
            ORDER BY 
                f.created_at DESC
            """
        )
        
        # Convert to DataFrame
        columns = [desc[0] for desc in cursor.description]
        data = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        df = pd.DataFrame(data, columns=columns)
        
        # Parse metadata JSON
        def parse_metadata(metadata_json):
            if metadata_json:
                try:
                    return json.loads(metadata_json)
                except:
                    return {}
            return {}
        
        if 'metadata' in df.columns:
            df['parsed_metadata'] = df['metadata'].apply(parse_metadata)
        
        return df
    
    except Exception as e:
        st.error(f"Error retrieving feedback data: {e}")
        return pd.DataFrame()

def app():
    st.title("Feedback Analysis Dashboard")
    
    # Check if user is logged in
    if not require_auth():
        return
    
    # Check admin status
    if not check_admin_status():
        st.warning("You need administrator privileges to access this page.")
        return
    
    # Get feedback statistics
    stats = get_feedback_stats()
    detailed_data = get_detailed_feedback_data()
    
    # Dashboard layout with tabs
    tab1, tab2, tab3 = st.tabs(["Overview", "Detailed Analysis", "Raw Data"])
    
    with tab1:
        st.subheader("Feedback Overview")
        
        # Key metrics in columns
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Feedback", stats["total"])
        
        with col2:
            avg_rating = round(stats["avg_rating"], 1)
            st.metric("Average Rating", f"{avg_rating}/5")
        
        with col3:
            positive_pct = int((stats["positive_count"] / stats["total"]) * 100) if stats["total"] > 0 else 0
            st.metric("Positive Feedback", f"{positive_pct}%")
        
        with col4:
            negative_pct = int((stats["negative_count"] / stats["total"]) * 100) if stats["total"] > 0 else 0
            st.metric("Negative Feedback", f"{negative_pct}%")
        
        st.markdown("---")
        
        # Rating distribution chart
        if detailed_data.empty:
            st.info("No feedback data available yet.")
        else:
            rating_counts = detailed_data['rating'].value_counts().sort_index()
            
            fig = px.bar(
                x=rating_counts.index,
                y=rating_counts.values,
                labels={'x': 'Rating', 'y': 'Count'},
                title="Rating Distribution",
                color=rating_counts.index,
                color_continuous_scale=px.colors.sequential.Viridis
            )
            
            fig.update_layout(
                xaxis=dict(tickmode='linear', tick0=1, dtick=1),
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Feedback over time
            st.subheader("Feedback Trends")
            
            # Convert created_at to datetime if it's not already
            if 'created_at' in detailed_data.columns:
                detailed_data['created_at'] = pd.to_datetime(detailed_data['created_at'])
                
                # Group by day and calculate average rating
                daily_ratings = detailed_data.groupby(detailed_data['created_at'].dt.date)['rating'].agg(['mean', 'count'])
                daily_ratings = daily_ratings.reset_index()
                
                # Line chart for ratings over time
                fig = px.line(
                    daily_ratings,
                    x='created_at',
                    y='mean',
                    labels={'created_at': 'Date', 'mean': 'Average Rating'},
                    title="Average Rating Over Time",
                    markers=True
                )
                
                fig.update_layout(yaxis=dict(range=[0.5, 5.5]))
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Add volume overlay
                fig = px.bar(
                    daily_ratings,
                    x='created_at',
                    y='count',
                    labels={'created_at': 'Date', 'count': 'Number of Responses'},
                    title="Daily Feedback Volume"
                )
                
                st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader("Detailed Feedback Analysis")
        
        if detailed_data.empty:
            st.info("No feedback data available yet.")
        else:
            # Filters
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Date range filter
                min_date = detailed_data['created_at'].min().date()
                max_date = detailed_data['created_at'].max().date()
                
                date_range = st.date_input(
                    "Date Range",
                    value=(
                        max_date - timedelta(days=30),
                        max_date
                    ),
                    min_value=min_date,
                    max_value=max_date
                )
            
            with col2:
                # Feedback type filter
                feedback_types = ['All'] + list(detailed_data['feedback_type'].unique())
                selected_type = st.selectbox("Feedback Type", feedback_types)
            
            with col3:
                # Rating filter
                rating_filter = st.multiselect(
                    "Rating",
                    options=[1, 2, 3, 4, 5],
                    default=[]
                )
            
            # Apply filters
            filtered_data = detailed_data.copy()
            
            if len(date_range) == 2:
                start_date, end_date = date_range
                start_date = pd.Timestamp(start_date)
                end_date = pd.Timestamp(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
                filtered_data = filtered_data[(filtered_data['created_at'] >= start_date) & 
                                            (filtered_data['created_at'] <= end_date)]
            
            if selected_type != 'All':
                filtered_data = filtered_data[filtered_data['feedback_type'] == selected_type]
            
            if rating_filter:
                filtered_data = filtered_data[filtered_data['rating'].isin(rating_filter)]
            
            st.markdown(f"**Showing {len(filtered_data)} feedback entries**")
            
            # Feature analysis
            if 'feature' in filtered_data.columns:
                feature_data = filtered_data[filtered_data['feature'].notna()]
                
                if not feature_data.empty:
                    feature_ratings = feature_data.groupby('feature').agg({
                        'rating': ['mean', 'count']
                    }).reset_index()
                    
                    feature_ratings.columns = ['feature', 'avg_rating', 'count']
                    
                    # Sort by count then rating
                    feature_ratings = feature_ratings.sort_values(['count', 'avg_rating'], ascending=[False, False])
                    
                    st.subheader("Feature Ratings")
                    
                    # Horizontal bar chart
                    fig = px.bar(
                        feature_ratings,
                        y='feature',
                        x='avg_rating',
                        color='avg_rating',
                        text='count',
                        labels={'avg_rating': 'Average Rating', 'feature': 'Feature', 'count': 'Responses'},
                        color_continuous_scale=px.colors.sequential.Viridis,
                        range_x=[0, 5],
                        hover_data=['count'],
                        orientation='h'
                    )
                    
                    fig.update_layout(yaxis={'categoryorder': 'total ascending'})
                    
                    st.plotly_chart(fig, use_container_width=True)
            
            # Page analysis
            if 'page' in filtered_data.columns:
                page_data = filtered_data[filtered_data['page'].notna()]
                
                if not page_data.empty:
                    page_ratings = page_data.groupby('page').agg({
                        'rating': ['mean', 'count']
                    }).reset_index()
                    
                    page_ratings.columns = ['page', 'avg_rating', 'count']
                    
                    # Sort by count then rating
                    page_ratings = page_ratings.sort_values(['count', 'avg_rating'], ascending=[False, False])
                    
                    st.subheader("Page Ratings")
                    
                    # Horizontal bar chart
                    fig = px.bar(
                        page_ratings,
                        y='page',
                        x='avg_rating',
                        color='avg_rating',
                        text='count',
                        labels={'avg_rating': 'Average Rating', 'page': 'Page', 'count': 'Responses'},
                        color_continuous_scale=px.colors.sequential.Viridis,
                        range_x=[0, 5],
                        hover_data=['count'],
                        orientation='h'
                    )
                    
                    fig.update_layout(yaxis={'categoryorder': 'total ascending'})
                    
                    st.plotly_chart(fig, use_container_width=True)
            
            # Comments analysis (most recent)
            st.subheader("Recent Comments")
            
            comments_data = filtered_data[filtered_data['comments'].notna()]
            if not comments_data.empty:
                comments_data = comments_data.sort_values('created_at', ascending=False).head(10)
                
                for _, row in comments_data.iterrows():
                    with st.container(border=True):
                        col1, col2 = st.columns([4, 1])
                        
                        with col1:
                            st.write(f"**Rating:** {'⭐' * int(row['rating'])}")
                            if row.get('feature'):
                                st.write(f"**Feature:** {row['feature']}")
                            if row.get('page'):
                                st.write(f"**Page:** {row['page']}")
                            st.write(f"{row['comments']}")
                        
                        with col2:
                            st.write(f"**Date:** {row['created_at'].strftime('%Y-%m-%d')}")
                            if 'email' in row and row['email']:
                                st.write(f"**User:** {row['email']}")
            else:
                st.info("No comments available for the selected filters.")
    
    with tab3:
        st.subheader("Raw Feedback Data")
        
        if detailed_data.empty:
            st.info("No feedback data available yet.")
        else:
            # Display columns selection
            display_cols = st.multiselect(
                "Select columns to display",
                options=detailed_data.columns.tolist(),
                default=['id', 'rating', 'feedback_type', 'feature', 'page', 'comments', 'created_at', 'email']
            )
            
            if not display_cols:
                display_cols = ['id', 'rating', 'feedback_type', 'feature', 'page', 'comments', 'created_at']
            
            # Display the data
            st.dataframe(
                detailed_data[display_cols],
                use_container_width=True,
                column_config={
                    "rating": st.column_config.NumberColumn(
                        "Rating",
                        format="%d ⭐"
                    ),
                    "created_at": st.column_config.DatetimeColumn(
                        "Date",
                        format="YYYY-MM-DD HH:mm"
                    )
                }
            )
            
            # Export options
            export_format = st.radio("Export Format", ["CSV", "Excel"], horizontal=True)
            
            if st.button("Export Data"):
                if export_format == "CSV":
                    csv = detailed_data.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name=f"feedback_export_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                else:
                    # Export to Excel
                    excel_buffer = detailed_data.to_excel(index=False)
                    st.download_button(
                        label="Download Excel",
                        data=excel_buffer,
                        file_name=f"feedback_export_{datetime.now().strftime('%Y%m%d')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

if __name__ == "__main__":
    app()