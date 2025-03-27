# VR Interview System: State Management Documentation

## Title and Overview

The State Management component of the VR Interview System is responsible for maintaining and controlling the conversation state for each user session. It implements a state machine pattern that ensures orderly progression through the interview process. The state manager tracks the current state of each session, validates state transitions, prevents invalid state changes, and communicates state updates to clients. It includes mechanisms to prevent deadlocks and handle error recovery.

## Architecture

The State Management system consists of two primary classes:

1. **StateManager**: The core class that manages the state machine logic, handles state transitions, and broadcasts state changes to clients.
2. **Session**: A data class representing a client session that stores the conversation history and metadata.

The state management system interacts with the following components:
- WebSocket Server: Receives state change broadcasts
- Error Handler: For error recovery
- LLM Client: Uses state information for contextual responses

### State Flow Diagram
```
┌───────┐    listen     ┌──────────┐     process    ┌───────────┐
│ IDLE  │───────────────►LISTENING │────────────────►PROCESSING │
└───┬───┘               └──────────┘                └─────┬─────┘
    │                                                     │
    │                                                     │
    │                                           respond   │
    │       ┌───────────┐              ┌───────────────◄─┘
    │       │  ERROR    │              │
    │       └─────┬─────┘              │
    │             │         recovery   │
    │             └────────────────────┤
    │                                  │
    │                                  ▼
    │                      ┌────────────────┐
    │         wait         │   RESPONDING   │
    └─────────────◄────────┤                │
                  complete └────────┬───────┘
                              │     │
                              │     │
                              ▼     │
                       ┌────────────┴───┐
                       │    WAITING     │
                       └────────────────┘
```

## Key Classes/Functions

### States Enumeration
```python
class States(Enum):
    """Enumeration of possible states for the conversation"""
    IDLE = auto()
    LISTENING = auto()
    PROCESSING = auto()
    RESPONDING = auto()
    WAITING = auto()
    ERROR = auto()
```

### StateManager Class
```python
class StateManager:
    """
    Manages the state machine for conversation sessions.
    
    This class handles state transitions and ensures they follow the defined flow:
    IDLE → LISTENING → PROCESSING → RESPONDING → WAITING → (repeat)
    
    It also handles broadcasting state changes to connected clients.
    """
```

#### Key Methods
- **`__init__()`**: Initializes state tracking structures
- **`create_session()`**: Creates a new session with initial IDLE state
- **`end_session()`**: Cleans up session resources
- **`transition_state()`**: Transitions a session to a new state with validation
- **`force_transition()`**: Forces a state transition without validation (emergency recovery)
- **`get_session()`**: Retrieves a session object by ID
- **`get_session_state()`**: Gets the current state for a session

### Session Class
```python
class Session:
    """
    Represents a conversation session with a client.
    
    Stores session-specific data including:
    - Connection information
    - Conversation history
    - State information
    - Session metadata
    """
```

#### Key Methods
- **`add_interaction()`**: Records a user-system interaction in history
- **`get_context()`**: Gets formatted conversation context for the LLM
- **`reset()`**: Resets the conversation history
- **`is_expired()`**: Checks if the session has expired due to inactivity
- **`to_dict()`**: Converts session to a dictionary for serialization
- **`save_to_file()`**: Saves the session data to a JSON file

## Usage Patterns

### State Transition Flow

The typical state transition flow follows this pattern:

1. **IDLE**: Initial state, ready for conversation
   ```python
   # Create a new session
   state_manager.create_session(session_id, session)
   # Session is automatically set to IDLE
   ```

2. **LISTENING**: Receiving audio from the user
   ```python
   await state_manager.transition_state(session_id, "LISTENING", {
       "message": "Receiving audio"
   })
   ```

3. **PROCESSING**: Processing input and generating response
   ```python
   await state_manager.transition_state(session_id, "PROCESSING", {
       "message": "Transcribing audio"
   })
   
   # Later in the processing pipeline:
   await state_manager.transition_state(session_id, "PROCESSING", {
       "message": "Generating response",
       "transcript": transcript,
       "stage": interaction_stage
   })
   ```

4. **RESPONDING**: Sending audio response to client
   ```python
   await state_manager.transition_state(session_id, "RESPONDING", {
       "message": "Playing response"
   })
   ```

5. **WAITING**: Waiting for next user input
   ```python
   await state_manager.transition_state(session_id, "WAITING", {
       "message": "Waiting for user input"
   })
   ```

6. **ERROR**: Error state with recovery mechanisms
   ```python
   await state_manager.transition_state(session_id, "ERROR", {
       "error": str(e)
   })
   ```

### Error Recovery Patterns

When an error occurs, the system can recover by forcing a state transition:

```python
# Force transition back to WAITING state
await state_manager.force_transition(session_id, "WAITING", {
    "message": "Ready for next question",
    "recovery": True
})
```

## Implementation Details

### State Transition Validation

The state manager validates transitions to ensure they follow the expected flow:

```python
def _is_valid_transition(self, current, next_state):
    """
    Validate that a state transition follows the allowed flow.
    
    Modified with more flexible transitions to prevent deadlocks:
    - Any state can transition to WAITING (helps recover from errors)
    - PROCESSING can go to any state (helps with LLM timeout recovery)
    - WAITING can go to RESPONDING for playback of prebuffered audio
    """
    # Allow these universal transitions
    if next_state in ["IDLE", "ERROR", "WAITING"]:
        return True
        
    # Handle the normal flow with some additions
    valid_transitions = {
        "IDLE": ["LISTENING", "WAITING", "PROCESSING", "RESPONDING"],
        "LISTENING": ["PROCESSING", "WAITING", "IDLE", "RESPONDING"],
        "PROCESSING": ["RESPONDING", "PROCESSING", "WAITING", "IDLE", "LISTENING", "ERROR"],
        "RESPONDING": ["WAITING", "IDLE", "ERROR"],
        "WAITING": ["LISTENING", "IDLE", "PROCESSING", "RESPONDING"],
        "ERROR": ["IDLE", "WAITING", "PROCESSING", "LISTENING", "RESPONDING"]
    }
    
    return next_state in valid_transitions.get(current, [])
```

### Deadlock Prevention

The state manager implements a deadlock prevention mechanism that detects and resolves potential deadlocks:

```python
async def _handle_deadlock(self, session_id, new_state, timeout):
    """
    Improved deadlock detection and resolution.
    Ensures conversations can continue even after state transition problems.
    """
    try:
        # Wait for the timeout period plus a buffer
        await asyncio.sleep(timeout + 0.5)
        
        # If we get here, the transition may be deadlocked
        self.logger.warning(
            f"Possible deadlock detected for session {session_id} "
            f"transitioning to {new_state}. Forcing resolution."
        )
        
        # Force a new lock to be created
        if session_id in self._state_locks:
            self._state_locks[session_id] = asyncio.Lock()
            
        # Force transition if the session still exists
        if session_id in self.sessions:
            session = self.sessions[session_id]
            previous_state = session.state
            
            # Update the state directly without lock
            session.state = new_state
            session.last_updated = time.time()
            
            self.logger.warning(
                f"Forced state transition after deadlock: {session_id}: {previous_state} to {new_state}"
            )
            
            # If we've been stuck in PROCESSING for too long, force to WAITING
            if previous_state == "PROCESSING" and new_state == "PROCESSING":
                session.state = "WAITING"
                await self._broadcast_state_change(
                    session_id, "PROCESSING", "WAITING", 
                    {"message": "Ready for next question", "forced_recovery": True}
                )
    except asyncio.CancelledError:
        # Task was cancelled normally
        pass
```

### State Change Broadcasting

The state manager broadcasts state changes to the client:

```python
async def _broadcast_state_change(self, session_id, previous, current, metadata):
    """Broadcast state change to the client"""
    session = self.sessions.get(session_id)
    if not session or not hasattr(session, 'websocket') or session.websocket is None:
        return
        
    try:
        # Create state update message
        message = {
            "type": "state_update",
            "session_id": session_id,
            "previous": previous,
            "current": current,
            "timestamp": time.time(),
            "metadata": metadata or {}
        }
        
        # Send message to client
        await session.websocket.send(json.dumps(message))
        
    except Exception as e:
        self.logger.error(f"Error broadcasting state change: {e}")
```

### Session Context Management

The Session class maintains context for the LLM:

```python
def get_context(self):
    """
    Get formatted conversation context for the LLM
    
    Returns a list of conversation turns formatted for the LLM context
    """
    context = []
    for interaction in self.history:
        context.append({
            "role": "user",
            "content": interaction["user_input"]
        })
        context.append({
            "role": "assistant",
            "content": interaction["system_response"]
        })
    return context
```

## Configuration

The State Management system does not have a separate configuration file, but it does leverage these key settings:

1. **Lock Timeout**: The maximum time to wait for acquiring a state lock (default: 2.0 seconds)
2. **Session Expiration**: The time after which inactive sessions are considered expired (default: 1800 seconds / 30 minutes)

## Common Issues

### State Transition Issues

1. **Invalid State Transitions**:
   - **Symptoms**: Warning logs about invalid transitions, unexpected client behavior
   - **Causes**: Concurrent operations attempting to change state in invalid ways
   - **Solution**: State validation with flexible recovery paths

2. **State Deadlocks**:
   - **Symptoms**: Session gets stuck in PROCESSING or other states
   - **Causes**: Long-running operations, task failures without state updates
   - **Solution**: Deadlock detection and forced state transitions

3. **Race Conditions**:
   - **Symptoms**: Duplicate or conflicting state updates
   - **Causes**: Multiple asynchronous operations trying to update state
   - **Solution**: State locks with timeouts to prevent blocking

### Session Management Issues

1. **Session Leaks**:
   - **Symptoms**: Server memory increases over time, performance degradation
   - **Causes**: Connections close without proper cleanup
   - **Solution**: Session expiration and cleanup mechanisms

2. **Context Growth**:
   - **Symptoms**: Responses becoming slower, context exceeding limits
   - **Causes**: History accumulation without bounds
   - **Solution**: Context truncation in the LLM client

## Code Examples

### Creating a Session

```python
def create_session(self, session_id, session):
    """Initialize a new session with IDLE state"""
    self.sessions[session_id] = session
    self._state_locks[session_id] = asyncio.Lock()
    self.logger.info(f"Created new session: {session_id}")
    
    # Set initial state
    asyncio.create_task(
        self.transition_state(session_id, "IDLE")
    )
```

### Transitioning State

```python
async def transition_state(self, session_id, new_state, metadata=None, timeout=2.0):
    """
    Transition session to a new state and broadcast the change.
    
    Uses locks with shorter timeouts to prevent blocking and improved deadlock prevention.
    """
    if session_id not in self.sessions:
        # More helpful log message with the session ID to make it easier to debug
        self.logger.error(f"Cannot transition state for unknown session: {session_id} (to state {new_state})")
        return False
    
    # Set up a task to handle deadlock timeout if needed
    if session_id in self._deadlock_timeouts:
        self._deadlock_timeouts[session_id].cancel()
        
    deadlock_task = asyncio.create_task(
        self._handle_deadlock(session_id, new_state, timeout)
    )
    self._deadlock_timeouts[session_id] = deadlock_task
        
    try:
        # Acquire lock with timeout to prevent blocking indefinitely
        lock_acquired = False
        try:
            # Use wait_for with a timeout to avoid deadlocks
            await asyncio.wait_for(
                self._state_locks[session_id].acquire(),
                timeout=timeout
            )
            lock_acquired = True
        except asyncio.TimeoutError:
            self.logger.warning(
                f"Timed out waiting for state lock on {session_id}. "
                f"Forcing transition to {new_state}."
            )
            # Force the transition by creating a new lock
            self._state_locks[session_id] = asyncio.Lock()
            
        try:
            session = self.sessions.get(session_id)
            if not session:
                self.logger.warning(f"Session {session_id} no longer exists during transition")
                return False
                
            previous_state = session.state
            
            # Validate the state transition
            if not self._is_valid_transition(previous_state, new_state):
                self.logger.warning(
                    f"Invalid state transition: {previous_state} to {new_state}"
                )
                # Allow the transition in production to prevent deadlocks
            
            # Update the session state
            session.state = new_state
            session.last_updated = time.time()
            
            # Add metadata if provided
            if metadata:
                session.metadata.update(metadata)
                
            self.logger.info(f"State transition: {session_id}: {previous_state} to {new_state}")
            
            # Cancel the deadlock timeout task
            if deadlock_task and not deadlock_task.done():
                deadlock_task.cancel()
            
            # Broadcast state change
            await self._broadcast_state_change(session_id, previous_state, new_state, metadata)
            
            return True
        finally:
            # Only release the lock if we acquired it
            if lock_acquired:
                self._state_locks[session_id].release()
            
    except Exception as e:
        self.logger.error(f"Error during state transition: {e}")
        return False
```

### Force Transition for Recovery

```python
async def force_transition(self, session_id, new_state, metadata=None):
    """
    Force a state transition without waiting for locks.
    For emergency recovery only.
    """
    if session_id not in self.sessions:
        self.logger.error(f"Cannot force transition for unknown session: {session_id}")
        return False
        
    try:
        session = self.sessions[session_id]
        previous_state = session.state
        
        # Force the state change directly
        session.state = new_state
        session.last_updated = time.time()
        
        # Update metadata if provided
        if metadata:
            session.metadata.update(metadata)
        else:
            metadata = {}
            
        # Add forced flag to metadata
        metadata["forced"] = True
        metadata["recovery"] = True
        metadata["message"] = metadata.get("message", "Forced state transition for recovery")
        
        self.logger.warning(
            f"Forced state transition: {session_id}: {previous_state} to {new_state}"
        )
        
        # Try to broadcast the change
        try:
            await self._broadcast_state_change(session_id, previous_state, new_state, metadata)
        except Exception as e:
            self.logger.error(f"Error broadcasting forced state change: {e}")
            
        return True
    except Exception as e:
        self.logger.error(f"Error during forced state transition: {e}")
        return False
```

### Session Management

```python
def add_interaction(self, user_input, system_response):
    """
    Record a user-system interaction in the conversation history
    """
    interaction = {
        "timestamp": datetime.now().isoformat(),
        "user_input": user_input,
        "system_response": system_response
    }
    self.history.append(interaction)
    self.last_updated = time.time()
    
def reset(self):
    """
    Reset the conversation history
    """
    self.history = []
    self.last_updated = time.time()
    
def is_expired(self, timeout_seconds=1800):  # 30 minutes default
    """
    Check if the session has expired due to inactivity
    """
    return (time.time() - self.last_updated) > timeout_seconds
```
