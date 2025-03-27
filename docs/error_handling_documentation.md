# VR Interview System: Error Handling Documentation

## Title and Overview

The Error Handling component of the VR Interview System provides a robust framework for detecting, managing, and recovering from errors throughout the system. It implements specialized recovery strategies for different error types, tracks error patterns, and ensures graceful degradation to maintain system availability. This component is critical for providing a seamless user experience even when underlying components encounter issues.

## Architecture

The Error Handling system is designed around the central `ErrorHandler` class that acts as the orchestrator for all error recovery operations. It uses a modular architecture with specialized recovery handlers for different types of errors, allowing for targeted recovery strategies.

Key architectural elements include:
1. **Error Type Categorization**: Different error types are defined and handled separately
2. **Recovery Handler Registry**: Recovery strategies are registered for each error type
3. **Error Tracking System**: Error patterns are tracked for analytics and recovery optimization
4. **Graceful Degradation Paths**: Fallback mechanisms ensure continued operation
5. **Recovery Cooldowns**: Prevents excessive recovery attempts

### Component Diagram
```
┌──────────────────────────────────────────────────────┐
│                   Error Handler                       │
└───────────────┬───────────────────────┬──────────────┘
                │                       │
    ┌───────────▼─────────┐    ┌────────▼──────────┐
    │ Recovery Handlers   │    │   Error Tracking  │
    └───────────┬─────────┘    └────────┬──────────┘
                │                       │
                ▼                       ▼
┌─────────────────────────────────────────────────────┐
│              Error Recovery System                  │
│                                                     │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐    │
│ │LLM Recovery │ │STT Recovery │ │TTS Recovery │    │
│ └─────────────┘ └─────────────┘ └─────────────┘    │
│                                                     │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐    │
│ │WebSocket    │ │System       │ │State        │    │
│ │Recovery     │ │Recovery     │ │Recovery     │    │
│ └─────────────┘ └─────────────┘ └─────────────┘    │
└─────────────────────────────────────────────────────┘
```

## Key Classes/Functions

### ErrorHandler Class

```python
class ErrorHandler:
    """
    Enhanced error handler with improved recovery mechanisms and diagnostics
    """
    
    # Error type constants
    LLM_ERROR = "llm_error"
    STT_ERROR = "stt_error"
    TTS_ERROR = "tts_error"
    WEBSOCKET_ERROR = "websocket_error"
    SYSTEM_ERROR = "system_error"
```

#### Core Methods

- **`__init__()`**: Initializes error tracking structures and default settings
- **`register_recovery_handler(error_type, handler)`**: Registers a handler for a specific error type
- **`handle_error(error_type, session_id, exception, context)`**: Main error handling method that routes to appropriate recovery handler
- **`_handle_exceeded_recovery_attempts(error_type, session_id, exception, context)`**: Handles the case when maximum recovery attempts are exceeded
- **`_handle_cooldown_recovery(error_type, session_id, exception, context)`**: Handles recovery during cooldown periods
- **`get_error_statistics(session_id)`**: Retrieves error statistics for analysis
- **`reset_session_errors(session_id)`**: Resets error tracking for a session
- **`cleanup_old_sessions(max_age_seconds)`**: Cleans up error tracking for old sessions

### Specialized Recovery Handlers

The system includes specialized handlers for each error type:

1. **LLM Error Handler**: Handles errors in LLM processing
2. **STT Error Handler**: Handles errors in speech-to-text processing
3. **TTS Error Handler**: Handles errors in text-to-speech processing
4. **WebSocket Error Handler**: Handles WebSocket connection errors
5. **System Error Handler**: Handles general system errors

## Usage Patterns

### Error Handling Flow

1. **Error Detection**: Error is detected in a system component
   ```python
   try:
       # Component operation
   except Exception as e:
       # Handle the error
       if self.error_handler:
           await self.error_handler.handle_error(
               ErrorHandler.LLM_ERROR,  # Error type
               session_id,              # Session identifier
               e,                       # Exception object
               {"context": "data"}      # Additional context
           )
   ```

2. **Error Routing**: The error is routed to the appropriate handler
   ```python
   if error_type in self.recovery_handlers:
       handler = self.recovery_handlers[error_type]
       
       # Provide enhanced context with error tracking
       enhanced_context = context or {}
       enhanced_context.update({
           "error_count": self.error_counts[session_id],
           "error_types": self.error_types[session_id],
           "recurring": recurring,
           "recovery_attempts": self.session_recovery_attempts[session_id]
       })
       
       # Call the handler
       success, metadata = await handler(session_id, exception, enhanced_context)
   ```

3. **Recovery Attempt**: The specialized handler attempts recovery
   ```python
   async def _handle_llm_error(self, session_id, exception, context):
       # Log the detailed error
       self.logger.error(f"LLM error recovery for {session_id}: {exception}")
       
       # Always transition to WAITING state to prevent client hang
       await self.state_manager.transition_state(session_id, "WAITING", {
           "message": "Ready for next question",
           "error": "Interview system needed to reset"
       })
       
       # Send fallback response directly if possible
       if "websocket" in context:
           websocket = context["websocket"]
           fallback_message = {
               "type": "text_response",
               "text": "I had a bit of trouble processing that. Let's continue the interview."
           }
           await websocket.send(json.dumps(fallback_message))
           
       return True  # Indicate successful recovery
   ```

4. **Error Tracking**: The error is tracked for pattern detection
   ```python
   # Add to error tracking
   if session_id not in self.error_counts:
       self.error_counts[session_id] = 0
       self.error_types[session_id] = {}
       self.session_recovery_attempts[session_id] = {}
       
   self.error_counts[session_id] += 1
   
   # Track error type
   error_name = error_type if isinstance(error_type, str) else error_type.__name__
   if error_name not in self.error_types[session_id]:
       self.error_types[session_id][error_name] = 0
   self.error_types[session_id][error_name] += 1
   ```

5. **Cooldown Check**: Cooldown periods prevent excessive recovery attempts
   ```python
   # Check for cooldown period
   cooldown_period = self.recovery_cooldowns.get(error_name, 5)
   last_recovery_time = self.last_recovery_times.get(session_id, {}).get(error_name, 0)
   time_since_last = current_time - last_recovery_time
   
   if time_since_last < cooldown_period and last_recovery_time > 0:
       self.logger.info(f"In cooldown period for {error_name} ({time_since_last:.1f}s < {cooldown_period}s)")
       # Use lite recovery during cooldown
       return await self._handle_cooldown_recovery(error_name, session_id, exception, context)
   ```

### State Recovery Patterns

1. **Force Transition**: Force state transition for recovery
   ```python
   try:
       # Import here to avoid circular imports
       from app.state.manager import StateManager
       state_manager = None
       
       # Try to get the StateManager instance
       if hasattr(StateManager, 'get_instance'):
           state_manager = StateManager.get_instance()
       else:
           state_manager = context.get('state_manager') if context else None
       
       if state_manager:
           # Check current state
           current_state = state_manager.get_session_state(session_id)
           
           # Only transition if not already in WAITING/IDLE
           if current_state not in ["WAITING", "IDLE"]:
               await state_manager.transition_state(session_id, "WAITING", {
                   "message": "Ready for next question after error recovery",
                   "error_recovered": True,
                   "error_type": error_name
               })
   except Exception as state_error:
       self.logger.error(f"Error transitioning state after error: {state_error}")
   ```

2. **Session Reset**: Reset session for persistent errors
   ```python
   # Reset session completely
   if hasattr(state_manager, 'reset_session'):
       await state_manager.reset_session(session_id)
       self.logger.info(f"Reset session {session_id} completely")
   
   # Force transition to IDLE (fresh start)
   await state_manager.transition_state(session_id, "IDLE", {
       "message": "Session reset due to recurring errors",
       "error_recovered": True,
       "error_type": error_type,
       "recovery_strategy": "aggressive"
   })
   ```

## Implementation Details

### Error Type Registration

The error handler allows registration of specialized handlers for each error type:

```python
def register_recovery_handler(self, error_type: str, handler: Callable):
    """Register a handler for a specific error type"""
    self.recovery_handlers[error_type] = handler
    self.logger.info(f"Registered recovery handler for {error_type}")
```

In the main server initialization:

```python
def _register_error_handlers(self):
    """Register handlers for different error types"""
    # Register LLM error handler
    self.error_handler.register_recovery_handler(
        ErrorHandler.LLM_ERROR,
        self._handle_llm_error
    )
    
    # Register STT error handler
    self.error_handler.register_recovery_handler(
        ErrorHandler.STT_ERROR,
        self._handle_stt_error
    )
    
    # Register TTS error handler
    self.error_handler.register_recovery_handler(
        ErrorHandler.TTS_ERROR,
        self._handle_tts_error
    )
    
    # Register WebSocket error handler
    self.error_handler.register_recovery_handler(
        ErrorHandler.WEBSOCKET_ERROR,
        self._handle_websocket_error
    )
    
    # Register system error handler
    self.error_handler.register_recovery_handler(
        ErrorHandler.SYSTEM_ERROR,
        self._handle_system_error
    )
```

### Error Tracking and Statistics

The error handler tracks errors to detect patterns and optimize recovery:

```python
def get_error_statistics(self, session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Get error statistics for debugging and monitoring
    
    Args:
        session_id: Optional session ID to get stats for a specific session
        
    Returns:
        Dictionary with error statistics
    """
    if session_id:
        # Return stats for a specific session
        return {
            "error_count": self.error_counts.get(session_id, 0),
            "error_types": self.error_types.get(session_id, {}),
            "recovery_attempts": self.session_recovery_attempts.get(session_id, {})
        }
    else:
        # Return global stats
        return {
            "total_sessions_with_errors": len(self.error_counts),
            "total_errors": sum(self.error_counts.values()) if self.error_counts else 0,
            "error_type_counts": self._aggregate_error_types(),
            "recent_errors": self.recent_errors
        }
```

### Recovery Cooldowns

To prevent recovery flooding, the system implements cooldown periods:

```python
# Cooldown periods between recovery attempts (seconds)
self.recovery_cooldowns = {
    self.LLM_ERROR: 5,
    self.STT_ERROR: 2,
    self.TTS_ERROR: 3,
    self.WEBSOCKET_ERROR: 10,
    self.SYSTEM_ERROR: 5
}
```

```python
async def _handle_cooldown_recovery(self, error_type: str, session_id: str,
                                  exception: Exception, context: Optional[Dict[str, Any]] = None):
    """
    Handle the case where we're in a cooldown period for an error type
    
    This uses lighter recovery strategies to avoid spamming the client with messages
    """
    self.logger.info(f"Using lite recovery for {error_type} in {session_id} - in cooldown period")
    
    # Only try to transition state, but don't send user-facing messages
    try:
        from app.state.manager import StateManager
        state_manager = None
        
        if hasattr(StateManager, 'get_instance'):
            state_manager = StateManager.get_instance()
        else:
            state_manager = context.get('state_manager') if context else None
        
        if state_manager:
            # Check current state
            current_state = state_manager.get_session_state(session_id)
            
            # Only transition if in a "stuck" state
            if current_state in ["PROCESSING", "RESPONDING", "ERROR"]:
                await state_manager.transition_state(session_id, "WAITING", {
                    "message": "Ready for next question",
                    "error_recovered": True,
                    "error_type": error_type,
                    "recovery_strategy": "lite"
                })
    except Exception as state_error:
        self.logger.error(f"Error during lite recovery: {state_error}")
    
    return False, {"strategy": "lite_recovery"}
```

### Aggressive Recovery for Persistent Errors

When errors persist despite multiple recovery attempts:

```python
async def _handle_exceeded_recovery_attempts(self, error_type: str, session_id: str, 
                                          exception: Exception, context: Optional[Dict[str, Any]] = None):
    """
    Handle the case where we've exceeded maximum recovery attempts for an error type
    
    This uses more aggressive recovery strategies:
    - Resets session state completely
    - Suggests client restart if applicable
    - Uses simpler fallback mechanisms
    """
    self.logger.info(f"Using aggressive recovery for {error_type} in {session_id} - exceeded max attempts")
    
    websocket = context.get("websocket") if context else None
    
    # Send reset notice to client
    if websocket:
        try:
            reset_message = {
                "type": "system_message",
                "session_id": session_id,
                "timestamp": time.time(),
                "message": "The system needs to reset. Please try asking a new question."
            }
            await websocket.send(json.dumps(reset_message))
        except Exception as ws_error:
            self.logger.error(f"Error sending reset message: {ws_error}")
    
    # Try to reset session state completely
    try:
        # Import here to avoid circular imports
        from app.state.manager import StateManager
        state_manager = None
        
        # Try to get the StateManager instance
        if hasattr(StateManager, 'get_instance'):
            state_manager = StateManager.get_instance()
        else:
            state_manager = context.get('state_manager') if context else None
        
        if state_manager:
            # Reset session completely
            if hasattr(state_manager, 'reset_session'):
                await state_manager.reset_session(session_id)
                self.logger.info(f"Reset session {session_id} completely")
            
            # Force transition to IDLE (fresh start)
            await state_manager.transition_state(session_id, "IDLE", {
                "message": "Session reset due to recurring errors",
                "error_recovered": True,
                "error_type": error_type,
                "recovery_strategy": "aggressive"
            })
    except Exception as reset_error:
        self.logger.error(f"Error during aggressive session reset: {reset_error}")
    
    # Reset the error counters for this session to give a fresh start
    if session_id in self.session_recovery_attempts:
        for err_type in self.session_recovery_attempts[session_id]:
            self.session_recovery_attempts[session_id][err_type] = 0
            
    # Return success=False to indicate we used fallback mechanisms
    return False, {"strategy": "aggressive_reset"}
```

## Configuration

The error handling system is not separately configured but uses internal defaults that can be modified:

1. **Recovery Attempt Limits**:
   ```python
   # Maximum recovery attempts per error type
   self.max_recovery_attempts = {
       self.LLM_ERROR: 3,
       self.STT_ERROR: 2,
       self.TTS_ERROR: 3,
       self.WEBSOCKET_ERROR: 3,
       self.SYSTEM_ERROR: 2
   }
   ```

2. **Recovery Cooldowns**:
   ```python
   # Cooldown periods between recovery attempts (seconds)
   self.recovery_cooldowns = {
       self.LLM_ERROR: 5,
       self.STT_ERROR: 2,
       self.TTS_ERROR: 3,
       self.WEBSOCKET_ERROR: 10,
       self.SYSTEM_ERROR: 5
   }
   ```

3. **Session Cleanup Age**:
   ```python
   # Default cleanup age for old sessions
   max_age_seconds = 3600  # 1 hour
   ```

## Common Issues

### Error Detection Issues

1. **Undetected Errors**:
   - **Symptoms**: System hangs or behaves unexpectedly without error logs
   - **Causes**: Missing try-except blocks, uncaught exceptions
   - **Solution**: Comprehensive error handling in all components

2. **Error Classification Issues**:
   - **Symptoms**: Errors handled with incorrect strategies
   - **Causes**: Misclassification of error types
   - **Solution**: Better error type detection and routing

3. **Circular Dependencies**:
   - **Symptoms**: Import errors when recovering state
   - **Causes**: Tight coupling between components
   - **Solution**: Dynamic imports in error handlers

### Recovery Issues

1. **Recovery Loops**:
   - **Symptoms**: Repeated error-recovery cycles
   - **Causes**: Failed recovery attempts triggering new errors
   - **Solution**: Cooldown periods and maximum attempt limits

2. **State Corruption**:
   - **Symptoms**: Inconsistent state after recovery
   - **Causes**: Partial state updates during errors
   - **Solution**: Force transition to known good states (IDLE or WAITING)

3. **Client Disconnect During Recovery**:
   - **Symptoms**: Recovery fails with WebSocket errors
   - **Causes**: Client disconnects during error recovery
   - **Solution**: Try-except blocks around all WebSocket operations

### Resource Management Issues

1. **Memory Leaks**:
   - **Symptoms**: Increasing memory usage over time
   - **Causes**: Accumulating error tracking data
   - **Solution**: Session cleanup and error history pruning

2. **Error Log Flooding**:
   - **Symptoms**: Excessive log entries
   - **Causes**: Repeated errors with full logging
   - **Solution**: Throttled logging during cooldown periods

## Code Examples

### Main Error Handler

```python
async def handle_error(self, error_type: str, session_id: str, 
                      exception: Exception, context: Optional[Dict[str, Any]] = None):
    """
    Enhanced error handler with improved tracking and recovery
    """
    try:
        # Add to error tracking
        if session_id not in self.error_counts:
            self.error_counts[session_id] = 0
            self.error_types[session_id] = {}
            self.session_recovery_attempts[session_id] = {}
            self.last_recovery_times[session_id] = {}
        
        self.error_counts[session_id] += 1
        
        # Track error type
        error_name = error_type if isinstance(error_type, str) else error_type.__name__
        if error_name not in self.error_types[session_id]:
            self.error_types[session_id][error_name] = 0
        self.error_types[session_id][error_name] += 1
        
        # Track recovery attempts for this error type
        if error_name not in self.session_recovery_attempts[session_id]:
            self.session_recovery_attempts[session_id][error_name] = 0
        self.session_recovery_attempts[session_id][error_name] += 1
        
        # Track recovery timestamp
        current_time = time.time()
        self.last_recovery_times[session_id][error_name] = current_time
        
        # Track recent errors for pattern detection (keep last 10)
        self.recent_errors.append({
            "time": current_time,
            "session_id": session_id,
            "error_type": error_name,
            "exception": str(exception)
        })
        if len(self.recent_errors) > 10:
            self.recent_errors.pop(0)
            
        # Log error with traceback
        self.logger.error(f"Error in session {session_id}: {exception}")
        self.logger.error(traceback.format_exc())
        
        # Check if we've exceeded the maximum recovery attempts for this error type
        max_attempts = self.max_recovery_attempts.get(error_name, 3)
        if self.session_recovery_attempts[session_id][error_name] > max_attempts:
            self.logger.warning(f"Exceeded max recovery attempts ({max_attempts}) for {error_name} in session {session_id}")
            # Use more aggressive fallback strategy when max attempts exceeded
            return await self._handle_exceeded_recovery_attempts(error_name, session_id, exception, context)
        
        # Check for cooldown period
        cooldown_period = self.recovery_cooldowns.get(error_name, 5)
        last_recovery_time = self.last_recovery_times.get(session_id, {}).get(error_name, 0)
        time_since_last = current_time - last_recovery_time
        
        if time_since_last < cooldown_period and last_recovery_time > 0:
            self.logger.info(f"In cooldown period for {error_name} ({time_since_last:.1f}s < {cooldown_period}s)")
            # Use lite recovery during cooldown
            return await self._handle_cooldown_recovery(error_name, session_id, exception, context)
        
        # Check for recurring errors
        recurring = False
        if self.error_counts[session_id] >= 3:
            # Check if same error type is recurring
            for err_type, count in self.error_types[session_id].items():
                if count >= 2:
                    recurring = True
                    break
        
        # Get special handler if available
        if error_type in self.recovery_handlers:
            handler = self.recovery_handlers[error_type]
            
            # Provide enhanced context with error tracking
            enhanced_context = context or {}
            enhanced_context.update({
                "error_count": self.error_counts[session_id],
                "error_types": self.error_types[session_id],
                "recurring": recurring,
                "recent_errors": self.recent_errors,
                "recovery_attempts": self.session_recovery_attempts[session_id]
            })
            
            # Call the handler
            try:
                success = await handler(session_id, exception, enhanced_context)
                return success, {}
            except Exception as handler_error:
                self.logger.error(f"Error in error handler for {error_type}: {handler_error}")
                # Continue to fallback
        
        # If handler not available or failed, use generic fallback
        # ... (fallback code)
        
        # Return False as we used fallback
        return False, {}
    except Exception as e:
        # Meta-error: error in error handler
        self.logger.critical(f"Critical error in error handler: {e}")
        self.logger.critical(traceback.format_exc())
        return False, {}
```

### LLM Error Handler

```python
async def _handle_llm_error(self, session_id, exception, context):
    """Handle errors in LLM processing with improved recovery"""
    try:
        # Log the detailed error
        self.logger.error(f"LLM error recovery for {session_id}: {exception}")
        
        # Always transition to WAITING state to prevent client hang
        await self.state_manager.transition_state(session_id, "WAITING", {
            "message": "Ready for next question",
            "error": "Interview system needed to reset"
        })
        
        # Send fallback response directly if possible
        if "websocket" in context:
            websocket = context["websocket"]
            fallback_message = {
                "type": "text_response",  # Use text_response type for better client handling
                "text": "I had a bit of trouble processing that. Let's continue the interview. Could you please ask me another question?",
                "message": "LLM processing error, showing text response instead"
            }
            await websocket.send(json.dumps(fallback_message))
            
        # Mark that this session had an error to avoid repeated failures
        session = self.state_manager.get_session(session_id)
        if session:
            if not hasattr(session, 'error_count'):
                session.error_count = 0
            session.error_count += 1
            
            # If multiple errors occur, suggest refreshing the client
            if session.error_count >= 3:
                if "websocket" in context:
                    websocket = context["websocket"]
                    reset_message = {
                        "type": "system_message",
                        "message": "Multiple errors detected. Consider refreshing your client application."
                    }
                    await websocket.send(json.dumps(reset_message))
            
        return True  # Indicate successful recovery
    except Exception as e:
        self.logger.error(f"Error during LLM error recovery: {e}")
        return False
```

### TTS Error Handler

```python
async def _handle_tts_error(self, session_id, exception, context):
    """Handle errors in text-to-speech processing with improved recovery"""
    try:
        # Check if this is a timeout error
        is_timeout = isinstance(exception, asyncio.TimeoutError) or "timeout" in str(exception).lower()
        
        # If we have the text response, send it directly as a fallback
        text_response = context.get("text_response")
        if text_response and "websocket" in context:
            websocket = context["websocket"]
            
            # For timeout errors, inform the client that we're still trying
            if is_timeout:
                trying_message = {
                    "type": "system_message",
                    "message": "Still generating audio, please wait a moment..."
                }
                try:
                    await websocket.send(json.dumps(trying_message))
                except:
                    # Connection might be closed, ignore
                    pass
                
                # Schedule a task to keep trying to get the audio
                asyncio.create_task(self._check_delayed_tts_response(
                    session_id, 
                    text_response, 
                    context
                ))
            else:
                # For non-timeout errors, just show text
                fallback_message = {
                    "type": "text_response",
                    "text": text_response,
                    "message": "Audio couldn't be generated. Displaying text instead."
                }
                await websocket.send(json.dumps(fallback_message))
            
        # Transition to WAITING state
        await self.state_manager.transition_state(session_id, "WAITING", {
            "message": "Ready for next question" if not is_timeout else "Still generating audio..."
        })
        
        return True  # Indicate successful recovery
    except Exception as e:
        self.logger.error(f"Error during TTS error recovery: {e}")
        # Final fallback - always try to get back to WAITING state
        try:
            await self.state_manager.transition_state(session_id, "WAITING", {})
        except:
            pass
        return False
```

### WebSocket Error Handler

```python
async def _handle_websocket_error(self, session_id, exception, context):
    """Handle WebSocket connection errors with improved cleanup"""
    try:
        self.logger.warning(f"WebSocket error for {session_id}. Scheduling cleanup.")
        
        # Try to send a final error message if websocket is still valid
        if "websocket" in context:
            try:
                websocket = context["websocket"]
                message = {
                    "type": "error",
                    "code": 1001,
                    "message": "Connection interrupted. Please reconnect.",
                    "session_id": session_id,
                    "timestamp": time.time()
                }
                await websocket.send(json.dumps(message))
            except:
                # Ignore errors in sending the message
                pass
        
        # Schedule session cleanup after a delay - reduce from 30s to 10s
        asyncio.get_event_loop().call_later(
            10, 
            lambda: asyncio.create_task(self.state_manager.end_session(session_id))
        )
        
        return True  # Indicate successful recovery
    except Exception as e:
        self.logger.error(f"Error during WebSocket error recovery: {e}")
        return False
```
