import logging
import os
import tempfile
import io
from typing import Optional, Union
from gtts import gTTS


class TTSService:
    """
    Text-to-Speech service using gTTS (Google Text-to-Speech).
    
    This service converts text responses to speech audio for the virtual interviewer.
    """
    
    def __init__(self, model_name: str = "gtts"):
        self.model_name = model_name
        self.logger = logging.getLogger("tts")
        self.voice = "en"  # Default voice
        
        self.logger.info(f"Initializing TTS service with model: {model_name}")
        
    def synthesize(self, text: str) -> bytes:
        """
        Convert text to speech
        
        Args:
            text: Text to synthesize
            
        Returns:
            Audio data as bytes
        """
        if not text:
            self.logger.warning("Empty text provided for synthesis")
            return b""
            
        try:
            if self.model_name == "gtts":
                return self._synthesize_gtts(text)
            else:
                self.logger.warning(f"Unknown TTS model: {self.model_name}, falling back to gTTS")
                return self._synthesize_gtts(text)
                
        except Exception as e:
            self.logger.error(f"TTS synthesis error: {e}")
            # Return empty audio on error
            return b""
            
    def _synthesize_gtts(self, text: str) -> bytes:
        """
        Synthesize speech using Google Text-to-Speech
        
        Args:
            text: Text to synthesize
            
        Returns:
            Audio data as bytes
        """
        self.logger.info(f"Synthesizing with gTTS: {len(text)} characters")
        
        # Use io.BytesIO to avoid writing to disk
        mp3_fp = io.BytesIO()
        
        try:
            # Create gTTS object
            tts = gTTS(text=text, lang=self.voice, slow=False)
            
            # Save to BytesIO object
            tts.write_to_fp(mp3_fp)
            
            # Get the bytes
            mp3_fp.seek(0)
            audio_data = mp3_fp.read()
            
            self.logger.info(f"Synthesis complete: {len(audio_data)} bytes")
            return audio_data
            
        except Exception as e:
            self.logger.error(f"gTTS error: {e}")
            raise
        finally:
            mp3_fp.close()
            
    def set_voice(self, voice: str):
        """
        Set the voice to use for synthesis
        
        Args:
            voice: Voice identifier (e.g., 'en', 'en-us', 'en-gb')
        """
        self.voice = voice
        self.logger.info(f"Voice set to: {voice}")
        
    def get_available_voices(self) -> list:
        """
        Get list of available voices
        
        Returns:
            List of available voice identifiers
        """
        # For gTTS, we return the supported languages
        # In a real implementation, this would be more comprehensive
        return ["en", "en-us", "en-gb", "en-au", "fr", "de", "es", "it"]
