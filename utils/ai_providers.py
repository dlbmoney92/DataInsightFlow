import streamlit as st
import os
import json
from enum import Enum

# Import the OpenAI client
from openai import OpenAI

# Define AI provider enum for future extensibility
class AIProvider(Enum):
    OPENAI = "openai"

# Initialize OpenAI client
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

class AIManager:
    def __init__(self, provider=AIProvider.OPENAI):
        """Initialize the AI manager with OpenAI as the provider."""
        self.provider = provider
        self._initialize_clients()
        
    def _initialize_clients(self):
        """Initialize OpenAI API client if the key is available."""
        self.openai_available = OPENAI_API_KEY is not None
        
        # Initialize client if API key is available
        if self.openai_available:
            self.openai_client = OpenAI(api_key=OPENAI_API_KEY)
        else:
            self.openai_client = None
        
        # For future compatibility - not currently used
        self.anthropic_available = False
    
    def is_available(self):
        """Check if OpenAI is available."""
        return self.openai_available
    
    def get_available_providers(self):
        """Get a list of available providers."""
        available = []
        if self.openai_available:
            available.append(AIProvider.OPENAI)
        return available
    
    def set_provider(self, provider):
        """Set the active provider - currently only OpenAI is supported."""
        if provider != AIProvider.OPENAI:
            raise ValueError(f"Unsupported AI provider: {provider}")
        self.provider = provider
        
    def generate_completion(self, prompt, system_message=None, json_response=False, max_tokens=1000):
        """Generate text completion using OpenAI.
        
        Args:
            prompt: The user prompt
            system_message: Optional system message to set context
            json_response: Whether to request JSON formatted response
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text or JSON object (if json_response=True)
        """
        if not self.is_available():
            return {"error": "OpenAI API key not configured"}
        
        try:
            return self._generate_openai_completion(prompt, system_message, json_response, max_tokens)
        except Exception as e:
            return {"error": str(e)}
    
    def _generate_openai_completion(self, prompt, system_message, json_response, max_tokens):
        """Generate completion using OpenAI."""
        messages = []
        
        if system_message:
            messages.append({"role": "system", "content": system_message})
            
        messages.append({"role": "user", "content": prompt})
        
        # Prepare completion parameters
        params = {
            # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
            # do not change this unless explicitly requested by the user
            "model": "gpt-4o",
            "messages": messages,
            "max_tokens": max_tokens
        }
        
        # Add response format if JSON is requested
        if json_response:
            params["response_format"] = {"type": "json_object"}
        
        # Call OpenAI API
        response = self.openai_client.chat.completions.create(**params)
        
        # Extract and return the content
        content = response.choices[0].message.content
        
        # If JSON response was requested, parse it
        if json_response:
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return {"error": "Failed to parse JSON response", "raw_content": content}
        
        return content

# Create a singleton instance
ai_manager = AIManager()

def get_ai_manager():
    """Get the global AI manager instance."""
    return ai_manager