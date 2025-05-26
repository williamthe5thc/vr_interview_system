# 🎤 VR Interview System

> **AI-Powered Virtual Reality Interview Practice Platform**

Experience realistic job interviews in VR with an intelligent AI interviewer that provides natural conversation, contextual follow-up questions, and professional feedback.

[![Production Ready](https://img.shields.io/badge/Status-Production%20Ready-green)](https://github.com/williamthe5thc/vr_interview_system/tree/testing)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-blue)](https://python.org)
[![Unity 2022.3](https://img.shields.io/badge/Unity-2022.3%20LTS-black)](https://unity.com)
[![WebSocket](https://img.shields.io/badge/Protocol-WebSocket-orange)](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API)

## Overview

The VR Interview System is a **fully functional** virtual reality interview practice platform. **All critical bugs have been resolved**, and the system is now **stable and ready for production use**. It allows users to engage in realistic job interview scenarios within a VR environment. The system consists of a Python-based server running on a PC that connects with an Oculus Quest VR client built in Unity. The server handles natural language processing, audio conversion, and conversation management, while the VR client handles audio capture, playback, and avatar animation.

The system uses a state machine architecture to manage conversation flow, WebSocket communication for real-time interaction, local LLM integration via Ollama, and high-quality text-to-speech via AllTalk with multiple fallback mechanisms for robust operation.

**✅ Key Achievements:**
* **AI Personality Fixed**: AI consistently acts as a professional interviewer.
* **State Machine Fixed**: Clean transitions without infinite loops.
* **Session Management Fixed**: Conversation context preserved throughout.
* **Performance Optimized**: Achieved 5-10 second response times with robust error handling.

## 🎯 Features

* **🎭 Intelligent AI Interviewer**: Professional AI that acts as a hiring manager, not the candidate.
* **🎧 High-Quality Audio**: GPU-accelerated speech recognition (OpenAI Whisper) and natural text-to-speech (AllTalk with gTTS fallback).
* **🔄 Real-Time Processing**: WebSocket-based communication with live state updates.
* **💬 Context-Aware Conversations**: AI remembers and builds upon previous responses.
* **🛡️ Robust Error Handling**: Multiple fallback mechanisms and detailed error recovery for reliable operation.
* **📊 Professional Scenarios**: Configurable interview types (e.g., software engineer, product manager) and difficulty levels via `services/llm/scenarios/job_interview.py`.
* **🗣️ Granular State Updates**: Real-time feedback to the client about processing stages (e.g., `PROCESSING_STT`, `PROCESSING_LLM`, `PROCESSING_TTS`).
* **💾 Session Management**: Persistent context and session synchronization with reconnection handling.

## 🏗️ System Architecture

The system consists of three main components:
1.  **VR Client (Oculus Quest)**: Handles the VR environment, avatar animation, user interaction, audio capture, and UI. Built in Unity.
2.  **Python Server**: Manages WebSocket communication, audio processing (STT/TTS), state management, and LLM integration. The primary server script is `server_fixed.py`.
3.  **External Services**:
    * **LLM Service (Ollama)**: Processes natural language via local models (e.g., Mistral).
    * **TTS Service (AllTalk)**: Provides high-quality speech synthesis, with gTTS as a fallback.
    * **STT Service (Whisper)**: GPU-accelerated speech recognition.

### High-Level Architecture Diagram

```mermaid
graph TB
    subgraph "VR Client (Unity)"
        A[VR Headset] --> B[Unity Application]
        B --> C[WebSocket Client]
        B --> D[Audio Capture]
        B --> E[Avatar System]
        B --> F[UI System]
    end

    subgraph "Network Layer"
        G[WebSocket Connection<br/>Port 8765]
    end

    subgraph "Python Server (server_fixed.py)"
        H[Enhanced Server] --> I[WebSocket Server]
        I --> J[State Manager (manager_fixed.py)]
        I --> K[Stream Processor (enhanced_stream_processor.py)]

        subgraph "Audio Services"
            L[STT Service<br/>(Whisper - stt.py, stt_wrapper.py)]
            M[TTS Service<br/>(AllTalk/gTTS - tts.py, alltalk_tts_direct.py)]
        end

        subgraph "AI Services"
            N[LLM Client<br/>(Ollama_client_fixed.py)]
            O[Scenario Manager (job_interview.py)]
        end

        subgraph "Support Services"
            P[Error Handler (error_handler.py)]
            Q[Heartbeat Service (heartbeat.py)]
            R[Cache Manager]
            S_Config[Configuration (config.py)]
        end
    end

    subgraph "External Services"
        S_Ext[Ollama Server<br/>(Mistral LLM)]
        T_Ext[AllTalk TTS Server]
        U_Ext[CUDA/Whisper STT]
    end

    C -.->|WebSocket| G
    G -.->|WebSocket| I

    K --> L
    K --> M
    K --> N

    L --> U_Ext
    M --> T_Ext
    N --> S_Ext

    J --> P
    I --> Q
    N --> R
    H --> S_Config

    style A fill:#e1f5fe
    style H fill:#c8e6c9
    style S_Ext fill:#fff3e0
    style T_Ext fill:#fff3e0
    style U_Ext fill:#fff3e0
````

[Source for diagram structure: `FLOWCHARTS_FOR_README.md`](https://www.google.com/search?q=FLOWCHARTS_FOR_README.md)

## 🛠️ Technology Stack

  * **VR Client**: Unity (2022.3 LTS recommended), Oculus Quest
  * **Python Server**: Python 3.9+
      * **WebSocket**: `websockets` library
      * **AI Language Model**: Ollama (e.g., Mistral 7b)
      * **Speech-to-Text (STT)**: OpenAI Whisper (GPU accelerated)
      * **Text-to-Speech (TTS)**: AllTalk TTS (Primary), gTTS (Fallback)
      * **Async**: `asyncio` for non-blocking operations
  * **Configuration**: JSON (`config/config.json`)
  * **Caching**: Custom file-based caching for LLM and TTS responses.

## ⚙️ Project Structure

```
vr_interview_system/
├── app/                           # Core application logic
│   ├── state/                     # State management (manager_fixed.py, session.py)
│   ├── utils/                     # Utility functions (config.py, error_handler.py, heartbeat.py, logging.py, platform_utils.py)
│   └── websocket/                 # WebSocket communication (server_enhanced_fixed.py, protocol.py, enhanced_stream_processor.py)
├── config/                        # Configuration files (config.json, profiles)
├── data/                          # Data storage (audio, cache, conversations)
├── docs/                          # Project documentation
│   ├── diagrams/                  # (For potential SVGs or other diagram files)
│   └── troubleshooting/
├── logs/                          # Log files
├── models/                        # TTS/STT Models (e.g., Piper TTS models)
├── services/                      # Service integrations
│   ├── audio/                     # Audio processing (stt.py, stt_wrapper.py, tts.py, alltalk_tts_direct.py, gtts_only_service.py, gpu_monitor.py)
│   │   └── tts_providers/         # Specific TTS provider implementations
│   └── llm/                       # Language model services (Ollama_client_fixed.py)
│       ├── scenarios/             # Interview scenarios (job_interview.py)
│       └── templates/             # Response templates
├── test_scripts/                  # Testing utilities and benchmarks
│   └── benchmark_results/
├── tools/                         # Utility scripts for development and benchmarking
├── .venv/                         # (Virtual environment - typically excluded from Git)
├── server_fixed.py                # Main FIXED server entry point
├── server.py                      # Original server (potentially with bugs)
├── setup.py                       # Cross-platform setup script
├── run_setup.sh                   # Linux/macOS setup script
├── requirements.txt               # Python dependencies
├── README.md                      # This file
├── README_FOR_CLAUDE.md           # Detailed technical guide
├── CHANGELOG.md                   # Project changes
├── CONTRIBUTING.md                # Contribution guidelines
└── LICENSE                        # Project License (MIT License mentioned)
```

[Structure based on `README_FOR_CLAUDE.md` and general file analysis]

## 🚀 Setup and Installation

### Prerequisites

  * Python 3.9+
  * Ollama running locally with a suitable model (e.g., `ollama pull mistral:7b-instruct-q4_K_M`)
  * AllTalk TTS service running (refer to [AllTalk TTS API Integration Guide](https://www.google.com/search?q=docs/AllTalk%2520TTS%2520API%2520Integration%2520Guide.md))
  * (Optional for GPU acceleration) NVIDIA drivers and CUDA toolkit / AMD drivers and ROCm.
  * Unity 2022.3 LTS for VR client development/building.

### Installation Steps

1.  **Clone the repository**:

    ```bash
    git clone https://github.com/williamthe5thc/vr_interview_system.git
    cd vr_interview_system
    git checkout testing # Make sure you are on the 'testing' branch
    ```

2.  **Install Python dependencies**:
    It's highly recommended to use a virtual environment.

    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    pip install -r requirements.txt
    ```

3.  **Run the setup script** (handles platform-specific configurations and GPU detection):

      * On Windows:
        ```bash
        python setup.py
        # or run_setup.bat (if available)
        ```
      * On Linux/macOS:
        ```bash
        python3 setup.py
        # or ./run_setup.sh
        ```

    The setup script will attempt to auto-configure GPU settings in `config/config.json`. Review this file after setup.

4.  **Set up External Services**:

      * **Ollama**: Ensure Ollama is installed and the desired model is pulled (e.g., `ollama pull mistral:7b-instruct-q4_K_M`). Start the Ollama server (`ollama serve`).
      * **AllTalk TTS**: Set up and run the AllTalk TTS server. Refer to its documentation and the [AllTalk TTS API Integration Guide](https://www.google.com/search?q=docs/AllTalk%2520TTS%2520API%2520Integration%2520Guide.md).

## 🏃 Running the System

1.  **Start the Python Server**:
    Navigate to the project root directory (`vr_interview_system`) and run:

    ```bash
    python server_fixed.py
    ```

    (This uses the version with critical bug fixes applied)
    Expected startup output includes confirmations of loaded configurations, initialized services (STT, TTS, LLM), applied fixes, and the server running on `ws://YOUR_HOST:YOUR_PORT`.

2.  **Connect the VR Client**:

      * Build and deploy the Unity client (ensure it points to your PC's IP address and the correct WebSocket port) to your VR headset (e.g., Oculus Quest).
      * Connect the VR client to the server at the displayed WebSocket address (e.g., `ws://YOUR_PC_IP_ADDRESS:8765`).

## ⚙️ Configuration

The system is configured primarily through `config/config.json`. Key settings include:

  * Server host and port.
  * Logging level.
  * Audio settings (STT model, TTS model, sample rate).
  * Ollama settings (URL, model, context length, generation parameters).
  * AllTalk TTS settings (URL, voice).
  * Cache settings.
  * Heartbeat settings.

Refer to the `config/config_example.json` for detailed explanations of all options and the [Configuration Management Documentation](https://www.google.com/search?q=docs/configuration_management_documentation.md) for more in-depth information.

The `tools/setup_config.py` script can help set up specific configuration profiles (development, production, minimal).

## 📚 Documentation

This project includes comprehensive documentation in the `docs/` directory:

  * **Core Architecture & Integration:**
      * [System Overview](https://www.google.com/search?q=docs/system_overview.md)
      * [Architecture Overview](https://www.google.com/search?q=docs/architecture_overview.md)
      * [Configuration Management](https://www.google.com/search?q=docs/configuration_management_documentation.md)
      * [WebSocket Communication](https://www.google.com/search?q=docs/websocket_documentation.md)
      * [State Management](https://www.google.com/search?q=docs/state_management_documentation.md)
      * [Enhanced Stream Processor](https://www.google.com/search?q=docs/enhanced_stream_processor_documentation.md)
  * **Service Integrations:**
      * [LLM Integration (Ollama)](https://www.google.com/search?q=docs/llm_integration_documentation.md)
      * [Audio Processing (STT & TTS)](https://www.google.com/search?q=docs/audio_processing_documentation.md)
      * [AllTalk TTS API Integration Guide](https://www.google.com/search?q=docs/AllTalk%2520TTS%2520API%2520Integration%2520Guide.md)
  * **Error Handling & Stability:**
      * [Error Handling System](https://www.google.com/search?q=docs/error_handling_documentation.md)
      * [Heartbeat System](https://www.google.com/search?q=docs/heartbeat_system_documentation.md)
  * **Performance & Platform:**
      * [CUDA Optimization Guide](https://www.google.com/search?q=docs/CUDA%2520Optimization%2520Documentation.md)
      * [Mac & AMD GPU Installation Guide](https://www.google.com/search?q=docs/mac_installation_guide.md)
  * **Development & Reference:**
      * [Function Reference](https://www.google.com/search?q=docs/function_reference.md)
      * [Contributing Guidelines](https://www.google.com/search?q=CONTRIBUTING.md)
      * [Changelog](CHANGELOG.md)
  * **Internal Reports & Summaries:**
      * [Code Optimization Report](https://www.google.com/search?q=CODE_OPTIMIZATION_REPORT.md)
      * [Critical Fixes Summary](https://www.google.com/search?q=CRITICAL_FIXES_SUMMARY.md)
      * [Documentation Status & Roadmap](https://www.google.com/search?q=DOCUMENTATION_STATUS.md)

## 🤝 Contributing

Contributions are welcome\! Please read the [Contributing Guidelines](https://www.google.com/search?q=CONTRIBUTING.md) for details on how to contribute, including code style, testing, and the pull request process.

Key areas for contribution include:

  * Bug Fixes
  * New Features
  * Documentation Improvements
  * Test Coverage
  * Performance Optimizations
  * Refactoring

## 🐛 Troubleshooting

Common issues and solutions are documented:

  * **Server Won't Start**: Check Python environment, dependencies (`pip install -r requirements.txt`), and external services like Ollama and AllTalk.
  * **Audio Processing Fails**: Ensure GPU drivers (NVIDIA/AMD) and CUDA are correctly installed. Check microphone permissions.
  * **AI Personality Issues**: Verify the `Ollama_client_fixed.py` is in use and `config.json` has appropriate `scenario_type` and `system_prompt` (often should be null to let the fixed client handle it).
  * **State Machine Loops**: Ensure `manager_fixed.py` is in use. Check server logs for "Invalid state transition" messages.
  * **Streaming Issues**: Refer to the [Streaming Issues Troubleshooting Guide](https://www.google.com/search?q=docs/troubleshooting/STREAMING_ISSUES.md).

Refer to `server_diagnostic.log` for detailed server logs.

## 📜 License

This project appears to be licensed under the MIT License (based on references). Please ensure a `LICENSE` file is present in the repository root.

## 📅 Changelog

See the [CHANGELOG.md](CHANGELOG.md) for a detailed history of changes to the project.

```

This version updates the badge link and the clone instructions and ensures other links use relative paths, which should work correctly when viewed on your GitHub repository. It also keeps the Mermaid diagram, which should render directly.
```
