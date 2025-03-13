import asyncio
import json
import logging
import time
import uuid
import base64
from websockets import serve, ConnectionClosed

from app.websocket.protocol import encode_message, decode_message, validate_message
from app.state.session import Session


class WebSocketServer:
    def __init__(self, host, port, state_manager, stt_service, tts_service, llm_client, 
                 error_handler=None, heartbeat_service=None):
        self.host = host
        self.port = port
        self.state_manager = state_manager
        self.stt_service = stt_service
        self.tts_service = tts_service
        self.llm_client = llm_client
        self.error_handler = error_handler
        self.heartbeat_service = heartbeat_service
        self.server = None
        self.active_connections = {}
        self.logger = logging.getLogger("websocket")
        
        # Task pool for managing async operations
        self.tasks = set()
        
        # Dictionary to track running pipeline tasks by session_id
        # This allows cancelling long-running operations when needed
        self.pipeline_tasks = {}

    async def start(self):
        """Start the WebSocket server"""
        self.server = await serve(
            self.handle_connection,
            self.host,
            self.port,
            ping_interval=30,
            ping_timeout=10
        )
        self.logger.info(f"WebSocket server started on {self.host}:{self.port}")
        print(f"\nVR Interview Server running at ws://{self.host}:{self.port}")
        print("Press Ctrl+C to stop the server\n")

    async def shutdown(self):
        """Shutdown the WebSocket server"""
        if self.server:
            self.logger.info("Shutting down WebSocket server...")
            self.server.close()
            await self.server.wait_closed()
            
            # Cancel all running tasks
            for task in self.tasks:
                task.cancel()
                
            # Cancel all pipeline tasks
            for session_id, task in self.pipeline_tasks.items():
                if not task.done():
                    self.logger.info(f"Cancelling pipeline task for session {session_id}")
                    task.cancel()
            
            self.logger.info("WebSocket server shut down")

    async def handle_connection(self, websocket, path):
        """Handle a new WebSocket connection"""
        session_id = str(uuid.uuid4())
        self.logger.info(f"New connection established: {session_id}")
        
        # Create a new session
        session = Session(session_id, websocket)
        self.active_connections[session_id] = websocket
        
        # Register session with state manager
        self.state_manager.create_session(session_id, session)
        
        # Start heartbeat for this session if available
        if self.heartbeat_service:
            await self.heartbeat_service.start_heartbeat(session_id, websocket)
        
        # Send initial IDLE state
        await self.state_manager.transition_state(session_id, "IDLE", {
            "message": "Ready for conversation"
        })
        
        try:
            async for message in websocket:
                # Process the incoming message - use create_task to avoid blocking
                task = asyncio.create_task(
                    self.process_message(session_id, message)
                )
                # Add task to the set to keep a reference to it
                self.tasks.add(task)
                # Remove task from set when it completes
                task.add_done_callback(lambda t: self.tasks.discard(t))
                
        except ConnectionClosed:
            self.logger.info(f"Connection closed: {session_id}")
        except Exception as e:
            self.logger.error(f"Error in connection handler: {e}")
            if self.error_handler:
                context = {"websocket": websocket}
                await self.error_handler.handle_error(
                    "WEBSOCKET_ERROR", session_id, e, context
                )
        finally:
            # Clean up session
            await self._cleanup_session(session_id)

    async def _cleanup_session(self, session_id):
        """Clean up resources associated with a session"""
        # Stop heartbeat if it exists
        if self.heartbeat_service:
            await self.heartbeat_service.stop_heartbeat(session_id)
            
        # Cancel any running pipeline task
        if session_id in self.pipeline_tasks and not self.pipeline_tasks[session_id].done():
            self.logger.info(f"Cancelling running pipeline for session {session_id}")
            self.pipeline_tasks[session_id].cancel()
            del self.pipeline_tasks[session_id]
            
        # Remove from active connections
        if session_id in self.active_connections:
            self.logger.info(f"Cleaned up session: {session_id}")
            del self.active_connections[session_id]
            
        # End session in state manager
        await self.state_manager.end_session(session_id)

    async def process_message(self, session_id, message):
        """Process an incoming WebSocket message"""
        try:
            # Decode and validate the message
            msg_data = decode_message(message)
            if not validate_message(msg_data):
                await self.send_error(session_id, 400, "Invalid message format")
                return
                
            msg_type = msg_data.get("type")
            self.logger.debug(f"Received message type: {msg_type} from {session_id}")
            
            # Route message based on type
            if msg_type == "audio_data":
                await self.process_audio(session_id, msg_data)
            elif msg_type == "ping":
                await self.send_pong(session_id)
            elif msg_type == "control":
                await self.process_control(session_id, msg_data)
            else:
                await self.send_error(session_id, 400, f"Unknown message type: {msg_type}")
                
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            await self.send_error(session_id, 500, "Internal server error")
            if self.error_handler:
                context = {"websocket": self.active_connections.get(session_id)}
                await self.error_handler.handle_error(
                    "WEBSOCKET_ERROR", session_id, e, context
                )

    async def process_audio(self, session_id, message):
        """Process incoming audio data"""
        try:
            # Check current state
            current_state = self.state_manager.get_session_state(session_id)
            if current_state not in ["IDLE", "WAITING"]:
                self.logger.warning(f"Received audio when in {current_state} state. Ignoring.")
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
                
            # Cancel any existing pipeline task for this session
            if session_id in self.pipeline_tasks and not self.pipeline_tasks[session_id].done():
                self.logger.info(f"Cancelling previous pipeline for session {session_id}")
                self.pipeline_tasks[session_id].cancel()
            
            # Start audio processing pipeline in a separate task to avoid blocking
            pipeline_task = asyncio.create_task(
                self.process_audio_pipeline(session_id, audio_data)
            )
            
            # Store the task reference
            self.pipeline_tasks[session_id] = pipeline_task
            
            # Add task cleanup callback
            pipeline_task.add_done_callback(
                lambda t: self._handle_pipeline_completion(session_id, t)
            )
            
        except Exception as e:
            self.logger.error(f"Error processing audio: {e}")
            await self.send_error(session_id, 500, "Error processing audio")
            if self.error_handler:
                context = {"websocket": self.active_connections.get(session_id)}
                await self.error_handler.handle_error(
                    "STT_ERROR", session_id, e, context
                )

    def _handle_pipeline_completion(self, session_id, task):
        """Handle completion of a pipeline task"""
        # Remove task from tracking dict when complete
        if session_id in self.pipeline_tasks and self.pipeline_tasks[session_id] == task:
            del self.pipeline_tasks[session_id]
            
        # Check for exceptions
        if not task.cancelled():
            try:
                task.result()  # Will raise exception if task failed
            except asyncio.CancelledError:
                self.logger.info(f"Pipeline task for session {session_id} was cancelled")
            except Exception as e:
                self.logger.error(f"Pipeline task for session {session_id} failed: {e}")
                # We could trigger error handling here, but that's usually handled
                # within the task itself

    async def process_audio_pipeline(self, session_id, audio_data):
        """Full audio processing pipeline - runs asynchronously"""
        progress_task = None
        try:
            # Transition to PROCESSING state
            await self.state_manager.transition_state(session_id, "PROCESSING", {
                "message": "Transcribing audio"
            })
            
            # 1. Transcribe audio in a separate thread pool to avoid blocking
            # This is crucial for CPU-intensive operations
            transcript = await asyncio.to_thread(
                self.stt_service.transcribe,
                audio_data
            )
            
            self.logger.info(f"Transcription: {transcript}")
            
            # Get the current session
            session = self.state_manager.get_session(session_id)
            if not session:
                self.logger.error(f"Session {session_id} not found")
                return
                
            # Update state with transcription info
            await self.state_manager.transition_state(session_id, "PROCESSING", {
                "message": "Generating response",
                "transcript": transcript
            })
            
            # 2. Start progress updates task during LLM processing
            # This keeps the client informed during lengthy processing
            progress_task = asyncio.create_task(
                self._send_progress_updates(session_id, "Generating response")
            )
            
            # 3. Generate LLM response in a separate thread pool
            # This prevents the CPU-intensive LLM generation from blocking the event loop
            response = await asyncio.to_thread(
                self.llm_client.generate_response,
                transcript,
                session.get_context()
            )
            
            # Cancel the progress update task
            if progress_task and not progress_task.done():
                progress_task.cancel()
                try:
                    await progress_task
                except asyncio.CancelledError:
                    pass
                progress_task = None
            
            # Add the exchange to session history
            session.add_interaction(transcript, response)
            
            self.logger.info(f"LLM Response: {response}")
            
            # Update state for speech synthesis
            await self.state_manager.transition_state(session_id, "PROCESSING", {
                "message": "Converting response to speech"
            })
            
            # 4. Generate speech in a separate thread pool
            audio_response = await asyncio.to_thread(
                self.tts_service.synthesize,
                response
            )
            
            # Transition to RESPONDING
            await self.state_manager.transition_state(session_id, "RESPONDING", {
                "message": "Playing response"
            })
            
            # 5. Send audio response to client
            await self.send_audio_response(session_id, audio_response)
            
            # Wait a moment to ensure audio is received
            await asyncio.sleep(0.5)
            
            # Transition to WAITING for next user input
            await self.state_manager.transition_state(session_id, "WAITING", {
                "message": "Waiting for user input"
            })
            
        except asyncio.CancelledError:
            # Handle cancellation gracefully
            self.logger.info(f"Audio pipeline cancelled for session {session_id}")
            if self.state_manager.get_session_state(session_id) == "PROCESSING":
                # Only transition if we're still in PROCESSING
                await self.state_manager.transition_state(session_id, "WAITING", {
                    "message": "Processing cancelled"
                })
            # Cancel any running progress task
            if progress_task and not progress_task.done():
                progress_task.cancel()
            
        except Exception as e:
            self.logger.error(f"Error in audio pipeline: {e}")
            # Cancel any running progress task
            if progress_task and not progress_task.done():
                progress_task.cancel()
                
            # Handle error based on where in the pipeline we are
            current_state = self.state_manager.get_session_state(session_id)
            
            if self.error_handler:
                context = {
                    "websocket": self.active_connections.get(session_id),
                    "state": current_state
                }
                await self.error_handler.handle_error(
                    "PIPELINE_ERROR", session_id, e, context
                )
            else:
                # Basic error handling if no error handler is available
                await self.state_manager.transition_state(session_id, "ERROR", {
                    "error": str(e)
                })
                await self.send_error(session_id, 500, "Error processing request")
                
                # Attempt to recover to WAITING state after a brief delay
                await asyncio.sleep(1)
                await self.state_manager.transition_state(session_id, "WAITING", {
                    "message": "Waiting for user input"
                })

    async def process_control(self, session_id, message):
        """Process control messages from client"""
        action = message.get("action")
        if action == "start":
            # Start a new session or reset the current one
            session = self.state_manager.get_session(session_id)
            if session:
                await self.state_manager.transition_state(session_id, "IDLE", {
                    "message": "Ready to begin"
                })
                
        elif action == "stop":
            # Cancel any running pipeline
            if session_id in self.pipeline_tasks and not self.pipeline_tasks[session_id].done():
                self.logger.info(f"Cancelling pipeline for session {session_id} due to stop request")
                self.pipeline_tasks[session_id].cancel()
                
            # Stop the current response
            current_state = self.state_manager.get_session_state(session_id)
            if current_state in ["PROCESSING", "RESPONDING"]:
                await self.state_manager.transition_state(session_id, "WAITING", {
                    "message": "Response stopped"
                })
                
        elif action == "reset":
            # Reset the conversation and cancel any tasks
            if session_id in self.pipeline_tasks and not self.pipeline_tasks[session_id].done():
                self.pipeline_tasks[session_id].cancel()
                
            session = self.state_manager.get_session(session_id)
            if session:
                session.reset()
                await self.state_manager.transition_state(session_id, "IDLE", {
                    "message": "Conversation reset"
                })

    async def send_audio_response(self, session_id, audio_data):
        """Send audio response to client"""
        websocket = self.active_connections.get(session_id)
        if not websocket:
            self.logger.error(f"No active connection for {session_id}")
            return
            
        try:
            message = {
                "type": "audio_response",
                "session_id": session_id,
                "timestamp": time.time(),
                "duration": 0.0,  # Would be calculated from audio metadata
                "data": base64.b64encode(audio_data).decode('utf-8')
            }
            await websocket.send(encode_message(message))
        except Exception as e:
            self.logger.error(f"Error sending audio response: {e}")
            if self.error_handler:
                context = {"websocket": websocket, "text_response": None}
                await self.error_handler.handle_error(
                    "TTS_ERROR", session_id, e, context
                )

    async def send_pong(self, session_id):
        """Send pong response to client"""
        websocket = self.active_connections.get(session_id)
        if not websocket:
            return
            
        try:
            message = {
                "type": "pong",
                "session_id": session_id,
                "timestamp": time.time()
            }
            await websocket.send(encode_message(message))
        except Exception as e:
            self.logger.error(f"Error sending pong: {e}")

    async def send_error(self, session_id, code, message):
        """Send error message to client"""
        websocket = self.active_connections.get(session_id)
        if not websocket:
            return
            
        try:
            error_message = {
                "type": "error",
                "session_id": session_id,
                "code": code,
                "message": message,
                "timestamp": time.time()
            }
            await websocket.send(encode_message(error_message))
        except Exception as e:
            self.logger.error(f"Error sending error message: {e}")
    
    async def _send_progress_updates(self, session_id, base_message, interval=2.0):
        """Send periodic progress updates during long-running operations"""
        dots = 0
        consecutive_errors = 0
        max_errors = 3  # Max consecutive errors before giving up
        
        try:
            while True:
                try:
                    # Create a progress message with animated dots
                    dots = (dots % 3) + 1
                    message = f"{base_message}{('.' * dots)}"
                    
                    # Update the state with the progress message
                    # Use the heartbeat system here
                    if session_id in self.active_connections:
                        await self.state_manager.transition_state(session_id, "PROCESSING", {
                            "message": message,
                            "progress": True
                        })
                        consecutive_errors = 0  # Reset error counter on success
                    else:
                        # Session no longer exists, exit loop
                        break
                        
                except Exception as e:
                    self.logger.warning(f"Error sending progress update: {e}")
                    consecutive_errors += 1
                    if consecutive_errors >= max_errors:
                        self.logger.error("Too many consecutive errors in progress updates, stopping")
                        break
                
                # Wait for the interval
                await asyncio.sleep(interval)
                
        except asyncio.CancelledError:
            # Task was cancelled normally when the operation completed
            pass
        except Exception as e:
            self.logger.error(f"Error in progress updates: {e}")


class HeartbeatService:
    """Service to send periodic heartbeat messages to clients"""
    
    def __init__(self, heartbeat_interval=5.0):
        self.heartbeat_interval = heartbeat_interval
        self.heartbeat_tasks = {}
        self.logger = logging.getLogger("heartbeat")
        
    async def start_heartbeat(self, session_id, websocket):
        """Start sending heartbeats to a client"""
        if session_id in self.heartbeat_tasks and not self.heartbeat_tasks[session_id].done():
            self.heartbeat_tasks[session_id].cancel()
            
        self.heartbeat_tasks[session_id] = asyncio.create_task(
            self._heartbeat_loop(session_id, websocket)
        )
        
    async def stop_heartbeat(self, session_id):
        """Stop sending heartbeats to a client"""
        if session_id in self.heartbeat_tasks and not self.heartbeat_tasks[session_id].done():
            self.heartbeat_tasks[session_id].cancel()
            try:
                await self.heartbeat_tasks[session_id]
            except asyncio.CancelledError:
                pass
            del self.heartbeat_tasks[session_id]
            
    async def stop_all(self):
        """Stop all heartbeat tasks"""
        for session_id, task in list(self.heartbeat_tasks.items()):
            if not task.done():
                task.cancel()
                
        # Wait for all tasks to complete
        if self.heartbeat_tasks:
            await asyncio.gather(*self.heartbeat_tasks.values(), return_exceptions=True)
        self.heartbeat_tasks.clear()
        
    async def _heartbeat_loop(self, session_id, websocket):
        """Send periodic heartbeat messages to a client"""
        try:
            while True:
                try:
                    message = {
                        "type": "heartbeat",
                        "session_id": session_id,
                        "timestamp": time.time()
                    }
                    await websocket.send(json.dumps(message))
                    
                except Exception as e:
                    self.logger.error(f"Error sending heartbeat: {e}")
                    break
                    
                # Wait for the next interval
                await asyncio.sleep(self.heartbeat_interval)
                
        except asyncio.CancelledError:
            # Task was cancelled normally
            pass
        except Exception as e:
            self.logger.error(f"Error in heartbeat loop: {e}")


class ErrorHandler:
    """Handles errors with configurable recovery strategies"""
    
    # Error type constants
    WEBSOCKET_ERROR = "websocket_error"
    STT_ERROR = "stt_error"
    TTS_ERROR = "tts_error"
    LLM_ERROR = "llm_error"
    PIPELINE_ERROR = "pipeline_error"
    
    def __init__(self):
        self.logger = logging.getLogger("error_handler")
        self.recovery_handlers = {}
        
    def register_recovery_handler(self, error_type, handler):
        """Register a handler for a specific error type"""
        self.recovery_handlers[error_type] = handler
        
    async def handle_error(self, error_type, session_id, exception, context=None):
        """Handle an error with the appropriate recovery strategy"""
        if context is None:
            context = {}
            
        self.logger.error(f"Handling {error_type} for session {session_id}: {exception}")
        
        # Get the appropriate handler for this error type
        handler = self.recovery_handlers.get(error_type)
        if handler:
            try:
                await handler(session_id, exception, context)
            except Exception as e:
                self.logger.error(f"Error in recovery handler: {e}")
        else:
            self.logger.warning(f"No handler registered for error type: {error_type}")
