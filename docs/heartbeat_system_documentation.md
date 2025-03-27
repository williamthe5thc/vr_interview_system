# VR Interview System: Heartbeat System Documentation

## Title and Overview

The Heartbeat System in the VR Interview System prevents WebSocket timeouts during long-running operations like LLM generation and speech synthesis. It sends periodic messages to clients to keep the connection alive and provide progress updates. This is crucial for maintaining the illusion of continuous conversation and avoiding disconnections during processing-intensive operations.

## Architecture

The Heartbeat System is implemented through the `HeartbeatService` class, which manages periodic message sending for each active session. It works in coordination with the WebSocket server and can be customized based on the current processing stage.

```
┌───────────────────┐      Sends      ┌───────────────┐
│ WebSocket Server  │◄───Heartbeats───┤HeartbeatService│
└─────────┬─────────┘                 └───────────────┘
          │                                   ▲
          │                                   │
┌─────────▼─────────┐     Request     ┌───────────────┐
│  Client Connection │───Heartbeats───►│Processing Stage│
└───────────────────┘                 └───────────────┘
```

## Key Classes/Functions

### HeartbeatService

The central class responsible for managing heartbeat messages:

```python
class HeartbeatService:
    """
    Service for sending periodic heartbeat messages to clients.
    
    This helps prevent WebSocket timeouts during long operations like
    LLM processing or speech synthesis.
    """
```

#### Core Methods

- **`__init__(heartbeat_interval)`**: Initializes the service with specified interval
- **`start_heartbeat(session_id, send_func, metadata)`**: Starts sending heartbeats for a session
- **`stop_heartbeat(session_id)`**: Stops heartbeats for a specific session
- **`stop_all()`**: Stops all active heartbeats
- **`_heartbeat_loop(session_id, send_func, metadata)`**: Internal loop that sends messages

## Usage Patterns

### Starting a Heartbeat

```python
# Create a heartbeat when beginning LLM processing
if self.heartbeat_service:
    heartbeat_task = asyncio.create_task(
        self.heartbeat_service.start_heartbeat(
            session_id,
            lambda msg: websocket.send(json.dumps(msg)),
            {"processing_stage": "generating_response"}
        )
    )
```

### Stopping a Heartbeat

```python
# Stop the heartbeat when processing completes
if heartbeat_task and not heartbeat_task.done():
    heartbeat_task.cancel()
    try:
        await heartbeat_task
    except asyncio.CancelledError:
        pass
```

### Heartbeat During Server Shutdown

```python
async def shutdown(self):
    """Gracefully shutdown the WebSocket server"""
    if self.server:
        self.logger.info("Shutting down WebSocket server...")
        self.server.close()
        await self.server.wait_closed()
        
        # Stop heartbeats if available
        if self.heartbeat_service:
            await self.heartbeat_service.stop_all()
```

## Implementation Details

### Dynamic Interval Adjustment

The heartbeat system adjusts its interval based on the current processing stage:

```python
# Determine interval based on processing stage
interval = self.heartbeat_interval
if metadata and "processing_stage" in metadata:
    stage = metadata["processing_stage"]
    if stage == "generating_response":
        # More frequent updates during LLM processing - critical for client responsiveness
        interval = 1.5  # Send more frequent updates during LLM processing
    elif stage == "transcribing":
        interval = 3.0  # Less frequent during STT
    elif stage == "generating_speech":
        interval = 2.0  # Medium frequency during TTS
```

### Heartbeat Message Format

Heartbeat messages include progress information and are formatted as JSON:

```json
{
  "type": "heartbeat",
  "session_id": "unique-session-id",
  "counter": 3,
  "timestamp": 1635789012.345,
  "metadata": {
    "processing_stage": "generating_response",
    "progress": 45
  }
}
```

### Task Management

The heartbeat service tracks active tasks for proper cleanup:

```python
async def start_heartbeat(
    self, 
    session_id: str, 
    send_func: Callable[[Dict[str, Any]], Awaitable[None]],
    metadata: Optional[Dict[str, Any]] = None
):
    # Stop any existing heartbeat for this session
    await self.stop_heartbeat(session_id)
    
    # Create a new heartbeat task
    task = asyncio.create_task(
        self._heartbeat_loop(session_id, send_func, metadata or {})
    )
    self.active_tasks[session_id] = task
```

## Configuration

The heartbeat system is configured through the main system configuration:

```json
"heartbeat": {
  "enabled": true,
  "interval": 5.0
}
```

Key configuration options:
- **enabled**: Whether the heartbeat system is active
- **interval**: Default time between heartbeats in seconds

## Common Issues

### Connection Timeouts

1. **Browser Timeouts**:
   - **Symptoms**: Client disconnects during long LLM processing
   - **Causes**: Browser WebSocket connection timeouts (typically 30-60 seconds)
   - **Solution**: Heartbeat messages keep the connection alive

2. **Proxy Timeouts**:
   - **Symptoms**: Intermittent disconnections in specific network environments
   - **Causes**: Intermediate proxies closing idle connections
   - **Solution**: Increase heartbeat frequency in high-latency environments

### Resource Management

1. **Task Leaks**:
   - **Symptoms**: Increasing memory usage over time
   - **Causes**: Uncancelled heartbeat tasks
   - **Solution**: Proper task tracking and session cleanup

2. **High CPU Usage**:
   - **Symptoms**: Increased server CPU with many clients
   - **Causes**: Too frequent heartbeats with many connections
   - **Solution**: Dynamic interval adjustment based on system load

## Code Examples

### Initializing the Heartbeat Service

```python
# Initialize heartbeat service if enabled
heartbeat_config = self.config.get("heartbeat", {})
if heartbeat_config.get("enabled", True):
    self.heartbeat_service = HeartbeatService(
        heartbeat_interval=heartbeat_config.get("interval", 5.0)
    )
    self.logger.info(
        f"Heartbeat service enabled with interval: "
        f"{heartbeat_config.get('interval', 5.0)}s"
    )
else:
    self.heartbeat_service = None
    self.logger.info("Heartbeat service disabled")
```

### Internal Heartbeat Loop

```python
async def _heartbeat_loop(
    self, 
    session_id: str, 
    send_func: Callable[[Dict[str, Any]], Awaitable[None]],
    metadata: Dict[str, Any]
):
    """
    Internal loop that sends periodic heartbeat messages.
    """
    try:
        counter = 0
        while True:
            counter += 1
            
            # Prepare heartbeat message
            message = {
                "type": "heartbeat",
                "session_id": session_id,
                "counter": counter,
                "timestamp": asyncio.get_event_loop().time(),
            }
            
            # Add metadata if provided
            if metadata:
                message["metadata"] = metadata
                
            # Send the heartbeat
            try:
                await send_func(message)
                logger.debug(f"Sent heartbeat #{counter} to session {session_id}")
            except Exception as e:
                logger.error(f"Error sending heartbeat to {session_id}: {e}")
                break
                
            # Determine interval based on processing stage
            interval = self.heartbeat_interval
            if metadata and "processing_stage" in metadata:
                stage = metadata["processing_stage"]
                if stage == "generating_response":
                    interval = 1.5  # More frequent for LLM processing
                elif stage == "transcribing":
                    interval = 3.0  # Less frequent for STT
                elif stage == "generating_speech":
                    interval = 2.0  # Medium frequency for TTS
            
            # Wait for next heartbeat
            await asyncio.sleep(interval)
    except asyncio.CancelledError:
        logger.debug(f"Heartbeat task cancelled for session {session_id}")
```

### Using Alternative Heartbeat in WebSocket Server

When the HeartbeatService is not available, the WebSocket server can use its own internal implementation:

```python
# Create a separate task for heartbeat if available
if self.heartbeat_service and websocket:
    heartbeat_task = asyncio.create_task(
        self.heartbeat_service.start_heartbeat(
            session_id,
            lambda msg: websocket.send(json.dumps(msg)),
            {"processing_stage": "generating_response"}
        )
    )
else:
    # Use our internal heartbeat implementation
    heartbeat_task = asyncio.create_task(
        self._send_heartbeat_during_llm(session_id, websocket)
    )
```
