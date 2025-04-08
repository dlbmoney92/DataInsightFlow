import streamlit as st
import os
from utils.ai_providers import AIManager, AIProvider, get_ai_manager

def display_api_key_form():
    """Display a form for users to enter their AI provider API keys."""
    st.subheader("Add AI Provider API Keys")
    
    # Create tabs for different AI providers
    openai_tab, anthropic_tab = st.tabs(["OpenAI", "Anthropic"])
    
    with openai_tab:
        # OpenAI API key form
        st.markdown("""
        To use OpenAI-powered features, you need to provide your OpenAI API key. 
        If you don't have one, you can get it by:
        1. Going to [OpenAI's website](https://platform.openai.com/api-keys)
        2. Creating an account or logging in
        3. Generating a new API key
        
        Your API key will be securely stored and used only for this application.
        """)
        
        openai_api_key = st.text_input("OpenAI API Key", type="password", 
                              help="Enter your OpenAI API key to enable OpenAI features")
        
        if st.button("Save OpenAI API Key") and openai_api_key:
            # In a production environment, this would securely store the API key
            # For now, we'll save it in session state and environment vars
            os.environ["OPENAI_API_KEY"] = openai_api_key
            st.session_state.openai_api_key = openai_api_key
            
            # Reinitialize the AI manager
            st.session_state.ai_manager = AIManager()
            
            st.success("OpenAI API key saved successfully!")
            st.info("Please reload this page to use AI features with your new API key.")
            if st.button("Reload Page", key="reload_openai"):
                st.rerun()
    
    with anthropic_tab:
        # Anthropic API key form
        st.markdown("""
        To use Anthropic's Claude model features, you need to provide your Anthropic API key. 
        If you don't have one, you can get it by:
        1. Going to [Anthropic's website](https://console.anthropic.com/)
        2. Creating an account or logging in
        3. Generating a new API key
        
        Your API key will be securely stored and used only for this application.
        """)
        
        anthropic_api_key = st.text_input("Anthropic API Key", type="password", 
                              help="Enter your Anthropic API key to enable Claude features")
        
        if st.button("Save Anthropic API Key") and anthropic_api_key:
            # In a production environment, this would securely store the API key
            # For now, we'll save it in session state and environment vars
            os.environ["ANTHROPIC_API_KEY"] = anthropic_api_key
            st.session_state.anthropic_api_key = anthropic_api_key
            
            # Reinitialize the AI manager
            st.session_state.ai_manager = AIManager()
            
            st.success("Anthropic API key saved successfully!")
            st.info("Please reload this page to use AI features with your new API key.")
            if st.button("Reload Page", key="reload_anthropic"):
                st.rerun()

def select_ai_provider():
    """Display a form to select the active AI provider."""
    ai_manager = get_ai_manager()
    available_providers = ai_manager.get_available_providers()
    
    if not available_providers:
        st.warning("No AI providers are configured. Please add an API key first.")
        return
    
    st.subheader("Select AI Provider")
    
    # Map enum values to display names
    provider_names = {
        AIProvider.OPENAI: "OpenAI (GPT-4o)",
        AIProvider.ANTHROPIC: "Anthropic (Claude 3.5 Sonnet)"
    }
    
    # Get display names for available providers
    provider_options = [provider_names[provider] for provider in available_providers]
    
    # Map from display name back to enum value
    name_to_provider = {name: provider for provider, name in provider_names.items()}
    
    # Get current provider display name
    current_provider_name = provider_names.get(ai_manager.provider, "Unknown")
    
    st.info(f"Current AI provider: {current_provider_name}")
    
    selected_provider_name = st.selectbox(
        "Select AI Provider",
        options=provider_options,
        index=provider_options.index(current_provider_name) if current_provider_name in provider_options else 0
    )
    
    # Get the corresponding provider enum value
    selected_provider = name_to_provider[selected_provider_name]
    
    if st.button("Set AI Provider") and selected_provider != ai_manager.provider:
        try:
            ai_manager.set_provider(selected_provider)
            st.success(f"AI provider changed to {selected_provider_name}")
            st.info("Please reload this page to use the new AI provider.")
            if st.button("Reload Page", key="reload_provider"):
                st.rerun()
        except ValueError as e:
            st.error(str(e))

def check_api_key_and_display_form():
    """Check if any AI provider API key is available, and if not, display the form to add it."""
    ai_manager = get_ai_manager()
    
    if not ai_manager.is_available():
        st.warning("AI features require an API key. Please add your OpenAI or Anthropic API key to use this feature.")
        display_api_key_form()
        return False
    
    # If API keys are available, show the provider selection
    available_providers = ai_manager.get_available_providers()
    if len(available_providers) > 1:
        st.sidebar.markdown("---")
        with st.sidebar.expander("AI Provider Settings"):
            select_ai_provider()
    
    return True