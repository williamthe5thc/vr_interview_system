"""
VR Interview System Integration Module

This module provides easy-to-use functions to integrate the enhanced components
into the existing VR interview system with minimal changes to the main code.
"""

import logging
import os
import json
import importlib.util
from typing import Dict, Any, Optional

# Check if whisper is available
def is_whisper_available():
    """Check if the whisper module is available."""
    try:
        import whisper
        return True
    except ImportError:
        return False
    except Exception:
        return False

HAS_WHISPER = is_whisper_available()

# Set up logger
logger = logging.getLogger("integration")


def get_enhanced_tts_service(config_path: str = "config_enhanced.json") -> Any:
    """
    Create and return an enhanced TTS service based on configuration.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Initialized enhanced TTS service
    """
    try:
        # Load configuration
        config = _load_config(config_path)
        tts_config = config.get("tts", {})
        
        # Import the enhanced TTS service
        from services.audio.enhanced_tts import EnhancedTTSService
        
        # Create and return service instance
        tts_service = EnhancedTTSService(tts_config)
        
        # Log available engines
        available_engines = tts_service.get_available_engines()
        logger.info(f"Enhanced TTS service initialized with engines: {', '.join(available_engines)}")
        
        return tts_service
        
    except ImportError as e:
        logger.warning(f"Failed to import enhanced TTS: {e}. Will use default implementation.")
        return None
    except Exception as e:
        logger.error(f"Error creating enhanced TTS service: {e}")
        return None


def get_enhanced_ollama_client(config_path: str = "config_enhanced.json") -> Any:
    """
    Create and return an enhanced Ollama client based on configuration.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Initialized enhanced Ollama client
    """
    try:
        # Load configuration
        config = _load_config(config_path)
        ollama_config = config.get("ollama", {})
        
        # Import the enhanced Ollama client
        from services.llm.enhanced_ollama_client import EnhancedOllamaClient
        
        # Create and return client instance
        ollama_client = EnhancedOllamaClient(
            ollama_config.get("url", "http://localhost:11434"),
            ollama_config.get("model", "llama3"),
            ollama_config.get("context_length", 8192),
            ollama_config
        )
        
        logger.info(f"Enhanced Ollama client initialized with model: {ollama_config.get('model', 'llama3')}")
        
        return ollama_client
        
    except ImportError as e:
        logger.warning(f"Failed to import enhanced Ollama client: {e}. Will use default implementation.")
        return None
    except Exception as e:
        logger.error(f"Error creating enhanced Ollama client: {e}")
        return None


def get_interview_scenario_prompt(
    position_type: str = "software_engineer",
    interview_style: str = "neutral",
    experience_level: str = "mid_level",
    company_type: str = "tech_startup",
    stage: str = "introduction",
    context_memory: str = ""
) -> str:
    """
    Get a formatted interview scenario prompt for the LLM.
    
    Args:
        position_type: Type of position (e.g., software_engineer)
        interview_style: Style of interviewer (e.g., supportive, challenging)
        experience_level: Level of experience (e.g., entry_level, senior_level)
        company_type: Type of company (e.g., tech_startup)
        stage: Current interview stage
        context_memory: String containing important context from previous exchanges
        
    Returns:
        Formatted system prompt for interview scenario
    """
    try:
        # Import the interview scenario module
        from services.llm.scenarios.job_interview import get_interview_prompt
        
        # Generate and return the prompt
        return get_interview_prompt(
            position_type=position_type,
            interview_style=interview_style,
            experience_level=experience_level,
            company_type=company_type,
            stage=stage,
            context_memory=context_memory
        )
        
    except ImportError as e:
        logger.warning(f"Failed to import interview scenario: {e}. Using default prompt.")
        return "You are a professional job interviewer conducting an interview with a candidate."
    except Exception as e:
        logger.error(f"Error generating interview prompt: {e}")
        return "You are a professional job interviewer conducting an interview with a candidate."


def update_config_with_enhanced_settings(config_path: str = "config.json", output_path: str = "config_enhanced.json") -> bool:
    """
    Update existing configuration with optimized settings for enhanced components.
    
    Args:
        config_path: Path to existing configuration file
        output_path: Path to save enhanced configuration
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Load existing configuration
        config = _load_config(config_path)
        
        # Enhanced TTS settings
        config["tts"] = config.get("tts", {})
        config["tts"].update({
            "primary_engine": "piper",
            "fallback_order": ["alltalk", "gtts"],
            "streaming": True,
            "cache_enabled": True,
            "engines": {
                "piper": {
                    "enabled": True,
                    "voice": "en_US-lessac-medium",
                    "model_dir": "./models/piper"
                },
                "emotivoice": {
                    "enabled": False,  # Disabled by default until installed
                    "url": "http://localhost:8501",
                    "voice": "default"
                },
                "alltalk": {
                    "enabled": True,
                    "url": config.get("alltalk", {}).get("url", "http://127.0.0.1:7851"),
                    "voice": config.get("alltalk", {}).get("voice", "Clint_Eastwood CC3 (enhanced).wav")
                },
                "gtts": {
                    "enabled": True
                }
            }
        })
        
        # Enhanced Ollama settings
        config["ollama"] = config.get("ollama", {})
        ollama_options = config["ollama"].get("options", {})
        
        config["ollama"].update({
            "precompute_enabled": True,
            "max_cache_entries": 500,
            "scenario_type": "interview",
            "options": {
                "temperature": ollama_options.get("temperature", 0.7),
                "top_p": ollama_options.get("top_p", 0.85),
                "top_k": ollama_options.get("top_k", 30),
                "repeat_penalty": ollama_options.get("repeat_penalty", 1.2),
                "num_predict": ollama_options.get("num_predict", 120),
                "seed": 42
            }
        })
        
        # Add scenario configuration
        config["scenario"] = {
            "type": "interview",
            "position_type": "software_engineer",
            "interview_style": "neutral",
            "experience_level": "mid_level",
            "company_type": "tech_startup"
        }
        
        # Save enhanced configuration
        with open(output_path, 'w') as f:
            json.dump(config, f, indent=2)
            
        logger.info(f"Enhanced configuration saved to {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating configuration: {e}")
        return False


def _load_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configuration dictionary
    """
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"Configuration file not found: {config_path}. Using default settings.")
        return {}
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in configuration file: {config_path}")
        return {}
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return {}


def setup_optimization(config_path: str = "config.json") -> Dict[str, Any]:
    """
    Setup all optimizations and return enhanced components.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Dictionary with enhanced components
    """
    try:
        # Create enhanced configuration
        enhanced_config_path = "config_enhanced.json"
        update_config_with_enhanced_settings(config_path, enhanced_config_path)
        
        # Initialize result dictionary
        result = {"config_path": enhanced_config_path}
        
        # Try to create enhanced TTS service - errors won't stop other components
        try:
            tts_service = get_enhanced_tts_service(enhanced_config_path)
            if tts_service:
                result["tts_service"] = tts_service
        except Exception as tts_error:
            logger.error(f"Error initializing enhanced TTS: {tts_error}")
        
        # Try to create enhanced Ollama client - errors won't stop other components
        try:
            ollama_client = get_enhanced_ollama_client(enhanced_config_path)
            if ollama_client:
                result["ollama_client"] = ollama_client
        except Exception as ollama_error:
            logger.error(f"Error initializing enhanced Ollama: {ollama_error}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error setting up optimization: {e}")
        return {}


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Run optimization setup
    print("Setting up optimized components...")
    result = setup_optimization()
    
    if result:
        print("Optimization setup complete!")
        print(f"Enhanced configuration saved to: {result.get('config_path', 'config_enhanced.json')}")
        
        # Check components
        if result.get("tts_service"):
            tts_engines = result["tts_service"].get_available_engines()
            print(f"TTS engines available: {', '.join(tts_engines)}")
        else:
            print("Enhanced TTS service not available")
            
        if result.get("ollama_client"):
            print(f"Enhanced Ollama client initialized with model: {result['ollama_client'].model}")
        else:
            print("Enhanced Ollama client not available")
    else:
        print("Optimization setup failed. Check logs for details.")
