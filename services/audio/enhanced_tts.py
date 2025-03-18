"""
Enhanced TTS Service with multiple engine support.
This module provides a unified interface for multiple TTS engines,
with automatic fallback and streaming support for faster responses.
"""

import logging
import time
import os
import io
import hashlib
import json
import importlib
from typing import Dict, Any, List, Optional, Callable
import asyncio
from concurrent.futures import ThreadPoolExecutor


class EnhancedTTSService:
    """
    Enhanced TTS service with multiple engine support, fallback, and streaming.
    """
    
    def __init__(self, config=None):
        self.logger = logging.getLogger("enhanced_tts")
        
        # Default configuration
        self.config = {
            "primary_engine": "piper",  # Default primary engine
            "fallback_order": ["alltalk", "gtts"],  # Fallback order
            "streaming": True,          # Enable streaming synthesis
            "cache_enabled": True,      # Enable caching
            "cache_dir": "data/tts_cache/enhanced",  # Cache directory
            "max_cache_entries": 2000,  # Maximum cache entries
            "engines": {
                "piper": {
                    "enabled": True,
                    "voice": "en_US-lessac-medium",
                    "model_dir": "./models/piper"
                },
                "emotivoice": {
                    "enabled": False,  # Disabled by default
                    "url": "http://localhost:8501",
                    "voice": "default",
                    "language": "en"
                },
                "alltalk": {
                    "enabled": True,
                    "url": "http://127.0.0.1:7851",
                    "voice": "Clint_Eastwood CC3 (enhanced).wav"
                },
                "gtts": {
                    "enabled": True,
                    "language": "en"
                }
            }
        }
        
        # Update with provided config
        if config:
            # Merge config recursively
            self._merge_config(self.config, config)
        
        # Initialize engines
        self.engines = {}
        self._initialize_engines()
        
        # Initialize cache
        if self.config["cache_enabled"]:
            os.makedirs(self.config["cache_dir"], exist_ok=True)
            self.cache = {}
            self._load_cache_index()
        
        # Initialize thread pool
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        self.logger.info(f"Enhanced TTS service initialized with primary engine: {self.config['primary_engine']}")
    
    def _merge_config(self, base_config: Dict, new_config: Dict) -> None:
        """Recursively merge configuration dictionaries."""
        for key, value in new_config.items():
            if key in base_config and isinstance(base_config[key], dict) and isinstance(value, dict):
                self._merge_config(base_config[key], value)
            else:
                base_config[key] = value
    
    def _initialize_engines(self) -> None:
        """Initialize all enabled TTS engines."""
        # Try to import and initialize each engine
        for engine_name, engine_config in self.config["engines"].items():
            if not engine_config.get("enabled", False):
                self.logger.info(f"TTS engine '{engine_name}' is disabled in config")
                continue
                
            try:
                self._init_engine(engine_name, engine_config)
            except Exception as e:
                self.logger.error(f"Failed to initialize TTS engine '{engine_name}': {e}")
        
        # Check if primary engine is available
        primary = self.config["primary_engine"]
        if primary not in self.engines or not self.engines[primary]:
            self.logger.warning(f"Primary TTS engine '{primary}' not available")
            
            # Try to find first available engine in fallback order
            for fallback in self.config["fallback_order"]:
                if fallback in self.engines and self.engines[fallback]:
                    self.logger.info(f"Using '{fallback}' as primary TTS engine instead")
                    self.config["primary_engine"] = fallback
                    break
    
    def _init_engine(self, engine_name: str, config: Dict) -> None:
        """Initialize a specific TTS engine."""
        try:
            if engine_name == "piper":
                try:
                    from .tts_providers.piper_tts import PiperTTSService
                    self.engines["piper"] = PiperTTSService(
                        voice=config.get("voice", "en_US-lessac-medium"),
                        model_dir=config.get("model_dir", "./models/piper")
                    )
                    self.logger.info("Piper TTS engine initialized")
                except ImportError:
                    self.logger.warning("Piper TTS not available: module not found")
                    self.engines["piper"] = None
                    
            elif engine_name == "emotivoice":
                try:
                    from .tts_providers.emotivoice_tts import EmotiVoiceTTSService
                    self.engines["emotivoice"] = EmotiVoiceTTSService(config)
                    available = self.engines["emotivoice"].is_available()
                    self.logger.info(f"EmotiVoice TTS engine initialized (available: {available})")
                    if not available:
                        self.engines["emotivoice"] = None
                except ImportError:
                    self.logger.warning("EmotiVoice TTS not available: module not found")
                    self.engines["emotivoice"] = None
                    
            elif engine_name == "alltalk":
                try:
                    from .alltalk_tts_improved import AllTalkTTSService
                    self.engines["alltalk"] = AllTalkTTSService(
                        config.get("url"),
                        config.get("voice"),
                        config
                    )
                    available = self.engines["alltalk"].is_available()
                    self.logger.info(f"AllTalk TTS engine initialized (available: {available})")
                    if not available:
                        self.engines["alltalk"] = None
                except ImportError:
                    self.logger.warning("AllTalk TTS not available: module not found")
                    self.engines["alltalk"] = None
                    
            elif engine_name == "gtts":
                try:
                    # Import default TTS fallback
                    from .tts import TTSService
                    self.engines["gtts"] = TTSService(config.get("language", "en"))
                    self.logger.info("gTTS engine initialized as fallback")
                except ImportError:
                    self.logger.warning("gTTS not available: module not found")
                    self.engines["gtts"] = None
                    
            else:
                self.logger.warning(f"Unknown TTS engine: {engine_name}")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize '{engine_name}' TTS engine: {e}")
            self.engines[engine_name] = None
    
    def synthesize(self, text: str, engine: str = None, emotion: str = None) -> bytes:
        """
        Synthesize speech from text using the configured TTS engines.
        
        Args:
            text: The text to synthesize
            engine: Optional engine override (piper, emotivoice, alltalk, gtts)
            emotion: Optional emotion for engines that support it
            
        Returns:
            WAV audio data as bytes
        """
        if not text or not text.strip():
            self.logger.warning("Empty text provided to TTS")
            return self._generate_silence()
        
        # Check cache first if enabled
        if self.config["cache_enabled"]:
            cache_key = self._create_cache_key(text, engine, emotion)
            cached_audio = self._get_from_cache(cache_key)
            if cached_audio:
                self.logger.info(f"Using cached TTS audio for: {text[:30]}...")
                return cached_audio
        
        # Use specified engine or primary
        engine_to_use = engine or self.config["primary_engine"]
        
        # Check if engine is available
        if engine_to_use not in self.engines or not self.engines[engine_to_use]:
            self.logger.warning(f"TTS engine '{engine_to_use}' not available, trying fallbacks")
            
            # Try fallbacks in order
            fallbacks = [engine_to_use] + self.config["fallback_order"]
            for fallback in fallbacks:
                if fallback in self.engines and self.engines[fallback]:
                    engine_to_use = fallback
                    self.logger.info(f"Using '{fallback}' TTS engine")
                    break
            else:
                # No engine available
                self.logger.error("No TTS engine available")
                return self._generate_silence()
        
        # For sentences longer than 100 characters and streaming enabled, use sentence streaming
        if len(text) > 100 and self.config["streaming"] and not engine and not emotion:
            return self._synthesize_by_sentences(text)
            
        start_time = time.time()
        
        try:
            # Synthesize using the selected engine
            if engine_to_use == "piper":
                audio_data = self.engines[engine_to_use].synthesize(text)
            elif engine_to_use == "emotivoice":
                audio_data = self.engines[engine_to_use].synthesize(text, emotion)
            elif engine_to_use == "alltalk":
                audio_data = self.engines[engine_to_use].synthesize(text)
            elif engine_to_use == "gtts":
                audio_data = self.engines[engine_to_use].synthesize(text)
            else:
                self.logger.error(f"Unknown TTS engine: {engine_to_use}")
                return self._generate_silence()
            
            elapsed = time.time() - start_time
            self.logger.info(f"TTS synthesis complete ({engine_to_use}): {len(audio_data)} bytes in {elapsed:.2f}s")
            
            # Cache the result if enabled
            if self.config["cache_enabled"]:
                cache_key = self._create_cache_key(text, engine_to_use, emotion)
                self._add_to_cache(cache_key, audio_data)
            
            return audio_data
            
        except Exception as e:
            self.logger.error(f"Error in TTS synthesis with {engine_to_use}: {e}")
            
            # Try one more fallback if we haven't already
            if engine_to_use != "gtts" and "gtts" in self.engines and self.engines["gtts"]:
                self.logger.info("Falling back to gTTS after error")
                try:
                    return self.engines["gtts"].synthesize(text)
                except Exception as fallback_error:
                    self.logger.error(f"Error in gTTS fallback: {fallback_error}")
            
            return self._generate_silence()
    
    def _synthesize_by_sentences(self, text: str) -> bytes:
        """Synthesize text by breaking it into sentences for faster response."""
        sentences = self._split_into_sentences(text)
        audio_chunks = []
        
        for sentence in sentences:
            if not sentence.strip():
                continue
            
            # Generate audio for each sentence
            sentence_cache_key = self._create_cache_key(sentence)
            cached_audio = self._get_from_cache(sentence_cache_key)
            
            if cached_audio:
                audio_chunks.append(cached_audio)
            else:
                # Synthesize this sentence
                sentence_audio = self.synthesize(sentence, self.config["primary_engine"])
                audio_chunks.append(sentence_audio)
        
        # Combine all audio chunks
        combined_audio = self._combine_audio_chunks(audio_chunks)
        
        # Cache the combined result
        if self.config["cache_enabled"]:
            cache_key = self._create_cache_key(text)
            self._add_to_cache(cache_key, combined_audio)
        
        return combined_audio
    
    async def stream_synthesize(self, text: str, callback: Callable[[bytes, bool], None]) -> bytes:
        """
        Stream synthesis sentence by sentence with callback for each chunk.
        
        Args:
            text: Text to synthesize
            callback: Function called for each audio chunk with (audio_data, is_last_chunk)
            
        Returns:
            Complete audio data
        """
        sentences = self._split_into_sentences(text)
        all_chunks = []
        
        for i, sentence in enumerate(sentences):
            if not sentence.strip():
                continue
            
            is_last = i == len(sentences) - 1
            
            # Check cache first
            cache_key = self._create_cache_key(sentence)
            audio = self._get_from_cache(cache_key) or self.synthesize(sentence)
            
            # Add to result
            all_chunks.append(audio)
            
            # Call callback with this chunk
            await callback(audio, is_last)
        
        # Combine all chunks
        return self._combine_audio_chunks(all_chunks)
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences for incremental processing."""
        import re
        # Split on common sentence terminators followed by space or end
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return sentences
    
    def _combine_audio_chunks(self, chunks: List[bytes]) -> bytes:
        """Combine multiple audio chunks into one audio file."""
        if not chunks:
            return self._generate_silence()
        
        # If only one chunk, return it directly
        if len(chunks) == 1:
            return chunks[0]
        
        try:
            from pydub import AudioSegment
            
            combined = AudioSegment.empty()
            for chunk in chunks:
                segment = AudioSegment.from_wav(io.BytesIO(chunk))
                combined += segment
            
            # Export to WAV
            output = io.BytesIO()
            combined.export(output, format="wav")
            output.seek(0)
            return output.read()
            
        except Exception as e:
            self.logger.error(f"Error combining audio chunks: {e}")
            # Return the first chunk as fallback
            return chunks[0] if chunks else self._generate_silence()
    
    def _create_cache_key(self, text: str, engine: str = None, emotion: str = None) -> str:
        """Create a unique cache key for the request."""
        engine_to_use = engine or self.config["primary_engine"]
        emotion_str = f"_{emotion}" if emotion else ""
        key_string = f"{engine_to_use}{emotion_str}_{text}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_from_cache(self, key: str) -> Optional[bytes]:
        """Get audio data from cache if available."""
        if not self.config["cache_enabled"] or key not in self.cache:
            return None
            
        cache_path = self.cache[key]
        try:
            if os.path.exists(cache_path):
                with open(cache_path, 'rb') as f:
                    return f.read()
        except Exception as e:
            self.logger.warning(f"Failed to read from cache: {e}")
        
        return None
    
    def _add_to_cache(self, key: str, audio_data: bytes) -> None:
        """Add audio data to cache."""
        if not self.config["cache_enabled"]:
            return
            
        if len(self.cache) >= self.config["max_cache_entries"]:
            # Remove oldest entries (10%)
            entries = list(self.cache.items())
            entries.sort(key=lambda x: os.path.getmtime(x[1]) if os.path.exists(x[1]) else 0)
            for old_key, old_path in entries[:max(1, len(entries) // 10)]:
                try:
                    if os.path.exists(old_path):
                        os.unlink(old_path)
                    del self.cache[old_key]
                except Exception as e:
                    self.logger.warning(f"Failed to remove cache entry: {e}")
        
        # Save new cache entry
        cache_path = os.path.join(self.config["cache_dir"], f"{key}.wav")
        try:
            with open(cache_path, 'wb') as f:
                f.write(audio_data)
            self.cache[key] = cache_path
            self._save_cache_index()
        except Exception as e:
            self.logger.error(f"Failed to cache audio: {e}")
    
    def _load_cache_index(self) -> None:
        """Load cache index from disk."""
        if not self.config["cache_enabled"]:
            return
            
        index_path = os.path.join(self.config["cache_dir"], "cache_index.json")
        if os.path.exists(index_path):
            try:
                with open(index_path, 'r') as f:
                    self.cache = json.load(f)
                self.logger.info(f"Loaded {len(self.cache)} TTS cache entries")
            except Exception as e:
                self.logger.warning(f"Failed to load cache index: {e}")
                self.cache = {}
    
    def _save_cache_index(self) -> None:
        """Save cache index to disk."""
        if not self.config["cache_enabled"]:
            return
            
        index_path = os.path.join(self.config["cache_dir"], "cache_index.json")
        try:
            with open(index_path, 'w') as f:
                json.dump(self.cache, f)
        except Exception as e:
            self.logger.warning(f"Failed to save cache index: {e}")
    
    def _generate_silence(self, duration_ms: int = 1000) -> bytes:
        """Generate silent audio as a fallback."""
        try:
            from pydub import AudioSegment
            
            silence = AudioSegment.silent(duration=duration_ms)
            output = io.BytesIO()
            silence.export(output, format="wav")
            output.seek(0)
            return output.read()
            
        except Exception as e:
            self.logger.error(f"Failed to generate silent audio: {e}")
            # Return minimal WAV header
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
    
    def is_available(self) -> bool:
        """Check if any TTS engine is available."""
        for engine in self.engines.values():
            if engine and hasattr(engine, "is_available") and engine.is_available():
                return True
        return False
    
    def get_available_engines(self) -> List[str]:
        """Get a list of available TTS engines."""
        return [name for name, engine in self.engines.items() 
                if engine and hasattr(engine, "is_available") and engine.is_available()]
    
    def get_engine_info(self) -> Dict[str, Any]:
        """Get information about available engines."""
        info = {
            "primary_engine": self.config["primary_engine"],
            "available_engines": self.get_available_engines(),
            "engines": {}
        }
        
        for name, engine in self.engines.items():
            if not engine:
                continue
                
            engine_info = {
                "available": hasattr(engine, "is_available") and engine.is_available(),
                "voices": []
            }
            
            # Get voices if available
            if hasattr(engine, "get_available_voices"):
                engine_info["voices"] = engine.get_available_voices()
            
            # Get emotions if available (EmotiVoice)
            if hasattr(engine, "get_available_emotions"):
                engine_info["emotions"] = engine.get_available_emotions()
                
            info["engines"][name] = engine_info
            
        return info
