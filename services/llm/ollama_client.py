import json
import logging
import requests
import time
from typing import List, Dict, Any, Optional


class OllamaClient:
    """
    Client for interacting with the Ollama API to generate LLM responses.
    
    Designed to work with local Ollama instance running Phi or similar models.
    """
    
    def __init__(self, url: str, model: str, context_length: int = 4096):
        self.url = url.rstrip('/')
        self.model = model
        self.context_length = context_length
        self.logger = logging.getLogger("ollama")
        
        # Load system prompt
        self.system_prompt = self._load_system_prompt()
        
        self.logger.info(f"Initialized Ollama client for model: {model}")
        
    def _load_system_prompt(self) -> str:
        """Load the system prompt for the interviewer persona"""
        # In a real implementation, this would load from config
        return """
        You are a professional job interviewer conducting an interview with a candidate.
        Your role is to ask relevant questions, provide thoughtful feedback, and evaluate responses.
        Keep your responses concise and focused on the interview.
        Avoid breaking character or mentioning that you are an AI.
        Speak naturally as a professional interviewer would in a real job interview.
        """
        
    def _format_prompt(self, user_input: str, context: List[Dict[str, str]]) -> str:
        """
        Format the prompt with system instructions and conversation history
        
        Args:
            user_input: The latest user input to respond to
            context: List of previous conversation turns
            
        Returns:
            Formatted prompt for the LLM
        """
        # Start with system prompt
        formatted_prompt = self.system_prompt + "\n\n"
        
        # Add conversation history if available
        if context:
            for turn in context:
                role = turn["role"]
                content = turn["content"]
                if role == "user":
                    formatted_prompt += f"Candidate: {content}\n"
                elif role == "assistant":
                    formatted_prompt += f"Interviewer: {content}\n"
                    
        # Add the current user input
        formatted_prompt += f"Candidate: {user_input}\n\nInterviewer:"
        
        return formatted_prompt
        
    def generate_response(
        self, 
        prompt: str,
        context: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Generate a response using the Ollama API
        
        Args:
            prompt: The user input to respond to
            context: Optional conversation history
            
        Returns:
            Generated response text
        """
        if context is None:
            context = []
            
        # Format the prompt with context
        formatted_prompt = self._format_prompt(prompt, context)
        
        # Prepare the API request
        api_url = f"{self.url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": formatted_prompt,
            "stream": False,
            "context": []  # Ollama context is different from our context
        }
        
        self.logger.debug(f"Sending request to Ollama: {api_url}")
        start_time = time.time()
        
        try:
            # Send the request to Ollama
            response = requests.post(api_url, json=payload, timeout=30)
            response.raise_for_status()
            
            # Parse the response
            result = response.json()
            generated_text = result.get("response", "")
            
            # Record timing for monitoring
            elapsed = time.time() - start_time
            self.logger.info(f"Response generated in {elapsed:.2f}s")
            
            return generated_text
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Ollama API error: {e}")
            # Provide a fallback response
            return "I'm sorry, I'm having trouble processing right now. Let's continue the interview in a moment."
        
    def stream_response(
        self,
        prompt: str,
        context: Optional[List[Dict[str, str]]] = None,
        callback=None
    ) -> str:
        """
        Stream a response from the Ollama API
        
        Args:
            prompt: The user input to respond to
            context: Optional conversation history
            callback: Function to call with each chunk of text
            
        Returns:
            Complete generated response
        """
        if context is None:
            context = []
            
        # Format the prompt with context
        formatted_prompt = self._format_prompt(prompt, context)
        
        # Prepare the API request
        api_url = f"{self.url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": formatted_prompt,
            "stream": True,
            "context": []
        }
        
        full_response = ""
        
        try:
            # Send the streaming request
            with requests.post(api_url, json=payload, timeout=60, stream=True) as response:
                response.raise_for_status()
                
                # Process the streaming response
                for line in response.iter_lines():
                    if not line:
                        continue
                        
                    try:
                        chunk = json.loads(line)
                        token = chunk.get("response", "")
                        full_response += token
                        
                        # Call the callback with the token if provided
                        if callback and callable(callback):
                            callback(token)
                            
                    except json.JSONDecodeError:
                        self.logger.warning(f"Failed to parse streaming response: {line}")
                        
            return full_response
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Ollama streaming error: {e}")
            error_response = "I'm having trouble processing. Let's continue shortly."
            
            if callback and callable(callback):
                callback(error_response)
                
            return error_response
            
    def _handle_error(self, error):
        """Log and handle errors from the Ollama API"""
        self.logger.error(f"Ollama error: {error}")
        # In a production system, we might implement retry logic,
        # fallback to different models, etc.
