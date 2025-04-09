import streamlit as st

def show_loading_animation():
    """
    Display a loading animation at the top of the page.
    This function should be used before starting time-consuming operations.
    """
    # Create a placeholder at the top of the page for the loading animation
    loading_placeholder = st.empty()
    
    # Add a spinner with custom styling to make it more prominent
    loading_placeholder.markdown("""
    <div class="loading-animation-container">
        <div class="loading-spinner"></div>
        <div class="loading-text">Processing your request...</div>
    </div>
    
    <style>
    .loading-animation-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 20px;
        margin-bottom: 20px;
        background-color: rgba(255, 255, 255, 0.9);
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }
    
    .loading-spinner {
        border: 5px solid #f3f3f3;
        border-top: 5px solid #2e6da4;
        border-radius: 50%;
        width: 50px;
        height: 50px;
        animation: spin 1s linear infinite;
        margin-bottom: 15px;
    }
    
    .loading-text {
        font-size: 18px;
        font-weight: 500;
        color: #2e6da4;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    </style>
    """, unsafe_allow_html=True)
    
    return loading_placeholder

def hide_loading_animation(placeholder):
    """
    Hide the loading animation when the operation is complete.
    
    Args:
        placeholder: The placeholder returned by show_loading_animation()
    """
    placeholder.empty()