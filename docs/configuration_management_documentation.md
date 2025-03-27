# VR Interview System: Configuration Management Documentation

## Title and Overview

The Configuration Management component of the VR Interview System provides a flexible, hierarchical approach to configuring all aspects of the system. It loads settings from a JSON file and supports overrides through environment variables, ensuring deployability across different environments. The configuration system includes validation to ensure all required settings are present and handles defaults for missing values.

## Architecture

The Configuration Management is implemented as a utility module with functions for loading, validating, and applying environment overrides to the system configuration. It follows a hierarchical approach with default values, file-based configuration, and environment variable overrides in increasing order of precedence.

```
┌────────────────┐   Load   ┌───────────────┐   Override  ┌─────────────────┐
│ Default Config │────────► │ File Config   │─────────────►Environment Config│
└────────────────┘          └───────────────┘             └────────┬─────────┘
                                                                   │
┌─────────────────────────────────────────────────────────────────▼───────────┐
│                               Validation                                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            Application Config                                │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Key Functions

### load_config

```python
def load_config(config_path: str = "config/config.json") -> Dict[str, Any]:
    """
    Load configuration from config.json and apply environment overrides
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configuration dictionary
    """
```

### _deep_update

```python
def _deep_update(target, source):
    """
    Recursively update nested dictionaries
    """
```

### _apply_env_overrides

```python
def _apply_env_overrides(config):
    """
    Override configuration values with environment variables
    
    Environment variables should be prefixed with VR_INTERVIEW_
    and use double underscore as separator for nested keys
    
    Example:
        VR_INTERVIEW_SERVER__PORT=8080
        VR_INTERVIEW_OLLAMA__URL=http://ollama:11434
    """
```

### _convert_env_value

```python
def _convert_env_value(value):
    """
    Convert environment variable string to appropriate type
    """
```

### validate_config

```python
def validate_config(config):
    """
    Validate that configuration has all required fields
    """
```

## Usage Patterns

### Loading Configuration

```python
# In EnhancedServer.__init__
def __init__(self, config_path="config/config.json"):
    # Load configuration
    self.config = self._load_config(config_path)
    
    # Setup logging
    setup_logging(self.config["server"].get("log_level", "INFO"))
```

### Accessing Configuration Values

```python
# Direct access with default fallback
log_level = self.config["server"].get("log_level", "INFO")

# Nested configuration access
ollama_config = self.config["ollama"]
self.llm_client = OllamaClient(
    ollama_config["url"],
    ollama_config["model"],
    ollama_config.get("context_length", 4096),
    config=ollama_config  # Pass complete config
)
```

### Environment Overrides

```
# Set environment variables before starting the server
export VR_INTERVIEW_SERVER__PORT=8080
export VR_INTERVIEW_OLLAMA__URL=http://ollama:11434
export VR_INTERVIEW_ALLTALK__VOICE=female_07.wav
```

## Implementation Details

### Default Configuration

The system defines sensible defaults for all configuration options:

```python
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
```

### Deep Config Merging

Configuration from files is deep-merged with the defaults:

```python
def _deep_update(target, source):
    """
    Recursively update nested dictionaries
    """
    for key, value in source.items():
        if key in target and isinstance(target[key], dict) and isinstance(value, dict):
            _deep_update(target[key], value)
        else:
            target[key] = value
```

### Environment Variable Naming Convention

Environment variables use a specific naming pattern for hierarchical configuration:

```python
# Environment variables should be prefixed with VR_INTERVIEW_
# and use double underscore as separator for nested keys
env_prefix = "VR_INTERVIEW_"

# Example:
# VR_INTERVIEW_SERVER__PORT=8080
# Modifies config["server"]["port"]
```

### Type Conversion

The system intelligently converts environment variable strings to appropriate types:

```python
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
```

### Configuration Validation

The system validates that all required configuration is present:

```python
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
```

## Configuration

The VR Interview System configuration is stored in a JSON file (`config/config.json`) with the following structure:

### Server Configuration
```json
"server": {
  "host": "0.0.0.0",
  "port": 8765,
  "log_level": "INFO"
}
```

### Audio Configuration
```json
"audio": {
  "stt_model": "medium",
  "tts_model": "en",
  "sample_rate": 16000,
  "channels": 1
}
```

### Storage Configuration
```json
"storage": {
  "audio_dir": "data/audio",
  "conversation_dir": "data/conversations",
  "retention_days": 30
}
```

### LLM Configuration
```json
"ollama": {
  "url": "http://localhost:11434",
  "model": "mistral:latest",
  "context_length": 8192,
  "system_prompt": "You are a job interviewer conducting an interview with the candidate...",
  "options": {
    "temperature": 0.7,
    "top_p": 0.9,
    "top_k": 40,
    "repeat_penalty": 1.1,
    "num_predict": 100,
    "seed": 42,
    "timeout": 60
  }
}
```

### TTS Configuration
```json
"alltalk": {
  "url": "http://127.0.0.1:7851",
  "voice": "female_06.wav",
  "format": "wav",
  "retries": 3,
  "timeout": 60,
  "direct_api_timeout": 60,
  "alltalk_dir": "D:/AllTalk/alltalk_tts",
  "default_language": "en"
}
```

### Heartbeat Configuration
```json
"heartbeat": {
  "enabled": true,
  "interval": 5.0
}
```

## Common Issues

### Configuration Loading Issues

1. **Missing Configuration File**:
   - **Symptoms**: Warnings about file not found, using defaults
   - **Causes**: Incorrect file path or missing config file
   - **Solution**: System falls back to default configuration

2. **Invalid JSON**:
   - **Symptoms**: Error loading configuration, JSON parsing errors
   - **Causes**: Syntax errors in the config file
   - **Solution**: Validate JSON format before deployment

3. **Missing Required Sections**:
   - **Symptoms**: Validation errors at startup
   - **Causes**: Incomplete configuration
   - **Solution**: Validation ensures all required fields are present

### Environment Variable Issues

1. **Case Sensitivity**:
   - **Symptoms**: Environment variables not being applied
   - **Causes**: Incorrect casing in variable names
   - **Solution**: Variables are converted to lowercase during processing

2. **Type Conversion**:
   - **Symptoms**: Unexpected configuration behavior
   - **Causes**: Incorrect type conversion from string
   - **Solution**: The `_convert_env_value` function handles common types

3. **Naming Conventions**:
   - **Symptoms**: Nested configuration not applied
   - **Causes**: Incorrect variable naming
   - **Solution**: Use double underscore as separator for nested keys

## Code Examples

### Complete Configuration Loading

```python
def load_config(config_path: str = "config/config.json") -> Dict[str, Any]:
    """
    Load configuration from config.json and apply environment overrides
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
```

### Applying Environment Overrides

```python
def _apply_env_overrides(config):
    """
    Override configuration values with environment variables
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
```

### Server Configuration Loading

```python
def _load_config(self, config_path):
    """Load configuration from file with fallback to default"""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        self.logger.error(f"Error loading config from {config_path}: {e}")
        self.logger.info("Falling back to default config/config.json")
        try:
            with open("config/config.json", 'r') as f:
                return json.load(f)
        except Exception as e2:
            self.logger.critical(f"Error loading fallback config: {e2}")
            sys.exit(1)
```
