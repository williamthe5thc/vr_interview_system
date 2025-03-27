# VR Interview System: Enhanced Stream Processor Documentation

## Title and Overview

The Enhanced Stream Processor provides optimized handling for audio processing in the VR Interview System. It implements a parallel processing pipeline that improves response times and user experience by overlapping operations, prewarming components, and handling delayed responses. This component specifically addresses the challenge of managing long-running operations in a real-time, interactive system.

## Architecture

The Enhanced Stream Processor follows a multi-stage parallel processing architecture that decouples the sequential steps of audio processing, allowing them to run concurrently where possible:

```
┌───────────────────┐
│ Audio Data Input  │
└─────────┬─────────┘
          │
┌─────────▼─────────┐
│  Transcription    │◄────────┐
└─────────┬─────────┘         │
          │                   │
          │             ┌─────┴────────┐
┌─────────▼─────────┐   │   TTS        │
│  LLM Processing   │   │  Prewarming  │
└─────────┬─────────┘   └──────────────┘
          │
┌─────────▼─────────┐
│ TTS Generation    │
└─────────┬─────────┘
          │
┌─────────▼─────────┐
│  Audio Response   │
└───────────────────┘
```

## Key Classes/Functions

### EnhancedStreamProcessor

The main class implementing the optimized processing pipeline:

```python
class EnhancedStreamProcessor:
    """
    Enhanced stream processor with optimized processing pipeline.
    
    Features:
    - Multi-stage parallel processing
    - Optimized direct audio generation
    - Intelligent caching for frequently used responses
    - Advanced error handling and recovery
    """
```

#### Core Methods

- **`__init__(state_manager, stt_service, tts_service, llm_client, error_handler)`**: Initializes with system components
- **`process_streaming_audio_pipeline(session_id, audio_data, websocket)`**: Processes audio with parallel optimization
- **`_generate_standard_tts(session_id, text, websocket)`**: Generates TTS response using direct API
- **`_prewarm_tts()`**: Prewarms TTS engine to reduce cold-start latency
- **`_handle_delayed_llm_response(session_id, llm_future, websocket)`**: Handles LLM responses that complete after timeout
- **`_send_progressive_updates(session_id, websocket)`**: Sends periodic updates during LLM processing

## Usage Patterns

### Streaming Audio Pipeline

The Enhanced Stream Processor is used by the WebSocket server to process audio with optimized performance:

```python
# In WebSocketServer.process_audio()
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
```

### Parallel Processing

Multiple operations are started in parallel to reduce end-to-end latency:

```python
# 1. Transcribe audio and update state

# 2. Start TTS prewarming in parallel with LLM generation
tts_prewarm_task = asyncio.create_task(self._prewarm_tts())
tasks.append(tts_prewarm_task)

# 3. Start heartbeat task to send updates during LLM processing
heartbeat_task = asyncio.create_task(
    self._send_progressive_updates(session_id, websocket)
)
tasks.append(heartbeat_task)

# 4. Generate LLM response with progress updates
```

### Handling Delayed Responses

The processor can handle LLM responses that complete after timeout:

```python
# Instead of canceling it, let it run in background
# Create a background task to handle it when it completes
asyncio.create_task(
    self._handle_delayed_llm_response(session_id, llm_future, websocket)
)
```

## Implementation Details

### TTS Prewarming

To reduce cold-start latency, the TTS engine is prewarmed:

```python
async def _prewarm_tts(self) -> bool:
    """
    Prewarm TTS engine to reduce cold-start latency.
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Send a simple request to make sure the TTS engine is ready
        await asyncio.to_thread(
            self.tts_service.synthesize,
            "Prewarming the text to speech system."
        )
        return True
    except Exception as e:
        self.logger.warning(f"TTS prewarm failed: {e}")
        return False
```

### Progressive Updates

To keep the user engaged during LLM processing, progressive updates are sent:

```python
async def _send_progressive_updates(self, session_id, websocket):
    """
    Send progressive updates to client during long LLM operations
    """
    update_messages = [
        "I'm thinking about your question...",
        "Still processing your question...",
        "This is a complex question, giving it some thought...",
        "Almost ready with a response...",
        "Finalizing my thoughts on this..."
    ]
    
    try:
        # Send updates every 5 seconds
        for i in range(len(update_messages)):
            await asyncio.sleep(5.0)
            
            # Send a system message
            await self._send_progress_update(websocket, update_messages[i % len(update_messages)])
    except asyncio.CancelledError:
        # Task was cancelled (normal when LLM completes)
        pass
```

### Delayed LLM Response Handling

The system can recover and utilize LLM responses that complete after the timeout:

```python
async def _handle_delayed_llm_response(self, session_id, llm_future, websocket):
    """
    Handle LLM response that completes after the timeout
    """
    try:
        # Wait for the LLM response (which is still running)
        response = await llm_future
        
        # Check if the session is still active
        session = self.state_manager.get_session(session_id)
        if not session:
            self.logger.warning(f"Session {session_id} no longer exists for delayed response")
            return
            
        # Add to session context if method exists
        if hasattr(session, 'add_assistant_message'):
            session.add_assistant_message(response)
        
        # Update the transcript with the delayed response
        await websocket.send(json.dumps({
            "type": "transcript_update",
            "session_id": session_id,
            "timestamp": time.time(),
            "transcript": response,
            "source": "llm",
            "delayed": True
        }))
        
        # Generate TTS for the delayed response
        try:
            audio_response = await asyncio.to_thread(
                self.tts_service.synthesize, response, session_id
            )
            
            # Send audio response if we're in a state where it makes sense
            current_state = session.state if hasattr(session, 'state') else None
            if current_state in ["WAITING", "IDLE"]:
                # Update state to RESPONDING
                await self.state_manager.transition_state(session_id, "RESPONDING", {
                    "message": "Playing delayed response"
                })
                
                # Send direct audio
                await websocket.send(json.dumps({
                    "type": "audio_response",
                    "session_id": session_id,
                    "timestamp": time.time(),
                    "audio_data": base64.b64encode(audio_response).decode('utf-8'),
                    "text": response,
                    "delayed": True
                }))
                
                # Return to WAITING when done
                await self.state_manager.transition_state(session_id, "WAITING", {
                    "message": "Waiting for user input"
                })
        except Exception as e:
            self.logger.error(f"Error processing delayed TTS: {e}")
    except Exception as e:
        self.logger.error(f"Error handling delayed LLM response: {e}")
```

### Task Management

The system carefully tracks tasks to ensure proper cleanup:

```python
# Track active tasks for proper cleanup
tasks = []

try:
    # Start multiple stages in parallel
    # ... operations ...
    
    # Track tasks
    transcript_future = asyncio.create_task(...)
    tasks.append(transcript_future)
    
    # Remove completed tasks
    if transcript_future in tasks:
        tasks.remove(transcript_future)
        
except Exception as e:
    # Cancel all running tasks
    for task in tasks:
        if not task.done():
            task.cancel()
```

## Configuration

The Enhanced Stream Processor is configured through the main system configuration, particularly the TTS and LLM settings:

```json
"ollama": {
  "url": "http://localhost:11434",
  "model": "mistral:latest",
  "timeout": 45
},
"alltalk": {
  "url": "http://127.0.0.1:7851",
  "timeout": 15
}
```

## Common Issues

### Processing Pipeline Issues

1. **Timeout Handling**:
   - **Symptoms**: Long LLM processing times exceeding timeouts
   - **Causes**: Large context, complex prompts, slow LLM server
   - **Solution**: Delayed response handling and progressive updates

2. **Task Cancellation**:
   - **Symptoms**: Incomplete processing or resource leaks
   - **Causes**: Improper task tracking and cancellation
   - **Solution**: Comprehensive task tracking and cleanup

3. **TTS Latency**:
   - **Symptoms**: Delayed audio responses
   - **Causes**: Cold-start TTS latency
   - **Solution**: TTS prewarming and text fallback

### Performance Optimizations

1. **Parallel Processing**:
   - Multiple stages run concurrently to reduce end-to-end latency
   - TTS prewarming happens during LLM processing
   - Progressive updates keep the user engaged

2. **User Experience**:
   - Progress messages show activity during long processing
   - Text fallbacks ensure communication even when audio fails
   - Delayed responses are still delivered when they complete

## Code Examples

### Main Processing Pipeline

```python
async def process_streaming_audio_pipeline(
    self,
    session_id: str,
    audio_data: bytes,
    websocket
):
    """
    Process audio with optimized streaming pipeline.
    """
    # Track active tasks for proper cleanup
    tasks = []
    
    try:
        # Start multiple stages in parallel
        # 1. Transcribe audio and notify state change
        await self.state_manager.transition_state(session_id, "LISTENING", {
            "message": "Receiving audio"
        })
        
        # Transcribe audio (CPU intensive) in a separate thread
        try:
            transcript_future = asyncio.create_task(
                asyncio.to_thread(self.stt_service.transcribe, audio_data)
            )
            tasks.append(transcript_future)
            
            # Add a timeout to prevent hanging
            transcript = await asyncio.wait_for(transcript_future, timeout=10.0)
            
            # Remove completed task
            if transcript_future in tasks:
                tasks.remove(transcript_future)
        except asyncio.TimeoutError:
            # Handle STT timeout
            # ...
            
        # 2. Update state and prepare for LLM processing
        await self.state_manager.transition_state(session_id, "PROCESSING", {
            "message": "Generating response",
            "transcript": transcript
        })
        
        # 3. Start TTS prewarming in parallel with LLM generation
        tts_prewarm_task = asyncio.create_task(self._prewarm_tts())
        tasks.append(tts_prewarm_task)
        
        # 4. Generate LLM response
        # ...
        
        # 5. Generate speech using direct API
        await self._generate_standard_tts(session_id, response, websocket)
            
    except Exception as e:
        # Error handling
        # ...
```

### TTS Generation

```python
async def _generate_standard_tts(self, session_id: str, text: str, websocket) -> None:
    """
    Generate TTS response using standard (non-streaming) approach.
    """
    try:
        # Generate speech with timeout
        tts_future = asyncio.create_task(
            asyncio.to_thread(self.tts_service.synthesize, text)
        )
        
        # Add timeout to prevent hanging
        audio_response = await asyncio.wait_for(tts_future, timeout=15.0)
        
        # Transition to RESPONDING state
        await self.state_manager.transition_state(session_id, "RESPONDING", {
            "message": "Playing response"
        })
        
        # Send audio response to client
        message = {
            "type": "audio_response",
            "session_id": session_id,
            "timestamp": time.time(),
            "format": "wav",
            "data": base64.b64encode(audio_response).decode('utf-8'),
            "text": text
        }
        
        await websocket.send(json.dumps(message))
        
        # Wait a moment to ensure audio is received
        await asyncio.sleep(0.5)
        
        # Transition to WAITING state
        await self.state_manager.transition_state(session_id, "WAITING", {
            "message": "Waiting for user input"
        })
        
    except asyncio.TimeoutError:
        # Send text-only response as fallback
        # ...
```