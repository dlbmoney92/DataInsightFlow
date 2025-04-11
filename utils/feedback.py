import streamlit as st
import datetime
import uuid
from typing import Optional, Dict, Any, List
import json
import os
from utils.database import get_db_connection

def initialize_feedback_database():
    """Create the feedback tables if they don't exist."""
    def _initialize_operation():
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create feedback table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_feedback (
            id SERIAL PRIMARY KEY,
            user_id INTEGER,
            feedback_id TEXT NOT NULL,
            feedback_type TEXT NOT NULL,
            rating INTEGER NOT NULL,
            comments TEXT,
            feature TEXT,
            page TEXT,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create feedback_responses table for tracking follow-up actions
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS feedback_responses (
            id SERIAL PRIMARY KEY,
            feedback_id TEXT NOT NULL,
            response_type TEXT NOT NULL,
            response_text TEXT,
            staff_id INTEGER,
            resolved BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        conn.commit()
        cursor.close()
        conn.close()
    
    try:
        _initialize_operation()
        return True
    except Exception as e:
        st.error(f"Error initializing feedback database: {e}")
        return False

def save_feedback(
    feedback_type: str,
    rating: int,
    comments: Optional[str] = None,
    feature: Optional[str] = None,
    page: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Save user feedback to the database.
    
    Parameters:
    - feedback_type: Type of feedback (e.g., 'usability', 'feature', 'bug', 'general')
    - rating: User rating (1-5)
    - comments: Optional user comments
    - feature: Specific feature being rated (if applicable)
    - page: Page where feedback was collected
    - metadata: Any additional contextual information
    
    Returns:
    - Success status (bool)
    """
    # Generate a unique ID for the feedback
    feedback_id = str(uuid.uuid4())
    
    # Get user ID if available
    user_id = st.session_state.get("user_id", None)
    
    # Serialize metadata if provided
    metadata_json = None
    if metadata:
        metadata_json = json.dumps(metadata)
    
    def _save_feedback_operation():
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO user_feedback 
            (user_id, feedback_id, feedback_type, rating, comments, feature, page, metadata, created_at)
        VALUES 
            (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            user_id,
            feedback_id,
            feedback_type,
            rating,
            comments,
            feature,
            page,
            metadata_json,
            datetime.datetime.now()
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
    
    try:
        return _save_feedback_operation()
    except Exception as e:
        st.error(f"Error saving feedback: {e}")
        return False

def get_feedback_stats(feedback_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Get statistics about collected feedback.
    
    Parameters:
    - feedback_type: Optional filter by feedback type
    
    Returns:
    - Dictionary with feedback statistics
    """
    def _get_stats_operation():
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Base query for all feedback
        query = "SELECT COUNT(*) as total FROM user_feedback"
        params = []
        
        # Add filter if feedback_type is provided
        if feedback_type:
            query += " WHERE feedback_type = %s"
            params.append(feedback_type)
            
        cursor.execute(query, params)
        total = cursor.fetchone()[0]
        
        # Get average rating
        avg_query = "SELECT AVG(rating) FROM user_feedback"
        if feedback_type:
            avg_query += " WHERE feedback_type = %s"
        
        cursor.execute(avg_query, params)
        avg_rating = cursor.fetchone()[0] or 0
        
        # Get counts by rating
        rating_query = "SELECT rating, COUNT(*) FROM user_feedback"
        if feedback_type:
            rating_query += " WHERE feedback_type = %s"
        rating_query += " GROUP BY rating ORDER BY rating"
        
        cursor.execute(rating_query, params)
        rating_counts = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Count positive ratings (4-5)
        positive_query = "SELECT COUNT(*) FROM user_feedback WHERE rating >= 4"
        if feedback_type:
            positive_query += " AND feedback_type = %s"
            
        cursor.execute(positive_query, params)
        positive_count = cursor.fetchone()[0]
        
        # Count negative ratings (1-2)
        negative_query = "SELECT COUNT(*) FROM user_feedback WHERE rating <= 2"
        if feedback_type:
            negative_query += " AND feedback_type = %s"
            
        cursor.execute(negative_query, params)
        negative_count = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return {
            "total": total,
            "avg_rating": avg_rating,
            "rating_counts": rating_counts,
            "positive_count": positive_count,
            "negative_count": negative_count
        }
    
    try:
        return _get_stats_operation()
    except Exception as e:
        st.error(f"Error retrieving feedback stats: {e}")
        return {
            "total": 0,
            "avg_rating": 0,
            "rating_counts": {},
            "positive_count": 0,
            "negative_count": 0
        }

def get_user_feedback_history(user_id: int) -> List[Dict[str, Any]]:
    """
    Get feedback history for a specific user.
    
    Parameters:
    - user_id: User ID to get feedback for
    
    Returns:
    - List of feedback entries
    """
    def _get_history_operation():
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT 
            id, feedback_id, feedback_type, rating, comments, feature, page, metadata, created_at
        FROM 
            user_feedback
        WHERE 
            user_id = %s
        ORDER BY 
            created_at DESC
        ''', (user_id,))
        
        columns = [desc[0] for desc in cursor.description]
        result = []
        
        for row in cursor.fetchall():
            feedback_entry = dict(zip(columns, row))
            
            # Parse metadata if it exists
            if feedback_entry.get('metadata'):
                try:
                    feedback_entry['metadata'] = json.loads(feedback_entry['metadata'])
                except:
                    feedback_entry['metadata'] = {}
                    
            result.append(feedback_entry)
        
        cursor.close()
        conn.close()
        
        return result
    
    try:
        return _get_history_operation()
    except Exception as e:
        st.error(f"Error retrieving feedback history: {e}")
        return []

def display_feedback_form(
    feedback_type: str = "general",
    feature: Optional[str] = None,
    page: Optional[str] = None,
    compact: bool = False
):
    """
    Display a feedback form and handle submission.
    
    Parameters:
    - feedback_type: Type of feedback (default: 'general')
    - feature: Specific feature being rated (if applicable)
    - page: Page where feedback was collected (default: current page)
    - compact: Whether to show a more compact version of the form
    """
    # If page is not provided, try to get it from the URL
    if not page and "page" in st.experimental_get_query_params():
        page = st.experimental_get_query_params()["page"][0]
    elif not page:
        # Default to current script name
        import inspect
        import os
        current_frame = inspect.currentframe()
        frame_info = inspect.getframeinfo(current_frame.f_back)
        page = os.path.basename(frame_info.filename)
    
    # Use either a form or an expander based on compact parameter
    container = st.form if not compact else st.expander
    
    with container("Share Your Feedback" if not compact else "Feedback"):
        # Rating
        rating = st.slider(
            "Rate your experience:",
            min_value=1,
            max_value=5,
            value=5,
            help="1 = Poor, 5 = Excellent",
            key=f"rating_{feedback_type}_{feature if feature else ''}_{page}"
        )
        
        # Comments
        comments = st.text_area(
            "Comments (optional):",
            key=f"comments_{feedback_type}_{feature if feature else ''}_{page}",
            height=100 if not compact else 80
        )
        
        # Metadata collection
        metadata = {
            "user_agent": st.session_state.get("user_agent", None),
            "screen_size": st.session_state.get("screen_size", None),
            "app_version": st.session_state.get("app_version", "1.0.0")
        }
        
        # Submit button (within the form)
        submit_button = st.form_submit_button("Submit Feedback")
        
        if submit_button:
            success = save_feedback(
                feedback_type=feedback_type,
                rating=rating,
                comments=comments,
                feature=feature,
                page=page,
                metadata=metadata
            )
            
            if success:
                st.success("Thank you for your feedback! We greatly appreciate your input.")
                # Clear form fields
                st.session_state[f"rating_{feedback_type}_{feature if feature else ''}_{page}"] = 5
                st.session_state[f"comments_{feedback_type}_{feature if feature else ''}_{page}"] = ""
            else:
                st.error("There was an issue saving your feedback. Please try again later.")

def display_quick_feedback(feature: str, position: str = "sidebar"):
    """
    Display a very compact feedback mechanism (thumbs up/down) in the sidebar or main area.
    
    Parameters:
    - feature: The feature being rated
    - position: Where to display the feedback ('sidebar' or 'main')
    """
    container = st.sidebar if position == "sidebar" else st
    
    with container:
        st.write("Quick feedback:")
        col1, col2 = st.columns(2)
        
        with col1:
            thumbs_up = st.button("👍 Helpful", key=f"thumbs_up_{feature}")
            if thumbs_up:
                success = save_feedback(
                    feedback_type="quick",
                    rating=5,
                    feature=feature,
                    page=None,
                    metadata={"quick_feedback": "positive"}
                )
                if success:
                    st.success("Thanks for your feedback!")
        
        with col2:
            thumbs_down = st.button("👎 Not helpful", key=f"thumbs_down_{feature}")
            if thumbs_down:
                # Show a follow-up form when the user gives negative feedback
                with st.expander("Help us improve", expanded=True):
                    comments = st.text_area("What could be improved?", key=f"improve_{feature}")
                    send = st.button("Send", key=f"send_improve_{feature}")
                    
                    if send:
                        success = save_feedback(
                            feedback_type="quick",
                            rating=1,
                            comments=comments,
                            feature=feature,
                            page=None,
                            metadata={"quick_feedback": "negative"}
                        )
                        if success:
                            st.success("Thank you for helping us improve!")

def display_nps_survey():
    """Display a Net Promoter Score (NPS) survey to measure customer loyalty."""
    # Check if we should show the survey (we don't want to annoy users)
    def _check_last_nps():
        if "last_nps_survey" in st.session_state:
            last_shown = st.session_state.last_nps_survey
            days_since_last = (datetime.datetime.now() - last_shown).days
            return days_since_last > 90  # Only show every 90 days
        return True
    
    if not _check_last_nps():
        return
    
    show_survey = st.session_state.get("show_nps_survey", False)
    
    if not show_survey:
        if st.button("Help us improve with a quick 1-minute survey"):
            st.session_state.show_nps_survey = True
            st.rerun()
        return
    
    with st.form("nps_survey"):
        st.write("### We'd love your feedback!")
        st.write("On a scale of 0-10, how likely are you to recommend Analytics Assist to a friend or colleague?")
        
        score = st.slider("", 0, 10, 8)
        
        reason = st.text_area("What's the primary reason for your score?")
        
        st.write("### What could we improve?")
        improvement = st.text_area("What's one thing we could do to make Analytics Assist better for you?")
        
        submitted = st.form_submit_button("Submit Feedback")
        
        if submitted:
            # Calculate NPS category
            if score >= 9:
                nps_category = "promoter"
            elif score >= 7:
                nps_category = "passive"
            else:
                nps_category = "detractor"
                
            # Save the feedback
            success = save_feedback(
                feedback_type="nps",
                rating=score,
                comments=reason,
                feature=None,
                page=None,
                metadata={
                    "nps_category": nps_category,
                    "improvement_suggestion": improvement
                }
            )
            
            if success:
                st.success("Thank you for your valuable feedback! We'll use it to improve Analytics Assist.")
                st.session_state.last_nps_survey = datetime.datetime.now()
                st.session_state.show_nps_survey = False
            else:
                st.error("There was an issue saving your feedback. Please try again later.")