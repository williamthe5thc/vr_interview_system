#!/usr/bin/env python3
import asyncio
import json
import logging
import signal
import sys
import os
from pathlib import Path

from app.websocket.server import WebSocketServer, HeartbeatService
from app.state.manager import StateManager
from services.audio.stt import STTService
from services.audio.tts import TTSService
from services.llm.ollama_client import OllamaClient
from app.utils.logging import setup_logging
from app.utils.config import load_config
from app.error_handler import ErrorHandler


class Server:
    def __init__(self):
        # Load configuration
        self.config = load_config()
        
        # Setup logging
        setup_logging(self.config["server"].get("log_level", "INFO"))
        self.logger = logging.getLogger("server")
        
        # Create directories if they don't exist
        self._setup_directories()
        
        # Initialize components
        self.state_manager = StateManager()
        self.stt_service = STTService(self.config["audio"]["stt_model"])
        self.tts_service = TTSService(self.config["audio"]["tts_model"])
        self.llm_client = OllamaClient(
            self.config["ollama"]["url"],
            self.config["ollama"]["model"],
            self.config["ollama"]["context_length"]
        )
        
        # Initialize support services
        self.error_handler = ErrorHandler()
        self.heartbeat_service = HeartbeatService(
            heartbeat_interval=self.config.get("heartbeat_interval", 5.0)
        )
        
        # Register error recovery handlers
        self._register_error_handlers()
        
        # Initialize WebSocket server with references to other components
        self.websocket_server = WebSocketServer(
            self.config["server"]["host"],
            self.config["server"]["port"],
            self.state_manager,
            self.stt_service,
            self.tts_service,
            self.llm_client,
            self.error_handler,
            self.heartbeat_service
        )
        
        # Setup signal handlers
        self._setup_signal_handlers()
        
        self.logger.info("Server initialized")

    def _setup_directories(self):
        """Create necessary directories for data storage"""
        Path(self.config["storage"]["audio_dir"]).mkdir(parents=True, exist_ok=True)
        Path(self.config["storage"]["conversation_dir"]).mkdir(parents=True, exist_ok=True)
        Path(f"{self.config['storage']['audio_dir']}/uploads").mkdir(parents=True, exist_ok=True)
        Path(f"{self.config['storage']['audio_dir']}/responses").mkdir(parents=True, exist_ok=True)

    def _setup_signal_handlers(self):
        """Setup handlers for graceful shutdown"""
        # Simple signal handling that works on both Windows and Unix
        try:
            # Register for SIGINT (Ctrl+C)
            signal.signal(signal.SIGINT, self._signal_handler)
            # Register for SIGTERM if available
            if hasattr(signal, 'SIGTERM'):
                signal.signal(signal.SIGTERM, self._signal_handler)
            self.logger.info("Signal handlers registered")
        except Exception as e:
            self.logger.warning(f"Could not set up signal handlers: {e}")
            
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
        
    async def _handle_llm_error(self, session_id, exception, context):
        """Handle errors in LLM processing"""
        try:
            # Log the detailed error
            self.logger.error(f"LLM error recovery for {session_id}: {exception}")
            
            # Transition to WAITING state to prepare for next input
            await self.state_manager.transition_state(session_id, "WAITING", {
                "message": "Ready for next question",
                "error": "Interview system needed to reset"
            })
            
            # Send fallback response directly if possible
            if "websocket" in context:
                websocket = context["websocket"]
                fallback_message = {
                    "type": "system_message",
                    "message": "I had a bit of trouble with that response. Let's continue with the interview."
                }
                await websocket.send(json.dumps(fallback_message))
                
        except Exception as e:
            self.logger.error(f"Error during LLM error recovery: {e}")
            
    async def _handle_stt_error(self, session_id, exception, context):
        """Handle errors in speech-to-text processing"""
        try:
            # Transition to WAITING state
            await self.state_manager.transition_state(session_id, "WAITING", {
                "message": "Speech recognition error, please try again"
            })
            
        except Exception as e:
            self.logger.error(f"Error during STT error recovery: {e}")
            
    async def _handle_tts_error(self, session_id, exception, context):
        """Handle errors in text-to-speech processing"""
        try:
            # If we have the text response, send it directly as a fallback
            text_response = context.get("text_response")
            if text_response and "websocket" in context:
                websocket = context["websocket"]
                fallback_message = {
                    "type": "text_response",
                    "text": text_response,
                    "message": "Audio couldn't be generated. Displaying text instead."
                }
                await websocket.send(json.dumps(fallback_message))
                
            # Transition to WAITING state
            await self.state_manager.transition_state(session_id, "WAITING", {
                "message": "Ready for next question"
            })
            
        except Exception as e:
            self.logger.error(f"Error during TTS error recovery: {e}")
            
    async def _handle_websocket_error(self, session_id, exception, context):
        """Handle WebSocket connection errors"""
        try:
            self.logger.warning(f"WebSocket error for {session_id}. Scheduling cleanup.")
            # Schedule session cleanup after a delay
            asyncio.get_event_loop().call_later(
                30, 
                lambda: asyncio.create_task(self.state_manager.end_session(session_id))
            )
            
        except Exception as e:
            self.logger.error(f"Error during WebSocket error recovery: {e}")
            
    def _signal_handler(self, sig, frame):
        """Handle termination signals"""
        self.logger.info(f"Received signal {sig}, initiating shutdown...")
        # Just exit cleanly - we can't do much else in a signal handler on Windows
        self.logger.info("Exiting...")
        os._exit(0)
        
    async def _shutdown(self):
        """Gracefully shutdown the server - used by internal logic, not signals"""
        self.logger.info("Shutting down...")
        # Stop heartbeat service
        await self.heartbeat_service.stop_all()
        # Close WebSocket server
        await self.websocket_server.shutdown()
        # Cleanup other resources
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        [task.cancel() for task in tasks]
        await asyncio.gather(*tasks, return_exceptions=True)
        asyncio.get_event_loop().stop()
        self.logger.info("Shutdown complete")

    async def start(self):
        """Start the server and all its components"""
        self.logger.info(f"Starting server on {self.config['server']['host']}:{self.config['server']['port']}")
        try:
            await self.websocket_server.start()
        except Exception as e:
            self.logger.error(f"Failed to start server: {e}")
            await self._shutdown()


if __name__ == "__main__":
    # Create and run the server
    server = Server()
    
    # Different approach based on platform
    if sys.platform == 'win32':
        # On Windows, we need a slightly different approach
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(server.start())
            loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            loop.close()
    else:
        # On Unix platforms, asyncio.run works fine
        asyncio.run(server.start())
