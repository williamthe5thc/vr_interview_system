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
    def __init__(self, host, port, state_manager, stt_service, tts_service, llm_client):
        self.host = host
        self.port = port
        self.state_manager = state_manager
        self.stt_service = stt_service
        self.tts_service = tts_service
        self.llm_client = llm_client
        self.server = None
        self.active_connections = {}
        self.logger = logging.getLogger("websocket")
        
        # Task pool for managing async operations
        self.tasks = set()

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
                # Add task to the set to keep a reference to it
                self.tasks.add(task)
                # Remove task from set when it completes
                task.add_done_callback(self.tasks.remove)
                
        except ConnectionClosed:
            self.logger.info(f"Connection closed: {session_id}")
        except Exception as e:
            self.logger.error(f"Error in connection handler: {e}")
        finally:
            # Clean up session
            if session_id in self.active_connections:
                del self.active_connections[session_id]
            self.state_manager.end_session(session_id)

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
            # Transition to ERROR state
            await self.state_manager.transition_state(session_id, "ERROR", {
                "error": str(e)
            })

    async def process_audio(self, session_id, message):
        """
        Process incoming audio data.
        This is where we need to carefully manage async operations to prevent blocking.
        """
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
                
            # Process audio asynchronously
            # This starts the non-blocking pipeline
            asyncio.create_task(self.process_audio_pipeline(session_id, audio_data))
            
        except Exception as e:
            self.logger.error(f"Error processing audio: {e}")
            await self.send_error(session_id, 500, "Error processing audio")
            await self.state_manager.transition_state(session_id, "ERROR", {
                "error": str(e)
            })

    async def process_audio_pipeline(self, session_id, audio_data):
        """
        Full audio processing pipeline - runs asynchronously to avoid blocking the WebSocket.
        This is the key to preventing LLM processing from blocking other operations.
        """
        try:
            # Save audio (non-blocking I/O)
            # In a real implementation, you would save the audio to disk
            
            # Transition to PROCESSING
            await self.state_manager.transition_state(session_id, "PROCESSING", {
                "message": "Transcribing audio"
            })
            
            # Transcribe audio (could be CPU intensive)
            # Run in a separate thread pool to prevent blocking
            transcript = await asyncio.to_thread(
                self.stt_service.transcribe,
                audio_data
            )
            
            self.logger.info(f"Transcription: {transcript}")
            
            # Get the current session and its conversation history
            session = self.state_manager.get_session(session_id)
            if not session:
                self.logger.error(f"Session {session_id} not found")
                return
                
            # Update state with transcription info
            await self.state_manager.transition_state(session_id, "PROCESSING", {
                "message": "Generating response",
                "transcript": transcript
            })
            
            # Generate LLM response (blocking operation)
            # Run in a separate thread pool to avoid blocking the event loop
            response = await asyncio.to_thread(
                self.llm_client.generate_response,
                transcript,
                session.get_context()
            )
            
            # Add the exchange to session history
            session.add_interaction(transcript, response)
            
            self.logger.info(f"LLM Response: {response}")
            
            # Update state with response generation info
            await self.state_manager.transition_state(session_id, "PROCESSING", {
                "message": "Converting response to speech"
            })
            
            # Generate speech (could be CPU intensive)
            # Run in a separate thread pool
            audio_response = await asyncio.to_thread(
                self.tts_service.synthesize,
                response
            )
            
            # Transition to RESPONDING
            await self.state_manager.transition_state(session_id, "RESPONDING", {
                "message": "Playing response"
            })
            
            # Send audio response to client
            await self.send_audio_response(session_id, audio_response)
            
            # Wait a moment to ensure audio is received before state change
            await asyncio.sleep(0.5)
            
            # Transition to WAITING for next user input
            await self.state_manager.transition_state(session_id, "WAITING", {
                "message": "Waiting for user input"
            })
            
        except Exception as e:
            self.logger.error(f"Error in audio pipeline: {e}")
            await self.state_manager.transition_state(session_id, "ERROR", {
                "error": str(e)
            })
            await self.send_error(session_id, 500, "Error processing request")

    async def process_control(self, session_id, message):
        """Process control messages from client"""
        action = message.get("action")
        if action == "reset":
            # Reset the conversation
            session = self.state_manager.get_session(session_id)
            if session:
                session.reset()
                await self.state_manager.transition_state(session_id, "IDLE", {
                    "message": "Conversation reset"
                })
        elif action == "stop":
            # Stop the current response
            current_state = self.state_manager.get_session_state(session_id)
            if current_state == "RESPONDING":
                await self.state_manager.transition_state(session_id, "WAITING", {
                    "message": "Response stopped"
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
