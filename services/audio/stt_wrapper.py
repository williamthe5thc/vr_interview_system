import logging
import os
import sys
import importlib
from typing import Union, Optional
import numpy as np

class STTService:
    """
    A wrapper for different Speech-to-Text services.
    This will try to use the OpenAI Whisper model first, then fall back to other implementations.
    """
    
    def __init__(self, model_name: str = "base"):
        self.model_name = model_name
        self.logger = logging.getLogger("stt_wrapper")
        self.logger.info(f"Initializing STT wrapper with model: {model_name}")
        
        # First try to load the original STT module
        self.original_stt = None
        try:
            # Directly try to use the original STT class but with safe import
            safe_whisper_import = False
            try:
                # Try to import whisper first to see if it works
                import whisper
                if hasattr(whisper, 'load_model'):
                    safe_whisper_import = True
                    self.logger.info("Detected proper OpenAI Whisper installation")
            except (ImportError, TypeError, AttributeError) as e:
                self.logger.warning(f"Whisper import error: {e}")
                
            if safe_whisper_import:
                # Original STT should now work since whisper import worked
                from .stt import STTService as OriginalSTT
                self.original_stt = OriginalSTT(model_name)
                self.logger.info("Successfully loaded original STT service")
        except Exception as e:
            self.logger.warning(f"Could not load original STT: {e}")
        
        # If original fails, try the simple STT
        if self.original_stt is None:
            try:
                from .simple_stt import SimpleSTTService
                self.original_stt = SimpleSTTService(model_name)
                self.logger.info("Using SimpleSTTService as fallback")
            except Exception as e:
                self.logger.warning(f"Could not load SimpleSTTService: {e}")
        
        # Set availability based on whether we found an implementation
        self.is_available = (self.original_stt is not None)
        if not self.is_available:
            self.logger.error("No STT implementation available!")
        else:
            self.logger.info("STT service initialized successfully")
        
    def transcribe(self, audio_data: Union[bytes, np.ndarray, str]) -> str:
        """
        Transcribe audio data to text using available STT implementation
        """
        if not self.is_available or self.original_stt is None:
            self.logger.error("No STT service available for transcription")
            return "I couldn't process your audio. Please check the server logs."
            
        try:
            self.logger.info(f"Transcribing using {type(self.original_stt).__name__}")
            result = self.original_stt.transcribe(audio_data)
            self.logger.info(f"Transcription complete: {len(result)} characters")
            return result
        except Exception as e:
            self.logger.error(f"Transcription error: {e}")
            return "I encountered an error while transcribing. Please try again."
            
    def get_model_info(self) -> dict:
        """
        Get information about the loaded model
        """
        if not self.is_available or self.original_stt is None:
            return {
                "name": self.model_name,
                "language": "unknown",
                "dimensions": {"width": 0, "height": 0},
            }
            
        try:
            return self.original_stt.get_model_info()
        except Exception as e:
            self.logger.error(f"Error getting model info: {e}")
            return {
                "name": self.model_name,
                "language": "error",
                "dimensions": {"width": 0, "height": 0},
            }
