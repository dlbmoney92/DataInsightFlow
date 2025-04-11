import streamlit as st
import time
from typing import List, Dict, Tuple, Optional, Callable
import json
import os

def initialize_quick_start():
    """Initialize quick start wizard settings in session state."""
    if 'quick_start_shown' not in st.session_state:
        st.session_state.quick_start_shown = False
    
    if 'quick_start_current_step' not in st.session_state:
        st.session_state.quick_start_current_step = 0
    
    if 'quick_start_completed' not in st.session_state:
        st.session_state.quick_start_completed = False
    
    # Set tour to enabled for testing
    if 'tour_enabled' not in st.session_state:
        st.session_state.tour_enabled = True
    
    if 'tour_current_step' not in st.session_state:
        st.session_state.tour_current_step = 1
    
    if 'tour_steps_completed' not in st.session_state:
        st.session_state.tour_steps_completed = set()

def should_show_quick_start():
    """Determine if the quick start wizard should be shown."""
    # Check if user is new (just signed up or no activity yet)
    is_new_user = False
    
    # If user is logged in, check for previous activity
    if 'user' in st.session_state:
        user_id = st.session_state.user.get('id')
        
        # Check if this user has completed onboarding before
        user_preferences_path = f"user_preferences/{user_id}_preferences.json"
        if os.path.exists(user_preferences_path):
            try:
                with open(user_preferences_path, 'r') as f:
                    preferences = json.load(f)
                    if not preferences.get('onboarding_completed', False):
                        is_new_user = True
            except:
                is_new_user = True
        else:
            is_new_user = True
    
    # If wizard has already been shown in this session, don't show it again
    if st.session_state.quick_start_shown:
        return False
    
    # If user explicitly completed or dismissed the wizard, don't show it
    if st.session_state.quick_start_completed:
        return False
    
    return is_new_user

def mark_quick_start_complete():
    """Mark the quick start wizard as completed."""
    st.session_state.quick_start_completed = True
    st.session_state.quick_start_shown = True
    
    # Save preference for the user if logged in
    if 'user' in st.session_state:
        user_id = st.session_state.user.get('id')
        user_preferences_path = f"user_preferences/{user_id}_preferences.json"
        
        preferences = {}
        if os.path.exists(user_preferences_path):
            try:
                with open(user_preferences_path, 'r') as f:
                    preferences = json.load(f)
            except:
                pass
        
        # Update preferences
        preferences['onboarding_completed'] = True
        
        # Create directory if it doesn't exist
        os.makedirs("user_preferences", exist_ok=True)
        
        # Save preferences
        with open(user_preferences_path, 'w') as f:
            json.dump(preferences, f)

def next_quick_start_step():
    """Advance to the next step in the quick start wizard."""
    st.session_state.quick_start_current_step += 1

def show_quick_start_wizard():
    """Display the quick start wizard."""
    st.session_state.quick_start_shown = True
    
    wizard_steps = [
        {
            "title": "Welcome to Analytics Assist!",
            "description": """
            We're excited to help you unlock insights from your data. 
            Let's take a quick tour of key features to get you started.
            
            Analytics Assist is designed to help you:
            - Upload and analyze your datasets with ease
            - Clean and transform your data with AI assistance
            - Generate powerful visualizations and insights
            - Export and share your findings
            """,
            "image": "assets/quick_start_fixed/welcome.svg"
        },
        {
            "title": "Upload Your Data",
            "description": """
            Start by uploading your data in the Upload Data page.
            We support various formats including:
            - CSV files
            - Excel spreadsheets
            - JSON data
            - Text data
            
            You can also try our sample datasets to explore the platform.
            """,
            "image": "assets/quick_start_fixed/upload.svg",
            "action": "Go to Upload Data",
            "action_target": "pages/01_Upload_Data.py"
        },
        {
            "title": "Preview and Explore",
            "description": """
            Once your data is uploaded, you can preview it and get basic statistics.
            The Data Preview page helps you understand:
            - Column types and distributions
            - Missing values
            - Basic statistics
            - Data quality issues
            """,
            "image": "assets/quick_start_fixed/preview.svg",
            "action": "Explore Data Preview",
            "action_target": "pages/02_Data_Preview.py"
        },
        {
            "title": "Transform Your Data",
            "description": """
            Clean and prepare your data using our transformation tools:
            - Fix missing values
            - Remove duplicates
            - Convert data types
            - Create calculated columns
            - Apply AI-suggested transformations
            """,
            "image": "assets/quick_start_fixed/transform.svg",
            "action": "Try Data Transformation",
            "action_target": "pages/04_Data_Transformation.py"
        },
        {
            "title": "Discover Insights",
            "description": """
            Our AI-powered insights engine analyzes your data to uncover:
            - Trends and patterns
            - Correlations between variables
            - Anomalies and outliers
            - Business recommendations
            
            Pro Tip: The more context you provide about your data, the better insights you'll receive!
            """,
            "image": "assets/quick_start_fixed/insights.svg",
            "action": "Generate Insights",
            "action_target": "pages/05_Insights_Dashboard.py"
        },
        {
            "title": "Share Your Findings",
            "description": """
            Export your analysis as professional reports in various formats:
            - Interactive web reports
            - PDF documents
            - Excel spreadsheets
            - CSV data files
            
            Share links with colleagues to collaborate on your findings.
            """,
            "image": "assets/quick_start_fixed/export.svg",
            "action": "Export Reports",
            "action_target": "pages/06_Export_Reports.py"
        },
        {
            "title": "You're Ready to Go!",
            "description": """
            You now know the basics of Analytics Assist!
            
            Enable the interactive tour for step-by-step guidance on each page,
            or jump right in and start exploring your data.
            
            Need help? Check out our comprehensive User Guide or contact our support team.
            """,
            "action": "Start Analyzing",
            "action_target": "pages/01_Upload_Data.py",
            "secondary_action": "Enable Tour Mode",
            "secondary_action_callback": enable_tour_mode
        }
    ]
    
    current_step = st.session_state.quick_start_current_step
    
    # Display the wizard in a dialog-like container
    with st.container():
        col1, col2, col3 = st.columns([1, 10, 1])
        
        with col2:
            st.markdown("""
            <div style="
                border: 1px solid #eee; 
                border-radius: 10px; 
                padding: 20px; 
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                background-color: white;
                max-width: 800px;
                margin: 0 auto;
            ">
            """, unsafe_allow_html=True)
            
            # Header with progress indicator
            progress_col1, progress_col2, progress_col3 = st.columns([2, 6, 2])
            
            with progress_col1:
                st.write(f"Step {current_step + 1}/{len(wizard_steps)}")
            
            with progress_col2:
                progress = (current_step) / (len(wizard_steps) - 1)
                st.progress(progress)
            
            with progress_col3:
                st.write(f"{int(progress * 100)}% Complete")
            
            # Step content
            step = wizard_steps[current_step]
            st.markdown(f"## {step['title']}")
            
            # If there's an image, display it
            if "image" in step and step["image"] and isinstance(step["image"], str) and os.path.exists(step["image"]):
                try:
                    st.image(step["image"], use_container_width=True)
                except Exception as e:
                    st.warning(f"Could not load image: {step['image']}")
            
            st.markdown(step["description"])
            
            # Navigation buttons
            button_cols = st.columns([1, 1, 1])
            
            with button_cols[0]:
                if current_step > 0:
                    if st.button("← Previous", key="wizard_prev"):
                        st.session_state.quick_start_current_step -= 1
                        st.rerun()
            
            with button_cols[1]:
                if st.button("Skip Tour", key="wizard_skip"):
                    mark_quick_start_complete()
                    st.rerun()
            
            with button_cols[2]:
                if current_step < len(wizard_steps) - 1:
                    next_label = "Next →"
                    if "action" in step:
                        next_label = step["action"]
                    
                    if st.button(next_label, key="wizard_next"):
                        if "action_target" in step:
                            st.session_state.quick_start_current_step += 1
                            st.switch_page(step["action_target"])
                        else:
                            st.session_state.quick_start_current_step += 1
                            st.rerun()
                else:
                    # Last step, complete button
                    final_action = step.get("action", "Finish")
                    if st.button(final_action, key="wizard_finish"):
                        mark_quick_start_complete()
                        
                        if "action_target" in step:
                            st.switch_page(step["action_target"])
                        else:
                            st.rerun()
            
            # Secondary action if available
            if "secondary_action" in step:
                if st.button(step["secondary_action"], key="wizard_secondary"):
                    if "secondary_action_callback" in step:
                        step["secondary_action_callback"]()
                    mark_quick_start_complete()
                    st.rerun()
            
            st.markdown("</div>", unsafe_allow_html=True)

def enable_tour_mode():
    """Enable the interactive tour mode."""
    st.session_state.tour_enabled = True
    st.session_state.tour_current_step = 0
    st.session_state.tour_steps_completed = set()

def disable_tour_mode():
    """Disable the interactive tour mode."""
    st.session_state.tour_enabled = False

def next_tour_step():
    """Advance to the next step in the interactive tour."""
    # Mark current step as completed first
    if "tour_page_key" in st.session_state and "tour_step_key" in st.session_state:
        completed_step = f"{st.session_state.tour_page_key}_{st.session_state.tour_current_step}"
        st.session_state.tour_steps_completed.add(completed_step)
        
    # Then advance to next step
    st.session_state.tour_current_step += 1
    
    # Print for debugging
    print(f"Advanced to tour step {st.session_state.tour_current_step}")

def show_tour_bubble(
    element_id: str,
    title: str,
    content: str,
    step: int,
    position: str = "right",
    page_key: str = None,
    on_complete: Callable = None
):
    """
    Display a tour bubble pointing to a specific element.
    
    Args:
        element_id: CSS selector for the target element
        title: Title of the tour bubble
        content: Content/description text
        step: The step number in the tour sequence
        position: Positioning of the bubble (top, right, bottom, left)
        page_key: Unique key for the current page
        on_complete: Callback function when this step is completed
    """
    if not st.session_state.tour_enabled:
        return
    
    # Set current page key in session state
    if page_key:
        st.session_state.tour_page_key = page_key
    
    # Set current step key in session state
    st.session_state.tour_step_key = step
    
    # Check if we're on the current step
    if st.session_state.tour_current_step != step:
        return
    
    # Check if this step was already completed
    if page_key:
        completed_step = f"{page_key}_{step}"
        if completed_step in st.session_state.tour_steps_completed:
            # If this step was completed but we're still on it,
            # automatically move to the next step
            next_tour_step()
            return
    
    # Create bubble with direct navigation buttons
    bubble_style = f"""
    <style>
    .tour-bubble {{
        position: fixed !important;
        width: 350px !important;
        background: white !important;
        border: 1px solid #ddd !important;
        border-radius: 8px !important;
        padding: 0 !important; /* Remove padding as we're styling the content internally */
        box-shadow: 0 4px 8px rgba(0,0,0,0.2) !important;
        z-index: 1000 !important;
        overflow: visible !important;
    }}
    
    .tour-bubble-title {{
        font-weight: bold;
        font-size: 16px;
        margin-bottom: 8px;
        color: #1E3C72;
    }}
    
    .tour-bubble-content {{
        margin-bottom: 15px;
        font-size: 14px;
    }}
    
    .tour-bubble-buttons {{
        display: flex;
        justify-content: space-between;
    }}
    
    /* Bubble positions with arrows */
    .tour-bubble-right:before {{
        content: "";
        position: absolute;
        left: -10px;
        top: 20px;
        border-top: 10px solid transparent;
        border-bottom: 10px solid transparent;
        border-right: 10px solid white;
    }}
    
    .tour-bubble-left:before {{
        content: "";
        position: absolute;
        right: -10px;
        top: 20px;
        border-top: 10px solid transparent;
        border-bottom: 10px solid transparent;
        border-left: 10px solid white;
    }}
    
    .tour-bubble-top:before {{
        content: "";
        position: absolute;
        bottom: -10px;
        left: 50%;
        transform: translateX(-50%);
        border-left: 10px solid transparent;
        border-right: 10px solid transparent;
        border-top: 10px solid white;
    }}
    
    .tour-bubble-bottom:before {{
        content: "";
        position: absolute;
        top: -10px;
        left: 50%;
        transform: translateX(-50%);
        border-left: 10px solid transparent;
        border-right: 10px solid transparent;
        border-bottom: 10px solid white;
    }}
    </style>
    """
    
    st.markdown(bubble_style, unsafe_allow_html=True)
    
    # Now using Streamlit native components for the bubble
    with st.container():
        bubble_container = st.container()
        
        with bubble_container:
            # Add custom styling for this container to make it look like a bubble
            st.markdown(f"""
                <div class="tour-bubble-header" style="background: linear-gradient(135deg, #1E3C72, #2A5298); color: white; padding: 10px; border-radius: 8px 8px 0 0;">
                    <h3 style="margin: 0; font-size: 16px;">{title}</h3>
                </div>
                <div class="tour-bubble-content" style="padding: 10px; font-size: 14px;">
                    {content}
                </div>
            """, unsafe_allow_html=True)
            
            # Navigation buttons with a more distinct UI
            st.markdown("""
                <div style="padding: 10px; border-top: 1px solid #eee;">
                </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Skip Tour", key=f"skip_tour_{step}", help="Skip the tour"):
                    disable_tour_mode()
                    st.rerun()
            
            with col2:
                # Make the Next button more prominent
                if st.button("▶ Next Step", key=f"next_step_{step}", use_container_width=True, type="primary", help="Continue to the next step"):
                    # Add print for debugging
                    print(f"Next button clicked on step {step}")
                    next_tour_step()
                    if on_complete:
                        on_complete()
                    # Print after next_tour_step
                    print(f"After next_tour_step(), current step is now {st.session_state.tour_current_step}")
                    st.rerun()
    
    # Use a simple CSS class approach instead of complex JavaScript
    position_class = "tour-bubble-" + position
    
    # Create a highlight script for the target element
    highlight_script = f"""
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            const targetElement = document.querySelector('{element_id}');
            if (targetElement) {{
                targetElement.style.position = 'relative';
                targetElement.style.zIndex = '999';
                targetElement.style.boxShadow = '0 0 0 4px rgba(30, 60, 114, 0.4)';
            }}
        }});
    </script>
    """
    
    # Add the highlight script
    st.markdown(highlight_script, unsafe_allow_html=True)

def add_quick_start_button():
    """Add a button to restart the quick start wizard."""
    if st.sidebar.button("Restart Quick Start Guide"):
        st.session_state.quick_start_shown = False
        st.session_state.quick_start_completed = False
        st.session_state.quick_start_current_step = 0
        st.rerun()