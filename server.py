#!/usr/bin/env python3
import asyncio
import json
import logging
import signal
import sys
import os
from pathlib import Path

from app.websocket.server import WebSocketServer
from app.state.manager import StateManager
from services.audio.stt import STTService
from services.audio.tts import TTSService
from services.llm.ollama_client import OllamaClient
from app.utils.logging import setup_logging
from app.utils.config import load_config


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
        
        # Initialize WebSocket server with references to other components
        self.websocket_server = WebSocketServer(
            self.config["server"]["host"],
            self.config["server"]["port"],
            self.state_manager,
            self.stt_service,
            self.tts_service,
            self.llm_client
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
            
    def _signal_handler(self, sig, frame):
        """Handle termination signals"""
        self.logger.info(f"Received signal {sig}, initiating shutdown...")
        # Just exit cleanly - we can't do much else in a signal handler on Windows
        self.logger.info("Exiting...")
        os._exit(0)
        
    async def _shutdown(self):
        """Gracefully shutdown the server - used by internal logic, not signals"""
        self.logger.info("Shutting down...")
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
