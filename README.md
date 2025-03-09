# VR Interview System

A WebSocket-based server system for VR interview practice with an intelligent virtual interviewer powered by local LLM technology.

## System Overview

The VR Interview System provides a realistic job interview practice environment in VR, with an intelligent interviewer powered by local LLM technology. The system consists of an Oculus Quest client and a PC server component connected via WebSockets, handling audio processing, conversation management, and LLM interactions.

## Architecture

The system is divided into three main components:
1. **VR Client (Oculus Quest)** - Handles VR environment, avatar animation, and user interaction
2. **Server Application (PC)** - Manages WebSocket communication, processes audio, and coordinates state
3. **LLM Service (Ollama)** - Handles natural language processing via local Phi or similar model

## Project Structure

```
vr_interview_system/
├── app/
│   ├── state/              # State management
│   │   ├── manager.py      # State machine implementation
│   │   └── session.py      # Session management
│   ├── utils/              # Utilities
│   │   ├── config.py       # Configuration management
│   │   └── logging.py      # Logging configuration
│   └── websocket/          # WebSocket components
│       ├── protocol.py     # Message protocol
│       └── server.py       # WebSocket server implementation
├── data/                   # Data directories
│   ├── audio/              # Audio storage
│   │   ├── responses/      # System audio responses
│   │   └── uploads/        # User audio recordings
│   └── conversations/      # Conversation history
├── logs/                   # Application logs
├── services/               # Core services
│   ├── audio/              # Audio processing
│   │   ├── stt.py          # Speech-to-text (Whisper)
│   │   └── tts.py          # Text-to-speech (gTTS)
│   └── llm/                # LLM integration
│       └── ollama_client.py # Ollama API client
├── tools/                  # Utility tools
│   └── test_client.py      # Test WebSocket client
├── config.json             # Configuration file
├── requirements.txt        # Python dependencies
└── server.py               # Main entry point
```

## Prerequisites

- Python 3.8+
- Ollama with Phi model
- OpenAI Whisper
- WebSockets server/client

## Installation

1. Clone the repository:
```bash
git clone https://your-repository-url.git
cd vr_interview_system
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install Ollama (https://ollama.ai/) and pull the Phi model:
```bash
ollama pull phi
```

## Configuration

Edit the `config.json` file to configure the system:

```json
{
  "server": {
    "host": "0.0.0.0",  // Server host address (0.0.0.0 for all interfaces)
    "port": 8765,       // WebSocket server port
    "log_level": "INFO" // Logging level
  },
  "audio": {
    "stt_model": "base", // Whisper model size: tiny, base, small, medium, large
    "tts_model": "gtts"  // Text-to-speech model
  },
  "ollama": {
    "url": "http://localhost:11434", // Ollama API URL
    "model": "phi",                  // LLM model name
    "context_length": 4096           // Context window size
  }
}
```

## Running the Server

1. Start the Ollama service:
```bash
ollama serve
```

2. In a separate terminal, run the server:
```bash
python server.py
```

The server will start and listen for WebSocket connections on the configured port.

## Testing

Use the included test client to test the server:

```bash
python tools/test_client.py --audio path/to/test_audio.webm
```

This will send an audio file to the server and play back the response.

## State Machine

The conversation follows these states:
- IDLE → LISTENING → PROCESSING → RESPONDING → WAITING → (repeat)
- ERROR state for handling failures with recovery paths

## WebSocket Protocol

### Client to Server Messages

**Audio Data Message**
```json
{
  "type": "audio_data",
  "session_id": "string",
  "timestamp": 1646721387.23,
  "data": "base64-encoded-audio"
}
```

**Control Message**
```json
{
  "type": "control",
  "session_id": "string",
  "action": "start|stop|reset",
  "timestamp": 1646721387.23
}
```

### Server to Client Messages

**State Update Message**
```json
{
  "type": "state_update",
  "session_id": "string",
  "previous": "string",
  "current": "string",
  "timestamp": 1646721387.23,
  "metadata": {}
}
```

**Audio Response Message**
```json
{
  "type": "audio_response",
  "session_id": "string",
  "timestamp": 1646721387.23,
  "duration": 2.5,
  "data": "base64-encoded-audio"
}
```

## Integration with Oculus Quest

For the Oculus Quest client:

1. Implement WebSocket client in Unity
2. Handle state updates and audio playback
3. Synchronize avatar mouth movements with audio
4. Implement audio capture and transmission

## Troubleshooting

### Common Issues

1. **WebSocket Connection Failed**
   - Check that the server is running
   - Verify firewall settings
   - Ensure client and server are on the same network

2. **Ollama Connection Failed**
   - Check that Ollama is running
   - Verify the Phi model is downloaded
   - Check the Ollama URL in config.json

3. **Audio Issues**
   - Check audio format compatibility
   - Verify that Whisper is properly installed
   - Check permissions for audio file access

### Logs

Check the logs in the `logs/` directory for detailed error information.

## License

[MIT License](LICENSE)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
