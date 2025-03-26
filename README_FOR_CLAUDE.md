# VR Interview System - Technical Guide

## Overview

The VR Interview System is a virtual reality interview practice platform that allows users to engage in realistic job interview scenarios within a VR environment. The system consists of a Python-based server running on a PC that connects with an Oculus Quest VR client built in Unity. The server handles natural language processing, audio conversion, and conversation management, while the VR client handles audio capture, playback, and avatar animation.

The system uses a state machine architecture to manage conversation flow, WebSocket communication for real-time interaction, local LLM integration via Ollama, and high-quality text-to-speech via AllTalk with multiple fallback mechanisms for robust operation.

## Project Location

- **Python Server Root**: `D:\vr_interview_system\`
- **Unity Client Root**: `D:\VRSystemTest\`
- **AllTalk TTS Root**: `D:/AllTalk/alltalk_tts`
- **Documentation**: `D:\vr_interview_system\docs\`

## Documentation

Comprehensive documentation is available in the `docs` directory, organized by system component:

1. **System Overview**: `docs/system_overview.md` - High-level architecture, component interactions, and system startup/shutdown
2. **WebSocket Documentation**: `docs/websocket_documentation.md` - Connection handling, message protocol, client capabilities
3. **State Management**: `docs/state_management_documentation.md` - State machine, transitions, session tracking, deadlock prevention
4. **Audio Processing**: `docs/audio_processing_documentation.md` - STT/TTS integration, streaming, fallback mechanisms
5. **LLM Integration**: `docs/llm_integration_documentation.md` - Ollama client, prompt engineering, response caching, context management
6. **Error Handling**: `docs/error_handling_documentation.md` - Recovery strategies, graceful degradation, error tracking
7. **Heartbeat System**: `docs/heartbeat_system_documentation.md` - Connection keepalive, progress updates, timing configuration
8. **Enhanced Stream Processor**: `docs/enhanced_stream_processor_documentation.md` - Optimized audio processing pipeline
9. **Configuration Management**: `docs/configuration_management_documentation.md` - Config structure, environment overrides, validation
10. **Function Reference**: `docs/function_reference.md` - Alphabetical reference of key functions across all components

## Implementation Details

### Core Functionality

1. **Asynchronous Architecture**
   - Based on Python's asyncio for non-blocking operation
   - Thread pool for CPU-intensive operations (STT, LLM, TTS)
   - Task tracking system for proper resource management

2. **State Machine**
   - Manages conversation flow through defined states:
     - IDLE: Initial state, ready for conversation
     - LISTENING: Receiving audio from user
     - PROCESSING: Generic processing state
     - PROCESSING_STT: Specifically transcribing speech to text
     - PROCESSING_LLM: Generating response with the language model
     - PROCESSING_TTS: Converting text response to audio
     - RESPONDING: Sending audio response to client
     - WAITING: Waiting for next user input
     - ERROR: Error state with recovery mechanisms
   - Validates state transitions with deadlock prevention
   - Provides recovery paths for error conditions

3. **Speech Processing**
   - STT using OpenAI Whisper models with fallback options
   - TTS using AllTalk direct API with multiple endpoint attempts
   - Format validation and conversion for audio interchange

4. **LLM Integration**
   - Connects to local Ollama instance running Mistral model
   - Optimized prompt formatting with context window management
   - Response caching for performance optimization
   - Timeout handling with retry strategies

5. **Error Handling**
   - Specialized recovery handlers for different error types
   - Pattern detection for recurring issues
   - Cooldown periods and attempt limits
   - Graceful degradation with fallback options

### Recent Improvements

1. **Enhanced LLM Response Handling**:
   - Extended LLM timeout from 12 to 45 seconds
   - Added progressive updates during LLM processing
   - Implemented background processing for LLM responses that exceed timeout
   - Added delayed response delivery when LLM completes processing after timeout

2. **Improved AllTalk Integration**:
   - Fixed API endpoint paths to match current AllTalk implementation
   - Added robust file discovery for generated audio content
   - Implemented multiple fallback strategies for API calls
   - Enhanced error handling with graceful degradation to gTTS

3. **Fixed Session ID Synchronization**:
   - Added proper client-server session ID synchronization
   - Implemented session ID mapping to handle mismatches
   - Added server-side session ID tracking for improved reliability
   - Separate tracking of client-generated and server-assigned IDs

4. **Cleanup and Consolidation**:
   - Removed redundant and experimental files
   - Consolidated multiple TTS implementations into a single robust service
   - Removed legacy streaming implementation in favor of direct API approach
   - Simplified heartbeat implementation with enhanced features

4. **Enhanced UI Experience**:
   - Added transcript display showing user and interviewer text
   - Implemented "Interviewer is thinking..." messages during processing
   - Added progress update messages during long processing operations
   - Created notification system for important status updates

5. **Enhanced Message Validation**:
   - Added validation for all outgoing WebSocket messages
   - Ensured required fields (type, session_id, timestamp) are always present
   - Implemented granular processing state reporting (PROCESSING_STT, PROCESSING_LLM, PROCESSING_TTS)
   - Enhanced progress visualization with detailed state information

## Common Problems

### WebSocket Connection Issues

1. **Timeouts During Long Operations**
   - **Symptom**: Client disconnects during long LLM processing
   - **Cause**: Default WebSocket timeout reached
   - **Solution**: Heartbeat mechanism sends periodic messages to keep connection alive

2. **Session ID Mismatch**
   - **Symptom**: Conversation history lost after reconnection
   - **Cause**: Client and server using different session IDs
   - **Solution**: Session ID mapping system to translate between client and server IDs

### Audio Processing Issues

1. **STT Failures**
   - **Symptom**: No transcription despite valid audio
   - **Cause**: Whisper model loading failure or incorrect format
   - **Solution**: STT wrapper with fallback to SimpleSTT and error recovery

2. **TTS Timeouts**
   - **Symptom**: Audio generation takes too long
   - **Cause**: AllTalk service under load or network issues
   - **Solution**: Text fallback with delayed audio delivery

3. **AllTalk API Issues**
   - **Symptom**: No audio despite successful text generation
   - **Cause**: AllTalk API endpoint changes or server unavailability
   - **Solution**: Multiple API attempts with fallback to gTTS

### LLM Processing Issues

1. **Slow Responses**
   - **Symptom**: Long wait times for LLM responses
   - **Cause**: Large context window or complex queries
   - **Solution**: Progressive updates during processing and optimized prompts

2. **Context Window Overflow**
   - **Symptom**: Unrelated or truncated responses
   - **Cause**: Conversation history exceeding model's context window
   - **Solution**: Context pruning strategy keeping only recent interactions

### Error Recovery Issues

1. **Recurring Errors**
   - **Symptom**: Same error occurs repeatedly
   - **Cause**: Persistent underlying issue
   - **Solution**: Pattern detection with adaptive recovery strategies

2. **State Deadlocks**
   - **Symptom**: System stuck in specific state
   - **Cause**: Failed state transition or error during transition
   - **Solution**: Deadlock detection with forced state transitions

## System Architecture

### High-Level Architecture

```
                               ┌─────────────────┐
                               │   Client (VR)   │
                               └────────┬────────┘
                                        │
                                        ▼
┌───────────────────────────────────────────────────────────────────────┐
│                        WebSocket Connection                           │
└───────────────────────────────┬───────────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────────┐
│                            Server Core                                │
│                         (EnhancedServer)                              │
└─┬─────────────┬───────────────┬────────────────┬──────────────────────┘
  │             │               │                │
  ▼             ▼               ▼                ▼
┌──────────┐ ┌───────┐  ┌───────────────┐ ┌─────────────┐
│WebSocket │ │ State │  │  STT Service  │ │ TTS Service │
│ Server   │ │Manager│  │(Whisper Model)│ │  (AllTalk)  │
└──────────┘ └───────┘  └───────────────┘ └──────┬──────┘
      │         │               │                │
      │         │               │                │
      │         │               ▼                │
      │         │        ┌──────────────┐        │
      │         │        │ LLM Client   │        │
      │         │        │   (Ollama)   │        │
      │         │        └──────────────┘        │
      │         │               │                │
      │         │               ▼                │
      │         │        ┌──────────────┐        │
      │         │        │ Response     │        │
      │         │        │ Generation   │        │
      │         │        └──────────────┘        │
      │         │               │                │
      ▼         ▼               ▼                ▼
┌───────────────────────────────────────────────────────────────────────┐
│                        Error Handler                                  │
└───────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

1. **EnhancedServer**: Central orchestrator that initializes and manages all components
2. **WebSocketServer**: Handles client connections and message routing
3. **StateManager**: Maintains conversation state and ensures valid transitions
4. **STTService**: Converts user audio to text using Whisper models
5. **TTSService**: Converts LLM responses to audio using AllTalk or fallbacks
6. **OllamaClient**: Communicates with Ollama LLM API for response generation
7. **ErrorHandler**: Provides specialized recovery strategies for different error types

## Data Flow

1. **Client Connection Establishment**
   - VR client connects to server via WebSocket
   - Server assigns unique session ID and initializes session
   - Client and server exchange capabilities information

2. **Audio Input Processing**
   - User speaks in VR headset
   - Audio is captured and encoded in base64
   - Audio data is sent to server with metadata
   - Server transcribes speech using STT service
   - Transcript is displayed in VR interface

3. **LLM Response Generation**
   - Server transitions to PROCESSING state
   - "Interviewer is thinking..." message displayed
   - Heartbeat messages maintain connection
   - LLM generates contextually appropriate response
   - Response is added to conversation history

4. **Audio Output Generation**
   - LLM response is sent to TTS service
   - AllTalk generates audio response
   - Audio data is encoded and sent to client
   - Client plays audio through avatar
   - Transcript is updated with interviewer response

5. **State Transitions**
   - IDLE → LISTENING → PROCESSING_STT → PROCESSING_LLM → PROCESSING_TTS → RESPONDING → WAITING
   - State changes are communicated to client with detailed metadata
   - Each processing state includes progress information and stage-specific messages
   - Error states trigger appropriate recovery strategies

## Project Structure

### Server Structure

```
D:\vr_interview_system\
├── app/                  # Core application modules
│   ├── state/            # State management
│   │   ├── manager.py    # State machine implementation
│   │   └── session.py    # Session data management
│   ├── utils/            # Utility functions
│   │   ├── config.py     # Configuration management
│   │   ├── error_handler.py # Error handling system
│   │   ├── heartbeat.py  # Connection keepalive
│   │   └── logging.py    # Logging configuration
│   └── websocket/        # WebSocket communication
│       ├── enhanced_stream_processor.py # Optimized audio pipeline
│       ├── protocol.py   # Message protocol definition
│       └── server_enhanced_fixed.py # WebSocket server
├── config/               # Configuration files
│   └── config.json       # Main configuration
├── data/                 # Data storage
│   ├── audio/            # Audio file storage
│   ├── cache/            # Response cache storage
│   └── conversations/    # Conversation history
├── docs/                 # Documentation
│   ├── system_overview.md          # System architecture overview
│   ├── websocket_documentation.md  # WebSocket implementation
│   ├── state_management_documentation.md # State machine
│   ├── audio_processing_documentation.md # Audio processing
│   ├── llm_integration_documentation.md  # LLM integration
│   ├── error_handling_documentation.md   # Error handling
│   ├── function_reference.md             # Function reference
│   └── ...               # Additional documentation
├── services/             # Service integrations
│   ├── audio/            # Audio processing services
│   │   ├── gtts_only_service.py  # Google TTS fallback
│   │   ├── stt.py              # Speech-to-text service
│   │   ├── stt_wrapper.py     # Speech-to-text wrapper
│   │   └── tts.py              # Unified text-to-speech service
│   └── llm/              # Language model services
│       ├── ollama_client.py      # Ollama API client
│       ├── scenarios/           # Interview scenario definitions
│       │   └── job_interview.py  # Job interview scenario framework
│       └── templates/            # Response templates
├── test_scripts/         # Testing utilities
│   ├── test_alltalk.py         # AllTalk diagnostics
│   ├── test_alltalk2.py        # AllTalk voice testing
│   ├── test_alltalk_streaming.py # AllTalk streaming tests
│   └── test_integration.py     # Full system integration testing
├── server.py             # Main server entry point
└── README.md             # Project documentation
```

## Key Files and Their Purposes

### Core Server Files

- **`server.py`**: Main entry point that initializes all components and starts the WebSocket server. It handles server startup, shutdown, and error registration.

- **`app/websocket/server_enhanced_fixed.py`**: WebSocket server implementation with improved error handling and heartbeat mechanism. Manages client connections, message routing, and state transitions.

- **`app/websocket/enhanced_stream_processor.py`**: Handles the audio processing pipeline with optimized async handling. Manages STT, LLM, and TTS operations using direct API only.

- **`app/websocket/protocol.py`**: Defines the WebSocket message protocol including message formats and validation.

- **`app/state/manager.py`**: Manages the conversation state machine with states like IDLE, LISTENING, PROCESSING, RESPONDING, and WAITING.

- **`app/state/session.py`**: Implements the session class that stores conversation context and metadata.

- **`app/utils/error_handler.py`**: Provides comprehensive error handling with pattern detection, adaptive recovery, and graceful degradation strategies.

- **`app/utils/config.py`**: Configuration loading and management.

- **`app/utils/logging.py`**: Configures and sets up logging throughout the application.

- **`app/utils/heartbeat.py`**: Implements heartbeat mechanism for long-running operations with dynamic intervals.

### Service Files

- **`services/audio/stt.py`**: Speech-to-text service using Whisper with GPU acceleration.

- **`services/audio/stt_wrapper.py`**: Speech-to-text wrapper with fallback mechanisms and additional error handling.

- **`services/audio/tts.py`**: Unified TTS service with AllTalk integration, multiple API fallback strategies, and gTTS fallback.

- **`services/llm/ollama_client.py`**: Client for the Ollama LLM API with context management, caching, and error handling.

## Configuration

The system's behavior is configured through `config/config.json`, with the following key sections:

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
  "system_prompt": "...",
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
  "alltalk_dir": "D:/AllTalk/alltalk_tts",
  "default_language": "en",
  "endpoints": ["tts-generate", "synthesize", "tts"]
},
"cache": {
  "enabled": true,
  "dir": "data/cache/tts",
  "max_entries": 1000
}
```

### Heartbeat Configuration
```json
"heartbeat": {
  "enabled": true,
  "interval": 5.0
}
```

Configuration can also be overridden through environment variables using the `VR_INTERVIEW_` prefix and double underscores for nested keys. For example:

```
VR_INTERVIEW_SERVER__PORT=8080
VR_INTERVIEW_OLLAMA__URL=http://ollama:11434
```

## Initial Setup

1. Run the setup script to create necessary files:
   ```
   run_setup.bat
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Start the server:
   ```
   python server.py
   ```

## Further Information

For more detailed information about specific components, please refer to the documentation in the `docs` directory. For information about the Unity client implementation, please refer to `D:\VRSystemTest\README_FOR_CLAUDE.md`.