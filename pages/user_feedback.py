import streamlit as st
import pandas as pd
from datetime import datetime
from utils.auth_redirect import require_auth
from utils.feedback import display_feedback_form, get_user_feedback_history
from utils.database import get_db_connection

def app():
    st.title("Your Feedback")
    
    # Check if user is logged in
    if not require_auth():
        return
    
    # Get user ID
    user_id = st.session_state.get("user_id")
    
    # Page layout with tabs
    tab1, tab2 = st.tabs(["Provide Feedback", "Your Feedback History"])
    
    with tab1:
        st.subheader("Help Us Improve Analytics Assist")
        
        st.markdown("""
        Your feedback is invaluable in helping us enhance Analytics Assist to better meet your needs.
        Please take a moment to share your thoughts on your experience with our platform.
        """)
        
        # Dropdown to select specific feature or area
        feedback_areas = [
            "Overall Experience",
            "Data Upload & Management",
            "Data Visualization",
            "Data Transformation",
            "AI-Powered Insights",
            "Export & Reporting",
            "User Interface",
            "Performance & Speed",
            "Documentation & Help",
            "Other"
        ]
        
        selected_area = st.selectbox(
            "What area would you like to provide feedback on?",
            feedback_areas
        )
        
        # Map selected area to feedback type and feature
        if selected_area == "Overall Experience":
            feedback_type = "general"
            feature = None
        elif selected_area == "Other":
            feedback_type = "other"
            feature = st.text_input("Please specify the feature or area:")
        else:
            feedback_type = "feature"
            feature = selected_area
        
        # Display the feedback form
        display_feedback_form(
            feedback_type=feedback_type,
            feature=feature,
            page="user_feedback",
            compact=False
        )
        
        # Additional information
        with st.expander("How we use your feedback"):
            st.markdown("""
            ### How We Use Your Feedback
            
            Your feedback directly influences our development roadmap and helps us prioritize new features and improvements.
            
            **What happens with your feedback:**
            - It's reviewed by our product team regularly
            - Common themes are identified and prioritized
            - Individual suggestions are evaluated for feasibility
            - Bugs and issues are addressed in our development sprints
            - Highly rated features receive additional development resources
            
            We're committed to continuously improving Analytics Assist based on your input.
            Thank you for taking the time to help us build a better product!
            """)
    
    with tab2:
        st.subheader("Your Previous Feedback")
        
        # Get user's feedback history
        feedback_history = get_user_feedback_history(user_id)
        
        if not feedback_history:
            st.info("You haven't provided any feedback yet. Your feedback history will appear here once you've submitted feedback.")
        else:
            # Convert to DataFrame for display
            df_feedback = pd.DataFrame(feedback_history)
            
            # Format created_at
            if 'created_at' in df_feedback.columns:
                df_feedback['created_at'] = pd.to_datetime(df_feedback['created_at']).dt.strftime('%Y-%m-%d %H:%M')
            
            # Display as a table
            st.dataframe(
                df_feedback[[
                    'created_at', 'feedback_type', 'rating', 
                    'feature', 'comments'
                ]].rename(columns={
                    'created_at': 'Date',
                    'feedback_type': 'Type',
                    'rating': 'Rating',
                    'feature': 'Feature/Area',
                    'comments': 'Comments'
                }),
                use_container_width=True,
                column_config={
                    "Rating": st.column_config.NumberColumn(
                        "Rating",
                        format="%d ⭐"
                    ),
                    "Date": st.column_config.TextColumn(
                        "Date"
                    )
                }
            )
            
            # Check for admin responses to feedback
            def _get_responses():
                conn = get_db_connection()
                cursor = conn.cursor()
                
                # Get all feedback_ids
                feedback_ids = [f['feedback_id'] for f in feedback_history]
                
                if not feedback_ids:
                    return []
                
                # Get responses
                placeholder = ','.join(['%s'] * len(feedback_ids))
                
                cursor.execute(
                    f"""
                    SELECT 
                        fr.feedback_id, fr.response_text, fr.created_at,
                        u.full_name as staff_name
                    FROM 
                        feedback_responses fr
                    LEFT JOIN
                        users u ON fr.staff_id = u.id
                    WHERE 
                        fr.feedback_id IN ({placeholder})
                    ORDER BY 
                        fr.created_at DESC
                    """, 
                    feedback_ids
                )
                
                columns = [desc[0] for desc in cursor.description]
                responses = []
                
                for row in cursor.fetchall():
                    responses.append(dict(zip(columns, row)))
                
                cursor.close()
                conn.close()
                
                return responses
            
            responses = _get_responses()
            
            if responses:
                st.subheader("Responses to Your Feedback")
                
                for response in responses:
                    with st.container(border=True):
                        st.markdown(f"**Date:** {response['created_at'].strftime('%Y-%m-%d %H:%M')}")
                        if response.get('staff_name'):
                            st.markdown(f"**From:** {response['staff_name']}")
                        st.markdown(response['response_text'])
            
            # Export option
            if st.button("Export Feedback History"):
                csv = df_feedback.to_csv(index=False)
                date_str = datetime.now().strftime('%Y%m%d')
                
                st.download_button(
                    label="Download as CSV",
                    data=csv,
                    file_name=f"feedback_history_{date_str}.csv",
                    mime="text/csv"
                )

if __name__ == "__main__":
    app()