# VR Interview System - Project Structure

## Overview

The VR Interview System is organized into a modular structure to enable better maintainability and clarity.

## Directory Structure

```
vr_interview_system/
│
├── app/                        # Application core
│   ├── state/                  # State management
│   │   ├── manager.py          # State machine implementation
│   │   └── session.py          # Session handling
│   ├── utils/                  # Utilities
│   │   ├── config.py           # Configuration handling
│   │   ├── error_handler.py    # Error handling
│   │   └── logging.py          # Logging setup
│   └── websocket/              # WebSocket implementation
│       ├── protocol.py         # Message protocol
│       └── server_enhanced.py  # Enhanced WebSocket server
│
├── bin/                        # Binaries and tools
│   └── tools/                  # Python tools
│       ├── list_microphones.py # Microphone listing utility
│       ├── test_client.py      # Test client
│       └── ...                 # Other tools
│
├── config/                     # Configuration files
│   ├── config.json             # Default configuration (consolidated)
│   ├── config_development.json # Development configuration
│   ├── config_production.json  # Production configuration
│   ├── config_minimal.json     # Minimal resource configuration
│   └── config_example.json     # Example configuration with comments
│
├── data/                       # Data storage
│   ├── audio/                  # Audio data
│   │   ├── responses/          # TTS responses
│   │   └── uploads/            # Audio uploads
│   └── conversations/          # Conversation history
│
├── docs/                       # Documentation
│   ├── quick_start.md           # Quick start guide
│   ├── configuration.md         # Configuration guide
│   ├── enhanced_features.md     # Enhanced features guide
│   ├── llm_optimization.md      # LLM optimization details
│   ├── system_optimizations.md   # System-wide optimizations
│   └── project_structure.md     # This document
│
├── logs/                       # Log files
│
├── scripts/                    # Batch scripts
│   ├── use_alltalk_final.bat   # Start with AllTalk
│   └── ...                     # Other scripts
│
├── services/                   # Service implementations
│   ├── audio/                  # Audio services
│   │   ├── alltalk_tts.py      # AllTalk TTS service
│   │   ├── stt.py              # Speech-to-text service
│   │   ├── tts.py              # Generic TTS service
│   │   ├── reload_alltalk.py   # AllTalk reload utility
│   │   └── backups/            # Implementation backups
│   └── llm/                    # LLM services
│       └── ollama_client.py    # Ollama client
│
├── server_enhanced.py          # Main enhanced server
├── start_interview_system.bat  # Main startup script
└── README.md                   # Project README
```

## Key Components

### Main Components

- **server_enhanced.py**: The main server that coordinates all components
- **app/websocket/server_enhanced.py**: WebSocket server implementation
- **app/state/manager.py**: State management system
- **services/audio/alltalk_tts.py**: AllTalk TTS integration
- **services/llm/ollama_client.py**: Ollama LLM client

### Configuration

- **config/config_enhanced.json**: Main configuration file for the enhanced server
- **config/config_alltalk.json**: AllTalk-specific configuration

### Scripts

- **scripts/use_alltalk_final.bat**: Start server with AllTalk integration
- **start_interview_system.bat**: Main startup script

## Starting the System

To start the VR Interview System:

```batch
start_interview_system.bat
```

This will start the enhanced server with AllTalk TTS integration.

## Development

For development and testing:

1. Modify the configuration files in the `config` directory
2. Use the backup implementations in `services/audio/backups` as reference
3. Check the logs in the `logs` directory for troubleshooting
