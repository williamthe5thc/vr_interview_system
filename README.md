# VR Interview System

A virtual reality job interview practice system with a conversational AI interviewer powered by local language models.

## Overview

The VR Interview System provides a realistic job interview practice environment in virtual reality, featuring an AI-powered interviewer that responds to your speech in natural language. The system uses local language models (via Ollama) for conversation generation and can stream audio responses for a seamless experience.

## System Architecture

The system consists of three main components:

1. **VR Client (Oculus Quest)**: Handles the VR environment, avatar animation, and user interaction
2. **Python Server**: Manages WebSocket communication, audio processing, state management, and LLM integration
3. **LLM Service (Ollama)**: Processes natural language via local models such as Phi, Mistral, or other models

## Key Features

- **Real-time Conversation**: Speak naturally to the AI interviewer and receive contextually appropriate responses
- **Audio Streaming**: Fast response time with AllTalk TTS streaming capability
- **Local Processing**: All processing happens locally without requiring cloud services
- **Realistic Avatar**: Professional interviewer avatar with synchronized speech and expressions
- **Robust Error Handling**: Graceful fallbacks when components fail

## Requirements

- Oculus Quest headset
- PC with Windows 10/11
- Python 3.9+
- [Ollama](https://ollama.ai/) with Mistral or similar model
- [AllTalk TTS](https://github.com/erew123/alltalk_tts) (for high-quality voice)

## Setup Instructions

### Server Setup

1. Clone the repository
   ```
   git clone https://github.com/yourusername/vr-interview-system.git
   cd vr-interview-system
   ```

2. Create and activate a virtual environment
   ```
   python -m venv venv
   venv\Scripts\activate
   ```

3. Install requirements
   ```
   pip install -r requirements.txt
   ```

4. Install and start Ollama
   - Download from [ollama.ai](https://ollama.ai/)
   - Pull the Mistral model: `ollama pull mistral`

5. Install and configure AllTalk TTS
   - Follow instructions at [AllTalk TTS GitHub](https://github.com/erew123/alltalk_tts)
   - Start AllTalk server

6. Configure the system
   - Modify `config/config.json` as needed

7. Start the server
   ```
   python server.py
   ```

### VR Client Setup

1. Open the Unity project in Unity 2022.3.7f1 or later
2. Set the server URL in the ConnectionManager component settings
3. Build for Oculus Quest
4. Install on your Quest headset

## Configuration

The system can be configured through the `config/config.json` file:

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8765,
    "log_level": "INFO"
  },
  "audio": {
    "stt_model": "medium",
    "tts_model": "en"
  },
  "ollama": {
    "url": "http://localhost:11434",
    "model": "mistral:latest"
  },
  "alltalk": {
    "url": "http://127.0.0.1:7851",
    "voice": "YourPreferredVoice.wav",
    "alltalk_dir": "D:/AllTalk/alltalk_tts"
  }
}
```

## AllTalk Streaming Integration

The system includes optimized integration with AllTalk TTS for streaming audio responses:

- Direct streaming from AllTalk to the VR client
- Parallel audio synthesis for fast fallback
- Multiple file location checking for reliable retrieval
- Automatic adaptation to AllTalk's file extensions
- Progressive timeouts to handle AllTalk's generation times

## Troubleshooting

### Audio Streaming Issues

If you experience issues with AllTalk streaming:

1. Check the server logs for streaming confirmation messages
2. Verify AllTalk is running and the URL is correct in config.json
3. Check permissions on the AllTalk outputs directory
4. Increase streaming timeout in config if needed
5. Check the Unity client logs for streaming status updates

### Connection Issues

1. Verify the server IP address is accessible from the Quest
2. Check firewall settings to ensure port 8765 is open
3. Restart both server and client

### LLM Integration Issues

1. Verify Ollama is running (`ollama serve`)
2. Check if the model is downloaded (`ollama list`)
3. Try a different model in config.json

## Development

The system uses an asynchronous architecture to prevent blocking during LLM and audio processing:

- WebSocket communication runs on the main asyncio event loop
- CPU-intensive tasks (STT, LLM, TTS) run in separate thread pools
- State transitions are synchronized across components

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Ollama](https://ollama.ai/) for local LLM hosting
- [AllTalk TTS](https://github.com/erew123/alltalk_tts) for high-quality TTS
- [Whisper](https://github.com/openai/whisper) for speech recognition
