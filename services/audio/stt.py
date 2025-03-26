"""
CUDA-Optimized Speech-to-Text service for VR Interview System.

This module implements enhanced Whisper model support with GPU acceleration.
"""

import logging
import os
import tempfile
import time
import torch
import numpy as np
from typing import Union, Optional


class STTService:
    """
    Speech-to-Text service using OpenAI's Whisper model with CUDA optimization.
    
    This service transcribes audio data to text with GPU acceleration when available.
    """
    
    def __init__(self, model_name: str = "medium"):
        self.model_name = model_name
        self.logger = logging.getLogger("stt")
        self.model = None  # Lazy-loaded on first use
        
        # Check for CUDA availability
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.logger.info(f"STT service initialized with device: {self.device}")
        
        if self.device == "cuda":
            self.logger.info(f"CUDA device: {torch.cuda.get_device_name(0)}")
            self.logger.info(f"CUDA version: {torch.version.cuda}")
            # Enable cuDNN auto-tuner for improved performance
            torch.backends.cudnn.benchmark = True
            
        # Check if whisper is available
        try:
            import whisper
            self.whisper = whisper
            self.is_available = True
            self.logger.info(f"Whisper module available, will use model: {model_name}")
        except ImportError:
            self.whisper = None
            self.logger.warning("Whisper module not available. Using dummy transcription.")
            self.is_available = False
            
    def _load_model(self):
        """
        Lazy-load the Whisper model with CUDA optimization
        """
        # Skip if whisper is not available
        if not self.is_available or self.whisper is None:
            self.logger.warning("Whisper is not available, skipping model loading")
            return
            
        if self.model is None:
            self.logger.info(f"Loading Whisper model: {self.model_name} on {self.device}")
            start_time = time.time()
            
            try:
                # Load the model directly to the correct device
                self.model = self.whisper.load_model(self.model_name).to(self.device)
                
                load_time = time.time() - start_time
                self.logger.info(f"Whisper model loaded successfully in {load_time:.2f}s")
                
                # Log GPU memory usage if using CUDA
                if self.device == "cuda":
                    allocated = torch.cuda.memory_allocated(0) / 1e9  # GB
                    reserved = torch.cuda.memory_reserved(0) / 1e9  # GB
                    self.logger.info(f"GPU memory after model load: {allocated:.2f}GB allocated, {reserved:.2f}GB reserved")
            except Exception as e:
                self.logger.error(f"Failed to load Whisper model: {e}")
                self.is_available = False  # Mark as unavailable after error
                self.logger.warning("Falling back to dummy transcription")
                return
                
    def transcribe(self, audio_data: Union[bytes, np.ndarray, str]) -> str:
        """
        Transcribe audio data to text with GPU acceleration when available
        
        Args:
            audio_data: Audio data as bytes, numpy array, or path to file
            
        Returns:
            Transcribed text
        """
        # Check if whisper is available
        if not self.is_available or self.whisper is None:
            # Return a dummy transcription for testing
            if isinstance(audio_data, bytes):
                # Return text based on the length of the audio data
                audio_length = len(audio_data)
                if audio_length < 50000:  # Short audio
                    return "Hello, can you tell me about your experience?"
                elif audio_length < 100000:  # Medium audio
                    return "What skills do you have that would be relevant for this position?"
                else:  # Long audio
                    return "Can you describe a challenging project you worked on and how you handled it?"
            elif isinstance(audio_data, str):
                # Return based on the content of the string
                return f"I simulated transcribing: {audio_data[:50]}..."
            else:
                return "Tell me about your qualifications for this position."
        
        # Ensure model is loaded if whisper is available
        self._load_model()
        
        try:
            # Free up GPU memory before processing if possible
            if self.device == "cuda":
                torch.cuda.empty_cache()
                
            start_time = time.time()
            
            # Handle different input types
            if isinstance(audio_data, bytes):
                # Save bytes to temporary file
                with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp_file:
                    tmp_file.write(audio_data)
                    tmp_path = tmp_file.name
                    
                # Transcribe from temporary file with CUDA optimization
                try:
                    # Use torch.no_grad to save memory
                    with torch.no_grad():
                        # Use FP16 for faster inference on GPU
                        if self.device == "cuda":
                            with torch.amp.autocast(device_type='cuda'):
                                result = self.model.transcribe(tmp_path, fp16=True)
                        else:
                            result = self.model.transcribe(tmp_path)
                finally:
                    # Clean up temporary file
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
                        
            elif isinstance(audio_data, np.ndarray):
                # Transcribe directly from numpy array with CUDA optimization
                with torch.no_grad():
                    if self.device == "cuda":
                        with torch.amp.autocast(device_type='cuda'):
                            result = self.model.transcribe(audio_data, fp16=True)
                    else:
                        result = self.model.transcribe(audio_data)
                
            elif isinstance(audio_data, str) and os.path.exists(audio_data):
                # Transcribe from file path with CUDA optimization
                with torch.no_grad():
                    if self.device == "cuda":
                        with torch.amp.autocast(device_type='cuda'):
                            result = self.model.transcribe(audio_data, fp16=True)
                    else:
                        result = self.model.transcribe(audio_data)
                
            else:
                raise ValueError("Unsupported audio data format")
                
            # Extract transcription text
            transcription = result.get("text", "").strip()
            elapsed = time.time() - start_time
            self.logger.info(f"Transcription complete: {len(transcription)} characters in {elapsed:.2f}s")
            
            # Clean up GPU memory after processing
            if self.device == "cuda":
                torch.cuda.empty_cache()
                
            return transcription
            
        except Exception as e:
            self.logger.error(f"Transcription error: {e}")
            return ""  # Return empty string on error
            
    def get_model_info(self) -> dict:
        """
        Get information about the loaded model
        """
        self._load_model()
        
        # Basic info
        info = {
            "name": self.model_name,
            "device": self.device,
            "cuda_available": torch.cuda.is_available(),
        }
        
        # Add model-specific info if available
        if self.model is not None:
            try:
                info["language"] = self.model.device.type
                info["dimensions"] = self.model.dims
                
                # Add GPU info if using CUDA
                if self.device == "cuda":
                    info["cuda_device"] = torch.cuda.get_device_name(0)
                    info["cuda_memory_allocated"] = f"{torch.cuda.memory_allocated(0) / 1e9:.2f}GB"
                    info["cuda_memory_reserved"] = f"{torch.cuda.memory_reserved(0) / 1e9:.2f}GB"
            except Exception as e:
                self.logger.warning(f"Error getting detailed model info: {e}")
                
        return info