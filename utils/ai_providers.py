import streamlit as st
import os
import json
from enum import Enum

# Import the OpenAI client
from openai import OpenAI

# Import Anthropic client
import anthropic
from anthropic import Anthropic

# Define AI provider enum for future extensibility
class AIProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"

# Initialize API keys
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

class AIManager:
    def __init__(self, provider=AIProvider.OPENAI):
        """Initialize the AI manager with OpenAI as the provider."""
        self.provider = provider
        self._initialize_clients()
        
    def _initialize_clients(self):
        """Initialize API clients for available providers."""
        # Check OpenAI availability and initialize client
        self.openai_available = OPENAI_API_KEY is not None
        if self.openai_available:
            self.openai_client = OpenAI(api_key=OPENAI_API_KEY)
        else:
            self.openai_client = None
        
        # Check Anthropic availability and initialize client
        self.anthropic_available = ANTHROPIC_API_KEY is not None
        if self.anthropic_available:
            self.anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)
        else:
            self.anthropic_client = None
    
    def is_available(self):
        """Check if any AI provider is available."""
        return self.openai_available or self.anthropic_available
    
    def get_available_providers(self):
        """Get a list of available providers."""
        available = []
        if self.openai_available:
            available.append(AIProvider.OPENAI)
        if self.anthropic_available:
            available.append(AIProvider.ANTHROPIC)
        return available
    
    def set_provider(self, provider):
        """Set the active provider."""
        if provider == AIProvider.OPENAI and self.openai_available:
            self.provider = provider
        elif provider == AIProvider.ANTHROPIC and self.anthropic_available:
            self.provider = provider
        else:
            raise ValueError(f"Unsupported or unavailable AI provider: {provider}")
        
    def generate_completion(self, prompt, system_message=None, json_response=False, max_tokens=1000):
        """Generate text completion using the selected AI provider.
        
        Args:
            prompt: The user prompt
            system_message: Optional system message to set context
            json_response: Whether to request JSON formatted response
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text or JSON object (if json_response=True)
        """
        if not self.is_available():
            return {"error": "No AI provider available. Please configure an API key."}
        
        try:
            if self.provider == AIProvider.OPENAI and self.openai_available:
                return self._generate_openai_completion(prompt, system_message, json_response, max_tokens)
            elif self.provider == AIProvider.ANTHROPIC and self.anthropic_available:
                return self._generate_anthropic_completion(prompt, system_message, json_response, max_tokens)
            else:
                # Fallback to any available provider
                if self.openai_available:
                    return self._generate_openai_completion(prompt, system_message, json_response, max_tokens)
                elif self.anthropic_available:
                    return self._generate_anthropic_completion(prompt, system_message, json_response, max_tokens)
                else:
                    return {"error": "No AI provider available"}
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

    def _generate_anthropic_completion(self, prompt, system_message, json_response, max_tokens):
        """Generate completion using Anthropic Claude."""
        # Build the messages
        messages = []
        
        if system_message:
            messages.append({
                "role": "assistant",
                "content": system_message
            })
            
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        # Prepare completion parameters
        params = {
            # the newest Anthropic model is "claude-3-5-sonnet-20241022" which was released October 22, 2024.
            # do not change this unless explicitly requested by the user
            "model": "claude-3-5-sonnet-20241022",
            "messages": messages,
            "max_tokens": max_tokens
        }
        
        # Request JSON response if needed
        if json_response:
            params["system"] = "Respond only with valid JSON object. No markdown, no explanation, just JSON."
        
        # Call Anthropic API
        response = self.anthropic_client.messages.create(**params)
        
        # Extract the content
        content = response.content[0].text
        
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