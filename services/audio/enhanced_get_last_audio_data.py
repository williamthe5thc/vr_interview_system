"""
Enhanced version of get_last_audio_data function for AllTalk TTS integration.

This file contains an improved implementation of the get_last_audio_data method
that provides more robust file discovery and fallback mechanisms.
"""

import os
import time
import logging
import requests
import traceback
from typing import Optional, List, Set

logger = logging.getLogger("alltalk_tts")

def enhanced_get_last_audio_data(self, session_id: Optional[str] = None) -> Optional[bytes]:
    """
    Enhanced retrieval of audio data for the most recently generated file for a session
    with improved file discovery and fallbacks.
    
    Args:
        session_id: Optional session ID to get session-specific file
        
    Returns:
        Audio data as bytes if available, None otherwise
    """
    try:
        # Try to find the most recent files for this session
        target_files = []
        
        # DIAGNOSTIC: Log file tracking data
        logger.info(f"==== ENHANCED AUDIO FILE RETRIEVAL DIAGNOSTICS =====")
        logger.info(f"Session ID: {session_id}")
        logger.info(f"All generated files: {self.generated_audio_files}")
        logger.info(f"Last output file: {self.last_output_file}")
        
        if session_id and session_id in self.generated_audio_files:
            # Get all files for this session
            if self.generated_audio_files[session_id]:
                target_files = self.generated_audio_files[session_id]
                logger.info(f"Found {len(target_files)} session-specific files: {target_files[-5:] if len(target_files) > 5 else target_files}")
        
        # Fall back to last output file if no session-specific files
        if not target_files and self.last_output_file:
            target_files = [self.last_output_file]
            logger.info(f"Using last output file: {self.last_output_file}")
            
        if not target_files:
            logger.warning("No recent audio files found to retrieve")
            return None
        
        # Get list of all possible file variations to check
        possible_extensions = []
        
        # Start with the target files as is
        for target_file in target_files:
            # Add variations of each target file
            possible_extensions.extend([
                target_file,  # Original target (complete path)
                target_file + ".wav",  # Add .wav if missing
                target_file + ".wav.wav",  # Add .wav.wav if missing
                target_file.replace(".wav.wav", ".wav"),  # Replace double with single
                target_file.replace(".wav", "") + ".wav",  # Strip and re-add .wav
                # Also handle the case where the target already includes the path
                os.path.basename(target_file),  # Just the filename
                os.path.basename(target_file) + ".wav",
                os.path.basename(target_file) + ".wav.wav",
            ])
        
        # Get the base names for later use in similar file search
        base_names = set()
        for target_file in target_files:
            base_name = os.path.basename(target_file).split('.')[0]
            base_names.add(base_name)
        logger.info(f"Base filenames for search: {base_names}")
        
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
        
        # FIRST PASS: Check all possible combinations of paths and filenames
        for output_path in output_paths_to_check:
            if not os.path.exists(output_path):
                logger.info(f"Output path doesn't exist: {output_path}")
                continue
                
            # List all files in this directory
            try:
                dir_files = os.listdir(output_path)
                logger.info(f"Found {len(dir_files)} files in {output_path}")
                
                # Look for exact filename matches first
                for ext in possible_extensions:
                    filename = os.path.basename(ext)
                    if filename in dir_files:
                        file_path = os.path.join(output_path, filename)
                        logger.info(f"Found exact match: {file_path}")
                        try:
                            with open(file_path, "rb") as f:
                                audio_data = f.read()
                            if len(audio_data) > 1000:  # Basic check to ensure it's an actual audio file
                                logger.info(f"Retrieved audio from {file_path}: {len(audio_data)} bytes")
                                return audio_data
                            else:
                                logger.warning(f"Retrieved file {file_path} seems too small: {len(audio_data)} bytes")
                        except Exception as e:
                            logger.warning(f"Error reading file {file_path}: {e}")
                
                # Look for files containing the base names
                similar_files = []
                for base_name in base_names:
                    similar_files.extend([f for f in dir_files if base_name in f and f.endswith(".wav")])
                
                if similar_files:
                    logger.info(f"Found {len(similar_files)} similar files: {similar_files[:5]}")
                    
                    # Sort by modification time (newest first)
                    similar_files.sort(key=lambda f: os.path.getmtime(os.path.join(output_path, f)), reverse=True)
                    
                    # Try the newest 3 similar files in case the most recent is corrupted
                    for i, similar_file in enumerate(similar_files[:3]):
                        file_path = os.path.join(output_path, similar_file)
                        try:
                            with open(file_path, "rb") as f:
                                audio_data = f.read()
                            if len(audio_data) > 1000:  # Basic check to ensure it's an actual audio file
                                logger.info(f"Retrieved audio from similar file {file_path}: {len(audio_data)} bytes")
                                return audio_data
                            else:
                                logger.warning(f"Similar file {file_path} seems too small: {len(audio_data)} bytes")
                        except Exception as e:
                            logger.warning(f"Error reading similar file {i+1}/3: {e}")
                            
            except Exception as e:
                logger.warning(f"Error listing directory {output_path}: {e}")
        
        # SECOND PASS: Broader search for any recent WAV files
        logger.info(f"First pass failed to find files, trying broader search...")
        for output_path in output_paths_to_check:
            if not os.path.exists(output_path):
                continue
                
            try:
                # Find all WAV files and sort by modification time (newest first)
                wav_files = [f for f in os.listdir(output_path) if f.endswith(".wav")]
                if wav_files:
                    wav_files.sort(key=lambda f: os.path.getmtime(os.path.join(output_path, f)), reverse=True)
                    logger.info(f"Found {len(wav_files)} WAV files, trying newest 3")
                    
                    # Try the 3 newest files
                    for newest_file in wav_files[:3]:
                        file_path = os.path.join(output_path, newest_file)
                        try:
                            with open(file_path, "rb") as f:
                                audio_data = f.read()
                            if len(audio_data) > 1000:
                                logger.info(f"Retrieved audio from recent file {file_path}: {len(audio_data)} bytes")
                                return audio_data
                        except Exception as e:
                            logger.warning(f"Error reading recent file: {e}")
            except Exception as e:
                logger.warning(f"Error during broad search in {output_path}: {e}")
        
        # If we get here, we couldn't find the file - try to make a new request to AllTalk
        logger.warning(f"Could not find audio file in any location, attempting to recreate")
        
        # Try a direct HTTP request to the API endpoint for the file
        for target_file in target_files[-3:]:  # Try the 3 most recent files
            try:
                file_url = f"{self.base_url}/audio/{os.path.basename(target_file)}"
                logger.info(f"Attempting to download directly from: {file_url}")
                
                response = requests.get(file_url, timeout=10)  # Increased timeout
                if response.status_code == 200 and len(response.content) > 1000:
                    logger.info(f"Successfully downloaded audio directly: {len(response.content)} bytes")
                    return response.content
            except Exception as http_err:
                logger.warning(f"HTTP request for file {target_file} failed: {http_err}")
            
            # Try alternate URL pattern
            try:
                file_url = f"{self.base_url}/outputs/{os.path.basename(target_file)}"
                logger.info(f"Attempting alternate download URL: {file_url}")
                
                response = requests.get(file_url, timeout=10)
                if response.status_code == 200 and len(response.content) > 1000:
                    logger.info(f"Successfully downloaded audio from alternate URL: {len(response.content)} bytes")
                    return response.content
            except Exception as http_err:
                logger.warning(f"Alternate HTTP request failed: {http_err}")
                
        # Try a direct API call to generate new audio as a last resort
        try:
            logger.info(f"Attempting to regenerate audio via direct API as last resort")
            # We can use the original text if we have it from a session context
            session = None
            if hasattr(self, 'state_manager'):
                session = self.state_manager.get_session(session_id)
                
            if session and hasattr(session, 'get_last_response'):
                text = session.get_last_response()
                if text:
                    logger.info(f"Retrieved text from session: {text[:30]}...")
                    audio_data = self._synthesize_gtts(text)
                    if audio_data and len(audio_data) > 1000:
                        logger.info(f"Successfully generated fallback audio via gTTS: {len(audio_data)} bytes")
                        return audio_data
        except Exception as e:
            logger.warning(f"Failed to generate new audio: {e}")
        
        # Nothing worked - return None
        logger.error(f"All audio retrieval methods failed for session {session_id}")
        return None
            
    except Exception as e:
        logger.error(f"Error retrieving last audio data: {e}")
        logger.error(traceback.format_exc())
        return None
