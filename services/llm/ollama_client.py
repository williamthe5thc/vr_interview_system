import json
import logging
import requests
import time
import asyncio
import os
import hashlib
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any, Optional, Callable, Union
from services.llm.templates.response_templates import TEMPLATES, SYSTEM_PROMPTS


class OllamaClient:
    """
    Client for interacting with the Ollama API to generate LLM responses.
    
    Designed to work with local Ollama instance running Phi or similar models.
    Includes optimized handling for concurrent requests and error management.
    """
    
    def __init__(self, url: str, model: str, context_length: int = 8192, config=None):
        self.url = url.rstrip('/')
        self.model = model
        self.context_length = context_length
        self.logger = logging.getLogger("ollama")
        
        # Store config for reference by other components
        self.config = config or {}
        
        # Thread pool for making requests with increased workers for performance
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Get scenario type from config
        self.scenario_type = self.config.get("scenario_type", "interview")
        
        # Load system prompt based on scenario type
        self.system_prompt = self._load_system_prompt()
        
        # Initialize enhanced response cache with metadata
        self.response_cache = {}
        self.max_cache_size = 200  # Increased for better hit ratio
        self.cache_dir = "data/cache"
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Cache analytics
        self.cache_hits = 0
        self.cache_misses = 0
        
        # Load cache from disk if available
        self._load_cache_from_disk()
        
        self.logger.info(f"Initialized Ollama client for model: {model} in {self.scenario_type} scenario")
        self.logger.info(f"Response caching enabled with max size: {self.max_cache_size} entries")
        
        # Log Ollama parameters for transparency
        options_str = json.dumps(self.config.get("options", {}), indent=2)
        self.logger.info(f"Using Ollama parameters: {options_str}")
        
        # Performance settings
        self.use_streaming = self.config.get("use_streaming", True)
        self.logger.info(f"Streaming responses: {'enabled' if self.use_streaming else 'disabled'}")
        
        # Timeout settings - increased for Phi/Mistral models
        self.default_timeout = self.config.get("timeout", 60)  # Increased from 20 to 60 seconds
        self.logger.info(f"Default request timeout: {self.default_timeout}s")
        
    def _load_system_prompt(self) -> str:
        """Load the system prompt for the current scenario type"""
        # Get system prompt from templates based on scenario type
        if self.scenario_type in SYSTEM_PROMPTS:
            return SYSTEM_PROMPTS[self.scenario_type]
        
        # Custom prompt from config if specified
        if self.config and "system_prompt" in self.config:
            return self.config["system_prompt"]
            
        # Default to interview prompt if nothing else specified
        return SYSTEM_PROMPTS["interview"]
        
    def _format_prompt(self, user_input: str, context: List[Dict[str, str]], interaction_stage: str = None) -> str:
        """
        Format the prompt with system instructions and conversation history
        
        Optimized for shorter, more focused prompts that reduce token usage and improve
        response generation speed.
        
        Args:
            user_input: The latest user input to respond to
            context: List of previous conversation turns
            interaction_stage: Current stage of the interaction (optional)
            
        Returns:
            Formatted prompt for the LLM
        """
        # Start with a more focused system prompt
        formatted_prompt = "You are a professional job interviewer. Keep responses under 3 sentences.\n\n"
        
        # Add minimal stage-specific guidance if available
        if interaction_stage:
            if interaction_stage == "greeting":
                formatted_prompt += "Introduce yourself briefly.\n"
            elif interaction_stage == "technical_question":
                formatted_prompt += "Ask a technical question.\n"
            elif interaction_stage == "behavioral_question":
                formatted_prompt += "Ask about soft skills.\n"
            elif interaction_stage == "wrap_up":
                formatted_prompt += "Wrap up the interview.\n"
        
        # Add only essential conversation history
        if context:
            # Drastically reduce context to just 3 most recent exchanges
            # This improves response speed while maintaining coherence
            max_turns = 3  # Simplified to just 3 recent turns
            
            # Only include the most recent exchanges
            recent_exchanges = context[-max_turns:] if len(context) > max_turns else context
            
            # Add the minimal conversation history to prompt
            for turn in recent_exchanges:
                role = turn["role"]
                content = turn["content"]
                # Limit content length to reduce token usage
                content = content[:100] + "..." if len(content) > 100 else content
                if role == "user":
                    formatted_prompt += f"Candidate: {content}\n"
                elif role == "assistant":
                    formatted_prompt += f"Interviewer: {content}\n"
                    
        # Add the current user input
        formatted_prompt += f"Candidate: {user_input}\n\nInterviewer:"
        
        return formatted_prompt
        
    def apply_template(self, template_name: str, **kwargs) -> str:
        """
        Apply a predefined response template with the given parameters
        
        Args:
            template_name: Name of the template to use
            **kwargs: Parameters to fill in the template
            
        Returns:
            Formatted template text
        """
        if template_name not in TEMPLATES:
            self.logger.warning(f"Template '{template_name}' not found")
            return kwargs.get("fallback_text", "")
            
        template = TEMPLATES[template_name]
        try:
            return template.format(**kwargs)
        except KeyError as e:
            self.logger.error(f"Missing parameter for template {template_name}: {e}")
            return kwargs.get("fallback_text", "")
    
    def _create_cache_key(self, prompt: str, context: List[Dict[str, str]] = None, 
                          interaction_stage: str = None) -> str:
        """
        Create a simplified cache key based primarily on the prompt
        
        This simpler implementation focuses on the actual prompt text to improve cache hit rates
        while maintaining reasonable response relevance.
        """
        if context is None:
            context = []
            
        # Simplify the prompt to improve cache hit rate
        # Take the prompt, normalize it, and use the first part (most important)
        normalized_prompt = prompt.strip().lower()[:100]  # First 100 chars, lowercase
        
        # Add minimal context fingerprint (just from the last exchange if any)
        context_fingerprint = ""
        if context and len(context) > 0:
            # Only use the most recent exchange for context fingerprint
            last_exchange = context[-1]
            # Create a minimal fingerprint
            last_content = last_exchange.get("content", "")[:20]  # Just first 20 chars
            if last_content:
                context_fingerprint = hashlib.md5(last_content.encode()).hexdigest()[:6]
        
        # Create a simpler compound key
        stage_str = f"_{interaction_stage[:5]}" if interaction_stage else ""  # Shortened stage name
        key_components = f"{normalized_prompt}_{context_fingerprint}{stage_str}"
        
        # Use MD5 hash for consistent keys
        return hashlib.md5(key_components.encode()).hexdigest()
    
    def generate_response(
        self, 
        prompt: str,
        context: Optional[List[Dict[str, str]]] = None,
        timeout: int = None,
        max_retries: int = None,
        interaction_stage: str = None
    ) -> str:
        """
        Generate a response using the Ollama API (synchronous version)
        
        Args:
            prompt: The user input to respond to
            context: Optional conversation history
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            interaction_stage: Current stage of the interaction
            
        Returns:
            Generated response text
        """
        if context is None:
            context = []
        
        # Use default values from config if not specified
        if timeout is None:
            timeout = self.default_timeout
        if max_retries is None:
            max_retries = self.config.get("max_retries", 2)
        
        if not prompt.strip():
            self.logger.warning("Empty prompt received")
            return "I didn't catch that. Could you please repeat your question?"
            
        # Format the prompt with context and stage information
        formatted_prompt = self._format_prompt(prompt, context, interaction_stage)
        
        # Create a more sophisticated cache key
        cache_key = self._create_cache_key(prompt, context, interaction_stage)
        
        # Check cache first to prevent duplicate responses
        if cache_key in self.response_cache:
            cache_entry = self.response_cache[cache_key]
            if isinstance(cache_entry, dict):
                cached_response = cache_entry.get("response", "")
                # Update usage statistics
                cache_entry["used_count"] = cache_entry.get("used_count", 0) + 1
                cache_entry["last_used"] = time.time()
            else:
                # Handle old cache format for backward compatibility
                cached_response = cache_entry
                
            self.logger.info(f"Cache hit for prompt: {prompt[:30]}...")
            self.cache_hits += 1
            return cached_response
        
        # Log cache metrics periodically
        if (self.cache_hits + self.cache_misses) % 50 == 0 and self.cache_hits + self.cache_misses > 0:
            hit_rate = self.cache_hits / (self.cache_hits + self.cache_misses) * 100
            self.logger.info(f"Cache performance: {hit_rate:.1f}% hit rate ({self.cache_hits} hits, {self.cache_misses} misses)")
        
        # Increment miss counter
        self.cache_misses += 1
        
        # Prepare the API request with optimized parameters from config
        api_url = f"{self.url}/api/generate"
        
        # Get options from config or use defaults
        options = self.config.get("options", {})
        
        # Define stop sequences based on scenario
        stop_sequences = ["\n\n", "Candidate:", "User:", "\n\nCandidate:"]
        if self.scenario_type == "interview":
            stop_sequences.extend(["Interviewer:", "\n\nInterviewer:"])
        elif self.scenario_type == "conflict_resolution":
            stop_sequences.extend(["Colleague:", "\n\nColleague:"])
        
        # Build the payload with config values
        payload = {
            "model": self.model,
            "prompt": formatted_prompt,
            "stream": False,
            "context": [],  # Ollama context is different from our context
            "options": {
                "temperature": options.get("temperature", 0.8),
                "top_p": options.get("top_p", 0.92),
                "top_k": options.get("top_k", 45),
                "repeat_penalty": options.get("repeat_penalty", 1.15),
                "num_predict": options.get("num_predict", 150),  # Increased for more complete responses
                "stop": stop_sequences,
                "seed": options.get("seed", None)  # Fixed seed for reproducible responses
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
                
                # Cache the response with metadata for future use and analysis
                if cache_key not in self.response_cache:
                    # Store response with metadata for cache management
                    self.response_cache[cache_key] = {
                        "response": generated_text,
                        "created_at": time.time(),
                        "used_count": 1,
                        "last_used": time.time(),
                        "generation_time": elapsed,
                        "prompt_length": len(formatted_prompt),
                        "response_length": len(generated_text),
                        "scenario_type": self.scenario_type,
                        "interaction_stage": interaction_stage
                    }
                    
                    # Limit cache size using intelligent pruning - remove least used entries
                    if len(self.response_cache) > self.max_cache_size:
                        # Find least recently used entries
                        entries_to_prune = sorted(
                            [(k, v.get("last_used", 0) if isinstance(v, dict) else 0) 
                             for k, v in self.response_cache.items()],
                            key=lambda x: x[1]
                        )[:max(1, int(self.max_cache_size * 0.1))]  # Prune 10% of oldest entries
                        
                        for key, _ in entries_to_prune:
                            self.logger.debug(f"Pruning cache entry: {key[:8]}...")
                            self.response_cache.pop(key, None)
                    
                    # Periodically save cache to disk (every 10 new entries)
                    if len(self.response_cache) % 10 == 0:
                        self._save_cache_to_disk()
                
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
        timeout: int = None,
        max_retries: int = None,
        progress_callback: Optional[Callable[[str], None]] = None,
        interaction_stage: str = None
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
        
        # Use default values from config if not specified
        if timeout is None:
            timeout = self.default_timeout
        if max_retries is None:
            max_retries = self.config.get("max_retries", 2)
            
        # Format the prompt with context and stage information (CPU-bound, but quick)
        formatted_prompt = self._format_prompt(prompt, context, interaction_stage)
        
        # Create a cache key for checking
        cache_key = self._create_cache_key(prompt, context, interaction_stage)
        
        # Check cache first before making network request
        if cache_key in self.response_cache:
            cache_entry = self.response_cache[cache_key]
            if isinstance(cache_entry, dict):
                cached_response = cache_entry.get("response", "")
                # Update usage statistics
                cache_entry["used_count"] = cache_entry.get("used_count", 0) + 1
                cache_entry["last_used"] = time.time()
            else:
                # Handle old cache format for backward compatibility
                cached_response = cache_entry
                
            self.logger.info(f"Cache hit for async prompt: {prompt[:30]}...")
            self.cache_hits += 1
            
            # Send update to callback if provided
            if progress_callback:
                await progress_callback("Using cached response")
                
            return cached_response
            
        # Cache miss - increment counter
        self.cache_misses += 1
        
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
                    formatted_prompt, timeout, max_retries, cache_key, interaction_stage
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
        max_retries: int,
        cache_key: str = None,
        interaction_stage: str = None
    ) -> str:
        """
        Make the actual HTTP request to Ollama API (meant to run in thread pool)
        """
        # Use provided cache key or create one if not provided
        if cache_key is None:
            cache_key = hashlib.md5(formatted_prompt.encode()).hexdigest()
        
        # Cache check should have been done in the calling function
        # This ensures we don't hit the cache twice
            
        api_url = f"{self.url}/api/generate"
        
        # Get options from config or use defaults
        options = self.config.get("options", {})
        
        # Define stop sequences based on scenario
        stop_sequences = ["\n\n", "Candidate:", "User:", "\n\nCandidate:"]
        if self.scenario_type == "interview":
            stop_sequences.extend(["Interviewer:", "\n\nInterviewer:"])
        elif self.scenario_type == "conflict_resolution":
            stop_sequences.extend(["Colleague:", "\n\nColleague:"])
        
        # Build the payload with config values
        payload = {
            "model": self.model,
            "prompt": formatted_prompt,
            "stream": False,
            "context": [],
            "options": {
                "temperature": options.get("temperature", 0.8),
                "top_p": options.get("top_p", 0.92),
                "top_k": options.get("top_k", 45),
                "repeat_penalty": options.get("repeat_penalty", 1.15),
                "num_predict": options.get("num_predict", 150),
                "stop": stop_sequences,
                "seed": options.get("seed", None)
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
                
                # Cache the response with metadata for future use and analysis
                if cache_key not in self.response_cache:
                    # Store response with metadata for cache management
                    self.response_cache[cache_key] = {
                        "response": generated_text,
                        "created_at": time.time(),
                        "used_count": 1,
                        "last_used": time.time(),
                        "generation_time": elapsed,
                        "prompt_length": len(formatted_prompt),
                        "response_length": len(generated_text),
                        "scenario_type": self.scenario_type,
                        "interaction_stage": interaction_stage,
                        "async": True
                    }
                    
                    # Intelligent cache pruning as needed
                    if len(self.response_cache) > self.max_cache_size:
                        # Find least recently used entries
                        entries_to_prune = sorted(
                            [(k, v.get("last_used", 0) if isinstance(v, dict) else 0) 
                             for k, v in self.response_cache.items()],
                            key=lambda x: x[1]
                        )[:max(1, int(self.max_cache_size * 0.1))]
                        
                        for key, _ in entries_to_prune:
                            self.logger.debug(f"Pruning async cache entry: {key[:8]}...")
                            self.response_cache.pop(key, None)
                    
                    # Periodically save cache to disk (every 10 new entries)
                    if len(self.response_cache) % 10 == 0:
                        self._save_cache_to_disk()
                
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
        callback: Optional[Callable[[str], None]] = None,
        interaction_stage: str = None
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
            
        # Format the prompt with context and stage information
        formatted_prompt = self._format_prompt(prompt, context, interaction_stage)
        
        # Create a cache key for checking
        cache_key = self._create_cache_key(prompt, context, interaction_stage)
        
        # Check cache first before streaming request
        if cache_key in self.response_cache:
            cache_entry = self.response_cache[cache_key]
            if isinstance(cache_entry, dict):
                cached_response = cache_entry.get("response", "")
                # Update usage statistics
                cache_entry["used_count"] = cache_entry.get("used_count", 0) + 1
                cache_entry["last_used"] = time.time()
            else:
                # Handle old cache format for backward compatibility
                cached_response = cache_entry
                
            self.logger.info(f"Cache hit for streaming prompt: {prompt[:30]}...")
            self.cache_hits += 1
            
            # If we have a callback, simulate streaming from cache
            if callback and callable(callback):
                # Split the cached response into word-like chunks to simulate streaming
                chunks = cached_response.split(" ")
                for chunk in chunks:
                    await callback(chunk + " ")
                    # Add small delay to simulate natural streaming
                    await asyncio.sleep(0.05)
                
            return cached_response
        
        # Cache miss - increment counter
        self.cache_misses += 1
        
        # Run the streaming request in a thread pool to avoid blocking
        try:
            return await asyncio.get_event_loop().run_in_executor(
                self.executor,
                lambda: self._stream_ollama_request(formatted_prompt, callback, cache_key, interaction_stage)
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
        callback: Optional[Callable[[str], None]] = None,
        cache_key: str = None,
        interaction_stage: str = None
    ) -> str:
        """
        Make a streaming request to Ollama API (meant to run in thread pool)
        """
        # Use provided cache key or create one if not provided
        if cache_key is None:
            cache_key = hashlib.md5(formatted_prompt.encode()).hexdigest()
            
        api_url = f"{self.url}/api/generate"
        
        # Get options from config or use defaults
        options = self.config.get("options", {})
        
        # Define stop sequences based on scenario
        stop_sequences = ["\n\n", "Candidate:", "User:", "\n\nCandidate:"]
        if self.scenario_type == "interview":
            stop_sequences.extend(["Interviewer:", "\n\nInterviewer:"])
        elif self.scenario_type == "conflict_resolution":
            stop_sequences.extend(["Colleague:", "\n\nColleague:"])
        
        # Build the payload with config values - but always use streaming
        payload = {
            "model": self.model,
            "prompt": formatted_prompt,
            "stream": True,
            "context": [],
            "options": {
                "temperature": options.get("temperature", 0.8),
                "top_p": options.get("top_p", 0.92),
                "top_k": options.get("top_k", 45),
                "repeat_penalty": options.get("repeat_penalty", 1.15),
                "num_predict": options.get("num_predict", 150),
                "stop": stop_sequences,
                "seed": options.get("seed", None)
            }
        }
        
        full_response = ""
        start_time = time.time()  # Track start time for performance metrics
        
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
                        
                        # Call the callback with the token if provided - only handle sync callbacks
                        if callback and callable(callback) and not asyncio.iscoroutinefunction(callback):
                            # Call sync callback directly
                            callback(token)
                            
                    except json.JSONDecodeError:
                        self.logger.warning(f"Failed to parse streaming response: {line}")
                        
            # Truncate if response is too long
            original_response = full_response
            if len(full_response) > 250:
                self.logger.info(f"Truncating streamed response (from {len(full_response)} chars)")
                sentences = full_response.split(". ")
                if len(sentences) > 2:
                    full_response = ". ".join(sentences[:2]) + "."
                else:
                    full_response = full_response[:250].rstrip() + "..."
            
            # Record streaming completion
            elapsed = time.time() - start_time
            self.logger.info(f"Streaming response completed in {elapsed:.2f}s")
            
            # Cache the response with metadata for future use - even if it's from streaming
            if cache_key not in self.response_cache:
                # Store response with metadata for cache management
                self.response_cache[cache_key] = {
                    "response": full_response,
                    "created_at": time.time(),
                    "used_count": 1,
                    "last_used": time.time(),
                    "generation_time": elapsed,
                    "prompt_length": len(formatted_prompt),
                    "response_length": len(full_response),
                    "scenario_type": self.scenario_type,
                    "interaction_stage": interaction_stage,
                    "streaming": True,
                    "original_length": len(original_response)
                }
                
                # Periodically save cache to disk
                if len(self.response_cache) % 10 == 0:
                    self._save_cache_to_disk()
                        
            return full_response
            
        except Exception as e:
            self.logger.error(f"Ollama streaming error: {e}")
            return "I'm having trouble processing that. Let's continue with a different question."

    def _save_cache_to_disk(self):
        """Save response cache to disk with improved error handling and compression"""
        try:
            cache_file = f"{self.cache_dir}/llm_response_cache.json"
            
            # Convert cache to serializable format
            serializable_cache = {}
            for key, value in self.response_cache.items():
                # Ensure we only save essential data to reduce file size
                if isinstance(value, dict):
                    # Keep only essential fields for disk storage
                    disk_entry = {
                        "response": value.get("response", ""),
                        "created_at": value.get("created_at", time.time()),
                        "used_count": value.get("used_count", 1),
                        "last_used": value.get("last_used", time.time()),
                        "scenario_type": value.get("scenario_type", self.scenario_type),
                        "interaction_stage": value.get("interaction_stage", None)
                    }
                    serializable_cache[str(key)] = disk_entry
                else:
                    # Legacy format - just store the string response
                    serializable_cache[str(key)] = value
                    
            # Use atomic write pattern for reliability
            temp_file = f"{cache_file}.temp"
            with open(temp_file, 'w') as f:
                json.dump(serializable_cache, f)
                
            # Rename temp file to final file (atomic operation on most file systems)
            os.replace(temp_file, cache_file)
                
            self.logger.info(f"Saved {len(serializable_cache)} cache entries to disk")
        except Exception as e:
            self.logger.error(f"Error saving cache to disk: {e}")

    def _load_cache_from_disk(self):
        """Load response cache from disk with improved error handling"""
        try:
            cache_file = f"{self.cache_dir}/llm_response_cache.json"
            if os.path.exists(cache_file):
                with open(cache_file, 'r') as f:
                    serialized_cache = json.load(f)
                    
                # Track stats for logging
                loaded_count = 0
                skipped_count = 0
                
                # Load entries with graceful error handling for each entry
                for key, value in serialized_cache.items():
                    try:
                        # Handle both new (dict) and old (string) format
                        if isinstance(value, dict):
                            # Convert to proper cache entry format
                            if "response" in value:
                                self.response_cache[key] = value
                                loaded_count += 1
                            else:
                                # Skip invalid entries
                                skipped_count += 1
                                continue
                        else:
                            # Legacy string format - keep as is
                            self.response_cache[key] = value
                            loaded_count += 1
                    except Exception as item_error:
                        # Skip problematic entries rather than failing entirely
                        self.logger.warning(f"Skipped cache entry {key}: {item_error}")
                        skipped_count += 1
                    
                self.logger.info(f"Loaded {loaded_count} cache entries from disk (skipped {skipped_count})")
        except Exception as e:
            self.logger.error(f"Error loading cache from disk: {e}")
            # Create fresh cache file on next save
            self.response_cache = {}
    
    def cleanup(self):
        """Clean up resources when shutting down"""
        # Save cache to disk before shutting down
        self._save_cache_to_disk()
        
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=True)
