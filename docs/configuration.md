# VR Interview System Configuration Guide

This document describes the configuration options for the VR Interview System.

## Configuration Files

The system uses JSON configuration files to control its behavior. Several configuration files are provided:

- `config.json` - The main configuration file used by default
- `config_example.json` - An example configuration file with comments explaining each option
- `config_minimal.json` - Minimal configuration for systems with limited resources
- `config_development.json` - Configuration optimized for development with extra debugging
- `config_production.json` - Configuration optimized for production use

## Loading Configuration

The server will load `config/config.json` by default. You can specify a different configuration file by creating a copy of one of the provided templates:

```bash
# For development
copy config\config_development.json config\config.json

# For production
copy config\config_production.json config\config.json

# For minimal resource usage
copy config\config_minimal.json config\config.json
```

## Configuration Options

### Server Settings

```json
"server": {
  "host": "0.0.0.0",  // Listen on all interfaces
  "port": 8765,       // WebSocket port
  "log_level": "INFO" // Logging level (DEBUG, INFO, WARNING, ERROR)
}
```

### Audio Settings

```json
"audio": {
  "stt_model": "medium", // Whisper model size: tiny, base, small, medium, large
  "tts_model": "en",     // Text-to-speech model
  "sample_rate": 16000,  // Audio sample rate
  "channels": 1          // Audio channels (mono = 1)
}
```

### Storage Settings

```json
"storage": {
  "audio_dir": "data/audio",               // Audio storage directory
  "conversation_dir": "data/conversations", // Conversation history storage
  "retention_days": 30                      // Data retention period
}
```

### AllTalk Integration (Optional)

```json
"alltalk": {
  "url": "http://127.0.0.1:7851",              // AllTalk server URL
  "voice": "Clint_Eastwood CC3 (enhanced).wav", // Voice to use
  "direct_mode": true,                         // Use direct mode for better performance
  "retries": 3,                                // Retry attempts on failure
  "timeout": 20                                // Request timeout in seconds
}
```

### Ollama LLM Settings

```json
"ollama": {
  "url": "http://localhost:11434", // Ollama server URL
  "model": "phi",                  // LLM model to use (e.g., phi, llama2, mistral)
  "context_length": 8192,          // Maximum context length
  "system_prompt": "You are a job interviewer...", // Initial system prompt
  "options": {                     // Model generation parameters
    "temperature": 0.7,            // Randomness (higher = more creative)
    "top_p": 0.85,                 // Nucleus sampling probability
    "top_k": 30,                   // Top tokens to consider
    "repeat_penalty": 1.2,         // Penalty for repeating tokens
    "num_predict": 120,            // Maximum tokens to generate
    "seed": 42                     // Random seed for reproducibility
  }
}
```

### Heartbeat Settings

```json
"heartbeat": {
  "enabled": true,  // Enable connection heartbeat
  "interval": 5.0   // Heartbeat interval in seconds
}
```

### Debug Settings (Development Only)

```json
"debug": {
  "save_transcripts": true,  // Save transcripts to files
  "save_responses": true,    // Save LLM responses to files
  "show_timing": true        // Show detailed timing information
}
```

## Environment Variables

Configuration values can be overridden using environment variables prefixed with `VR_INTERVIEW_` and using double underscore as separator for nested keys:

```bash
# Override server port
export VR_INTERVIEW_SERVER__PORT=8080

# Override Ollama URL
export VR_INTERVIEW_OLLAMA__URL=http://ollama:11434
```

## Configuration Tips

1. **Model Size**: Start with a smaller STT model (`tiny` or `base`) if you experience performance issues, then gradually increase.

2. **Ollama Context Length**: Larger context lengths allow for more conversation history but use more memory.

3. **Temperature**: Lower values (0.5-0.7) keep the interviewer more focused, while higher values (0.7-0.9) create more varied responses.

4. **Logging**: Use `INFO` level for normal operation, `DEBUG` for development, and `WARNING` for production.

5. **Heartbeat**: Keep enabled to detect connection issues, but increase the interval in production.
