import logging
import os
import tempfile
import whisper
import numpy as np
from typing import Union, Optional


class STTService:
    """
    Speech-to-Text service using OpenAI's Whisper model.
    
    This service transcribes audio data to text, optimized for the interview context.
    """
    
    def __init__(self, model_name: str = "base"):
        self.model_name = model_name
        self.logger = logging.getLogger("stt")
        self.model = None  # Lazy-loaded on first use
        
        self.logger.info(f"Initializing STT service with model: {model_name}")
        
    def _load_model(self):
        """
        Lazy-load the Whisper model
        """
        if self.model is None:
            self.logger.info(f"Loading Whisper model: {self.model_name}")
            try:
                self.model = whisper.load_model(self.model_name)
                self.logger.info("Whisper model loaded successfully")
            except Exception as e:
                self.logger.error(f"Failed to load Whisper model: {e}")
                raise
                
    def transcribe(self, audio_data: Union[bytes, np.ndarray, str]) -> str:
        """
        Transcribe audio data to text
        
        Args:
            audio_data: Audio data as bytes, numpy array, or path to file
            
        Returns:
            Transcribed text
        """
        # Ensure model is loaded
        self._load_model()
        
        try:
            # Handle different input types
            if isinstance(audio_data, bytes):
                # Save bytes to temporary file
                with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp_file:
                    tmp_file.write(audio_data)
                    tmp_path = tmp_file.name
                    
                # Transcribe from temporary file
                try:
                    result = self.model.transcribe(tmp_path)
                finally:
                    # Clean up temporary file
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
                        
            elif isinstance(audio_data, np.ndarray):
                # Transcribe directly from numpy array
                result = self.model.transcribe(audio_data)
                
            elif isinstance(audio_data, str) and os.path.exists(audio_data):
                # Transcribe from file path
                result = self.model.transcribe(audio_data)
                
            else:
                raise ValueError("Unsupported audio data format")
                
            # Extract transcription text
            transcription = result.get("text", "").strip()
            self.logger.info(f"Transcription complete: {len(transcription)} characters")
            
            return transcription
            
        except Exception as e:
            self.logger.error(f"Transcription error: {e}")
            return ""  # Return empty string on error
            
    def get_model_info(self) -> dict:
        """
        Get information about the loaded model
        """
        self._load_model()
        return {
            "name": self.model_name,
            "language": self.model.device.type,
            "dimensions": self.model.dims,
        }
