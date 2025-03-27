# VR Interview System: WebSocket Documentation

## Title and Overview

The WebSocket component of the VR Interview System provides the real-time communication channel between the VR client application and the server. It handles bi-directional, full-duplex communication, enabling the exchange of audio data, text, and control messages. The WebSocket server is optimized for handling both long-polling operations (like LLM generation) and high-frequency updates without blocking or disconnecting the client.

## Architecture

The WebSocket implementation follows an enhanced asynchronous architecture designed to prevent blocking during long-running operations. It consists of several key components:

1. **WebSocketServer Class**: The main server class managing client connections, message routing, and lifecycle
2. **EnhancedStreamProcessor**: Specialized handler for streaming audio processing pipeline
3. **Protocol Module**: Handles message encoding, decoding, and validation
4. **Session Management**: Tracks active connections and associated session data
5. **Task Management System**: Ensures proper tracking and cleanup of asyncio tasks

### Where This Component Fits

The WebSocket server acts as the central communication hub of the VR Interview System:

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
│                            WebSocket Server                           │
└─────┬────────────────────┬────────────────────┬──────────────────┬────┘
      │                    │                    │                  │
      ▼                    ▼                    ▼                  ▼
┌───────────┐     ┌────────────────┐    ┌─────────────┐    ┌────────────┐
│State      │     │Stream Processor│    │STT/TTS      │    │LLM         │
│Manager    │     │                │    │Services     │    │Client      │
└───────────┘     └────────────────┘    └─────────────┘    └────────────┘
```

## Key Classes/Functions

### WebSocketServer

```python
class WebSocketServer:
    """
    Enhanced WebSocket server with improved error handling and task management.
    
    This server ensures that long-running operations like LLM processing don't
    block WebSocket communication and state updates.
    """
```

#### Core Methods

- **`__init__`**: Initializes the WebSocket server with references to all system components
- **`start()`**: Starts the WebSocket server and begins accepting connections
- **`shutdown()`**: Gracefully shuts down the server and cleans up resources
- **`handle_connection()`**: Handles new WebSocket connections and session creation
- **`process_message()`**: Processes incoming WebSocket messages
- **`process_audio()`**: Handles audio data messages from clients
- **`process_audio_pipeline()`**: Orchestrates the full audio processing workflow
- **`process_control()`**: Processes control messages (reset, stop, etc.)
- **`send_audio_response()`**: Sends audio responses back to clients
- **`handle_playback_complete()`**: Processes playback completion notifications
- **`handle_client_capabilities()`**: Processes client capability information

### Message Types

The WebSocket server handles various message types:

1. **`audio_data`**: Contains raw audio data from the client
2. **`ping`**: Simple ping message for connection health checks
3. **`pong`**: Response to ping messages
4. **`control`**: Client control messages (reset, stop)
5. **`state_update`**: Server state change notifications
6. **`playback_complete`**: Client notification of audio playback completion
7. **`client_capabilities`**: Client feature and format support information
8. **`system_message`**: System notifications and status updates
9. **`error`**: Error messages and codes
10. **`text_response`**: Text responses (when audio unavailable)
11. **`audio_response`**: Audio response data
12. **`audio_file_url`**: URLs for direct audio file access

## Usage Patterns

### Connection Lifecycle

1. **Connection Establishment**:
   ```python
   # Server side
   async def handle_connection(self, websocket, path):
       session_id = str(uuid.uuid4())
       session = Session(session_id, websocket)
       self.active_connections[session_id] = websocket
       
       # Send initial session ID
       await websocket.send(json.dumps({
           "type": "session_init",
           "session_id": session_id,
           "timestamp": time.time()
       }))
   ```

2. **Client Capability Exchange**:
   ```python
   # Client sends capabilities
   {
     "type": "client_capabilities",
     "capabilities": {
       "audio_formats": ["wav", "mp3"],
       "browser": {"name": "unity"}
     }
   }
   
   # Server acknowledges and provides supported features
   {
     "type": "state_update",
     "current": "IDLE",
     "metadata": {
       "supported_features": {
         "direct_audio": true,
         "streaming": false
       }
     }
   }
   ```

3. **Audio Processing**:
   ```python
   # Client sends audio
   {
     "type": "audio_data",
     "data": "base64-encoded-audio-data",
     "format": "wav"
   }
   
   # Server processes and responds with audio
   {
     "type": "audio_response",
     "data": "base64-encoded-audio-data",
     "format": "wav",
     "text": "Fallback text version"
   }
   ```

4. **Playback Completion**:
   ```python
   # Client notifies when audio playback completes
   {
     "type": "playback_complete",
     "session_id": "unique-session-id"
   }
   ```

5. **Connection Termination**:
   ```python
   # Server cleans up on disconnection
   async def _cleanup_session(self, session_id):
       # Cancel tasks, stop heartbeats, remove from active connections
       # End session in state manager
   ```

### Error Handling

```python
try:
    # Process message
    await self.process_message(session_id, message)
except Exception as e:
    # Use error handler if available
    if self.error_handler:
        await self.error_handler.handle_error(
            ErrorHandler.SYSTEM_ERROR,
            session_id,
            e,
            {"websocket": self.active_connections.get(session_id)}
        )
```

### Task Management

```python
def _track_task(self, task: asyncio.Task, session_id: Optional[str] = None):
    """Track a task for proper cleanup"""
    self.tasks.add(task)
    
    # Add to session-specific tasks if session_id provided
    if session_id and session_id in self.session_tasks:
        self.session_tasks[session_id].add(task)
        
    # Set up callback to remove task when done
    task.add_done_callback(lambda t: self._remove_task(t, session_id))
```

## Implementation Details

### Audio Processing Pipeline

The WebSocket server supports two processing pipelines:

1. **Standard Pipeline**: Sequential processing of audio → text → LLM → audio
   ```python
   async def process_audio_pipeline(self, session_id, audio_data):
       # 1. Transition to PROCESSING state
       # 2. Transcribe audio with STT service
       # 3. Generate response with LLM
       # 4. Convert response to audio with TTS
       # 5. Send audio response to client
   ```

2. **Streaming Pipeline**: Optimized for faster responses with parallel processing
   ```python
   async def process_streaming_audio_pipeline(self, session_id, audio_data, websocket):
       # Process transcription and start LLM generation before TTS completes
   ```

### Preventing WebSocket Timeouts

The server uses a heartbeat mechanism to prevent client timeouts during long-running operations:

```python
async def _send_heartbeat_during_llm(self, session_id, websocket):
    """Send periodic heartbeat messages during LLM processing"""
    count = 0
    try:
        while True:
            # Send a heartbeat every 2 seconds
            await asyncio.sleep(2)
            count += 1
            
            try:
                message = {
                    "type": "heartbeat",
                    "session_id": session_id,
                    "timestamp": time.time(),
                    "progress": min(99, count * 5),  # Simulate progress
                    "message": f"Processing your response... ({count*2}s)"
                }
                await websocket.send(json.dumps(message))
            except Exception as e:
                self.logger.error(f"Error sending heartbeat: {e}")
                break
                
            # Stop after 45 seconds to prevent infinite loop
            if count >= 22:  # 22 * 2s = 44 seconds
                break
    except asyncio.CancelledError:
        # Task was cancelled normally
        pass
```

### Safety Timeouts

The system includes safety timeouts to prevent hanging in case of failures:

```python
async def _safety_timeout(self, session_id: str, timeout_seconds: float):
    """Force transition to WAITING state if processing takes too long"""
    try:
        await asyncio.sleep(timeout_seconds)
        
        # Check current state
        current_state = self.state_manager.get_session_state(session_id)
        
        # If still in PROCESSING state after timeout, force transition to WAITING
        if current_state == "PROCESSING":
            self.logger.warning(f"Safety timeout triggered for session {session_id}")
            await self.state_manager.transition_state(session_id, "WAITING", {
                "message": "Ready for next question (timeout recovery)"
            })
    except asyncio.CancelledError:
        # Task was cancelled normally
        pass
```

## Configuration

The WebSocket server's configuration is controlled via the main system config:

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8765,
    "log_level": "INFO"
  }
}
```

Key configuration options:
- **Host**: The network interface to bind to (0.0.0.0 = all interfaces)
- **Port**: The WebSocket port to listen on
- **Log Level**: Logging verbosity (DEBUG, INFO, WARNING, ERROR)

## Common Issues

### Connection Handling Issues

1. **Connection Timeout**: 
   - **Cause**: Long-running operations (like LLM processing) exceed client timeout thresholds.
   - **Solution**: The heartbeat mechanism sends periodic updates to keep the connection alive.

2. **Disconnection During Processing**:
   - **Cause**: Network issues or client-side problems during processing.
   - **Solution**: Session cleanup and resource release in the `_cleanup_session()` method.

3. **Race Conditions**:
   - **Cause**: Asynchronous operations competing for resources.
   - **Solution**: Proper task tracking and lock management.

### Audio Processing Issues

1. **Audio Format Compatibility**:
   - **Cause**: Client sends audio in an unsupported format.
   - **Solution**: The `_validate_wav_format()` method checks format validity.

2. **Empty or Invalid Audio**:
   - **Cause**: Client sends empty or corrupted audio data.
   - **Solution**: Input validation and appropriate error messages.

## Code Examples

### Handling a New Connection

```python
async def handle_connection(self, websocket, path):
    """Handle a new WebSocket connection"""
    session_id = str(uuid.uuid4())
    self.logger.info(f"New connection established: {session_id}")
    
    # Create a new session
    session = Session(session_id, websocket)
    self.active_connections[session_id] = websocket
    self.session_tasks[session_id] = set()
    
    # Register session with state manager
    self.state_manager.create_session(session_id, session)
    
    # Send initial message with session ID to synchronize client and server IDs
    await websocket.send(json.dumps({
        "type": "session_init",
        "session_id": session_id,
        "timestamp": time.time()
    }))
    
    # Send initial IDLE state
    await self.state_manager.transition_state(session_id, "IDLE", {
        "message": "Ready for conversation"
    })
    
    try:
        async for message in websocket:
            # Process the incoming message in a separate task
            task = asyncio.create_task(
                self.process_message(session_id, message)
            )
            # Track the task
            self._track_task(task, session_id)
            
    except ConnectionClosed:
        self.logger.info(f"Connection closed: {session_id}")
    except Exception as e:
        self.logger.error(f"Error in connection handler: {e}")
        if self.error_handler:
            await self.error_handler.handle_error(
                ErrorHandler.WEBSOCKET_ERROR,
                session_id,
                e,
                {"websocket": websocket}
            )
    finally:
        # Clean up session
        await self._cleanup_session(session_id)
```

### Processing Audio Data

```python
async def process_audio(self, session_id: str, message: Dict[str, Any]):
    """
    Process incoming audio data.
    This is where we need to carefully manage async operations to prevent blocking.
    """
    try:
        # Check current state
        current_state = self.state_manager.get_session_state(session_id)
        if current_state not in ["IDLE", "WAITING"]:
            self.logger.warning(
                f"Received audio when in {current_state} state. Ignoring."
            )
            return
            
        # Transition to LISTENING
        await self.state_manager.transition_state(session_id, "LISTENING", {
            "message": "Receiving audio"
        })
        
        # Decode audio data
        audio_data = base64.b64decode(message.get("data", ""))
        if not audio_data:
            await self.send_error(session_id, 400, "Empty audio data")
            return
            
        # Determine whether to use streaming or standard pipeline
        config = getattr(self.llm_client, 'config', {}) or {}
        use_streaming = config.get('use_streaming', True)
        
        if use_streaming:
            # Use optimized streaming pipeline for faster responses
            task = asyncio.create_task(
                self.stream_processor.process_streaming_audio_pipeline(
                    session_id, 
                    audio_data,
                    self.active_connections.get(session_id)
                )
            )
            self._track_task(task, session_id)
        else:
            # Use standard pipeline
            task = asyncio.create_task(
                self.process_audio_pipeline(session_id, audio_data)
            )
            self._track_task(task, session_id)
    
    except Exception as e:
        self.logger.error(f"Error processing audio: {e}")
        
        # Try to use error handler if available
        if self.error_handler:
            await self.error_handler.handle_error(
                ErrorHandler.SYSTEM_ERROR,
                session_id,
                e,
                {"websocket": self.active_connections.get(session_id)}
            )
        else:
            # Fallback error handling
            await self.send_error(session_id, 500, "Error processing audio")
            await self.state_manager.transition_state(session_id, "ERROR", {
                "error": str(e)
            })
```

### Sending Audio Response

```python
async def send_audio_response(
    self, 
    session_id: str, 
    audio_data: bytes,
    text_response: Optional[str] = None
):
    """
    Send audio response to client using direct audio data
    """
    websocket = self.active_connections.get(session_id)
    if not websocket:
        self.logger.error(f"No active connection for {session_id}")
        return
        
    try:
        # Check if we have valid audio data
        has_valid_audio = (audio_data is not None and 
                         len(audio_data) > 1000 and 
                         self._validate_wav_format(audio_data))
        
        if has_valid_audio:
            # We have valid audio data - send it directly
            self.logger.info(f"Using direct audio data for {session_id}")
            
            # Create the audio response message
            message = {
                "type": "audio_response",
                "session_id": session_id,
                "timestamp": time.time(),
                "format": "wav",  # Explicitly specify format
                "data": base64.b64encode(audio_data).decode('utf-8')
            }
            
            # Include text response as a fallback
            if text_response:
                message["text"] = text_response
                
            await websocket.send(encode_message(message))
            self.logger.debug(f"Sent audio response to {session_id}, size: {len(audio_data)} bytes")
            
        else:
            # No valid audio - use text fallback
            self.logger.warning(f"No valid audio available for {session_id}, using text fallback")
            
            if text_response:
                text_message = {
                    "type": "text_response",
                    "session_id": session_id,
                    "timestamp": time.time(),
                    "text": text_response,
                    "message": "Audio unavailable, showing text instead"
                }
                await websocket.send(encode_message(text_message))
            else:
                # No text either - send generic error
                await self.send_error(session_id, 500, "Audio synthesis failed")
        
    except Exception as e:
        self.logger.error(f"Error sending audio response: {e}")
        
        # Try to send a text-only response if audio fails
        if text_response:
            try:
                text_message = {
                    "type": "text_response",
                    "session_id": session_id,
                    "timestamp": time.time(),
                    "text": text_response,
                    "message": "Audio playback failed, showing text instead"
                }
                await websocket.send(encode_message(text_message))
            except Exception as text_error:
                self.logger.error(f"Failed to send text fallback: {text_error}")
```
