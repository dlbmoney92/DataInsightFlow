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
    
    if 'tour_enabled' not in st.session_state:
        st.session_state.tour_enabled = False
    
    if 'tour_current_step' not in st.session_state:
        st.session_state.tour_current_step = 0
    
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
            "image": "assets/quick_start/welcome.png"  # You'll need to create these images
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
            "image": "assets/quick_start/upload.png",
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
            "image": "assets/quick_start/preview.png",
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
            "image": "assets/quick_start/transform.png",
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
            "image": "assets/quick_start/insights.png",
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
            "image": "assets/quick_start/export.png",
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
            if "image" in step and os.path.exists(step["image"]):
                st.image(step["image"], use_column_width=True)
            
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
    st.session_state.tour_current_step += 1
    
    # Mark current step as completed
    if "tour_page_key" in st.session_state and "tour_step_key" in st.session_state:
        completed_step = f"{st.session_state.tour_page_key}_{st.session_state.tour_current_step-1}"
        st.session_state.tour_steps_completed.add(completed_step)

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
    
    # Use custom CSS and JavaScript to create and position the tour bubble
    bubble_html = f"""
    <div id="tour-bubble-{step}" class="tour-bubble tour-bubble-{position}">
        <div class="tour-bubble-title">{title}</div>
        <div class="tour-bubble-content">{content}</div>
        <div class="tour-bubble-buttons">
            <button onclick="document.dispatchEvent(new CustomEvent('tourSkip'))">Skip Tour</button>
            <button onclick="document.dispatchEvent(new CustomEvent('tourNext'))">Next</button>
        </div>
    </div>
    
    <style>
    .tour-bubble {{
        position: absolute;
        width: 300px;
        background: white;
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 15px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        z-index: 1000;
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
    
    .tour-bubble-buttons button {{
        padding: 5px 10px;
        border: none;
        border-radius: 4px;
        cursor: pointer;
    }}
    
    .tour-bubble-buttons button:first-child {{
        background: #f2f2f2;
        color: #333;
    }}
    
    .tour-bubble-buttons button:last-child {{
        background: #1E3C72;
        color: white;
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
    
    <script>
    // Position the bubble relative to the target element
    function positionBubble() {{
        const targetElement = document.querySelector('{element_id}');
        const bubble = document.getElementById('tour-bubble-{step}');
        
        if (!targetElement || !bubble) return;
        
        const targetRect = targetElement.getBoundingClientRect();
        
        // Highlight the target element
        targetElement.style.position = 'relative';
        targetElement.style.zIndex = '999';
        targetElement.style.boxShadow = '0 0 0 4px rgba(30, 60, 114, 0.4)';
        
        // Position based on specified position
        switch('{position}') {{
            case 'right':
                bubble.style.left = (targetRect.right + 20) + 'px';
                bubble.style.top = (targetRect.top + window.scrollY) + 'px';
                break;
            case 'left':
                bubble.style.left = (targetRect.left - bubble.offsetWidth - 20) + 'px';
                bubble.style.top = (targetRect.top + window.scrollY) + 'px';
                break;
            case 'top':
                bubble.style.left = (targetRect.left + (targetRect.width / 2) - (bubble.offsetWidth / 2)) + 'px';
                bubble.style.top = (targetRect.top + window.scrollY - bubble.offsetHeight - 20) + 'px';
                break;
            case 'bottom':
                bubble.style.left = (targetRect.left + (targetRect.width / 2) - (bubble.offsetWidth / 2)) + 'px';
                bubble.style.top = (targetRect.bottom + window.scrollY + 20) + 'px';
                break;
        }}
    }}
    
    // Event listeners for tour navigation
    document.addEventListener('tourNext', function() {{
        fetch('/_stcore/process_form', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{ 
                form_data: {{"tour_action": "next"}},
                form_id: "tour_navigation"
            }})
        }}).then(response => {{
            if (response.ok) {{
                window.location.reload();
            }}
        }});
    }});
    
    document.addEventListener('tourSkip', function() {{
        fetch('/_stcore/process_form', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{ 
                form_data: {{"tour_action": "skip"}},
                form_id: "tour_navigation"
            }})
        }}).then(response => {{
            if (response.ok) {{
                window.location.reload();
            }}
        }});
    }});
    
    // Position when loaded and on resize
    document.addEventListener('DOMContentLoaded', positionBubble);
    window.addEventListener('resize', positionBubble);
    positionBubble(); // Call immediately as well
    </script>
    """
    
    st.markdown(bubble_html, unsafe_allow_html=True)
    
    # Handle form submissions for tour navigation
    if st.form("tour_navigation", clear_on_submit=True):
        tour_action = st.text_input("tour_action", key="tour_action_input", label_visibility="collapsed")
        submitted = st.form_submit_button("Submit", type="primary", help="Submit the form", label_visibility="collapsed")
        
        if submitted:
            if tour_action == "next":
                next_tour_step()
                if on_complete:
                    on_complete()
            elif tour_action == "skip":
                disable_tour_mode()
            
            st.rerun()
    else:
        # No form submission, display normally
        pass

def add_quick_start_button():
    """Add a button to restart the quick start wizard."""
    if st.sidebar.button("Restart Quick Start Guide"):
        st.session_state.quick_start_shown = False
        st.session_state.quick_start_completed = False
        st.session_state.quick_start_current_step = 0
        st.rerun()