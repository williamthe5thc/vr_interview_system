"""
Improved AllTalk TTS integration for VR Interview System with streaming support.

This module provides a robust integration with the AllTalk TTS API,
including streaming capabilities for direct client playback and fallbacks.
"""

import requests
import json
import time
import logging
import os
import io
import sys
import traceback
import urllib.parse
from typing import Dict, Any, List, Optional, Union, Tuple

class AllTalkTTSService:
    """
    AllTalk TTS service with robust error handling, streaming support, and fallbacks.
    """
    
    def __init__(self, url=None, voice=None, config=None):
        self.logger = logging.getLogger("alltalk_tts")
        
        # Store the URL
        self.base_url = url.rstrip('/') if url else "http://127.0.0.1:7851"
        self.logger.info(f"Initializing AllTalk TTS with URL: {self.base_url}")
        
        # Store the voice
        self.voice = voice or "alloy"
        
        # Store the config
        self.config = config or {}
        
        # Set timeout and add longer timeout for direct API
        self.timeout = self.config.get('timeout', 30)
        self.direct_api_timeout = self.config.get('direct_api_timeout', 40)
        
        # Default to assuming APIs are available until server check
        self.direct_api_available = True
        self.streaming_api_available = True
        
        # Track generated audio files by session ID for retrieval
        self.generated_audio_files = {}
        self.last_output_file = None
        
        # Get alltalk directory from config or use default
        self.alltalk_dir = self.config.get("alltalk_dir", "D:/AllTalk/alltalk_tts")
        self.outputs_dir = os.path.join(self.alltalk_dir, "outputs")
        
        # Check if directories exist and log
        self.logger.info(f"AllTalk directory set to: {self.alltalk_dir}")
        self.logger.info(f"AllTalk outputs directory set to: {self.outputs_dir}")
        self.logger.info(f"AllTalk directory exists: {os.path.exists(self.alltalk_dir)}")
        self.logger.info(f"AllTalk outputs directory exists: {os.path.exists(self.outputs_dir)}")
        
        # Check if AllTalk is available
        self.available = self._check_server()
        
        if self.available:
            direct_api_status = "available" if self.direct_api_available else "not available"
            streaming_api_status = "available" if self.streaming_api_available else "not available"
            self.logger.info(f"Initialized TTS service with voice: {self.voice}, using AllTalk: True, direct API: {direct_api_status}, streaming API: {streaming_api_status}")
        else:
            self.logger.warning(f"AllTalk service not available. Falling back to gTTS.")
    
    def _check_server(self) -> bool:
        """Check if AllTalk server is available"""
        try:
            # Try multiple ways to reach the AllTalk server
            self.logger.info(f"Testing AllTalk connection at {self.base_url}")
            
            # Try the ready endpoint first - most reliable
            try:
                # Add retry logic with increased timeout
                for attempt in range(3):  # Try up to 3 times
                    try:
                        response = requests.get(f"{self.base_url}/api/ready", timeout=5 + (attempt * 2))
                        if response.status_code == 200:
                            self.logger.info(f"AllTalk status endpoint available (attempt {attempt+1})")
                            break
                        else:
                            self.logger.warning(f"AllTalk returned non-200 status on attempt {attempt+1}: {response.status_code}")
                            if attempt < 2:  # Don't sleep on last attempt
                                time.sleep(1)  # Short delay between retries
                    except (requests.RequestException, ConnectionError) as e:
                        self.logger.warning(f"Connection error on attempt {attempt+1}: {e}")
                        if attempt < 2:  # Don't sleep on last attempt
                            time.sleep(1)  # Short delay between retries
                        continue
                
                # Check if last attempt was successful
                if response.status_code == 200:
                    self.logger.info("AllTalk status endpoint confirmed available")
                    
                    # Also check for voices
                    voices_response = requests.get(f"{self.base_url}/api/voices", timeout=5)
                    if voices_response.status_code == 200:
                        voices_data = voices_response.json()
                        voices = voices_data.get('voices', [])
                        self.logger.info(f"Found {len(voices)} voices")
                        
                        # Store the voices
                        self.voices = voices
                        
                        # Update voice if needed
                        if self.voice not in voices and len(voices) > 0 and isinstance(voices[0], str):
                            self.logger.warning(f"Voice {self.voice} not found, using {voices[0]}")
                            self.voice = voices[0]
                    
                    # Check API endpoints systematically with robust testing
                    self._test_alltalk_api_endpoints()
                    
                    # Also check for direct API support with more robust testing
                    self.direct_api_available = self._test_direct_api()
                    
                    return True
            except Exception as e:
                self.logger.warning(f"AllTalk status check failed: {e}")
            
            return False
        except Exception as e:
            self.logger.warning(f"AllTalk server check failed: {e}")
            return False
    
    def _test_direct_api(self) -> bool:
        """Test direct TTS API with multiple methods"""
        methods_to_try = [
            self._test_tts_generate_api,
            self._test_synthesize_api,
            self._test_tts_api
        ]
        
        for method in methods_to_try:
            if method():
                self.logger.info(f"Direct API available via {method.__name__}")
                return True
        
        self.logger.warning("Failed to confirm direct API availability")
        return False
        
    def _test_tts_generate_api(self) -> bool:
        """Test the tts-generate API endpoint"""
        try:
            test_file = f"test_direct_{int(time.time())}"
            response = requests.post(
                f"{self.base_url}/api/tts-generate",
                data={
                    "text_input": "Test",
                    "character_voice_gen": self.voice,
                    "output_file_name": test_file,
                    "format": "wav"
                },
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=5
            )
            
            if response.status_code == 200 and len(response.content) > 100:
                return True
                
            self.logger.warning(f"tts-generate test failed: {response.status_code}")
            return False
        except Exception as e:
            self.logger.warning(f"tts-generate test error: {e}")
            return False
    
    def _test_synthesize_api(self) -> bool:
        """Test the synthesize API endpoint"""
        try:
            response = requests.post(
                f"{self.base_url}/api/synthesize",
                data={
                    "text": "Test",
                    "voice": self.voice,
                    "format": "wav"
                },
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=5
            )
            
            if response.status_code == 200 and len(response.content) > 100:
                return True
                
            self.logger.warning(f"synthesize test failed: {response.status_code}")
            return False
        except Exception as e:
            self.logger.warning(f"synthesize test error: {e}")
            return False
            
    def _test_tts_api(self) -> bool:
        """Test the tts API endpoint"""
        try:
            response = requests.post(
                f"{self.base_url}/api/tts",
                json={
                    "text": "Test",
                    "voice": self.voice,
                    "format": "wav"
                },
                timeout=5
            )
            
            if response.status_code == 200 and len(response.content) > 100:
                return True
                
            self.logger.warning(f"tts test failed: {response.status_code}")
            return False
        except Exception as e:
            self.logger.warning(f"tts test error: {e}")
            return False
    
    def _test_alltalk_api_endpoints(self) -> None:
        """Test different AllTalk API endpoints systematically"""
        # Test streaming API
        self.streaming_api_available = False  # Default to unavailable
        
        # Try multiple ways to test streaming
        methods_to_try = [
            self._test_streaming_api_post,
            self._test_streaming_api_get,
            self._test_direct_streaming
        ]
        
        for method in methods_to_try:
            if method():
                self.streaming_api_available = True
                self.logger.info(f"AllTalk streaming API available via {method.__name__}")
                break
        
        if not self.streaming_api_available:
            self.logger.warning("Failed to confirm AllTalk streaming API availability")
    
    def _test_streaming_api_post(self) -> bool:
        """Test streaming API via POST request"""
        try:
            # Use short timeout for test
            response = requests.post(
                f"{self.base_url}/api/tts-generate-streaming",
                data={
                    "text": "Test",
                    "voice": self.voice,
                    "language": "en",
                    "output_file": f"test_stream_{int(time.time())}"
                },
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                stream=True,
                timeout=5
            )
            
            if response.status_code == 200:
                # Close the connection without reading the full response
                response.close()
                return True
            
            self.logger.warning(f"Streaming POST test failed: {response.status_code}")
            return False
        except Exception as e:
            self.logger.warning(f"Streaming POST test error: {e}")
            return False
    
    def _test_streaming_api_get(self) -> bool:
        """Test streaming API via GET request with URL parameters"""
        try:
            # Test with URL parameters instead of POST data
            test_text = urllib.parse.quote("Test")
            url = f"{self.base_url}/api/tts-generate-streaming?text={test_text}&voice={self.voice}&output_file=test_get_{int(time.time())}" 
            
            response = requests.get(
                url,
                stream=True,
                timeout=5
            )
            
            if response.status_code == 200:
                # Close the connection without reading the full response
                response.close()
                return True
            
            self.logger.warning(f"Streaming GET test failed: {response.status_code}")
            return False
        except Exception as e:
            self.logger.warning(f"Streaming GET test error: {e}")
            return False
    
    def _test_direct_streaming(self) -> bool:
        """Test direct streaming to file generation"""
        try:
            # Generate a unique test filename
            test_file = f"test_direct_{int(time.time())}"
            
            # Request file generation
            response = requests.post(
                f"{self.base_url}/api/tts-generate",
                data={
                    "text_input": "Hello test",
                    "character_voice_gen": self.voice,
                    "output_file_name": test_file,
                    "format": "wav"
                },
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=5
            )
            
            if response.status_code == 200 and len(response.content) > 100:
                return True
            
            self.logger.warning(f"Direct streaming test failed: {response.status_code}")
            return False
        except Exception as e:
            self.logger.warning(f"Direct streaming test error: {e}")
            return False
    
    def is_available(self) -> bool:
        """Check if AllTalk is available"""
        return self.available
        
    def get_available_voices(self) -> List[str]:
        """Get available voices"""
        return getattr(self, 'voices', [])
    
    def get_streaming_url(self, text: str, session_id: Optional[str] = None) -> str:
        """
        Get a URL that the client can use to stream audio directly from AllTalk
        
        Args:
            text: The text to convert to speech
            session_id: Optional session ID for tracking generated audio
            
        Returns:
            URL string that the client can use to stream audio directly, or None if streaming not available
        """
        self.logger.info(f"get_streaming_url called with text length: {len(text)}, session_id: {session_id}")
        
        # Initialize as available - be optimistic
        if not hasattr(self, 'streaming_api_available'):
            self.streaming_api_available = True
            self.logger.info("Initializing streaming_api_available flag to True")
        
        if not self.available or not self.streaming_api_available:
            self.logger.warning("AllTalk streaming not available, cannot generate streaming URL")
            return None
            
        try:
            # Generate a unique output filename
            timestamp = int(time.time())
            # Make a more unique ID that includes any session_id prefix to avoid collisions
            prefix = session_id[:8] if session_id else "vr"
            # Avoid double extension by NOT adding .wav here - AllTalk will add it
            output_file = f"{prefix}_interview_{timestamp}"
            
            # Store the filename for possible retrieval later - add multiple possible extensions
            # AllTalk can generate output files with double extensions in some versions
            possible_files = [
                f"{output_file}.wav",
                f"{output_file}.wav.wav",
                output_file,
                f"{output_file}.mp3"
            ]
            self.last_output_file = possible_files[0]  # Default to first option
            
            # Track all possible filenames with the session if provided
            if session_id:
                if session_id not in self.generated_audio_files:
                    self.generated_audio_files[session_id] = []
                for file in possible_files:
                    self.generated_audio_files[session_id].append(file)
                self.logger.info(f"Tracking output files {possible_files} for session {session_id}")
            
            # Based on AllTalk API documentation, properly prepare the streaming URL
            # Using the tts-generate-streaming endpoint as shown in the documentation
            # Using query parameters for GET request compatibility
            
            # Handle very long text - truncate for URL if needed but keep for processing
            full_text = text
            if len(text) > 4000:
                self.logger.warning(f"Text is very long ({len(text)} chars), truncating for URL")
                text = text[:4000] + "..."
            
            # Escape text properly for URL
            encoded_text = urllib.parse.quote(text)
            encoded_voice = urllib.parse.quote(self.voice)
            language = self.config.get('default_language', 'en')
            
            # For streaming API, we must use the old parameter names according to the documentation
            # (text, voice, output_file) - NOT the newer ones (text_input, character_voice_gen, etc.)
            streaming_url = f"{self.base_url}/api/tts-generate-streaming?text={encoded_text}&voice={encoded_voice}&language={language}&output_file={output_file}"
            
            # Add timestamp parameter to bypass caching
            streaming_url += f"&_t={timestamp}"
            
            self.logger.info(f"Created AllTalk streaming URL: {streaming_url[:100]}...")
            
            # Now actually trigger audio generation via POST (more reliable than waiting for client to trigger it)
            # This happens in parallel and will not block this function
            try:
                self.logger.info("Proactively triggering audio generation via POST request")
                # Creating a thread to execute this asynchronously
                import threading
                
                def trigger_generation():
                    try:
                        # Use POST request to more reliably generate the file
                        response = requests.post(
                            f"{self.base_url}/api/tts-generate-streaming",
                            data={
                                "text": full_text,  # Use full text here
                                "voice": self.voice,
                                "language": language,
                                "output_file": output_file
                            },
                            headers={'Content-Type': 'application/x-www-form-urlencoded'},
                            timeout=30  # Generous timeout
                        )
                        
                        # Check response
                        if response.status_code == 200:
                            self.logger.info("Successfully triggered audio generation: HTTP 200")
                        else:
                            self.logger.warning(f"Unexpected response when triggering audio: {response.status_code}")
                    except Exception as trigger_err:
                        self.logger.warning(f"Error triggering audio generation: {trigger_err}")
                
                # Start the thread
                thread = threading.Thread(target=trigger_generation)
                thread.daemon = True  # Don't let this prevent program exit
                thread.start()
                
            except Exception as trigger_setup_err:
                self.logger.warning(f"Error setting up trigger thread: {trigger_setup_err}")
            
            # Create a test file in outputs directory to verify permissions
            try:
                if not os.path.exists(self.outputs_dir):
                    os.makedirs(self.outputs_dir, exist_ok=True)
                    self.logger.info(f"Created outputs directory: {self.outputs_dir}")
                
                # Write a test file to ensure we have write permissions
                test_file_path = os.path.join(self.outputs_dir, f"test_access_{timestamp}.txt")
                with open(test_file_path, "w") as f:
                    f.write(f"Test file for session {session_id} - {timestamp}")
                
                # Read it back to confirm permissions
                with open(test_file_path, "r") as f:
                    test_content = f.read()
                    self.logger.info(f"Successfully created test file: {test_content[:30]}")
                
                # Clean up test file
                os.remove(test_file_path)
            except Exception as test_err:
                self.logger.warning(f"File permission test failed: {test_err}")
            
            return streaming_url
            
        except Exception as e:
            self.logger.error(f"Error generating streaming URL: {e}")
            self.logger.error(traceback.format_exc())
            return None
    
    def get_last_audio_data(self, session_id: Optional[str] = None) -> Optional[bytes]:
        """
        Retrieve the audio data for the most recently generated file for a session
        
        This is used as a fallback mechanism when streaming fails
        
        Args:
            session_id: Optional session ID to get session-specific file
            
        Returns:
            Audio data as bytes if available, None otherwise
        """
        try:
            # Try to find the most recent file for this session
            target_file = None
            
            # DIAGNOSTIC: Log file tracking data
            self.logger.info(f"==== AUDIO FILE RETRIEVAL DIAGNOSTICS =====")
            self.logger.info(f"Session ID: {session_id}")
            self.logger.info(f"All generated files: {self.generated_audio_files}")
            self.logger.info(f"Last output file: {self.last_output_file}")
            
            if session_id and session_id in self.generated_audio_files:
                # Get the most recent file for this session
                if self.generated_audio_files[session_id]:
                    target_file = self.generated_audio_files[session_id][-1]
                    self.logger.info(f"Found session-specific file: {target_file}")
            
            # Fall back to last output file if no session-specific file
            if not target_file and self.last_output_file:
                target_file = self.last_output_file
                self.logger.info(f"Using last output file: {target_file}")
                
            if not target_file:
                self.logger.warning("No recent audio file found to retrieve")
                return None
            
            # First check if the file has the correct extension
            # AllTalk produces audio files with extensions like .wav.wav or just .wav
            possible_extensions = [
                target_file,  # Original target (complete path)
                target_file + ".wav",  # Add .wav if missing
                target_file + ".wav.wav",  # Add .wav.wav if missing
                target_file.replace(".wav.wav", ".wav"),  # Replace double with single
                target_file.replace(".wav", "") + ".wav",  # Strip and re-add .wav
                # Also handle the case where the target already includes the path
                os.path.basename(target_file),  # Just the filename
                os.path.basename(target_file) + ".wav",
                os.path.basename(target_file) + ".wav.wav",
            ]
            
            # Get the basename for later use in similar file search
            base_name = os.path.basename(target_file).split('.')[0]
            self.logger.info(f"Base filename for search: {base_name}")
            
            # Based on AllTalk documentation - try to access the file from the outputs dir
            # Using the standard output location pattern
            output_paths_to_check = [
                # Main outputs directory as configured
                self.outputs_dir,
                # Expected AllTalk output paths
                os.path.join(self.alltalk_dir, "outputs"),
                # Additional possible paths
                os.path.join(self.alltalk_dir),
                os.path.join(self.alltalk_dir, "audio_out"),
                "./audio_out",
                "./outputs",
                "./data/audio/responses",
            ]
            
            # Remove any duplicates
            output_paths_to_check = list(set(output_paths_to_check))
            
            # Check all possible combinations of paths and filenames
            for output_path in output_paths_to_check:
                if not os.path.exists(output_path):
                    self.logger.info(f"Output path doesn't exist: {output_path}")
                    continue
                    
                # List all files in this directory
                try:
                    dir_files = os.listdir(output_path)
                    self.logger.info(f"Found {len(dir_files)} files in {output_path}")
                    
                    # Look for exact filename matches first
                    for ext in possible_extensions:
                        filename = os.path.basename(ext)
                        if filename in dir_files:
                            file_path = os.path.join(output_path, filename)
                            self.logger.info(f"Found exact match: {file_path}")
                            try:
                                with open(file_path, "rb") as f:
                                    audio_data = f.read()
                                self.logger.info(f"Retrieved audio from {file_path}: {len(audio_data)} bytes")
                                return audio_data
                            except Exception as e:
                                self.logger.warning(f"Error reading file {file_path}: {e}")
                    
                    # Look for files containing the base name
                    similar_files = [f for f in dir_files if base_name in f]
                    if similar_files:
                        self.logger.info(f"Found {len(similar_files)} similar files: {similar_files[:5]}")
                        
                        # Sort by modification time (newest first)
                        similar_files.sort(key=lambda f: os.path.getmtime(os.path.join(output_path, f)), reverse=True)
                        
                        # Try the newest similar file
                        newest_file = similar_files[0]
                        file_path = os.path.join(output_path, newest_file)
                        try:
                            with open(file_path, "rb") as f:
                                audio_data = f.read()
                            self.logger.info(f"Retrieved audio from newest similar file {file_path}: {len(audio_data)} bytes")
                            return audio_data
                        except Exception as e:
                            self.logger.warning(f"Error reading newest similar file: {e}")
                            
                except Exception as e:
                    self.logger.warning(f"Error listing directory {output_path}: {e}")
            
            # If we get here, we couldn't find the file - try to make a new request to AllTalk
            self.logger.warning(f"Could not find audio file in any location, attempting to recreate")
            
            # Try a direct HTTP request to the API endpoint for the file
            try:
                file_url = f"{self.base_url}/audio/{os.path.basename(target_file)}"
                self.logger.info(f"Attempting to download directly from: {file_url}")
                
                response = requests.get(file_url, timeout=5)
                if response.status_code == 200 and len(response.content) > 1000:
                    self.logger.info(f"Successfully downloaded audio directly: {len(response.content)} bytes")
                    return response.content
            except Exception as http_err:
                self.logger.warning(f"HTTP request for file failed: {http_err}")
                
            # Try a direct API call to generate new audio as a last resort
            try:
                self.logger.info(f"Attempting to regenerate audio via direct API as last resort")
                # We can use the original text if we have it from a session context
                session = self.state_manager.get_session(session_id) if hasattr(self, 'state_manager') else None
                if session and hasattr(session, 'get_last_response'):
                    text = session.get_last_response()
                    if text:
                        self.logger.info(f"Retrieved text from session: {text[:30]}...")
                        audio_data = self._synthesize_gtts(text)
                        return audio_data
            except Exception as e:
                self.logger.warning(f"Failed to generate new audio: {e}")
            
            return None
                
        except Exception as e:
            self.logger.error(f"Error retrieving last audio data: {e}")
            self.logger.error(traceback.format_exc())
            return None
    
    def generate_audio_file(self, text, voice=None):
        """Generate audio file using AllTalk API"""
        voice = voice or self.voice
        
        try:
            # Log request details
            self.logger.info(f"Generating audio for text: '{text[:30]}...' using voice: {voice}")
            
            # Build the request
            request_data = {
                "voice": voice,
                "text": text,
                "format": "wav"  # or mp3 based on your configuration
            }
            
            # Log full request
            self.logger.debug(f"AllTalk request: {request_data}")
            
            # Send the request to AllTalk
            response = requests.post(f"{self.base_url}/api/tts", json=request_data, timeout=30)
            
            # Log response status
            self.logger.info(f"AllTalk response status: {response.status_code}")
            
            if response.status_code != 200:
                self.logger.error(f"AllTalk API error: {response.status_code}, Response: {response.text[:200]}")
                return None
                
            # Save audio file
            audio_file_path = os.path.join("data/audio/responses", f"{int(time.time())}.wav")
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(audio_file_path), exist_ok=True)
            
            # Log file path
            self.logger.info(f"Saving audio file to: {audio_file_path}")
            
            # Write to file
            with open(audio_file_path, 'wb') as f:
                f.write(response.content)
                
            # Verify file was created
            if os.path.exists(audio_file_path):
                self.logger.info(f"Audio file created successfully: {os.path.getsize(audio_file_path)} bytes")
            else:
                self.logger.error(f"Failed to create audio file at {audio_file_path}")
                
            return audio_file_path
            
        except Exception as e:
            self.logger.error(f"Error generating audio file: {str(e)}")
            self.logger.debug(f"Exception details:", exc_info=True)
            return None
    
    def synthesize(self, text: str, session_id: Optional[str] = None) -> bytes:
        """
        Synthesize speech from text using direct file generation for better reliability.
        
        This implementation prioritizes successful audio generation over streaming and
        uses multiple fallback strategies to ensure audio is always produced.
        
        Args:
            text: The text to convert to speech
            session_id: Optional session ID for tracking generated audio
            
        Returns:
            WAV audio data as bytes
        """
        if not text:
            self.logger.warning("Empty text provided to synthesize")
            return self._generate_silence()
        
        # First check if AllTalk is available if we haven't recently
        if not hasattr(self, '_last_check_time') or time.time() - self._last_check_time > 60:
            self.available = self._check_server()
            self._last_check_time = time.time()
            self.logger.info(f"Refreshed AllTalk availability: {self.available}")
            
        if not self.available:
            self.logger.warning("AllTalk not available, using gTTS fallback")
            return self._synthesize_gtts(text)
            
        try:
            self.logger.info(f"Synthesizing with AllTalk: {len(text)} characters")
            start_time = time.time()
            
            # Generate a unique output filename
            timestamp = int(time.time())
            prefix = session_id[:8] if session_id else "vr"
            output_file = f"{prefix}_interview_{timestamp}"  # More unique filename
            
            # Store possible filenames for retrieval
            possible_files = [
                f"{output_file}.wav",
                f"{output_file}.wav.wav",
                output_file,
                f"{output_file}.mp3"
            ]
            self.last_output_file = possible_files[0]
            
            # Track all possible filenames with the session
            if session_id:
                if session_id not in self.generated_audio_files:
                    self.generated_audio_files[session_id] = []
                for file in possible_files:
                    self.generated_audio_files[session_id].append(file)
                    
            # Use the most reliable method: direct API call
            max_retries = 3
            retry_count = 0
            audio_data = None
            
            # Try direct API with retries
            while retry_count < max_retries and not audio_data:
                retry_count += 1
                self.logger.info(f"Direct API generation attempt {retry_count}/{max_retries}")
                try:
                    # First try the direct API method - most reliable
                    response = requests.post(
                        f"{self.base_url}/api/tts-generate",
                        data={
                            "text_input": text,
                            "character_voice_gen": self.voice,
                            "format": "wav",
                            "language": self.config.get('default_language', 'en'),
                            "output_file_name": output_file,
                            "output_file_timestamp": "true"
                        },
                        headers={
                            'Content-Type': 'application/x-www-form-urlencoded',
                            'Accept': 'audio/wav'
                        },
                        timeout=self.direct_api_timeout
                    )
                    
                    if response.status_code == 200 and response.content:
                        audio_data = response.content
                        self.logger.info(f"Direct API synthesis complete: {len(audio_data)} bytes")
                        
                        # Write to disk for retrieval later
                        try:
                            os.makedirs("audio_out", exist_ok=True)
                            with open(f"audio_out/{output_file}.wav", "wb") as f:
                                f.write(audio_data)
                            self.logger.info(f"Saved audio to file: audio_out/{output_file}.wav")
                        except Exception as e:
                            self.logger.warning(f"Could not save audio file: {e}")
                    else:
                        self.logger.warning(f"Direct API failed: status {response.status_code}")
                except Exception as e:
                    self.logger.warning(f"Direct API error: {e}")
                    
                # Wait before retry
                if not audio_data and retry_count < max_retries:
                    time.sleep(1)
                    
            # If direct API failed, try alternative API
            if not audio_data:
                self.logger.info("Direct API failed, trying alternative API endpoints")
                try:
                    # Try the file generation API
                    # This is a separate endpoint that has different parameters
                    file_gen_response = requests.post(
                        f"{self.base_url}/api/tts-generate-streaming",
                        data={
                            "text": text,
                            "voice": self.voice,
                            "language": self.config.get('default_language', 'en'),
                            "output_file": f"{output_file}.wav"
                        },
                        headers={'Content-Type': 'application/x-www-form-urlencoded'},
                        timeout=40  # Longer timeout for file generation
                    )
                    
                    if file_gen_response.status_code == 200:
                        self.logger.info("File generation API succeeded, waiting for file...")
                        # Wait for file to be generated
                        time.sleep(2)
                        
                        # Look for the file
                        output_paths_to_check = [
                            self.outputs_dir,
                            os.path.join(self.alltalk_dir, "outputs"),
                            "./audio_out",
                            "./outputs"
                        ]
                        
                        # Check each path and file pattern
                        for output_path in output_paths_to_check:
                            if not os.path.exists(output_path):
                                continue
                            
                            for ext in possible_files:
                                file_path = os.path.join(output_path, os.path.basename(ext))
                                if os.path.exists(file_path):
                                    with open(file_path, "rb") as f:
                                        audio_data = f.read()
                                    self.logger.info(f"Found and loaded file: {file_path}")
                                    break
                            
                            if audio_data:
                                break
                    else:
                        self.logger.warning(f"File generation API failed: {file_gen_response.status_code}")
                except Exception as e:
                    self.logger.warning(f"File generation API error: {e}")
            
            # If still no audio data, try last resort OpenTTS API
            if not audio_data:
                self.logger.info("Trying OpenTTS API as last resort")
                try:
                    open_tts_response = requests.post(
                        f"{self.base_url}/api/synthesize",
                        data={
                            "text": text,
                            "voice": self.voice,
                            "format": "wav",
                            "output_file": output_file
                        },
                        headers={
                            'Content-Type': 'application/x-www-form-urlencoded',
                            'Accept': 'audio/wav'
                        },
                        timeout=self.timeout
                    )
                    
                    if open_tts_response.status_code == 200 and open_tts_response.content:
                        audio_data = open_tts_response.content
                        self.logger.info(f"OpenTTS API succeeded: {len(audio_data)} bytes")
                except Exception as e:
                    self.logger.warning(f"OpenTTS API error: {e}")
                    
            # If all methods fail, fall back to gTTS
            if not audio_data:
                self.logger.warning("All AllTalk methods failed, falling back to gTTS")
                return self._synthesize_gtts(text)
                
            return audio_data
            
        except Exception as e:
            self.logger.error(f"Error in AllTalk synthesis: {e}")
            return self._synthesize_gtts(text)
    
    def _synthesize_gtts(self, text: str) -> bytes:
        """
        Fallback synthesis using gTTS.
        
        Args:
            text: The text to convert to speech
            
        Returns:
            WAV audio data as bytes
        """
        try:
            from gtts import gTTS
            import io
            from pydub import AudioSegment
            
            start_time = time.time()
            
            # Use gTTS to generate MP3
            tts = gTTS(text=text, lang=self.config.get('default_language', 'en'))
            mp3_fp = io.BytesIO()
            tts.write_to_fp(mp3_fp)
            mp3_fp.seek(0)
            
            # Convert MP3 to WAV
            audio = AudioSegment.from_mp3(mp3_fp)
            wav_fp = io.BytesIO()
            audio.export(wav_fp, format="wav")
            wav_fp.seek(0)
            audio_data = wav_fp.read()
            
            duration = time.time() - start_time
            self.logger.info(f"gTTS synthesis complete: {len(audio_data)} bytes in {duration:.2f}s")
            
            # Save to file for possible retrieval later
            output_file = f"vr_interview_gtts_{int(time.time())}"
            self.last_output_file = f"{output_file}.wav"
            
            try:
                os.makedirs("audio_out", exist_ok=True)
                with open(f"audio_out/{output_file}.wav", "wb") as f:
                    f.write(audio_data)
            except Exception as save_error:
                self.logger.warning(f"Failed to save gTTS audio file: {save_error}")
                
            return audio_data
            
        except Exception as e:
            self.logger.error(f"Error in gTTS synthesis: {e}\n{traceback.format_exc()}")
            self.logger.warning("Using silent audio as fallback")
            return self._generate_silence()
    
    def _generate_silence(self, duration_ms: int = 1000) -> bytes:
        """
        Generate silent audio as a last resort fallback.
        
        Args:
            duration_ms: Duration of silence in milliseconds
            
        Returns:
            WAV audio data as bytes
        """
        try:
            from pydub import AudioSegment
            import io
            
            silence = AudioSegment.silent(duration=duration_ms)
            wav_fp = io.BytesIO()
            silence.export(wav_fp, format="wav")
            wav_fp.seek(0)
            return wav_fp.read()
        except Exception as e:
            self.logger.error(f"Failed to generate silent audio: {e}")
            # Return an empty WAV file (44-byte header)
            return bytes.fromhex(
                "52494646" +  # "RIFF"
                "2C000000" +  # Chunk size (44 bytes)
                "57415645" +  # "WAVE"
                "666D7420" +  # "fmt "
                "10000000" +  # Subchunk1 size (16 bytes)
                "0100" +      # Audio format (1 = PCM)
                "0100" +      # Num channels (1)
                "44AC0000" +  # Sample rate (44100)
                "88580100" +  # Byte rate (44100*2)
                "0200" +      # Block align (2)
                "1000" +      # Bits per sample (16)
                "64617461" +  # "data"
                "00000000"    # Subchunk2 size (0 bytes of data)
            )
    
    def cleanup_old_files(self, max_age_hours: int = 24):
        """
        Clean up old audio files to prevent disk space issues.
        
        Args:
            max_age_hours: Maximum age of files to keep in hours
        """
        try:
            # Create list of common directories to check
            dirs_to_check = [
                "audio_out",
                "../audio_out"
            ]
            
            # Add AllTalk directory if configured
            alltalk_dir = self.alltalk_dir
            if alltalk_dir:
                dirs_to_check.append(f"{alltalk_dir}/audio_out")
                dirs_to_check.append(f"{alltalk_dir}/outputs")
                
            now = time.time()
            max_age_seconds = max_age_hours * 3600
            
            # Check each directory
            for directory in dirs_to_check:
                if not os.path.exists(directory):
                    continue
                    
                try:
                    for filename in os.listdir(directory):
                        if filename.startswith("vr_interview_") and (filename.endswith(".wav") or filename.endswith(".wav.wav")):
                            file_path = os.path.join(directory, filename)
                            file_age = now - os.path.getmtime(file_path)
                            
                            if file_age > max_age_seconds:
                                try:
                                    os.remove(file_path)
                                    self.logger.info(f"Removed old audio file: {file_path}")
                                except Exception as remove_error:
                                    self.logger.warning(f"Failed to remove old file {file_path}: {remove_error}")
                except Exception as dir_error:
                    self.logger.warning(f"Error checking directory {directory}: {dir_error}")
                    
        except Exception as e:
            self.logger.error(f"Error cleaning up old files: {e}")
    
    def clear_session_data(self, session_id: str):
        """
        Clear tracking data for a session when it ends.
        
        Args:
            session_id: The session ID to clear
        """
        if session_id in self.generated_audio_files:
            del self.generated_audio_files[session_id]
