import streamlit as st
import pandas as pd
import numpy as np
import json
import plotly.express as px
import plotly.graph_objects as go
from utils.ai_learning import display_learning_preferences_form, get_ai_learning_stats
from utils.access_control import check_access

def app():
    st.title("AI Learning System")
    
    # Check if user is logged in
    if "logged_in" not in st.session_state or not st.session_state.logged_in:
        st.warning("Please log in to access the AI Learning System.")
        st.button("Go to Login", on_click=lambda: st.switch_page("pages/login.py"))
        return
    
    # Get the current user's subscription tier
    user_tier = st.session_state.get("subscription_tier", "free")
    
    # Introduction text
    st.markdown("""
    The AI Learning System improves over time based on your feedback and interactions.
    As you use the app, it learns your preferences and builds a knowledge base to provide
    better insights, visualizations, and transformations.
    """)
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["Your AI Preferences", "Learning Progress", "How It Works"])
    
    with tab1:
        st.subheader("Your AI Learning Preferences")
        
        # Check if user has access to learning preferences
        if not check_access("ai", "learning_preferences"):
            st.warning("🔒 AI Learning Preferences require a higher subscription tier.")
            st.write("Upgrade your subscription to customize how the AI works for you.")
            
            # Show upgrade button
            if st.button("Upgrade Subscription"):
                st.switch_page("pages/subscription.py")
        else:
            # Display learning preferences form
            display_learning_preferences_form()
    
    with tab2:
        st.subheader("AI Learning Progress")
        
        # Check if user has access to learning stats
        if not check_access("ai", "learning_stats"):
            st.warning("🔒 AI Learning Statistics require a higher subscription tier.")
            st.write("Upgrade your subscription to view detailed AI learning statistics.")
            
            # Show upgrade button
            if st.button("Upgrade Subscription", key="upgrade_stats"):
                st.switch_page("pages/subscription.py")
        else:
            # Get AI learning statistics
            stats = get_ai_learning_stats()
            
            if not stats or (stats["feedback"]["total"] == 0 and stats["training"]["total_examples"] == 0):
                st.info("The AI Learning System is just getting started. As you and other users provide feedback, it will learn and improve.")
            else:
                # Display statistical cards in 3 columns
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Feedback", stats["feedback"]["total"])
                    st.metric("Average Rating", stats["feedback"]["avg_rating"])
                
                with col2:
                    st.metric("Positive Feedback", stats["feedback"]["positive_feedback"])
                    st.metric("Negative Feedback", stats["feedback"]["negative_feedback"])
                
                with col3:
                    st.metric("Training Examples", stats["training"]["total_examples"])
                    st.metric("Unique Transformations", stats["training"]["unique_transformations"])
                
                # Create feedback type distribution chart
                feedback_types = {
                    "Insights": stats["feedback"]["insight_feedback"],
                    "Visualizations": stats["feedback"]["visualization_feedback"],
                    "Transformations": stats["feedback"]["transformation_feedback"]
                }
                
                # Filter out zero values
                feedback_types = {k: v for k, v in feedback_types.items() if v > 0}
                
                if feedback_types:
                    st.subheader("Feedback Distribution")
                    
                    fig = px.pie(
                        values=list(feedback_types.values()),
                        names=list(feedback_types.keys()),
                        title="Feedback by Type",
                        hole=0.4
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                
                # Display rating distribution chart
                st.subheader("Your Contribution")
                
                # In a real implementation, this would be a query for the user's contributions
                # This is a placeholder/example visualization
                user_ratings = {
                    "Rating 5 ⭐⭐⭐⭐⭐": 7,
                    "Rating 4 ⭐⭐⭐⭐": 12,
                    "Rating 3 ⭐⭐⭐": 5,
                    "Rating 2 ⭐⭐": 2,
                    "Rating 1 ⭐": 1
                }
                
                fig2 = px.bar(
                    x=list(user_ratings.keys()),
                    y=list(user_ratings.values()),
                    title="Your Feedback Ratings",
                    labels={"x": "Rating", "y": "Count"}
                )
                
                fig2.update_layout(xaxis_tickangle=-45)
                
                st.plotly_chart(fig2, use_container_width=True)
    
    with tab3:
        st.subheader("How AI Learning Works")
        
        st.markdown("""
        ### The AI Learning System works in several ways:
        
        1. **User Feedback Loop**
           - Every time you provide feedback on insights, visualizations, or transformations
           - The system records what worked well and what didn't
           - Future suggestions are adjusted based on this feedback
        
        2. **Preference Learning**
           - Your preferences for data visualization styles, insight types, and more are stored
           - These preferences are incorporated into AI prompts
           - Results become more personalized to your needs
        
        3. **Transformation Outcomes**
           - When you apply data transformations, the system remembers the results
           - It learns which transformations work best for different data types
           - Future transformation recommendations improve based on this knowledge
        
        4. **Cross-Dataset Learning**
           - Patterns learned from one dataset can be applied to similar datasets
           - The system builds a knowledge base across all datasets
           - Common data cleaning and analysis patterns emerge over time
        
        ### Privacy and Security
        
        - All learning is done using anonymized data
        - Sensitive information is never stored in the learning system
        - Your specific data values remain private and secure
        """)
        
        st.info("Pro and Enterprise tier users get access to advanced personalization and learning features that significantly improve AI performance over time.")

if __name__ == "__main__":
    app()