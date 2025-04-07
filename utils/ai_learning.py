import streamlit as st
import json
import os
import datetime
import pandas as pd
import numpy as np
from utils.database import execute_with_retry
from sqlalchemy import text
import pickle

def initialize_ai_learning_database():
    """Create the AI learning tables if they don't exist."""
    def _initialize_operation():
        create_feedback_table = """
        CREATE TABLE IF NOT EXISTS ai_feedback (
            id SERIAL PRIMARY KEY,
            user_id INTEGER,
            feedback_type VARCHAR(50) NOT NULL,
            content_id VARCHAR(100),
            rating INTEGER,
            comment TEXT,
            original_prompt TEXT,
            original_response TEXT,
            metadata JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
        );
        """
        
        create_training_data_table = """
        CREATE TABLE IF NOT EXISTS ai_training_data (
            id SERIAL PRIMARY KEY,
            dataset_hash VARCHAR(64) NOT NULL,
            column_name VARCHAR(100),
            original_values TEXT,
            transformed_values TEXT,
            transformation_type VARCHAR(50),
            result_quality FLOAT,
            metadata JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        create_learning_preferences_table = """
        CREATE TABLE IF NOT EXISTS ai_learning_preferences (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            preference_type VARCHAR(50) NOT NULL,
            preference_value JSONB NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE(user_id, preference_type)
        );
        """
        
        from utils.database import engine
        with engine.connect() as conn:
            conn.execute(text(create_feedback_table))
            conn.execute(text(create_training_data_table))
            conn.execute(text(create_learning_preferences_table))
            conn.commit()
    
    # Execute the initialization operation with retry
    execute_with_retry(_initialize_operation)

def save_user_feedback(feedback_type, content_id, rating, comment=None, original_prompt=None, original_response=None, metadata=None):
    """
    Save user feedback on AI-generated content.
    
    Parameters:
    - feedback_type: Type of content (e.g., 'insight', 'visualization', 'transformation')
    - content_id: Identifier for the specific content
    - rating: User rating (typically 1-5)
    - comment: Optional user comment
    - original_prompt: The prompt that was sent to the AI
    - original_response: The AI's response
    - metadata: Any additional metadata as a dict
    """
    def _save_feedback_operation():
        # Get user ID if logged in
        user_id = st.session_state.get("user_id", None)
        
        query = """
        INSERT INTO ai_feedback 
        (user_id, feedback_type, content_id, rating, comment, original_prompt, original_response, metadata)
        VALUES (:user_id, :feedback_type, :content_id, :rating, :comment, :original_prompt, :original_response, :metadata)
        RETURNING id
        """
        
        params = {
            "user_id": user_id,
            "feedback_type": feedback_type,
            "content_id": content_id,
            "rating": rating,
            "comment": comment,
            "original_prompt": original_prompt,
            "original_response": original_response,
            "metadata": json.dumps(metadata) if metadata else None
        }
        
        from utils.database import engine
        with engine.connect() as conn:
            result = conn.execute(text(query), params)
            feedback_id = result.fetchone()[0]
            conn.commit()
            return feedback_id
    
    # Execute the save operation with retry
    return execute_with_retry(_save_feedback_operation)

def save_transformation_outcome(dataset_hash, column_name, original_values, transformed_values, transformation_type, result_quality=None, metadata=None):
    """
    Save the outcome of a transformation to use for future AI training.
    
    Parameters:
    - dataset_hash: A hash representing the dataset (to avoid storing full data)
    - column_name: The name of the column that was transformed
    - original_values: Sample of original values (as JSON string)
    - transformed_values: Sample of transformed values (as JSON string)
    - transformation_type: Type of transformation applied
    - result_quality: A score of how well the transformation worked (0-1)
    - metadata: Any additional metadata as a dict
    """
    def _save_transformation_operation():
        query = """
        INSERT INTO ai_training_data 
        (dataset_hash, column_name, original_values, transformed_values, transformation_type, result_quality, metadata)
        VALUES (:dataset_hash, :column_name, :original_values, :transformed_values, :transformation_type, :result_quality, :metadata)
        RETURNING id
        """
        
        params = {
            "dataset_hash": dataset_hash,
            "column_name": column_name,
            "original_values": original_values,
            "transformed_values": transformed_values,
            "transformation_type": transformation_type,
            "result_quality": result_quality,
            "metadata": json.dumps(metadata) if metadata else None
        }
        
        from utils.database import engine
        with engine.connect() as conn:
            result = conn.execute(text(query), params)
            data_id = result.fetchone()[0]
            conn.commit()
            return data_id
    
    # Execute the save operation with retry
    return execute_with_retry(_save_transformation_operation)

def save_learning_preference(preference_type, preference_value):
    """
    Save a user's AI learning preference.
    
    Parameters:
    - preference_type: Type of preference (e.g., 'visualization_style', 'insight_detail_level')
    - preference_value: The preference value as a dictionary
    """
    def _save_preference_operation():
        # Get user ID if logged in
        user_id = st.session_state.get("user_id", None)
        if not user_id:
            return False
        
        # First check if a preference already exists
        check_query = """
        SELECT id FROM ai_learning_preferences
        WHERE user_id = :user_id AND preference_type = :preference_type
        """
        
        upsert_query = """
        INSERT INTO ai_learning_preferences
        (user_id, preference_type, preference_value)
        VALUES (:user_id, :preference_type, :preference_value)
        ON CONFLICT (user_id, preference_type)
        DO UPDATE SET 
            preference_value = :preference_value,
            updated_at = CURRENT_TIMESTAMP
        RETURNING id
        """
        
        params = {
            "user_id": user_id,
            "preference_type": preference_type,
            "preference_value": json.dumps(preference_value)
        }
        
        from utils.database import engine
        with engine.connect() as conn:
            result = conn.execute(text(upsert_query), params)
            pref_id = result.fetchone()[0]
            conn.commit()
            return pref_id
    
    # Execute the save operation with retry
    return execute_with_retry(_save_preference_operation)

def get_user_preferences():
    """Get all learning preferences for the current user."""
    def _get_preferences_operation():
        # Get user ID if logged in
        user_id = st.session_state.get("user_id", None)
        if not user_id:
            return {}
        
        query = """
        SELECT preference_type, preference_value 
        FROM ai_learning_preferences
        WHERE user_id = :user_id
        """
        
        params = {"user_id": user_id}
        
        from utils.database import engine
        with engine.connect() as conn:
            result = conn.execute(text(query), params)
            preferences = {}
            for row in result:
                preferences[row[0]] = json.loads(row[1])
            return preferences
    
    # Execute the get operation with retry
    return execute_with_retry(_get_preferences_operation)

def get_user_preference(preference_type):
    """Get a specific learning preference for the current user."""
    preferences = get_user_preferences()
    return preferences.get(preference_type, {})

def get_similar_transformations(column_name, sample_values, transformation_type, limit=5):
    """
    Find similar past transformations to learn from.
    
    Parameters:
    - column_name: Name of the column to be transformed
    - sample_values: Sample of values to match against
    - transformation_type: Type of transformation to look for
    - limit: Maximum number of examples to return
    
    Returns:
    - List of similar transformations with their outcomes
    """
    def _get_similar_transformations_operation():
        # This is a simplified implementation that just matches on transformation_type and column_name
        # A more advanced implementation would use semantic matching or other similarity metrics
        
        query = """
        SELECT dataset_hash, column_name, original_values, transformed_values, 
               transformation_type, result_quality, metadata
        FROM ai_training_data
        WHERE transformation_type = :transformation_type
        AND (column_name = :column_name OR column_name LIKE :column_pattern)
        ORDER BY result_quality DESC NULLS LAST
        LIMIT :limit
        """
        
        params = {
            "transformation_type": transformation_type,
            "column_name": column_name,
            "column_pattern": f"%{column_name.split('_')[-1]}%",  # Try to match similar columns
            "limit": limit
        }
        
        from utils.database import engine
        with engine.connect() as conn:
            result = conn.execute(text(query), params)
            transformations = []
            for row in result:
                transformations.append({
                    "dataset_hash": row[0],
                    "column_name": row[1],
                    "original_values": json.loads(row[2]) if row[2] else None,
                    "transformed_values": json.loads(row[3]) if row[3] else None,
                    "transformation_type": row[4],
                    "result_quality": row[5],
                    "metadata": json.loads(row[6]) if row[6] else None
                })
            return transformations
    
    # Execute the get operation with retry
    return execute_with_retry(_get_similar_transformations_operation)

def calculate_dataset_hash(df, columns=None):
    """
    Calculate a hash for a dataset or subset of columns.
    This helps identify similar datasets without storing actual data.
    
    Parameters:
    - df: The DataFrame
    - columns: Optional list of columns to include in the hash
    
    Returns:
    - A hash string representing the data
    """
    import hashlib
    
    if columns:
        df_subset = df[columns].copy()
    else:
        df_subset = df.copy()
    
    # Get basic stats about each column to create a fingerprint
    stats = []
    for col in df_subset.columns:
        col_stats = {
            "name": col,
            "dtype": str(df_subset[col].dtype),
            "nunique": df_subset[col].nunique(),
            "has_nulls": df_subset[col].isna().any()
        }
        
        # Add numeric stats if applicable
        if pd.api.types.is_numeric_dtype(df_subset[col]):
            if not df_subset[col].isna().all():
                col_stats.update({
                    "min": float(df_subset[col].min()),
                    "max": float(df_subset[col].max()),
                    "mean": float(df_subset[col].mean()),
                    "std": float(df_subset[col].std())
                })
        
        stats.append(col_stats)
    
    # Create a stable string representation
    stats_str = json.dumps(stats, sort_keys=True)
    
    # Create a hash
    return hashlib.sha256(stats_str.encode()).hexdigest()

def display_feedback_form(feedback_type, content_id, title="How useful was this?"):
    """
    Display a feedback form and handle submission.
    
    Parameters:
    - feedback_type: Type of content (e.g., 'insight', 'visualization', 'transformation')
    - content_id: Identifier for the specific content
    - title: Title for the feedback form
    """
    # Create a unique key for this feedback form
    key_base = f"{feedback_type}_{content_id}"
    
    # Check if we've already shown and handled this feedback
    if f"{key_base}_submitted" in st.session_state and st.session_state[f"{key_base}_submitted"]:
        st.success("Thank you for your feedback!")
        return
    
    with st.expander(title, expanded=False):
        st.write("Your feedback helps us improve our AI suggestions.")
        
        # Rating
        rating = st.slider(
            "Rating", 
            min_value=1, 
            max_value=5, 
            value=3, 
            key=f"{key_base}_rating"
        )
        
        # Comment
        comment = st.text_area(
            "Comments (optional)", 
            key=f"{key_base}_comment"
        )
        
        # Submit button
        if st.button("Submit Feedback", key=f"{key_base}_submit"):
            success = save_user_feedback(
                feedback_type=feedback_type,
                content_id=content_id,
                rating=rating,
                comment=comment
            )
            
            if success:
                st.session_state[f"{key_base}_submitted"] = True
                st.success("Thank you for your feedback!")
                st.rerun()

def create_feedback_buttons(feedback_type, content_id, original_prompt=None, original_response=None, metadata=None):
    """
    Create simple thumbs up/down feedback buttons.
    
    Parameters:
    - feedback_type: Type of content (e.g., 'insight', 'visualization', 'transformation')
    - content_id: Identifier for the specific content
    - original_prompt: The prompt that was sent to the AI
    - original_response: The AI's response
    - metadata: Any additional metadata as a dict
    """
    # Create a unique key for this feedback
    key_base = f"{feedback_type}_{content_id}"
    
    # Check if feedback already given for this item
    if f"{key_base}_rating" in st.session_state:
        if st.session_state[f"{key_base}_rating"] > 0:
            st.success("Thanks for your feedback!")
        return
    
    # Create columns for the buttons
    col1, col2, col3 = st.columns([1, 1, 5])
    
    with col1:
        if st.button("👍", key=f"{key_base}_thumbs_up"):
            save_user_feedback(
                feedback_type=feedback_type,
                content_id=content_id,
                rating=5,
                original_prompt=original_prompt,
                original_response=original_response,
                metadata=metadata
            )
            st.session_state[f"{key_base}_rating"] = 5
            st.rerun()
    
    with col2:
        if st.button("👎", key=f"{key_base}_thumbs_down"):
            # When users give negative feedback, collect more detailed information
            st.session_state[f"{key_base}_show_comment"] = True
            st.session_state[f"{key_base}_rating"] = 1
            st.rerun()
    
    # Show comment box if requested
    if st.session_state.get(f"{key_base}_show_comment", False):
        comment = st.text_area(
            "How can we improve this? (optional)", 
            key=f"{key_base}_comment_text"
        )
        
        if st.button("Submit Feedback", key=f"{key_base}_submit_comment"):
            save_user_feedback(
                feedback_type=feedback_type,
                content_id=content_id,
                rating=1,
                comment=comment,
                original_prompt=original_prompt,
                original_response=original_response,
                metadata=metadata
            )
            # Clear the comment flag
            st.session_state[f"{key_base}_show_comment"] = False
            st.success("Thank you for your feedback!")
            st.rerun()

def get_ai_learning_stats():
    """Get statistics about AI learning progress."""
    def _get_stats_operation():
        query = """
        SELECT 
            COUNT(*) as total_feedback,
            AVG(rating) as avg_rating,
            COUNT(DISTINCT user_id) as unique_users,
            COUNT(DISTINCT content_id) as unique_contents,
            COUNT(*) FILTER (WHERE feedback_type = 'insight') as insight_feedback,
            COUNT(*) FILTER (WHERE feedback_type = 'visualization') as visualization_feedback,
            COUNT(*) FILTER (WHERE feedback_type = 'transformation') as transformation_feedback,
            COUNT(*) FILTER (WHERE rating >= 4) as positive_feedback,
            COUNT(*) FILTER (WHERE rating <= 2) as negative_feedback
        FROM ai_feedback
        """
        
        training_query = """
        SELECT
            COUNT(*) as total_training_examples,
            COUNT(DISTINCT transformation_type) as unique_transformations,
            AVG(result_quality) as avg_quality
        FROM ai_training_data
        """
        
        from utils.database import engine
        with engine.connect() as conn:
            feedback_result = conn.execute(text(query)).fetchone()
            training_result = conn.execute(text(training_query)).fetchone()
            
            stats = {
                "feedback": {
                    "total": feedback_result[0],
                    "avg_rating": round(feedback_result[1], 2) if feedback_result[1] else 0,
                    "unique_users": feedback_result[2],
                    "unique_contents": feedback_result[3],
                    "insight_feedback": feedback_result[4],
                    "visualization_feedback": feedback_result[5],
                    "transformation_feedback": feedback_result[6],
                    "positive_feedback": feedback_result[7],
                    "negative_feedback": feedback_result[8]
                },
                "training": {
                    "total_examples": training_result[0],
                    "unique_transformations": training_result[1],
                    "avg_quality": round(training_result[2], 2) if training_result[2] else 0
                }
            }
            return stats
    
    # Execute the get operation with retry
    return execute_with_retry(_get_stats_operation)

def enhance_prompt_with_learning(original_prompt, prompt_type, metadata=None):
    """
    Enhance AI prompts based on previous user feedback and preferences.
    
    Parameters:
    - original_prompt: The base prompt to enhance
    - prompt_type: Type of prompt (insight, visualization, transformation, etc.)
    - metadata: Additional context about the prompt
    
    Returns:
    - Enhanced prompt with learned preferences
    """
    # Get user preferences
    preferences = get_user_preferences()
    
    # Start with the original prompt
    enhanced_prompt = original_prompt
    
    # Add user-specific preferences if available
    if preferences:
        # Add a section for user preferences
        enhanced_prompt += "\n\nUser preferences:"
        
        # Add relevant preferences based on prompt type
        if prompt_type == "insight" and "insight_preferences" in preferences:
            prefs = preferences["insight_preferences"]
            if "detail_level" in prefs:
                enhanced_prompt += f"\n- Prefer {prefs['detail_level']} level of detail"
            if "focus_areas" in prefs and prefs["focus_areas"]:
                enhanced_prompt += f"\n- Focus on: {', '.join(prefs['focus_areas'])}"
        
        elif prompt_type == "visualization" and "visualization_preferences" in preferences:
            prefs = preferences["visualization_preferences"]
            if "preferred_charts" in prefs and prefs["preferred_charts"]:
                enhanced_prompt += f"\n- Preferred chart types: {', '.join(prefs['preferred_charts'])}"
            if "color_scheme" in prefs:
                enhanced_prompt += f"\n- Preferred color scheme: {prefs['color_scheme']}"
        
        elif prompt_type == "transformation" and "transformation_preferences" in preferences:
            prefs = preferences["transformation_preferences"]
            if "cleaning_priorities" in prefs and prefs["cleaning_priorities"]:
                enhanced_prompt += f"\n- Cleaning priorities: {', '.join(prefs['cleaning_priorities'])}"
    
    # Analyze past feedback to improve the prompt
    # This would be more sophisticated in a real implementation
    
    return enhanced_prompt

def display_learning_preferences_form():
    """Display a form for users to set their AI learning preferences."""
    st.subheader("AI Learning Preferences")
    st.write("Customize how the AI analyzes and presents data to you.")
    
    # Get current preferences
    current_prefs = get_user_preferences()
    
    # Insight Preferences
    st.markdown("### Insight Preferences")
    
    insight_prefs = current_prefs.get("insight_preferences", {})
    
    # Detail level preference
    detail_level = st.radio(
        "Preferred level of detail in insights",
        options=["High", "Medium", "Low"],
        index=["High", "Medium", "Low"].index(insight_prefs.get("detail_level", "Medium")),
        horizontal=True
    )
    
    # Focus areas
    focus_areas_options = [
        "Data Quality Issues", 
        "Outliers", 
        "Correlations",
        "Trends",
        "Anomalies",
        "Distribution Analysis"
    ]
    
    current_focus_areas = insight_prefs.get("focus_areas", [])
    
    focus_areas = st.multiselect(
        "Focus areas for insights",
        options=focus_areas_options,
        default=current_focus_areas
    )
    
    # Visualization Preferences
    st.markdown("### Visualization Preferences")
    
    viz_prefs = current_prefs.get("visualization_preferences", {})
    
    # Preferred chart types
    chart_options = [
        "Bar Charts", 
        "Line Charts", 
        "Scatter Plots",
        "Histograms",
        "Box Plots",
        "Heatmaps",
        "Pie Charts"
    ]
    
    current_charts = viz_prefs.get("preferred_charts", [])
    
    preferred_charts = st.multiselect(
        "Preferred chart types",
        options=chart_options,
        default=current_charts
    )
    
    # Color scheme
    color_scheme = st.selectbox(
        "Preferred color scheme",
        options=["Default", "Blues", "Greens", "Reds", "Purples", "Oranges", "Viridis", "Plasma", "Inferno", "Magma"],
        index=["Default", "Blues", "Greens", "Reds", "Purples", "Oranges", "Viridis", "Plasma", "Inferno", "Magma"].index(viz_prefs.get("color_scheme", "Default"))
    )
    
    # Transformation Preferences
    st.markdown("### Transformation Preferences")
    
    transform_prefs = current_prefs.get("transformation_preferences", {})
    
    # Cleaning priorities
    cleaning_options = [
        "Missing Values", 
        "Outliers", 
        "Data Type Conversion",
        "Normalization",
        "Categorical Encoding",
        "Text Cleaning"
    ]
    
    current_cleaning = transform_prefs.get("cleaning_priorities", [])
    
    cleaning_priorities = st.multiselect(
        "Data cleaning priorities",
        options=cleaning_options,
        default=current_cleaning
    )
    
    # Save button
    if st.button("Save Preferences"):
        # Update insight preferences
        save_learning_preference("insight_preferences", {
            "detail_level": detail_level,
            "focus_areas": focus_areas
        })
        
        # Update visualization preferences
        save_learning_preference("visualization_preferences", {
            "preferred_charts": preferred_charts,
            "color_scheme": color_scheme
        })
        
        # Update transformation preferences
        save_learning_preference("transformation_preferences", {
            "cleaning_priorities": cleaning_priorities
        })
        
        st.success("Your AI learning preferences have been saved!")
        st.rerun()

# Initialize the database tables when the module is imported
initialize_ai_learning_database()