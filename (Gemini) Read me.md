# VR Interview System

A virtual reality job interview practice system with a conversational AI interviewer powered by local language models. This system is stable and ready for production use. All critical bugs related to AI personality, state machine loops, and session management have been resolved.

## Overview

The VR Interview System provides a realistic job interview practice environment in virtual reality, featuring an AI-powered interviewer that responds to your speech in natural language. The system uses local language models (via Ollama) for conversation generation and can stream audio responses for a seamless experience.

## System Architecture

The system consists of three main components:

1.  **VR Client (Oculus Quest)**: Handles the VR environment, avatar animation, and user interaction.
2.  **Python Server**: Manages WebSocket communication, audio processing, state management, and LLM integration. (Uses the fixed versions of server logic, state management, and LLM client as per the project's cleanup plan).
3.  **LLM Service (Ollama)**: Processes natural language via local models such as Phi, Mistral, or other compatible models.

### Architecture Diagram
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
      ▼         ▼               ▼                ▼
┌───────────────────────────────────────────────────────────────────────┐
│                        Error Handler                                  │
└───────────────────────────────────────────────────────────────────────┘
```

## Key Features

-   **Real-time Conversation**: Speak naturally to the AI interviewer and receive contextually appropriate responses.
-   **Consistent AI Personality**: AI consistently acts as a professional interviewer.
-   **Audio Streaming**: Fast response time with AllTalk TTS streaming capability.
-   **Local Processing**: All processing happens locally without requiring cloud services.
-   **Realistic Avatar**: Professional interviewer avatar with synchronized speech and expressions.
-   **Robust State Management**: Clean state flow (`IDLE → LISTENING → PROCESSING_STT → PROCESSING_LLM → PROCESSING_TTS → RESPONDING → WAITING`) without infinite loops.
-   **Robust Error Handling**: Graceful fallbacks when components fail.
-   **Session Management**: Persistent sessions with context preservation and synchronized client-server session IDs.
-   **Heartbeat Mechanism**: Maintains connection during long-running operations.
-   **Cross-Platform Support**: Works on Windows, macOS, and Linux, with automatic GPU detection.

## State Machine

The system uses a state machine to manage conversation flow:

-   **IDLE**: Initial state, ready for conversation.
-   **LISTENING**: Receiving audio from user.
-   **PROCESSING_STT**: Specifically transcribing speech to text.
-   **PROCESSING_LLM**: Generating response with the language model.
-   **PROCESSING_TTS**: Converting text response to audio.
-   **RESPONDING**: Sending audio response to client.
-   **WAITING**: Waiting for next user input.
-   **ERROR**: Error state with recovery mechanisms.

*(Note: A generic `PROCESSING` state is also available for backward compatibility or broader status updates.)*

## Requirements

-   Oculus Quest headset
-   PC with Windows 10/11, macOS, or Linux
-   Python 3.9+
-   [Ollama](https://ollama.ai/) with Mistral or similar model (e.g., `ollama pull mistral`)
-   [AllTalk TTS](https://github.com/erew123/alltalk_tts) (optional, for high-quality voice)

## Installation

### 1. Clone the Repository

```bash
git clone [https://github.com/williamthe5thc/vr_interview_system.git](https://github.com/williamthe5thc/vr_interview_system.git)
cd vr_interview_system
```

### 2. Run the Setup Script

The setup script automatically configures the system for your platform:

```bash
python setup.py
```

This will:
-   Detect your GPU (NVIDIA, AMD, or Apple Silicon)
-   Create necessary directories (logs, data, cache) in your user's application data folder.
-   Generate platform-specific configuration in the application data folder (`VRInterviewSystem/config/config.json`).
-   Install dependencies from `requirements.txt`.
-   Create a launch script (`run_server.bat` or `run_server.sh`).

*(Note: The setup script aims to place user-specific data and configuration outside the main project directory for cleaner management, especially for updates.)*

### 3. Install External Services

#### Install Ollama
-   Download from [ollama.ai](https://ollama.ai/)
-   Pull the Mistral model (or your preferred model): `ollama pull mistral`
-   Start Ollama: `ollama serve`

#### Install AllTalk TTS (Optional)
-   Follow instructions at [AllTalk TTS GitHub](https://github.com/erew123/alltalk_tts)
-   Install to the default location (e.g., `D:/AllTalk/alltalk_tts` on Windows, `~/Applications/AllTalk` on macOS, `~/alltalk_tts` on Linux) or update the path in `VRInterviewSystem/config/config.json`.
-   Start AllTalk server.

### 4. Start the Server

Use the generated launch script from the root of the repository:

**Windows:**
```batch
run_server.bat
```

**macOS/Linux:**
```bash
./run_server.sh
```
This will use `server.py` (which incorporates the fixed logic).

### 5. Setup VR Client

1.  Open the Unity project in Unity 2022.3.7f1 or later.
2.  Set the server URL in the ConnectionManager component (e.g., `ws://localhost:8765`).
3.  Build for Oculus Quest.
4.  Install on your Quest headset.

## Configuration

The primary system configuration is managed through `VRInterviewSystem/config/config.json` in your user's application data directory (e.g., `~/.vr_interview_system/config/config.json` on Linux, `~/Library/Application Support/VRInterviewSystem/config/config.json` on macOS, `%APPDATA%\VRInterviewSystem\config\config.json` on Windows).

An example structure (refer to `config/config_example.json` in the repository for more details):
```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8765,
    "log_level": "INFO"
  },
  "audio": {
    "stt_model": "medium",
    "tts_model": "en",
    "sample_rate": 16000,
    "channels": 1,
    "device": "cuda" // Auto-detected: "cuda", "mps", "rocm", or "cpu"
  },
  "storage": { // Paths are auto-configured by setup.py
    "audio_dir": "path/to/data/audio",
    "conversation_dir": "path/to/data/conversations",
    "retention_days": 30
  },
  "ollama": {
    "url": "http://localhost:11434",
    "model": "mistral:latest",
    "context_length": 8192,
    "system_prompt": "You are an AI interviewer conducting a job interview.",
    "options": {
      "temperature": 0.7,
      "top_p": 0.9,
      "top_k": 40,
      // ... other Ollama options
      "timeout": 60
    }
  },
  "alltalk": { // Paths are auto-configured by setup.py
    "url": "[http://127.0.0.1:7851](http://127.0.0.1:7851)",
    "voice": "female_06.wav",
    "alltalk_dir": "path/to/AllTalk/alltalk_tts",
    "endpoints": ["tts-generate", "synthesize", "tts"]
    // ... other AllTalk options
  },
  "heartbeat": {
    "enabled": true,
    "interval": 5.0
  },
  "cache": { // Paths are auto-configured by setup.py
    "enabled": true,
    "dir": "path/to/data/cache/tts",
    "max_entries": 1000
  }
}
```

Configuration can also be overridden through environment variables using the `VR_INTERVIEW_` prefix (e.g., `export VR_INTERVIEW_SERVER__PORT=8080`).

## Project Structure (Post-Cleanup)

Based on the `CLEANUP_DEPLOYMENT_PLAN.md`, the project structure effectively uses the fixed versions of key files. The structure below reflects this intended state:

```
vr_interview_system/
├── app/                  # Core application modules
│   ├── state/            # State management
│   │   ├── manager.py    # State machine (fixed version)
│   │   └── session.py    # Session data management
│   ├── utils/            # Utility functions
│   │   ├── config.py     # Configuration management
│   │   ├── error_handler.py # Error handling system
│   │   ├── heartbeat.py  # Connection keepalive
│   │   └── logging.py    # Logging configuration
│   │   └── platform_utils.py # Platform-specific utilities
│   └── websocket/        # WebSocket communication
│       ├── enhanced_stream_processor.py # Optimized audio pipeline
│       ├── protocol.py   # Message protocol definition
│       └── server_enhanced_fixed.py # WebSocket server implementation
├── config/               # Example configuration files
├── data/                 # Data storage (typically created in user app data dir)
│   ├── audio/            # Audio file storage
│   ├── cache/            # Response cache storage
│   └── conversations/    # Conversation history
├── docs/                 # Documentation files
├── services/             # Service integrations
│   ├── audio/            # Audio processing services
│   │   ├── stt.py        # Speech-to-text service (Whisper)
│   │   ├── stt_wrapper.py # STT with fallback mechanisms
│   │   └── tts.py        # Text-to-speech service (AllTalk, gTTS)
│   │   └── gpu_monitor.py # GPU monitoring utility
│   └── llm/              # Language model services
│       ├── ollama_client.py # Ollama API client (fixed version)
│       └── scenarios/    # Interview scenarios
├── test_scripts/         # Testing utilities
├── server.py             # Main server entry point (uses fixed version)
├── setup.py              # Cross-platform setup script
├── requirements.txt      # Python dependencies
├── README.md             # This file
├── CHANGELOG.md          # Project changes
├── CONTRIBUTING.md       # Contribution guidelines
└── LICENSE                 # Project license (Assumed to exist)
```

## Documentation

Comprehensive documentation is available in the `docs/` directory:
- `system_overview.md` - High-level architecture and component interactions
- `websocket_documentation.md` - WebSocket protocol and message formats
- `state_management_documentation.md` - State machine implementation details
- `audio_processing_documentation.md` - STT/TTS integration and audio pipeline
- `llm_integration_documentation.md` - Ollama client and prompt engineering
- `error_handling_documentation.md` - Error recovery strategies
- `heartbeat_system_documentation.md` - Connection keepalive mechanism
- `configuration_management_documentation.md` - Configuration system details
- `CUDA_Optimization_Documentation.md` - GPU optimization guide
- `AllTalk_TTS_API_Integration_Guide.md` - AllTalk TTS setup
- `mac_installation_guide.md` - macOS specific installation
- `function_reference.md` - API reference for key functions

## Recent Improvements

Refer to `CHANGELOG.md` for a detailed list of changes. Key recent updates include:
-   **Critical Fixes**: Addressed AI personality confusion, invalid state transitions (loops), and session ID mismatches.
-   **Enhanced LLM Response Handling**: Extended timeout to 45 seconds with progressive updates.
-   **Improved AllTalk Integration**: Fixed API endpoints with multiple fallback strategies.
-   **Session ID Synchronization**: Proper client-server session ID mapping.
-   **Message Validation**: All outgoing messages validated for required fields.
-   **Granular Processing States**: Detailed state reporting (STT, LLM, TTS).
-   **Background Processing**: LLM responses can be delivered even after an initial timeout.
-   **Enhanced UI Experience**: Transcript display with "Interviewer is thinking..." messages.
-   **Cross-Platform Support**: `setup.py` for automatic GPU detection and configuration.

## Testing

Run the test suite using `test_runner.py` located in the `test_scripts/` directory:
```bash
python test_scripts/test_runner.py
```
Or run specific test groups:
```bash
python test_scripts/test_runner.py --group core
```
Individual test utilities are also available (e.g., `test_alltalk.py`, `test_ollama.py`, `test_websocket.py`).

## Troubleshooting

### Connection Issues
1.  Verify the server IP address is accessible from the Quest.
2.  Check firewall settings to ensure the configured port (default: 8765) is open.
3.  Restart both server and client.

### Audio Issues
-   If experiencing issues with AllTalk:
    1.  Check server logs (`server_diagnostic.log`) for streaming confirmation or errors.
    2.  Verify AllTalk server is running and accessible.
    3.  Check the AllTalk `outputs` directory permissions.
    4.  The system will fall back to gTTS if AllTalk fails.

### LLM Issues
1.  Verify Ollama is running: `ollama serve`.
2.  Check if the model is downloaded: `ollama list`.
3.  Try a different model in your `config.json`.

### GPU Issues
-   **NVIDIA**: Ensure CUDA toolkit is installed and NVIDIA drivers are up to date.
-   **AMD (Linux)**: Ensure ROCm drivers are installed.
-   **Apple Silicon**: MPS acceleration is used automatically.
-   The system will fall back to CPU if GPU acceleration fails or is not configured. Check `app/utils/config.py` and `services/audio/stt.py` for device detection logic.

## Development

The system uses an asynchronous architecture:
-   WebSocket communication on the main asyncio event loop.
-   CPU-intensive tasks (STT, LLM, TTS) are generally run in separate thread pools to avoid blocking.
-   State transitions are synchronized across components.
-   Comprehensive error recovery mechanisms are in place.

## Unity Client

The Unity client provides the VR interface with:
-   Dual avatar support (Unity standard and VRM formats).
-   Real-time WebSocket communication.
-   Voice activity detection.
-   Transcript display with speaker identification.
-   Facial expression and lip sync animation.
-   VR-optimized UI with controller interaction.

For detailed Unity client documentation, see the Unity project's README.

## License

This project is licensed under the MIT License - see the `LICENSE` file for details.

## Acknowledgments

-   [Ollama](https://ollama.ai/) for local LLM hosting
-   [AllTalk TTS](https://github.com/erew123/alltalk_tts) for high-quality TTS
-   [Whisper](https://github.com/openai/whisper) for speech recognition
-   [Unity](https://unity.com/) for the VR client platform

## Contributing

Contributions are welcome! Please read `CONTRIBUTING.md` for details on our code of conduct and the process for submitting pull requests.

## Support

For questions or issues:
1.  Check the documentation in the `docs/` directory.
2.  Review the troubleshooting section.
3.  Open an issue on GitHub.
4.  Contact the maintainers.

---
For detailed technical information, see the documentation in the `docs/` directory.
The current project status is **Production Ready** following critical bug fixes.
```
