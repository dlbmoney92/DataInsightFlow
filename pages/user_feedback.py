import streamlit as st
import pandas as pd
import datetime
import uuid
import json
from utils.database import get_db_connection
from utils.custom_navigation import render_navigation, initialize_navigation
from utils.auth_redirect import require_auth
from utils.feedback import display_feedback_form, get_user_feedback_history

# Set the page configuration
st.set_page_config(
    page_title="Feedback | Analytics Assist",
    page_icon="💬",
    layout="wide"
)

# Authentication check
require_auth()

# Hide Streamlit's default menu
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {
            display: none !important;
        }
    </style>
""", unsafe_allow_html=True)

# Initialize navigation
initialize_navigation()

# Render custom navigation bar
render_navigation()

def app():
    st.title("We Value Your Feedback")
    
    st.markdown("""
    <div style="background: linear-gradient(to right, #1e3c72, #2a5298); padding: 20px; border-radius: 10px; margin-bottom: 20px;">
        <h2 style="color: white; margin-bottom: 10px;">Help Us Improve Analytics Assist</h2>
        <p style="color: white; font-size: 1.1em;">
            Your feedback helps us create a better experience for you and all our users.
            Please share your thoughts, suggestions, and concerns.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create tabs for different types of feedback
    tab1, tab2, tab3, tab4 = st.tabs(["General Feedback", "Feature Requests", "Report Issues", "Your Feedback History"])
    
    with tab1:
        st.header("General Feedback")
        st.markdown("Let us know your overall experience with Analytics Assist.")
        
        # Display the feedback form
        display_feedback_form(
            feedback_type="general",
            page="user_feedback.py",
            compact=False
        )
    
    with tab2:
        st.header("Feature Requests")
        st.markdown("What features would you like to see added or improved?")
        
        # Create a form for feature requests
        with st.form("feature_request_form"):
            # Feature name
            feature_name = st.text_input("Feature Name", key="feature_name")
            
            # Feature description
            feature_description = st.text_area(
                "Please describe the feature you'd like to see:",
                height=150,
                key="feature_description"
            )
            
            # Priority rating
            priority = st.select_slider(
                "How important is this feature to you?",
                options=["Nice to have", "Important", "Very Important", "Critical"],
                value="Important",
                key="feature_priority"
            )
            
            # Use case
            use_case = st.text_area(
                "How would you use this feature? Please describe your use case:",
                height=100,
                key="use_case"
            )
            
            # Submit button
            submitted = st.form_submit_button("Submit Feature Request")
            
            if submitted:
                # Create metadata for the feature request
                metadata = {
                    "feature_name": feature_name,
                    "priority": priority,
                    "use_case": use_case,
                    "request_type": "feature"
                }
                
                # Map priority to numeric rating
                priority_map = {
                    "Nice to have": 3,
                    "Important": 4,
                    "Very Important": 5,
                    "Critical": 5
                }
                
                # Save the feedback
                from utils.feedback import save_feedback
                success = save_feedback(
                    feedback_type="feature_request",
                    rating=priority_map.get(priority, 3),
                    comments=feature_description,
                    feature=feature_name,
                    page="user_feedback.py",
                    metadata=metadata
                )
                
                if success:
                    st.success("Thank you for your feature request! We'll review it and consider it for future updates.")
                    # Clear form fields
                    st.session_state.feature_name = ""
                    st.session_state.feature_description = ""
                    st.session_state.feature_priority = "Important"
                    st.session_state.use_case = ""
                else:
                    st.error("There was an issue submitting your feature request. Please try again.")
    
    with tab3:
        st.header("Report Issues")
        st.markdown("Help us fix problems by reporting any issues you encounter.")
        
        # Create a form for bug reports
        with st.form("bug_report_form"):
            # Issue title
            issue_title = st.text_input("Issue Title", key="issue_title")
            
            # Issue description
            issue_description = st.text_area(
                "Please describe the issue in detail:",
                height=150,
                key="issue_description"
            )
            
            # Steps to reproduce
            steps_to_reproduce = st.text_area(
                "Steps to reproduce the issue:",
                height=100,
                key="steps_to_reproduce"
            )
            
            # Expected behavior
            expected_behavior = st.text_area(
                "What did you expect to happen?",
                height=80,
                key="expected_behavior"
            )
            
            # Actual behavior
            actual_behavior = st.text_area(
                "What actually happened?",
                height=80,
                key="actual_behavior"
            )
            
            # Severity rating
            severity = st.select_slider(
                "How severe is this issue?",
                options=["Minor", "Moderate", "Major", "Critical"],
                value="Moderate",
                key="severity"
            )
            
            # Submit button
            submitted = st.form_submit_button("Submit Bug Report")
            
            if submitted:
                # Create metadata for the bug report
                metadata = {
                    "issue_title": issue_title,
                    "steps_to_reproduce": steps_to_reproduce,
                    "expected_behavior": expected_behavior,
                    "actual_behavior": actual_behavior,
                    "severity": severity,
                    "report_type": "bug"
                }
                
                # Map severity to numeric rating
                severity_map = {
                    "Minor": 2,
                    "Moderate": 3,
                    "Major": 4,
                    "Critical": 5
                }
                
                # Save the feedback
                from utils.feedback import save_feedback
                success = save_feedback(
                    feedback_type="bug_report",
                    rating=severity_map.get(severity, 3),
                    comments=issue_description,
                    feature=issue_title,
                    page="user_feedback.py",
                    metadata=metadata
                )
                
                if success:
                    st.success("Thank you for reporting this issue! Our team will investigate it and work on a solution.")
                    # Clear form fields
                    st.session_state.issue_title = ""
                    st.session_state.issue_description = ""
                    st.session_state.steps_to_reproduce = ""
                    st.session_state.expected_behavior = ""
                    st.session_state.actual_behavior = ""
                    st.session_state.severity = "Moderate"
                else:
                    st.error("There was an issue submitting your bug report. Please try again.")
    
    with tab4:
        st.header("Your Feedback History")
        
        # Get user ID from session state
        user_id = st.session_state.get("user_id")
        
        if user_id:
            # Fetch feedback history for the logged-in user
            feedback_history = get_user_feedback_history(user_id)
            
            if feedback_history:
                # Create a DataFrame for display
                feedback_data = []
                for entry in feedback_history:
                    # Format data for display
                    feedback_type = entry.get('feedback_type', '').replace('_', ' ').title()
                    rating = entry.get('rating', 0)
                    created_at = entry.get('created_at', datetime.datetime.now()).strftime('%Y-%m-%d %H:%M')
                    feature = entry.get('feature', 'General')
                    comments = entry.get('comments', 'No comments provided')
                    
                    # Truncate long comments for display
                    if comments and len(comments) > 100:
                        comments = comments[:97] + "..."
                    
                    feedback_data.append({
                        'Date': created_at,
                        'Type': feedback_type,
                        'Rating': rating,
                        'Subject': feature,
                        'Comments': comments
                    })
                
                # Convert to DataFrame for display
                if feedback_data:
                    df = pd.DataFrame(feedback_data)
                    st.dataframe(df, use_container_width=True)
                    
                    # Option to view full details
                    with st.expander("View Full Feedback Details"):
                        selected_index = st.selectbox(
                            "Select feedback item to view complete details:",
                            range(len(feedback_history)),
                            format_func=lambda i: f"{feedback_data[i]['Date']} - {feedback_data[i]['Subject']}"
                        )
                        
                        if selected_index is not None:
                            selected_feedback = feedback_history[selected_index]
                            
                            st.subheader(f"Feedback Details: {selected_feedback.get('feature', 'General')}")
                            
                            # Display feedback details
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown(f"**Type:** {selected_feedback.get('feedback_type', '').replace('_', ' ').title()}")
                                st.markdown(f"**Date:** {selected_feedback.get('created_at').strftime('%Y-%m-%d %H:%M')}")
                                st.markdown(f"**Rating:** {selected_feedback.get('rating', 0)} / 5")
                            
                            with col2:
                                st.markdown(f"**Page:** {selected_feedback.get('page', 'Not specified')}")
                                if selected_feedback.get('metadata'):
                                    metadata = selected_feedback.get('metadata', {})
                                    if isinstance(metadata, str):
                                        try:
                                            metadata = json.loads(metadata)
                                        except:
                                            metadata = {}
                                    
                                    if isinstance(metadata, dict):
                                        if 'severity' in metadata:
                                            st.markdown(f"**Severity:** {metadata.get('severity', 'Not specified')}")
                                        if 'priority' in metadata:
                                            st.markdown(f"**Priority:** {metadata.get('priority', 'Not specified')}")
                            
                            # Display full comments
                            st.markdown("### Comments")
                            st.markdown(selected_feedback.get('comments', 'No comments provided'))
                            
                            # Display additional metadata if available
                            if selected_feedback.get('metadata'):
                                metadata = selected_feedback.get('metadata', {})
                                if isinstance(metadata, str):
                                    try:
                                        metadata = json.loads(metadata)
                                    except:
                                        metadata = {}
                                
                                if isinstance(metadata, dict):
                                    st.markdown("### Additional Information")
                                    
                                    if 'steps_to_reproduce' in metadata:
                                        st.markdown("**Steps to Reproduce:**")
                                        st.markdown(metadata.get('steps_to_reproduce', 'Not provided'))
                                    
                                    if 'expected_behavior' in metadata:
                                        st.markdown("**Expected Behavior:**")
                                        st.markdown(metadata.get('expected_behavior', 'Not provided'))
                                    
                                    if 'actual_behavior' in metadata:
                                        st.markdown("**Actual Behavior:**")
                                        st.markdown(metadata.get('actual_behavior', 'Not provided'))
                                    
                                    if 'use_case' in metadata:
                                        st.markdown("**Use Case:**")
                                        st.markdown(metadata.get('use_case', 'Not provided'))
                else:
                    st.info("Your feedback history is empty.")
            else:
                st.info("You haven't provided any feedback yet.")
        else:
            st.warning("Please log in to view your feedback history.")
    
    # Contact information
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; margin-top: 20px;">
        <h3>Need help or have questions?</h3>
        <p>
            Our support team is here to assist you. Please visit our 
            <a href="/pages/contact_us.py">Contact Us</a> page for more ways to reach us.
        </p>
    </div>
    """, unsafe_allow_html=True)

# Run the app
app()