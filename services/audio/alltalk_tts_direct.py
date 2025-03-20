"""
AllTalk TTS integration for VR Interview System using direct API only.

This module provides a simplified integration with the AllTalk TTS API
that only uses direct API calls and falls back to gTTS when needed.
"""

import requests
import json
import time
import logging
import os
import io
import traceback
from typing import Dict, Any, Optional


class AllTalkTTSDirectService:
    """
    AllTalk TTS service that uses only direct API calls with gTTS fallback.
    No streaming is used in this implementation.
    """
    
    def __init__(self, url=None, voice=None, config=None):
        self.logger = logging.getLogger("alltalk_tts_direct")
        
        # Store the URL
        self.base_url = url.rstrip('/') if url else "http://127.0.0.1:7851"
        self.logger.info(f"Initializing AllTalk TTS Direct with URL: {self.base_url}")
        
        # Store the voice
        self.voice = voice or "female_06.wav"
        
        # Store the config
        self.config = config or {}
        
        # Set timeout for API calls
        self.timeout = self.config.get('direct_api_timeout', 40)
        
        # Default to assuming API is available until server check
        self.direct_api_available = True
        
        # Get alltalk directory from config or use default
        self.alltalk_dir = self.config.get("alltalk_dir", "D:/AllTalk/alltalk_tts")
        self.outputs_dir = os.path.join(self.alltalk_dir, "outputs")
        
        # Check if directories exist and log
        self.logger.info(f"AllTalk directory set to: {self.alltalk_dir}")
        self.logger.info(f"AllTalk outputs directory set to: {self.outputs_dir}")
        
        # Check if AllTalk is available
        self.available = self._check_server()
        
        if self.available:
            self.logger.info(f"Initialized TTS service with voice: {self.voice}, using AllTalk Direct API")
        else:
            self.logger.warning(f"AllTalk service not available. Will use gTTS fallback.")
        
        # Create local audio directory for fallbacks
        os.makedirs("audio_out", exist_ok=True)
    
    def _check_server(self) -> bool:
        """Check if AllTalk server is available"""
        try:
            # Try the ready endpoint first
            self.logger.info(f"Testing AllTalk connection at {self.base_url}")
            
            for attempt in range(3):  # Try up to 3 times
                try:
                    response = requests.get(f"{self.base_url}/api/ready", timeout=5 + (attempt * 2))
                    if response.status_code == 200:
                        self.logger.info(f"AllTalk status endpoint available (attempt {attempt+1})")
                        break
                    else:
                        self.logger.warning(f"AllTalk returned non-200 status: {response.status_code}")
                        if attempt < 2:
                            time.sleep(1)
                except Exception as e:
                    self.logger.warning(f"Connection error on attempt {attempt+1}: {e}")
                    if attempt < 2:
                        time.sleep(1)
                    continue
            
            # Also check for voices
            try:
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
            except Exception as e:
                self.logger.warning(f"Could not retrieve voices: {e}")
            
            # Test direct API
            self.direct_api_available = self._test_direct_api()
            
            return self.direct_api_available
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
    
    def is_available(self) -> bool:
        """Check if AllTalk is available"""
        return self.available
        
    def get_available_voices(self):
        """Get available voices"""
        return getattr(self, 'voices', [])
    
    def synthesize(self, text: str, session_id: Optional[str] = None) -> bytes:
        """
        Synthesize speech from text using direct API call with gTTS fallback.
        
        Args:
            text: The text to convert to speech
            session_id: Optional session ID (not used in direct version)
            
        Returns:
            WAV audio data as bytes
        """
        if not text:
            self.logger.warning("Empty text provided to synthesize")
            return self._generate_silence()
        
        # Check if AllTalk is available if we haven't recently
        if not hasattr(self, '_last_check_time') or time.time() - self._last_check_time > 60:
            self.available = self._check_server()
            self._last_check_time = time.time()
            
        if not self.available:
            self.logger.warning("AllTalk not available, using gTTS fallback")
            return self._synthesize_gtts(text)
            
        try:
            self.logger.info(f"Synthesizing with AllTalk direct API: {len(text)} characters")
            
            # Try multiple API endpoints in sequence for best reliability
            audio_data = None
            methods_to_try = [
                self._try_tts_generate_api,
                self._try_synthesize_api,
                self._try_tts_api
            ]
            
            # Try each method until one succeeds
            for method in methods_to_try:
                try:
                    audio_data = method(text)
                    if audio_data and len(audio_data) > 1000:
                        self.logger.info(f"Successfully generated audio using {method.__name__}: {len(audio_data)} bytes")
                        break
                except Exception as e:
                    self.logger.warning(f"Method {method.__name__} failed: {e}")
            
            # If all methods fail, fall back to gTTS
            if not audio_data or len(audio_data) < 1000:
                self.logger.warning("All AllTalk methods failed, falling back to gTTS")
                return self._synthesize_gtts(text)
                
            return audio_data
            
        except Exception as e:
            self.logger.error(f"Error in AllTalk synthesis: {e}")
            return self._synthesize_gtts(text)
            
    def _try_tts_generate_api(self, text: str) -> Optional[bytes]:
        """Try generating speech using tts-generate API"""
        try:
            # Create a safe output filename without special characters
            timestamp = int(time.time())
            output_file = f"vr_interview_{timestamp}"
            
            response = requests.post(
                f"{self.base_url}/api/tts-generate",
                data={
                    "text_input": text,
                    "character_voice_gen": self.voice,
                    "format": "wav",
                    "output_file_name": output_file
                },
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=self.timeout
            )
            
            # Fixed: Status code 200 means SUCCESS, not failure!
            if response.status_code == 200:
                # Check if meaningful content was returned
                if len(response.content) > 1000:
                    # Save to local file for caching
                    try:
                        with open(f"audio_out/{output_file}.wav", "wb") as f:
                            f.write(response.content)
                    except Exception as e:
                        self.logger.warning(f"Could not save audio file: {e}")
                        
                    self.logger.info(f"tts-generate successful: {len(response.content)} bytes")
                    return response.content
                else:
                    # AllTalk might have written to file instead of returning content
                    self.logger.info(f"tts-generate returned success status with minimal content. Looking for output file...")
                    # Try to find and load the file
                    audio_data = self._try_load_output_file(output_file)
                    if audio_data:
                        self.logger.info(f"Found AllTalk output file with {len(audio_data)} bytes")
                        return audio_data
                        
                    self.logger.warning(f"tts-generate returned success status but no audio data could be found")
                    
            else:
                self.logger.warning(f"tts-generate call failed with status code: {response.status_code}")
            return None
        except Exception as e:
            self.logger.warning(f"Error using tts-generate API: {e}")
            return None
            
    def _try_synthesize_api(self, text: str) -> Optional[bytes]:
        """Try generating speech using synthesize API"""
        try:
            response = requests.post(
                f"{self.base_url}/api/synthesize",
                data={
                    "text": text,
                    "voice": self.voice,
                    "format": "wav"
                },
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                if len(response.content) > 1000:
                    # Save to local file for caching
                    timestamp = int(time.time())
                    output_file = f"vr_interview_synth_{timestamp}"
                    try:
                        with open(f"audio_out/{output_file}.wav", "wb") as f:
                            f.write(response.content)
                    except Exception as e:
                        self.logger.warning(f"Could not save audio file: {e}")
                        
                    self.logger.info(f"synthesize successful: {len(response.content)} bytes")
                    return response.content
                else:
                    # AllTalk might have written to file instead of returning content
                    output_file = f"vr_interview_synth_{int(time.time())}"
                    audio_data = self._try_load_output_file(output_file)
                    if audio_data:
                        return audio_data
                        
                    self.logger.warning(f"synthesize returned success status but no audio data")
                    
            self.logger.warning(f"synthesize call failed: {response.status_code}")
            return None
        except Exception as e:
            self.logger.warning(f"Error using synthesize API: {e}")
            return None
            
    def _try_tts_api(self, text: str) -> Optional[bytes]:
        """Try generating speech using tts API"""
        try:
            response = requests.post(
                f"{self.base_url}/tts",
                json={
                    "text": text,
                    "voice": self.voice
                },
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                if len(response.content) > 1000:
                    # Save to local file for caching
                    timestamp = int(time.time())
                    output_file = f"vr_interview_tts_{timestamp}"
                    try:
                        with open(f"audio_out/{output_file}.wav", "wb") as f:
                            f.write(response.content)
                    except Exception as e:
                        self.logger.warning(f"Could not save audio file: {e}")
                        
                    self.logger.info(f"tts API successful: {len(response.content)} bytes")
                    return response.content
                else:
                    # AllTalk might have written to file instead of returning content
                    output_file = f"vr_interview_tts_{int(time.time())}"
                    audio_data = self._try_load_output_file(output_file)
                    if audio_data:
                        return audio_data
                        
                    self.logger.warning(f"tts API returned success status but no audio data")
                    
            self.logger.warning(f"tts call failed: {response.status_code}")
            return None
        except Exception as e:
            self.logger.warning(f"Error using tts API: {e}")
            return None
    
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
            timestamp = int(time.time())
            output_file = f"vr_interview_gtts_{timestamp}"
            
            try:
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
    
    def _try_load_output_file(self, filename_base: str) -> Optional[bytes]:
        """
        Try to find and load AllTalk output file from possible locations.
        
        Args:
            filename_base: Base filename without extension
            
        Returns:
            Audio data as bytes if found, None otherwise
        """
        # Log all files in the outputs directory for debugging
        try:
            self.logger.info(f"Looking for AllTalk output file with base name: {filename_base}")
            if os.path.exists(self.outputs_dir):
                files = os.listdir(self.outputs_dir)
                self.logger.info(f"Found {len(files)} files in outputs directory: {', '.join(files[:10])}{'...' if len(files) > 10 else ''}")
                
                # Look for filenames containing our base name (AllTalk might append timestamps or other info)
                matching_files = [f for f in files if filename_base in f]
                if matching_files:
                    self.logger.info(f"Found potential matching files: {matching_files}")
                    
                    # Use the most recent matching file
                    matching_files.sort(key=lambda f: os.path.getmtime(os.path.join(self.outputs_dir, f)), reverse=True)
                    most_recent = matching_files[0]
                    self.logger.info(f"Using most recent matching file: {most_recent}")
                    
                    with open(os.path.join(self.outputs_dir, most_recent), "rb") as f:
                        data = f.read()
                        if len(data) > 1000:
                            self.logger.info(f"Successfully loaded audio file: {most_recent} ({len(data)} bytes)")
                            return data
        except Exception as e:
            self.logger.warning(f"Error examining outputs directory: {e}")
        
        # If we didn't find a match above, try standard locations
        possible_paths = [
            os.path.join(self.outputs_dir, f"{filename_base}.wav"),
            os.path.join(self.outputs_dir, f"{filename_base}_gen.wav"),
            os.path.join(self.alltalk_dir, "outputs", f"{filename_base}.wav"),
            os.path.join(self.alltalk_dir, "outputs", f"{filename_base}_gen.wav"),
            f"audio_out/{filename_base}.wav",
            # Add AllTalk's 'outputs' directory at its root
            os.path.join(self.alltalk_dir, "outputs", "temp.wav"),
            # Try the last generated file regardless of name
            self._find_most_recent_wav(self.outputs_dir)
        ]
        
        # Filter out None values (from _find_most_recent_wav)
        possible_paths = [p for p in possible_paths if p]
        
        for path in possible_paths:
            try:
                if os.path.exists(path):
                    self.logger.info(f"Found generated audio file: {path}")
                    with open(path, "rb") as f:
                        data = f.read()
                        if len(data) > 1000:
                            self.logger.info(f"Successfully loaded audio file: {path} ({len(data)} bytes)")
                            return data
            except Exception as e:
                self.logger.warning(f"Error reading potential file {path}: {e}")
        
        self.logger.warning(f"Could not find any audio file for {filename_base}")
        return None
        
    def _find_most_recent_wav(self, directory):
        """Find the most recently modified WAV file in the directory"""
        try:
            if not os.path.exists(directory):
                return None
                
            wav_files = [f for f in os.listdir(directory) if f.endswith('.wav')]
            if not wav_files:
                return None
                
            wav_files.sort(key=lambda f: os.path.getmtime(os.path.join(directory, f)), reverse=True)
            return os.path.join(directory, wav_files[0])
        except Exception as e:
            self.logger.warning(f"Error finding most recent WAV file: {e}")
            return None
        
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
            
            now = time.time()
            max_age_seconds = max_age_hours * 3600
            
            # Check each directory
            for directory in dirs_to_check:
                if not os.path.exists(directory):
                    continue
                    
                try:
                    for filename in os.listdir(directory):
                        if filename.startswith("vr_interview_") and (filename.endswith(".wav") or filename.endswith(".mp3")):
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
