import json
import os
import logging
from typing import Dict, Any


def load_config(config_path: str = "config.json") -> Dict[str, Any]:
    """
    Load configuration from config.json and apply environment overrides
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configuration dictionary
    """
    logger = logging.getLogger("config")
    
    # Default configuration
    default_config = {
        "server": {
            "host": "0.0.0.0",
            "port": 8765,
            "log_level": "INFO"
        },
        "audio": {
            "stt_model": "base",
            "tts_model": "gtts",
            "sample_rate": 16000,
            "channels": 1
        },
        "ollama": {
            "url": "http://localhost:11434",
            "model": "phi",
            "context_length": 4096,
            "system_prompt": "You are a job interviewer..."
        },
        "storage": {
            "audio_dir": "data/audio",
            "conversation_dir": "data/conversations",
            "retention_days": 30
        }
    }
    
    # Load configuration from file
    config = default_config.copy()
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                file_config = json.load(f)
                
                # Update default config with file config
                _deep_update(config, file_config)
                logger.info(f"Loaded configuration from {config_path}")
        else:
            logger.warning(f"Configuration file {config_path} not found, using defaults")
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        
    # Apply environment overrides
    config = _apply_env_overrides(config)
    
    # Validate configuration
    validate_config(config)
    
    return config


def _deep_update(target, source):
    """
    Recursively update nested dictionaries
    """
    for key, value in source.items():
        if key in target and isinstance(target[key], dict) and isinstance(value, dict):
            _deep_update(target[key], value)
        else:
            target[key] = value


def _apply_env_overrides(config):
    """
    Override configuration values with environment variables
    
    Environment variables should be prefixed with VR_INTERVIEW_
    and use double underscore as separator for nested keys
    
    Example:
        VR_INTERVIEW_SERVER__PORT=8080
        VR_INTERVIEW_OLLAMA__URL=http://ollama:11434
    """
    logger = logging.getLogger("config")
    env_prefix = "VR_INTERVIEW_"
    
    for env_key, env_value in os.environ.items():
        if env_key.startswith(env_prefix):
            # Remove prefix and split by double underscore
            key_path = env_key[len(env_prefix):].lower().split("__")
            
            if len(key_path) == 1:
                # Top-level key
                config[key_path[0]] = _convert_env_value(env_value)
            elif len(key_path) == 2:
                # Nested key
                if key_path[0] in config:
                    config[key_path[0]][key_path[1]] = _convert_env_value(env_value)
                    logger.info(f"Applied env override: {env_key}={env_value}")
                    
    return config


def _convert_env_value(value):
    """
    Convert environment variable string to appropriate type
    """
    # Try to convert to int
    try:
        return int(value)
    except ValueError:
        pass
        
    # Try to convert to float
    try:
        return float(value)
    except ValueError:
        pass
        
    # Try to convert to bool
    if value.lower() in ("true", "yes", "1"):
        return True
    if value.lower() in ("false", "no", "0"):
        return False
        
    # Return as string
    return value


def validate_config(config):
    """
    Validate that configuration has all required fields
    """
    logger = logging.getLogger("config")
    
    # Check required sections
    required_sections = ["server", "audio", "ollama", "storage"]
    for section in required_sections:
        if section not in config:
            logger.error(f"Missing required configuration section: {section}")
            raise ValueError(f"Missing required configuration section: {section}")
            
    # Validate server config
    if "host" not in config["server"]:
        logger.error("Missing server.host configuration")
        raise ValueError("Missing server.host configuration")
        
    if "port" not in config["server"]:
        logger.error("Missing server.port configuration")
        raise ValueError("Missing server.port configuration")
        
    # Validate Ollama config
    if "url" not in config["ollama"]:
        logger.error("Missing ollama.url configuration")
        raise ValueError("Missing ollama.url configuration")
        
    if "model" not in config["ollama"]:
        logger.error("Missing ollama.model configuration")
        raise ValueError("Missing ollama.model configuration")
