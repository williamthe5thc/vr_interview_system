import json
import logging
import requests
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any, Optional, Callable


class OllamaClient:
    """
    Client for interacting with the Ollama API to generate LLM responses.
    
    Designed to work with local Ollama instance running Phi or similar models.
    Includes optimized handling for concurrent requests and error management.
    """
    
    def __init__(self, url: str, model: str, context_length: int = 4096):
        self.url = url.rstrip('/')
        self.model = model
        self.context_length = context_length
        self.logger = logging.getLogger("ollama")
        
        # Thread pool for making requests
        self.executor = ThreadPoolExecutor(max_workers=3)
        
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
        VERY IMPORTANT: Keep all responses extremely brief - no more than 2-3 sentences maximum.
        Do not provide lengthy explanations or multiple questions in one response.
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
        
        # Add specific instruction for keeping responses concise
        formatted_prompt += "IMPORTANT: Keep your responses very brief - no more than 2-3 sentences. " \
                           "Provide direct and concise answers without unnecessary elaboration.\n\n"
        
        # Add conversation history if available
        if context:
            # Limit context to prevent context window overflow
            recent_context = context[-10:]  # Keep only most recent turns
            
            for turn in recent_context:
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
        context: Optional[List[Dict[str, str]]] = None,
        timeout: int = 30,
        max_retries: int = 2
    ) -> str:
        """
        Generate a response using the Ollama API (synchronous version)
        
        Args:
            prompt: The user input to respond to
            context: Optional conversation history
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            
        Returns:
            Generated response text
        """
        if context is None:
            context = []
        
        if not prompt.strip():
            self.logger.warning("Empty prompt received")
            return "I didn't catch that. Could you please repeat your question?"
            
        # Format the prompt with context
        formatted_prompt = self._format_prompt(prompt, context)
        
        # Prepare the API request
        api_url = f"{self.url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": formatted_prompt,
            "stream": False,
            "context": [],  # Ollama context is different from our context
            "options": {
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "num_predict": 100,  # Limit the length of the response to around 100 tokens
                "stop": ["\n\n", "Candidate:", "User:", "\n\nCandidate:"]  # Stop at paragraph breaks or role changes
            }
        }
        
        self.logger.debug(f"Sending request to Ollama: {api_url}")
        start_time = time.time()
        
        # Retry loop
        for attempt in range(max_retries + 1):
            try:
                # Send the request to Ollama
                response = requests.post(api_url, json=payload, timeout=timeout)
                response.raise_for_status()
                
                # Parse the response
                result = response.json()
                generated_text = result.get("response", "")
                
                # Handle empty responses
                if not generated_text.strip():
                    self.logger.warning("Received empty response from Ollama")
                    return "I need a moment to think. Could you tell me about your technical skills?"
                
                # Truncate overly long responses
                if len(generated_text) > 250:  # About 2-3 sentences
                    self.logger.info(f"Truncating long response (from {len(generated_text)} chars)")
                    
                    # Try to find a sentence break for clean truncation
                    sentences = generated_text.split(". ")
                    if len(sentences) > 2:
                        # Keep first two sentences
                        truncated = ". ".join(sentences[:2]) + "."
                    else:
                        # Just take the first 250 characters if we can't find sentence breaks
                        truncated = generated_text[:250].rstrip() + "..."
                        
                    generated_text = truncated
                
                # Record timing for monitoring
                elapsed = time.time() - start_time
                self.logger.info(f"Response generated in {elapsed:.2f}s after {attempt + 1} attempts")
                
                return generated_text
                
            except requests.exceptions.Timeout:
                if attempt < max_retries:
                    self.logger.warning(f"Ollama API timeout. Retrying ({attempt + 1}/{max_retries})")
                    # Increase timeout for retry
                    timeout += 15
                else:
                    self.logger.error("Ollama API timeout after max retries")
                    return "I apologize for the delay. Our system is taking longer than expected to process. Let's try a different approach to continue our interview."
                    
            except requests.exceptions.ConnectionError:
                self.logger.error("Ollama API connection error")
                return "I'm having trouble connecting to our thinking engine. Let's pause for a moment while I reset."
                
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Ollama API error: {e}")
                # Provide a fallback response
                return "I'm sorry, I'm having trouble processing right now. Let's continue the interview in a moment."
                
            except Exception as e:
                self.logger.error(f"Unexpected error during LLM generation: {e}")
                return "I encountered an unexpected issue. Let's move on to another question."
        
    async def generate_response_async(
        self, 
        prompt: str,
        context: Optional[List[Dict[str, str]]] = None,
        timeout: int = 30,
        max_retries: int = 2,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> str:
        """
        Generate a response using the Ollama API (async version)
        
        Args:
            prompt: The user input to respond to
            context: Optional conversation history
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            progress_callback: Optional callback for progress updates
            
        Returns:
            Generated response text
        """
        if context is None:
            context = []
        
        # Format the prompt (this is CPU-bound, but typically quick)
        formatted_prompt = self._format_prompt(prompt, context)
        
        # Run the actual API request in a thread pool executor to avoid blocking the event loop
        # This is crucial for maintaining responsiveness during LLM processing
        try:
            # If progress callback provided, send initial update
            if progress_callback:
                await progress_callback("Starting LLM request...")
                
            # Use the executor to run the blocking HTTP request
            response_text = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                lambda: self._make_ollama_request(
                    formatted_prompt, timeout, max_retries
                )
            )
            
            # Send final progress update
            if progress_callback:
                await progress_callback("LLM response complete")
                
            return response_text
            
        except Exception as e:
            self.logger.error(f"Async LLM error: {e}")
            return "I'm sorry, I encountered a problem with my thinking process. Let's try a different question."
            
    def _make_ollama_request(
        self, 
        formatted_prompt: str, 
        timeout: int, 
        max_retries: int
    ) -> str:
        """
        Make the actual HTTP request to Ollama API (meant to run in thread pool)
        """
        api_url = f"{self.url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": formatted_prompt,
            "stream": False,
            "context": [],
            "options": {
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "num_predict": 100,
                "stop": ["\n\n", "Candidate:", "User:", "\n\nCandidate:"]
            }
        }
        
        start_time = time.time()
        
        # Retry loop
        for attempt in range(max_retries + 1):
            try:
                # Send the request to Ollama
                response = requests.post(api_url, json=payload, timeout=timeout)
                response.raise_for_status()
                
                # Parse the response
                result = response.json()
                generated_text = result.get("response", "")
                
                # Handle empty responses
                if not generated_text.strip():
                    self.logger.warning("Received empty response from Ollama")
                    return "I need a moment to think. Could you tell me about your technical skills?"
                
                # Truncate overly long responses
                if len(generated_text) > 250:
                    self.logger.info(f"Truncating long response (from {len(generated_text)} chars)")
                    sentences = generated_text.split(". ")
                    if len(sentences) > 2:
                        truncated = ". ".join(sentences[:2]) + "."
                    else:
                        truncated = generated_text[:250].rstrip() + "..."
                    generated_text = truncated
                
                # Record timing
                elapsed = time.time() - start_time
                self.logger.info(f"Response generated in {elapsed:.2f}s after {attempt + 1} attempts")
                
                return generated_text
                
            except requests.exceptions.Timeout:
                if attempt < max_retries:
                    self.logger.warning(f"Ollama API timeout. Retrying ({attempt + 1}/{max_retries})")
                    timeout += 15  # Increase timeout for next attempt
                else:
                    self.logger.error("Ollama API timeout after max retries")
                    return "I apologize for the delay. Let's continue with a different question."
                    
            except Exception as e:
                self.logger.error(f"Ollama request error: {e}")
                if attempt < max_retries:
                    continue
                return "I'm having trouble with my thinking process. Let's try something else."
        
    async def stream_response(
        self,
        prompt: str,
        context: Optional[List[Dict[str, str]]] = None,
        callback: Optional[Callable[[str], None]] = None
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
        
        # Run the streaming request in a thread pool to avoid blocking
        try:
            return await asyncio.get_event_loop().run_in_executor(
                self.executor,
                lambda: self._stream_ollama_request(formatted_prompt, callback)
            )
            
        except Exception as e:
            self.logger.error(f"Async streaming error: {e}")
            error_response = "I encountered an issue while processing your question."
            if callback:
                await callback(error_response)
            return error_response
            
    def _stream_ollama_request(
        self, 
        formatted_prompt: str,
        callback: Optional[Callable[[str], None]] = None
    ) -> str:
        """
        Make a streaming request to Ollama API (meant to run in thread pool)
        """
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
                        
            # Truncate if response is too long
            if len(full_response) > 250:
                self.logger.info(f"Truncating streamed response (from {len(full_response)} chars)")
                sentences = full_response.split(". ")
                if len(sentences) > 2:
                    full_response = ". ".join(sentences[:2]) + "."
                else:
                    full_response = full_response[:250].rstrip() + "..."
                        
            return full_response
            
        except Exception as e:
            self.logger.error(f"Ollama streaming error: {e}")
            return "I'm having trouble processing that. Let's continue with a different question."

    def cleanup(self):
        """Clean up resources when shutting down"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=True)
