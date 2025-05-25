# VR Interview System

A virtual reality job interview practice system with a conversational AI interviewer powered by local language models.

## Overview

The VR Interview System provides a realistic job interview practice environment in virtual reality, featuring an AI-powered interviewer that responds to your speech in natural language. The system uses local language models (via Ollama) for conversation generation and can stream audio responses for a seamless experience.

## System Architecture

The system consists of three main components:

1. **VR Client (Oculus Quest)**: Handles the VR environment, avatar animation, and user interaction
2. **Python Server**: Manages WebSocket communication, audio processing, state management, and LLM integration
3. **LLM Service (Ollama)**: Processes natural language via local models such as Phi, Mistral, or other models

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

- **Real-time Conversation**: Speak naturally to the AI interviewer and receive contextually appropriate responses
- **Audio Streaming**: Fast response time with AllTalk TTS streaming capability
- **Local Processing**: All processing happens locally without requiring cloud services
- **Realistic Avatar**: Professional interviewer avatar with synchronized speech and expressions
- **Robust Error Handling**: Graceful fallbacks when components fail
- **State Machine Architecture**: Well-defined conversation states with transitions
- **Session Management**: Persistent sessions with context preservation
- **Heartbeat Mechanism**: Maintains connection during long-running operations
- **Cross-Platform Support**: Works on Windows, macOS, and Linux

## State Machine

The system uses a state machine to manage conversation flow:

- **IDLE**: Initial state, ready for conversation
- **LISTENING**: Receiving audio from user
- **PROCESSING**: Generic processing state
- **PROCESSING_STT**: Specifically transcribing speech to text
- **PROCESSING_LLM**: Generating response with the language model
- **PROCESSING_TTS**: Converting text response to audio
- **RESPONDING**: Sending audio response to client
- **WAITING**: Waiting for next user input
- **ERROR**: Error state with recovery mechanisms

## Requirements

- Oculus Quest headset
- PC with Windows 10/11, macOS, or Linux
- Python 3.9+
- [Ollama](https://ollama.ai/) with Mistral or similar model
- [AllTalk TTS](https://github.com/erew123/alltalk_tts) (optional, for high-quality voice)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/vr-interview-system.git
cd vr-interview-system
```

### 2. Run the Setup Script

The setup script automatically configures the system for your platform:

```bash
python setup.py
```

This will:
- Detect your GPU (NVIDIA, AMD, or Apple Silicon)
- Create necessary directories
- Generate platform-specific configuration
- Install dependencies
- Create a launch script

### 3. Install External Services

#### Install Ollama
- Download from [ollama.ai](https://ollama.ai/)
- Pull the Mistral model: `ollama pull mistral`
- Start Ollama: `ollama serve`

#### Install AllTalk TTS (Optional)
- Follow instructions at [AllTalk TTS GitHub](https://github.com/erew123/alltalk_tts)
- Install to the default location or update the config file
- Start AllTalk server

### 4. Start the Server

Use the generated launch script:

**Windows:**
```batch
run_server.bat
```

**macOS/Linux:**
```bash
./run_server.sh
```

### 5. Setup VR Client

1. Open the Unity project in Unity 2022.3.7f1 or later
2. Set the server URL in the ConnectionManager component
3. Build for Oculus Quest
4. Install on your Quest headset

## Configuration

The system is configured through `config/config.json`:

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
    "device": "cuda"  // or "cpu", "mps" for Apple Silicon
  },
  "storage": {
    "audio_dir": "data/audio",
    "conversation_dir": "data/conversations",
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
      "repeat_penalty": 1.1,
      "num_predict": 100,
      "seed": 42,
      "timeout": 60
    }
  },
  "alltalk": {
    "url": "http://127.0.0.1:7851",
    "voice": "female_06.wav",
    "format": "wav",
    "retries": 3,
    "timeout": 60,
    "default_language": "en",
    "endpoints": ["tts-generate", "synthesize", "tts"]
  },
  "heartbeat": {
    "enabled": true,
    "interval": 5.0
  },
  "cache": {
    "enabled": true,
    "dir": "data/cache/tts",
    "max_entries": 1000
  }
}
```

Configuration can also be overridden through environment variables using the `VR_INTERVIEW_` prefix:

```bash
export VR_INTERVIEW_SERVER__PORT=8080
export VR_INTERVIEW_OLLAMA__URL=http://ollama:11434
```

## Project Structure

```
vr_interview_system/
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
├── services/             # Service integrations
│   ├── audio/            # Audio processing services
│   │   ├── stt.py        # Speech-to-text service
│   │   ├── stt_wrapper.py # STT with fallback mechanisms
│   │   └── tts.py        # Text-to-speech service
│   └── llm/              # Language model services
│       └── ollama_client.py # Ollama API client
├── test_scripts/         # Testing utilities
├── server.py             # Main server entry point
├── setup.py              # Cross-platform setup script
├── requirements.txt      # Python dependencies
└── README.md             # This file
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
- `function_reference.md` - API reference for key functions

## Recent Improvements

- **Enhanced LLM Response Handling**: Extended timeout to 45 seconds with progressive updates
- **Improved AllTalk Integration**: Fixed API endpoints with multiple fallback strategies
- **Session ID Synchronization**: Proper client-server session ID mapping
- **Message Validation**: All outgoing messages validated for required fields
- **Granular Processing States**: Detailed state reporting (STT, LLM, TTS)
- **Background Processing**: LLM responses delivered even after timeout
- **Enhanced UI Experience**: Transcript display with "thinking" indicators
- **Cross-Platform Support**: Automatic GPU detection and configuration

## Testing

Run the test suite:

```bash
python -m pytest test_scripts/
```

Individual test utilities:

- `test_alltalk.py` - Test AllTalk TTS connection
- `test_ollama.py` - Test Ollama LLM connection
- `test_websocket.py` - Test WebSocket communication
- `test_integration.py` - Full system integration test

## Troubleshooting

### Connection Issues

1. Verify the server IP address is accessible from the Quest
2. Check firewall settings to ensure port 8765 is open
3. Restart both server and client

### Audio Issues

If you experience issues with AllTalk:

1. Check server logs for streaming confirmation
2. Verify AllTalk is running and accessible
3. Check the AllTalk outputs directory permissions
4. System will fall back to gTTS if AllTalk fails

### LLM Issues

1. Verify Ollama is running: `ollama serve`
2. Check if model is downloaded: `ollama list`
3. Try a different model in config.json

### GPU Issues

- **NVIDIA**: Ensure CUDA is installed
- **AMD**: ROCm support on Linux, CPU fallback on Windows
- **Apple Silicon**: MPS acceleration used automatically

## Development

The system uses an asynchronous architecture:

- WebSocket communication on the main asyncio event loop
- CPU-intensive tasks (STT, LLM, TTS) in separate thread pools
- State transitions synchronized across components
- Comprehensive error recovery mechanisms

## Unity Client

The Unity client provides the VR interface with:

- Dual avatar support (Unity standard and VRM formats)
- Real-time WebSocket communication
- Voice activity detection
- Transcript display with speaker identification
- Facial expression and lip sync animation
- VR-optimized UI with controller interaction

For detailed Unity client documentation, see the Unity project README.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Ollama](https://ollama.ai/) for local LLM hosting
- [AllTalk TTS](https://github.com/erew123/alltalk_tts) for high-quality TTS
- [Whisper](https://github.com/openai/whisper) for speech recognition
- [Unity](https://unity.com/) for the VR client platform

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## Support

For questions or issues:

1. Check the documentation in the `docs/` directory
2. Review the troubleshooting section
3. Open an issue on GitHub
4. Contact the maintainers

---

For detailed technical information, see the documentation in the `docs/` directory and the current development status in the README_FOR_CLAUDE.md file.