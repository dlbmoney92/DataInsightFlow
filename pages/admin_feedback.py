import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import datetime
import io
from utils.custom_navigation import render_navigation, initialize_navigation
from utils.auth_redirect import require_auth
from utils.database import get_db_connection

# Set the page configuration
st.set_page_config(
    page_title="Feedback Dashboard | Analytics Assist",
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
    
    # Check if user is an admin based on is_admin flag
    cursor.execute("""
    SELECT is_admin FROM users WHERE id = %s
    """, (user_id,))
    
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if result and result[0] == 1:
        return True
    return False

def get_detailed_feedback_data():
    """Get detailed feedback data for analysis."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT 
        f.id, 
        f.user_id, 
        f.feedback_id, 
        f.feedback_type, 
        f.rating, 
        f.comments, 
        f.feature, 
        f.page, 
        f.metadata, 
        f.created_at,
        u.email,
        u.subscription_tier
    FROM 
        user_feedback f
    LEFT JOIN 
        users u ON f.user_id = u.id
    ORDER BY 
        f.created_at DESC
    """)
    
    columns = [desc[0] for desc in cursor.description]
    results = []
    
    for row in cursor.fetchall():
        feedback_entry = dict(zip(columns, row))
        
        # Parse metadata if it exists
        def parse_metadata(metadata_json):
            if not metadata_json:
                return {}
            try:
                if isinstance(metadata_json, str):
                    return json.loads(metadata_json)
                return metadata_json
            except:
                return {}
        
        feedback_entry['metadata'] = parse_metadata(feedback_entry.get('metadata'))
        
        # Format timestamps
        if 'created_at' in feedback_entry and feedback_entry['created_at']:
            if isinstance(feedback_entry['created_at'], str):
                try:
                    feedback_entry['created_at'] = datetime.datetime.fromisoformat(
                        feedback_entry['created_at'].replace('Z', '+00:00')
                    )
                except:
                    pass
        
        results.append(feedback_entry)
    
    cursor.close()
    conn.close()
    
    return results

def app():
    st.title("Feedback Analytics Dashboard")
    
    # Check if user has admin privileges
    is_admin = check_admin_status()
    
    if not is_admin:
        st.error("You don't have permission to access this page. Please contact an administrator if you believe this is a mistake.")
        st.stop()
    
    # Get all feedback data
    feedback_data = get_detailed_feedback_data()
    
    if not feedback_data:
        st.info("No feedback data has been collected yet.")
        st.stop()
    
    # Convert to DataFrame for analysis
    df = pd.DataFrame(feedback_data)
    
    # Create dashboard layout
    st.markdown("""
    <div style="background: linear-gradient(to right, #1e3c72, #2a5298); padding: 20px; border-radius: 10px; margin-bottom: 20px;">
        <h2 style="color: white; margin-bottom: 10px;">User Feedback Analytics</h2>
        <p style="color: white; font-size: 1.1em;">
            Analyze user feedback to understand satisfaction levels and identify areas for improvement.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Dashboard metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_feedback = len(df)
        st.metric("Total Feedback", total_feedback)
    
    with col2:
        avg_rating = df['rating'].mean() if 'rating' in df and not df['rating'].empty else 0
        st.metric("Avg Rating", f"{avg_rating:.1f}/5")
    
    with col3:
        positive_feedback = len(df[df['rating'] >= 4]) if 'rating' in df else 0
        positive_pct = (positive_feedback / total_feedback * 100) if total_feedback > 0 else 0
        st.metric("Positive Feedback", f"{positive_pct:.1f}%")
    
    with col4:
        unique_users = df['user_id'].nunique() if 'user_id' in df else 0
        st.metric("Unique Users", unique_users)
    
    # Create tabs for different analyses
    tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Ratings Analysis", "Feedback Details", "Export Data"])
    
    with tab1:
        st.header("Feedback Overview")
        
        # Create two columns layout
        col1, col2 = st.columns(2)
        
        with col1:
            # Feedback type distribution
            if 'feedback_type' in df.columns:
                feedback_counts = df['feedback_type'].value_counts().reset_index()
                feedback_counts.columns = ['Type', 'Count']
                
                # Clean up the type names
                feedback_counts['Type'] = feedback_counts['Type'].str.replace('_', ' ').str.title()
                
                fig = px.pie(
                    feedback_counts, 
                    values='Count', 
                    names='Type',
                    title='Feedback by Type',
                    hole=0.4,
                    color_discrete_sequence=px.colors.sequential.Blues_r
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Rating distribution
            if 'rating' in df.columns:
                rating_counts = df['rating'].value_counts().reset_index()
                rating_counts.columns = ['Rating', 'Count']
                rating_counts = rating_counts.sort_values('Rating')
                
                fig = px.bar(
                    rating_counts,
                    x='Rating',
                    y='Count',
                    title='Rating Distribution',
                    labels={'Count': 'Number of Feedback'},
                    color='Count',
                    color_continuous_scale='Blues'
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Feedback over time
        if 'created_at' in df.columns:
            # Convert to datetime if it's not already
            if not pd.api.types.is_datetime64_any_dtype(df['created_at']):
                df['created_at'] = pd.to_datetime(df['created_at'])
            
            # Create date column for grouping
            df['date'] = df['created_at'].dt.date
            
            # Group by date
            feedback_by_date = df.groupby('date').size().reset_index()
            feedback_by_date.columns = ['Date', 'Count']
            
            # Sort by date
            feedback_by_date = feedback_by_date.sort_values('Date')
            
            # Create timeseries chart
            fig = px.line(
                feedback_by_date,
                x='Date',
                y='Count',
                title='Feedback Over Time',
                labels={'Count': 'Number of Feedback', 'Date': 'Date Received'}
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.header("Ratings Analysis")
        
        # Filter controls
        col1, col2 = st.columns(2)
        
        with col1:
            if 'feedback_type' in df.columns:
                feedback_types = ['All'] + sorted(df['feedback_type'].unique().tolist())
                selected_type = st.selectbox('Filter by Feedback Type:', feedback_types)
        
        with col2:
            if 'subscription_tier' in df.columns:
                subscription_tiers = ['All'] + sorted(df['subscription_tier'].unique().tolist())
                selected_tier = st.selectbox('Filter by Subscription Tier:', subscription_tiers)
        
        # Apply filters
        filtered_df = df.copy()
        if selected_type != 'All':
            filtered_df = filtered_df[filtered_df['feedback_type'] == selected_type]
        if selected_tier != 'All':
            filtered_df = filtered_df[filtered_df['subscription_tier'] == selected_tier]
        
        # Display analytics
        col1, col2 = st.columns(2)
        
        with col1:
            # Average rating by feedback type
            if 'feedback_type' in df.columns and 'rating' in df.columns:
                avg_by_type = filtered_df.groupby('feedback_type')['rating'].mean().reset_index()
                avg_by_type.columns = ['Type', 'Average Rating']
                avg_by_type['Type'] = avg_by_type['Type'].str.replace('_', ' ').str.title()
                
                fig = px.bar(
                    avg_by_type,
                    x='Type',
                    y='Average Rating',
                    title='Average Rating by Feedback Type',
                    color='Average Rating',
                    color_continuous_scale='Blues'
                )
                fig.update_layout(yaxis_range=[0, 5])
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Average rating by subscription tier
            if 'subscription_tier' in df.columns and 'rating' in df.columns:
                avg_by_tier = filtered_df.groupby('subscription_tier')['rating'].mean().reset_index()
                avg_by_tier.columns = ['Subscription Tier', 'Average Rating']
                avg_by_tier['Subscription Tier'] = avg_by_tier['Subscription Tier'].str.capitalize()
                
                fig = px.bar(
                    avg_by_tier,
                    x='Subscription Tier',
                    y='Average Rating',
                    title='Average Rating by Subscription Tier',
                    color='Average Rating',
                    color_continuous_scale='Blues'
                )
                fig.update_layout(yaxis_range=[0, 5])
                st.plotly_chart(fig, use_container_width=True)
        
        # Rating trend over time
        if 'created_at' in filtered_df.columns and 'rating' in filtered_df.columns:
            # Convert to datetime if it's not already
            if not pd.api.types.is_datetime64_any_dtype(filtered_df['created_at']):
                filtered_df['created_at'] = pd.to_datetime(filtered_df['created_at'])
            
            # Create date column for grouping
            filtered_df['date'] = filtered_df['created_at'].dt.date
            
            # Group by date
            rating_by_date = filtered_df.groupby('date')['rating'].mean().reset_index()
            rating_by_date.columns = ['Date', 'Average Rating']
            
            # Sort by date
            rating_by_date = rating_by_date.sort_values('Date')
            
            # Create timeseries chart
            fig = px.line(
                rating_by_date,
                x='Date',
                y='Average Rating',
                title='Average Rating Over Time',
                labels={'Average Rating': 'Average Rating', 'Date': 'Date Received'}
            )
            fig.update_layout(yaxis_range=[0, 5])
            st.plotly_chart(fig, use_container_width=True)
        
        # Feature heatmap
        if 'feature' in filtered_df.columns and 'rating' in filtered_df.columns:
            # Group by feature 
            feature_stats = filtered_df.groupby('feature').agg(
                avg_rating=('rating', 'mean'),
                count=('rating', 'count')
            ).reset_index()
            
            # Sort by count descending
            feature_stats = feature_stats.sort_values('count', ascending=False).head(10)
            
            # Create bubble chart 
            fig = px.scatter(
                feature_stats,
                x='feature',
                y='avg_rating',
                size='count',
                title='Feature Rating Performance',
                labels={
                    'feature': 'Feature',
                    'avg_rating': 'Average Rating',
                    'count': 'Number of Feedback'
                },
                color='avg_rating',
                color_continuous_scale='RdYlGn',
                size_max=50
            )
            fig.update_layout(yaxis_range=[0, 5])
            st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.header("Feedback Details")
        
        # Search filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            search_text = st.text_input("Search in comments:", "")
        
        with col2:
            min_rating = st.number_input("Minimum Rating:", min_value=1, max_value=5, value=1)
        
        with col3:
            if 'feedback_type' in df.columns:
                feedback_types = ['All'] + sorted(df['feedback_type'].unique().tolist())
                search_type = st.selectbox('Feedback Type:', feedback_types, key="search_type")
        
        # Apply filters for search
        search_df = df.copy()
        
        if search_text:
            if 'comments' in search_df.columns:
                # Filter for comments containing the search text
                search_df = search_df[search_df['comments'].str.contains(search_text, case=False, na=False)]
        
        if 'rating' in search_df.columns:
            search_df = search_df[search_df['rating'] >= min_rating]
        
        if search_type != 'All':
            search_df = search_df[search_df['feedback_type'] == search_type]
        
        # Display feedback table
        if not search_df.empty:
            # Prepare display dataframe
            display_cols = ['id', 'feedback_type', 'rating', 'feature', 'comments', 'email', 'created_at']
            display_df = search_df[display_cols].copy() if all(col in search_df.columns for col in display_cols) else search_df.copy()
            
            # Format columns for display
            if 'feedback_type' in display_df.columns:
                display_df['feedback_type'] = display_df['feedback_type'].str.replace('_', ' ').str.title()
            
            if 'comments' in display_df.columns:
                display_df['comments'] = display_df['comments'].apply(lambda x: x[:100] + "..." if isinstance(x, str) and len(x) > 100 else x)
            
            # Rename columns for display
            column_map = {
                'id': 'ID',
                'feedback_type': 'Type',
                'rating': 'Rating',
                'feature': 'Feature',
                'comments': 'Comments',
                'email': 'User Email',
                'created_at': 'Date'
            }
            display_df.rename(columns=column_map, inplace=True)
            
            st.dataframe(display_df, use_container_width=True)
            
            # Detailed view
            if st.checkbox("Show detailed feedback"):
                selected_id = st.selectbox(
                    "Select feedback to view details:",
                    search_df['id'].tolist(),
                    format_func=lambda x: f"ID: {x} - {search_df[search_df['id'] == x]['created_at'].iloc[0].strftime('%Y-%m-%d %H:%M')} - {search_df[search_df['id'] == x]['feature'].iloc[0]}"
                )
                
                selected_feedback = search_df[search_df['id'] == selected_id].iloc[0]
                
                st.markdown("---")
                st.subheader(f"Feedback Details: {selected_feedback.get('feature', 'N/A')}")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**ID:** {selected_feedback.get('id', 'N/A')}")
                    st.markdown(f"**Type:** {selected_feedback.get('feedback_type', '').replace('_', ' ').title()}")
                    st.markdown(f"**Rating:** {selected_feedback.get('rating', 'N/A')}/5")
                    st.markdown(f"**User:** {selected_feedback.get('email', 'Anonymous')}")
                    st.markdown(f"**Subscription:** {selected_feedback.get('subscription_tier', 'N/A').capitalize()}")
                
                with col2:
                    st.markdown(f"**Date:** {selected_feedback.get('created_at').strftime('%Y-%m-%d %H:%M')}")
                    st.markdown(f"**Page:** {selected_feedback.get('page', 'N/A')}")
                    st.markdown(f"**Feature:** {selected_feedback.get('feature', 'N/A')}")
                
                st.markdown("### Comments")
                st.markdown(selected_feedback.get('comments', 'No comments provided'))
                
                # Display metadata if available
                metadata = selected_feedback.get('metadata', {})
                if metadata and isinstance(metadata, dict) and len(metadata) > 0:
                    st.markdown("### Additional Information")
                    
                    # Format the metadata for display
                    for key, value in metadata.items():
                        formatted_key = key.replace('_', ' ').title()
                        if isinstance(value, (dict, list)):
                            st.markdown(f"**{formatted_key}:**")
                            st.json(value)
                        else:
                            st.markdown(f"**{formatted_key}:** {value}")
                
                # Add response section
                with st.expander("Respond to this feedback", expanded=False):
                    response_text = st.text_area("Your response:", key=f"response_{selected_id}")
                    resolve_status = st.checkbox("Mark as resolved", key=f"resolve_{selected_id}")
                    
                    if st.button("Submit Response", key=f"submit_response_{selected_id}"):
                        # Save response to database
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        
                        try:
                            cursor.execute("""
                            INSERT INTO feedback_responses
                                (feedback_id, response_type, response_text, staff_id, resolved, created_at)
                            VALUES
                                (%s, %s, %s, %s, %s, %s)
                            """, (
                                selected_feedback.get('feedback_id'),
                                'admin_response',
                                response_text,
                                st.session_state.get('user_id'),
                                resolve_status,
                                datetime.datetime.now()
                            ))
                            
                            conn.commit()
                            st.success("Response submitted successfully!")
                        except Exception as e:
                            st.error(f"Error submitting response: {e}")
                        finally:
                            cursor.close()
                            conn.close()
        else:
            st.info("No feedback entries match your search criteria.")
    
    with tab4:
        st.header("Export Feedback Data")
        
        # Export options
        st.markdown("Download the feedback data for further analysis.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            export_format = st.selectbox(
                "Export Format:",
                ["CSV", "Excel", "JSON"],
                key="export_format"
            )
        
        with col2:
            date_range = st.date_input(
                "Date Range (optional):",
                value=(
                    df['created_at'].min().date() if 'created_at' in df.columns and not df.empty else datetime.date.today() - datetime.timedelta(days=30),
                    df['created_at'].max().date() if 'created_at' in df.columns and not df.empty else datetime.date.today()
                ),
                key="export_date_range"
            )
        
        # Prepare data for export
        export_df = df.copy()
        
        # Apply date filter if selected
        if len(date_range) == 2 and 'created_at' in export_df.columns:
            start_date, end_date = date_range
            # Convert end_date to end of day
            end_date = datetime.datetime.combine(end_date, datetime.time.max)
            export_df = export_df[(export_df['created_at'] >= pd.Timestamp(start_date)) & 
                                 (export_df['created_at'] <= pd.Timestamp(end_date))]
        
        # Convert metadata to string for export
        if 'metadata' in export_df.columns:
            export_df['metadata'] = export_df['metadata'].apply(
                lambda x: json.dumps(x) if isinstance(x, (dict, list)) else x
            )
        
        # Generate download button
        if not export_df.empty:
            if export_format == "CSV":
                csv_data = export_df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv_data,
                    file_name=f"feedback_data_{datetime.date.today().strftime('%Y-%m-%d')}.csv",
                    mime="text/csv"
                )
            elif export_format == "Excel":
                # Convert to Excel
                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                    export_df.to_excel(writer, index=False, sheet_name='Feedback Data')
                excel_data = excel_buffer.getvalue()
                
                st.download_button(
                    label="Download Excel",
                    data=excel_data,
                    file_name=f"feedback_data_{datetime.date.today().strftime('%Y-%m-%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            elif export_format == "JSON":
                # Convert to JSON
                json_data = export_df.to_json(orient='records', date_format='iso')
                st.download_button(
                    label="Download JSON",
                    data=json_data,
                    file_name=f"feedback_data_{datetime.date.today().strftime('%Y-%m-%d')}.json",
                    mime="application/json"
                )
        else:
            st.info("No data available for export with the selected filters.")

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