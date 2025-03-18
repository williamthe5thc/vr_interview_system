# VR Interview System - Technical Guide for Claude (Server)

## Project Overview

The VR Interview System is a virtual reality interview practice platform that allows users to engage in realistic job interview scenarios within a VR environment. The system consists of a Python-based server running on a PC that connects with an Oculus Quest VR client built in Unity. The server handles natural language processing, audio conversion, and conversation management, while the VR client handles audio capture, playback, and avatar animation.

## Recent Updates

### System Improvements (March 2025)

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

4. **Enhanced UI Experience**:
   - Added transcript display showing user and interviewer text
   - Implemented "Interviewer is thinking..." messages during processing
   - Added progress update messages during long processing operations
   - Created notification system for important status updates

## Project Location

- **Python Server Root**: `D:\vr_interview_system\`
- **Unity Client Root**: `D:\VRSystemTest\`
- **AllTalk TTS Root**: `D:/AllTalk/alltalk_tts`

> **Note**: For information about the Unity client implementation, please refer to `D:\VRSystemTest\README_FOR_CLAUDE.md`, which contains details about the client-side components, UI implementation, and Unity-specific considerations.

## Implementation Details

### Extended LLM Timeout Handling

The previous implementation had a 12-second timeout which caused frequent timeouts during LLM processing. The new system has these improvements:

1. **Extended Timeout**: Increased from 12 to 45 seconds to accommodate slower LLM responses
2. **Progressive Updates**: System now sends "thinking" updates every 5 seconds during processing
3. **Delayed Response Handling**: If LLM exceeds the timeout, the task continues in the background
4. **Graceful Recovery**: When a delayed response completes, it's properly delivered to the user

This approach prevents the previous pattern of frequent timeout errors while providing better feedback to users during long processing times.

### Improved AllTalk Integration

The AllTalk integration now uses correct endpoints and includes better error handling:

1. **Fixed API Endpoints**: Updated to use correct paths (/tts-generate instead of /api/tts-generate)
2. **Robust Connection Checking**: Added retry logic and better availability detection
3. **Multiple API Approaches**: Now tries multiple API methods in sequence with fallbacks
4. **Graceful Degradation**: Falls back to gTTS with proper error logging when needed

### Session ID Synchronization

Fixed the issue where client and server had different session IDs:

1. **Server-Generated IDs**: Client now properly accepts server-generated session IDs
2. **ID Mapping**: Added mapping system to translate between client and server IDs
3. **Session Context Preservation**: Ensured session context is maintained across reconnections

## System Architecture

### Core Components

1. **Python Server**: Manages WebSocket connections, audio processing, and conversation flow
   - Uses asyncio for non-blocking operations
   - Implements state machine for conversation management
   - Integrates with local LLM (Ollama) and TTS (AllTalk) services

2. **Oculus Quest Client**: Provides the VR interface for the user (see Unity README for details)
   - Built in Unity with WebSocket communication
   - Handles audio capture and playback
   - Animates interviewer avatar based on conversation state
   - Displays transcript of conversation for better user experience

3. **External Services**:
   - **Ollama**: Local LLM service running the Mistral model
   - **AllTalk**: High-quality TTS service using direct API (no streaming)

### Data Flow

1. User speaks in VR headset
2. Audio is captured and sent to server via WebSocket
3. Server transcribes speech using Whisper
4. User's transcript is displayed in the VR interface
5. "Interviewer is thinking..." message is shown
6. Transcript is processed by Ollama LLM
7. Response is converted to speech using AllTalk direct API
8. LLM response text is displayed in the transcript panel
9. Audio is sent back to VR client and played through avatar
10. Avatar speaks and animates in sync with audio

## Project Structure

### Server Structure

```
D:\vr_interview_system\
├── app/                  # Core application modules
│   ├── state/            # State management
│   ├── utils/            # Utility functions 
│   └── websocket/        # WebSocket communication
├── config/               # Configuration files
├── data/                 # Data storage
├── docs/                 # Documentation
├── services/             # Service integrations
│   ├── audio/            # Audio processing services
│   └── llm/              # Language model services
├── tools/                # Utility tools and diagnostics
└── server.py             # Main server entry point
```

### Key Files and Their Purposes

#### Core Server Files

- **`server.py`**: Main entry point that initializes all components and starts the WebSocket server. It handles server startup, shutdown, and error registration.

- **`app/websocket/server_enhanced_fixed.py`**: WebSocket server implementation with improved error handling and heartbeat mechanism. Manages client connections, message routing, and state transitions.

- **`app/websocket/enhanced_stream_processor.py`**: Handles the audio processing pipeline with optimized async handling. Manages STT, LLM, and TTS operations using direct API only.

- **`app/websocket/protocol.py`**: Defines the WebSocket message protocol including message formats and validation.

- **`app/state/manager.py`**: Manages the conversation state machine with states like IDLE, LISTENING, PROCESSING, RESPONDING, and WAITING.

- **`app/state/session.py`**: Implements the session class that stores conversation context and metadata.

- **`app/utils/enhanced_error_handler.py`**: Provides comprehensive error handling with pattern detection, adaptive recovery, and graceful degradation strategies.

- **`app/utils/config.py`**: Configuration loading and management.

- **`app/utils/logging.py`**: Configures and sets up logging throughout the application.

- **`app/utils/heartbeat.py`**: Implements heartbeat mechanism for long-running operations.

#### Service Files

- **`services/audio/alltalk_tts_direct.py`**: Direct-API-only AllTalk TTS integration with multiple API fallback strategies and gTTS fallback.

- **`services/audio/stt_wrapper.py`**: Speech-to-text service using Whisper with additional error handling.

- **`services/audio/gtts_only_service.py`**: Fallback TTS service using Google TTS when AllTalk is unavailable.

- **`services/llm/ollama_client.py`**: Client for the Ollama LLM API with context management and error handling.

## Key Technical Challenges

### 1. Preventing WebSocket Blocking
The system uses asyncio to run CPU-intensive operations like STT, LLM, and TTS in separate threads, preventing them from blocking the WebSocket communication. It uses task tracking, heartbeats, and timeouts to ensure responsiveness.

### 2. AllTalk Direct API Integration
The AllTalk TTS service integration now uses direct API calls exclusively with multiple fallback strategies:
- Multiple API endpoints are tried in sequence (tts-generate, synthesize, tts)
- Direct API timeout handling with appropriate error recovery
- gTTS as ultimate fallback when AllTalk is unavailable or fails

### 3. State Management
The state machine ensures reliable conversation flow with proper transitions, deadlock prevention, and error recovery. It tracks session state with metadata and broadcasts state changes to clients.

### 4. Error Recovery
The enhanced error handler provides robust recovery from various failure types with pattern detection and adaptive strategies:
- Progressive fallback for repeated errors
- Cooldown periods between recovery attempts
- Maximum recovery attempts to prevent infinite loops
- Detection of recurring error patterns

### 5. Client-Server Synchronization
The system implements proper session ID synchronization and reconnection handling to ensure a coherent conversation experience even if the connection is temporarily interrupted.

## Setup and Running

### Initial Setup

1. Run the setup script to create necessary files:
   ```
   run_setup.bat
   ```

2. Start the server:
   ```
   python server.py
   ```

### Configuration

The system's behavior can be configured through `config/config.json`, with the following key sections:

- **server**: WebSocket server settings (host, port, etc.)
- **audio**: Speech-to-text and text-to-speech settings
- **ollama**: LLM integration settings
- **alltalk**: AllTalk TTS service settings
- **storage**: File storage locations and retention settings

## Recommended Development Practices

When working on this system:

1. Follow the asynchronous programming patterns with proper task tracking
2. Implement comprehensive error handling with fallback strategies
3. Use direct API calls with proper timeout handling
4. Maintain the state machine integrity with valid transitions
5. Consider client capabilities for optimal audio delivery

## Common Issues Claude Can Help With

1. **Async Programming Patterns**:
   - Task creation and tracking
   - Proper exception handling in async code
   - Preventing deadlocks and race conditions

2. **Error Handling Strategies**:
   - Multi-level fallback mechanisms
   - Service availability detection
   - Graceful degradation patterns

3. **AllTalk Integration**:
   - File discovery algorithms
   - API fallback sequences
   - Audio file format handling

4. **LLM Context Management**:
   - Efficient prompt formatting
   - History pruning strategies
   - Context window optimization

By understanding these components and their interactions, you can effectively enhance and maintain the VR Interview System for a reliable and immersive interview practice experience.