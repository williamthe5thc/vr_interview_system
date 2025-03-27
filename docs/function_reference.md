# VR Interview System: Function Reference

This document provides an alphabetical reference to key functions and methods in the VR Interview System. Each function is documented with its purpose, parameters, return values, examples, and related functions.

## Table of Contents

1. [EnhancedServer](#enhancedserver)
2. [ErrorHandler](#errorhandler)
3. [OllamaClient](#ollamaclient)
4. [Session](#session)
5. [StateManager](#statemanager)
6. [STTService](#sttservice)
7. [TTS Services](#tts-services)
8. [WebSocketServer](#websocketserver)

---

## EnhancedServer

### `__init__(self, config_path="config/config.json")`

**Purpose:**  
Initializes the enhanced server with all required components.

**Parameters:**  
- `config_path` (str): Path to the configuration file

**Returns:**  
None

**Example:**
```python
server = EnhancedServer("config/custom_config.json")
```

**Related Functions:**
- `start()`: Starts the server
- `_load_config()`: Loads configuration from file

### `start(self)`

**Purpose:**  
Starts the WebSocket server and initializes all services.

**Parameters:**  
None

**Returns:**  
None (asynchronous function)

**Example:**
```python
await server.start()
```

**Related Functions:**
- `shutdown()`: Shuts down the server
- `_setup_directories()`: Creates necessary directories

### `_load_config(self, config_path)`

**Purpose:**  
Loads configuration from a file with fallback to default configuration.

**Parameters:**  
- `config_path` (str): Path to the configuration file

**Returns:**  
- `dict`: Loaded configuration

**Example:**
```python
config = self._load_config("config/config.json")
```

**Related Functions:**
- `__init__()`: Main initialization function

### `_register_error_handlers(self)`

**Purpose:**  
Registers handlers for different error types.

**Parameters:**  
None

**Returns:**  
None

**Example:**
```python
self._register_error_handlers()
```

**Related Functions:**
- `_handle_llm_error()`: Handles LLM errors
- `_handle_stt_error()`: Handles STT errors
- `_handle_tts_error()`: Handles TTS errors

### `_shutdown(self)`

**Purpose:**  
Gracefully shuts down the server and cleans up resources.

**Parameters:**  
None

**Returns:**  
None (asynchronous function)

**Example:**
```python
await server._shutdown()
```

**Related Functions:**
- `_signal_handler()`: Handles termination signals

---

## ErrorHandler

### `__init__(self)`

**Purpose:**  
Initializes the error handler with tracking structures.

**Parameters:**  
None

**Returns:**  
None

**Example:**
```python
error_handler = ErrorHandler()
```

**Related Functions:**
- `register_recovery_handler()`: Registers handlers for error types
- `handle_error()`: Main error handling method

### `handle_error(self, error_type, session_id, exception, context=None)`

**Purpose:**  
Handles errors with appropriate recovery strategies.

**Parameters:**  
- `error_type` (str): Type of error (use class constants)
- `session_id` (str): Session identifier
- `exception` (Exception): The exception that occurred
- `context` (dict, optional): Additional context information for recovery

**Returns:**  
- `tuple`: (success, metadata)

**Example:**
```python
success, metadata = await error_handler.handle_error(
    ErrorHandler.LLM_ERROR,
    session_id,
    exception,
    {"websocket": websocket}
)
```

**Related Functions:**
- `_handle_exceeded_recovery_attempts()`: Handles excessive recovery attempts
- `_handle_cooldown_recovery()`: Handles recovery during cooldown

### `register_recovery_handler(self, error_type, handler)`

**Purpose:**  
Registers a handler function for a specific error type.

**Parameters:**  
- `error_type` (str): Type of error to handle
- `handler` (callable): Function to handle the error

**Returns:**  
None

**Example:**
```python
error_handler.register_recovery_handler(
    ErrorHandler.LLM_ERROR,
    self._handle_llm_error
)
```

**Related Functions:**
- `handle_error()`: Main error handling method

### `get_error_statistics(self, session_id=None)`

**Purpose:**  
Gets error statistics for debugging and monitoring.

**Parameters:**  
- `session_id` (str, optional): Session ID for specific session stats

**Returns:**  
- `dict`: Error statistics

**Example:**
```python
stats = error_handler.get_error_statistics(session_id)
```

**Related Functions:**
- `_aggregate_error_types()`: Aggregates error types across sessions

### `reset_session_errors(self, session_id)`

**Purpose:**  
Resets error tracking for a specific session.

**Parameters:**  
- `session_id` (str): Session identifier to reset

**Returns:**  
None

**Example:**
```python
error_handler.reset_session_errors(session_id)
```

**Related Functions:**
- `cleanup_old_sessions()`: Cleans up error tracking for old sessions

---

## OllamaClient

### `__init__(self, url, model, context_length=8192, config=None)`

**Purpose:**  
Initializes the Ollama client with configuration.

**Parameters:**  
- `url` (str): The URL of the Ollama API
- `model` (str): The model to use (e.g., "mistral:latest")
- `context_length` (int): Maximum context length for the model
- `config` (dict, optional): Additional configuration

**Returns:**  
None

**Example:**
```python
llm_client = OllamaClient(
    "http://localhost:11434",
    "mistral:latest",
    8192,
    config
)
```

**Related Functions:**
- `_load_system_prompt()`: Loads the system prompt for the scenario
- `generate_response()`: Generates a response from the LLM

### `generate_response(self, prompt, context=None, timeout=None, max_retries=None, interaction_stage=None)`

**Purpose:**  
Generates a response using the Ollama API.

**Parameters:**  
- `prompt` (str): The user input to respond to
- `context` (list, optional): Conversation history
- `timeout` (int, optional): Request timeout in seconds
- `max_retries` (int, optional): Maximum retry attempts
- `interaction_stage` (str, optional): Current stage of the interaction

**Returns:**  
- `str`: Generated response text

**Example:**
```python
response = llm_client.generate_response(
    "Tell me about your experience with Python",
    context,
    timeout=30,
    max_retries=2,
    interaction_stage="technical_question"
)
```

**Related Functions:**
- `_format_prompt()`: Formats the prompt with context
- `_create_cache_key()`: Creates a cache key for the request

### `generate_response_async(self, prompt, context=None, timeout=None, max_retries=None, progress_callback=None, interaction_stage=None)`

**Purpose:**  
Generates a response asynchronously, without blocking.

**Parameters:**  
- `prompt` (str): The user input to respond to
- `context` (list, optional): Conversation history
- `timeout` (int, optional): Request timeout in seconds
- `max_retries` (int, optional): Maximum retry attempts
- `progress_callback` (callable, optional): Callback for progress updates
- `interaction_stage` (str, optional): Current stage of the interaction

**Returns:**  
- `str`: Generated response text

**Example:**
```python
response = await llm_client.generate_response_async(
    prompt,
    context,
    timeout=30,
    progress_callback=update_progress
)
```

**Related Functions:**
- `_make_ollama_request()`: Makes the actual HTTP request

### `_format_prompt(self, user_input, context, interaction_stage=None)`

**Purpose:**  
Formats the prompt with system instructions and conversation history.

**Parameters:**  
- `user_input` (str): The user's input
- `context` (list): Conversation history
- `interaction_stage` (str, optional): Current stage of the interaction

**Returns:**  
- `str`: Formatted prompt for the LLM

**Example:**
```python
formatted_prompt = llm_client._format_prompt(
    user_input,
    context,
    "technical_question"
)
```

**Related Functions:**
- `generate_response()`: Generates a response using the prompt

### `stream_response(self, prompt, context=None, callback=None, interaction_stage=None)`

**Purpose:**  
Streams a response with incremental output.

**Parameters:**  
- `prompt` (str): The user input to respond to
- `context` (list, optional): Conversation history
- `callback` (callable, optional): Function to call with each text chunk
- `interaction_stage` (str, optional): Current stage of the interaction

**Returns:**  
- `str`: Complete generated response

**Example:**
```python
response = await llm_client.stream_response(
    prompt,
    context,
    on_token_received,
    "greeting"
)
```

**Related Functions:**
- `_stream_ollama_request()`: Makes the streaming request

---

## Session

### `__init__(self, session_id, websocket)`

**Purpose:**  
Initializes a new session with a client.

**Parameters:**  
- `session_id` (str): Unique identifier for the session
- `websocket`: WebSocket connection object

**Returns:**  
None

**Example:**
```python
session = Session(session_id, websocket)
```

**Related Functions:**
- `add_interaction()`: Records a user-system interaction
- `get_context()`: Gets conversation context for the LLM

### `add_interaction(self, user_input, system_response)`

**Purpose:**  
Records a user-system interaction in the conversation history.

**Parameters:**  
- `user_input` (str): User's input
- `system_response` (str): System's response

**Returns:**  
None

**Example:**
```python
session.add_interaction(transcript, response)
```

**Related Functions:**
- `get_context()`: Gets the conversation context from history

### `get_context(self)`

**Purpose:**  
Gets formatted conversation context for the LLM.

**Parameters:**  
None

**Returns:**  
- `list`: Conversation turns formatted for the LLM

**Example:**
```python
context = session.get_context()
```

**Related Functions:**
- `add_interaction()`: Adds to the conversation history

### `reset(self)`

**Purpose:**  
Resets the conversation history.

**Parameters:**  
None

**Returns:**  
None

**Example:**
```python
session.reset()
```

**Related Functions:**
- `add_interaction()`: Adds to the conversation history

### `is_expired(self, timeout_seconds=1800)`

**Purpose:**  
Checks if the session has expired due to inactivity.

**Parameters:**  
- `timeout_seconds` (int): Inactivity timeout in seconds (default: 30 minutes)

**Returns:**  
- `bool`: True if expired, False otherwise

**Example:**
```python
if session.is_expired(3600):  # 1 hour
    # Handle expired session
```

**Related Functions:**
- `to_dict()`: Converts session to a dictionary

### `to_dict(self)`

**Purpose:**  
Converts session to a dictionary for storage or serialization.

**Parameters:**  
None

**Returns:**  
- `dict`: Session data as a dictionary

**Example:**
```python
session_data = session.to_dict()
```

**Related Functions:**
- `save_to_file()`: Saves the session data to a file

---

## StateManager

### `__init__(self)`

**Purpose:**  
Initializes the state manager for conversation sessions.

**Parameters:**  
None

**Returns:**  
None

**Example:**
```python
state_manager = StateManager()
```

**Related Functions:**
- `create_session()`: Creates a new session
- `transition_state()`: Handles state transitions

### `create_session(self, session_id, session)`

**Purpose:**  
Initializes a new session with IDLE state.

**Parameters:**  
- `session_id` (str): Unique identifier for the session
- `session` (Session): Session object

**Returns:**  
None

**Example:**
```python
state_manager.create_session(session_id, session)
```

**Related Functions:**
- `end_session()`: Cleans up session resources
- `transition_state()`: Transitions a session to a new state

### `end_session(self, session_id)`

**Purpose:**  
Cleans up session resources.

**Parameters:**  
- `session_id` (str): Session identifier to end

**Returns:**  
None (asynchronous function)

**Example:**
```python
await state_manager.end_session(session_id)
```

**Related Functions:**
- `create_session()`: Creates a new session

### `transition_state(self, session_id, new_state, metadata=None, timeout=2.0)`

**Purpose:**  
Transitions a session to a new state with validation.

**Parameters:**  
- `session_id` (str): The session to update
- `new_state` (str): The new state to transition to
- `metadata` (dict, optional): Additional metadata for the state update
- `timeout` (float): Maximum time to wait for lock acquisition

**Returns:**  
- `bool`: True if successful, False otherwise

**Example:**
```python
success = await state_manager.transition_state(
    session_id,
    "PROCESSING",
    {"message": "Generating response"}
)
```

**Related Functions:**
- `_is_valid_transition()`: Validates state transitions
- `_broadcast_state_change()`: Broadcasts state changes to clients

### `force_transition(self, session_id, new_state, metadata=None)`

**Purpose:**  
Forces a state transition without validation for emergency recovery.

**Parameters:**  
- `session_id` (str): The session to update
- `new_state` (str): The new state to transition to
- `metadata` (dict, optional): Additional metadata for the state update

**Returns:**  
- `bool`: True if successful, False otherwise

**Example:**
```python
success = await state_manager.force_transition(
    session_id,
    "WAITING",
    {"message": "Recovery after error"}
)
```

**Related Functions:**
- `transition_state()`: Normal state transition with validation

### `get_session_state(self, session_id)`

**Purpose:**  
Gets the current state name for a session.

**Parameters:**  
- `session_id` (str): The session to query

**Returns:**  
- `str`: Current state name, or None if session not found

**Example:**
```python
current_state = state_manager.get_session_state(session_id)
if current_state == "PROCESSING":
    # Handle processing state
```

**Related Functions:**
- `get_session()`: Gets the session object
- `transition_state()`: Changes the session state

---

## STTService

### `__init__(self, model_name="base")`

**Purpose:**  
Initializes the STT wrapper with specific model size.

**Parameters:**  
- `model_name` (str): The Whisper model size to use ("tiny", "base", "small", "medium", "large")

**Returns:**  
None

**Example:**
```python
stt_service = STTService("medium")
```

**Related Functions:**
- `transcribe()`: Transcribes audio to text

### `transcribe(self, audio_data)`

**Purpose:**  
Transcribes audio data to text using available STT implementation.

**Parameters:**  
- `audio_data` (bytes/ndarray/str): Audio data to transcribe

**Returns:**  
- `str`: Transcribed text

**Example:**
```python
transcript = stt_service.transcribe(audio_data)
```

**Related Functions:**
- `get_model_info()`: Gets information about the loaded model

### `get_model_info(self)`

**Purpose:**  
Gets information about the loaded model.

**Parameters:**  
None

**Returns:**  
- `dict`: Model information including name, language, dimensions

**Example:**
```python
model_info = stt_service.get_model_info()
```

**Related Functions:**
- `transcribe()`: Transcribes audio to text

---

## TTS Services

### AllTalkTTSDirectService

#### `__init__(self, url=None, voice=None, config=None)`

**Purpose:**  
Initializes the AllTalk TTS service with configuration.

**Parameters:**  
- `url` (str): The URL of the AllTalk API server
- `voice` (str): The voice to use
- `config` (dict): Additional configuration options

**Returns:**  
None

**Example:**
```python
tts_service = AllTalkTTSDirectService(
    "http://127.0.0.1:7851",
    "female_06.wav",
    config
)
```

**Related Functions:**
- `synthesize()`: Converts text to speech
- `_check_server()`: Checks if AllTalk server is available

#### `synthesize(self, text, session_id=None)`

**Purpose:**  
Converts text to speech using AllTalk with gTTS fallback.

**Parameters:**  
- `text` (str): The text to convert to speech
- `session_id` (str, optional): Session identifier

**Returns:**  
- `bytes`: WAV audio data

**Example:**
```python
audio_data = tts_service.synthesize(
    "Hello, how can I help you with your interview preparation?",
    session_id
)
```

**Related Functions:**
- `_try_tts_generate_api()`: Attempts to use the tts-generate API
- `_synthesize_gtts()`: Fallback synthesis using gTTS

#### `_try_tts_generate_api(self, text)`

**Purpose:**  
Attempts to generate speech using the tts-generate API endpoint.

**Parameters:**  
- `text` (str): The text to convert to speech

**Returns:**  
- `bytes` or `None`: Audio data if successful, None otherwise

**Example:**
```python
audio_data = tts_service._try_tts_generate_api(text)
```

**Related Functions:**
- `_try_synthesize_api()`: Attempts using the synthesize API
- `_try_tts_api()`: Attempts using the tts API

#### `_synthesize_gtts(self, text)`

**Purpose:**  
Fallback synthesis using Google Text-to-Speech (gTTS).

**Parameters:**  
- `text` (str): The text to convert to speech

**Returns:**  
- `bytes`: WAV audio data

**Example:**
```python
audio_data = tts_service._synthesize_gtts(text)
```

**Related Functions:**
- `_generate_silence()`: Generates silent audio as a last resort

#### `is_available(self)`

**Purpose:**  
Checks if the AllTalk service is available.

**Parameters:**  
None

**Returns:**  
- `bool`: True if available, False otherwise

**Example:**
```python
if tts_service.is_available():
    # Use AllTalk for TTS
else:
    # Use fallback
```

**Related Functions:**
- `_check_server()`: Verifies AllTalk server availability

---

## WebSocketServer

### `__init__(self, host, port, state_manager, stt_service, tts_service, llm_client, error_handler=None, heartbeat_service=None)`

**Purpose:**  
Initializes the WebSocket server with all required components.

**Parameters:**  
- `host` (str): The network interface to bind to
- `port` (int): The port to listen on
- `state_manager`: State management component
- `stt_service`: Speech-to-text service
- `tts_service`: Text-to-speech service
- `llm_client`: Language model client
- `error_handler`: Error handling component
- `heartbeat_service`: Heartbeat mechanism for connection health

**Returns:**  
None

**Example:**
```python
websocket_server = WebSocketServer(
    "0.0.0.0",
    8765,
    state_manager,
    stt_service,
    tts_service,
    llm_client,
    error_handler,
    heartbeat_service
)
```

**Related Functions:**
- `start()`: Starts the WebSocket server
- `handle_connection()`: Processes new client connections

### `start(self)`

**Purpose:**  
Starts the WebSocket server.

**Parameters:**  
None

**Returns:**  
None (asynchronous function)

**Example:**
```python
await websocket_server.start()
```

**Related Functions:**
- `shutdown()`: Gracefully shuts down the server

### `shutdown(self)`

**Purpose:**  
Gracefully shuts down the WebSocket server.

**Parameters:**  
None

**Returns:**  
None (asynchronous function)

**Example:**
```python
await websocket_server.shutdown()
```

**Related Functions:**
- `start()`: Starts the WebSocket server

### `handle_connection(self, websocket, path)`

**Purpose:**  
Handles a new WebSocket connection.

**Parameters:**  
- `websocket`: WebSocket connection object
- `path`: Connection path

**Returns:**  
None (asynchronous function)

**Example:**
```python
# Called internally by websockets library
```

**Related Functions:**
- `process_message()`: Processes incoming messages
- `_cleanup_session()`: Cleans up when connection closes

### `process_message(self, session_id, message)`

**Purpose:**  
Processes an incoming WebSocket message.

**Parameters:**  
- `session_id` (str): Session identifier
- `message` (str): Message data

**Returns:**  
None (asynchronous function)

**Example:**
```python
# Called by handle_connection
task = asyncio.create_task(
    self.process_message(session_id, message)
)
```

**Related Functions:**
- `process_audio()`: Handles audio data messages
- `process_control()`: Handles control messages

### `process_audio(self, session_id, message)`

**Purpose:**  
Processes incoming audio data.

**Parameters:**  
- `session_id` (str): Session identifier
- `message` (dict): Message data including audio

**Returns:**  
None (asynchronous function)

**Example:**
```python
await websocket_server.process_audio(session_id, message)
```

**Related Functions:**
- `process_audio_pipeline()`: Full audio processing workflow

### `process_audio_pipeline(self, session_id, audio_data)`

**Purpose:**  
Orchestrates the full audio processing workflow from transcription to response.

**Parameters:**  
- `session_id` (str): Session identifier
- `audio_data` (bytes): Audio data to process

**Returns:**  
None (asynchronous function)

**Example:**
```python
task = asyncio.create_task(
    websocket_server.process_audio_pipeline(session_id, audio_data)
)
```

**Related Functions:**
- `send_audio_response()`: Sends audio response to client

### `send_audio_response(self, session_id, audio_data, text_response=None)`

**Purpose:**  
Sends audio response to client using direct audio data.

**Parameters:**  
- `session_id` (str): Session identifier
- `audio_data` (bytes): Audio data to send
- `text_response` (str, optional): Text version for fallback

**Returns:**  
None (asynchronous function)

**Example:**
```python
await websocket_server.send_audio_response(
    session_id,
    audio_data,
    response_text
)
```

**Related Functions:**
- `_validate_wav_format()`: Validates WAV format
- `send_error()`: Sends error message to client

### `handle_client_capabilities(self, websocket, session_id, message)`

**Purpose:**  
Processes client capability information.

**Parameters:**  
- `websocket`: WebSocket connection object
- `session_id` (str): Session identifier
- `message` (dict): Message with capabilities

**Returns:**  
None (asynchronous function)

**Example:**
```python
await websocket_server.handle_client_capabilities(
    websocket,
    session_id,
    message
)
```

**Related Functions:**
- `handle_playback_complete()`: Processes playback completion

### `_track_task(self, task, session_id=None)`

**Purpose:**  
Tracks a task for proper cleanup.

**Parameters:**  
- `task` (asyncio.Task): Task to track
- `session_id` (str, optional): Associated session

**Returns:**  
None

**Example:**
```python
self._track_task(task, session_id)
```

**Related Functions:**
- `_remove_task()`: Removes completed task from tracking

### `_send_heartbeat_during_llm(self, session_id, websocket)`

**Purpose:**  
Sends periodic heartbeat messages during LLM processing.

**Parameters:**  
- `session_id` (str): Session identifier
- `websocket`: WebSocket connection object

**Returns:**  
None (asynchronous function)

**Example:**
```python
heartbeat_task = asyncio.create_task(
    self._send_heartbeat_during_llm(session_id, websocket)
)
```

**Related Functions:**
- `_safety_timeout()`: Enforces timeout for safety

### `_cleanup_session(self, session_id)`

**Purpose:**  
Cleans up a session's resources.

**Parameters:**  
- `session_id` (str): Session to clean up

**Returns:**  
None (asynchronous function)

**Example:**
```python
await self._cleanup_session(session_id)
```

**Related Functions:**
- `handle_connection()`: Main connection handler
