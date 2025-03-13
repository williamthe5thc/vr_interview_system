# VR Interview System

A WebSocket-based server system for VR interview practice with an intelligent virtual interviewer powered by local LLM technology.

## Quick Start Guide

1. **Install dependencies**:
   ```
   install_dependencies.bat
   ```

2. **Run the system with microphone input**:
   ```
   use_mic.bat
   ```

3. **Run with AllTalk for better voice quality**:
   ```
   use_alltalk_mic.bat
   ```

4. **Run an automated interview simulation**:
   ```
   use_simulation.bat
   ```

## System Overview

The VR Interview System provides a realistic job interview practice environment, with an intelligent interviewer powered by local LLM technology. The system consists of a WebSocket server and client components, handling audio processing, conversation management, and LLM interactions.

## Architecture

The system is divided into three main components:
1. **WebSocket Server** - Manages WebSocket communication, processes audio, and coordinates state
2. **LLM Service (Ollama)** - Handles natural language processing via local Phi or similar model
3. **Client Components** - Microphone input or automated simulation

## Features

- **Real-time conversation** with an AI interviewer using your microphone
- **Automated simulation** with pre-defined interview questions
- **AllTalk integration** for high-quality speech synthesis
- **Fallback to gTTS** when AllTalk is not available
- **State machine** tracking conversation flow

## Batch Files

The system includes several batch files for easy usage:

- **install_dependencies.bat**: Install required Python packages
- **use_mic.bat**: Run with microphone input
- **use_alltalk_mic.bat**: Run with AllTalk and microphone input
- **use_simulation.bat**: Run automated interview simulation
- **use_alltalk.bat**: Run the server with AllTalk integration

## Troubleshooting

### Common Issues:

1. **Missing dependencies**:
   - Run `install_dependencies.bat` to install required packages

2. **Port already in use**:
   - Run `kill_server.py` to kill any existing servers
   - Or restart your computer to free up all ports

3. **AllTalk connection issues**:
   - Make sure AllTalk is running at http://127.0.0.1:7851
   - Check the AllTalk console for errors

4. **Audio issues**:
   - Check if your microphone is working
   - Adjust the silence threshold in mic_client.py if needed

## Advanced Usage

See the extended README (README_EXTENDED.md) for more detailed information on:
- Advanced configuration options
- Customizing voices
- API details
- Development guidelines

## License

MIT License
