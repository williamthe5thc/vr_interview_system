"""
Create the EnhancedStreamProcessor class file if it doesn't exist.
This file will ensure the server has all required dependencies.
"""

import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("setup")

# Define the target file path
target_file = "app/websocket/enhanced_stream_processor.py"

# Check if the file already exists
if os.path.exists(target_file):
    logger.info(f"File {target_file} already exists. No need to create it.")
else:
    logger.info(f"Creating {target_file} with simplified StreamProcessor implementation...")
    
    # Make sure the directory exists
    os.makedirs(os.path.dirname(target_file), exist_ok=True)
    
    # The content for the file
    content = """\"\"\"
Enhanced Stream Processor for VR Interview System.

This module provides optimized processing of audio data with direct API
capabilities for better user experience.
\"\"\"

import asyncio
import json
import logging
import time
from typing import Dict, Any, Optional, List, Callable
import base64
import os
import io

class EnhancedStreamProcessor:
    \"\"\"
    Enhanced stream processor with optimized processing pipeline.
    
    Features:
    - Multi-stage parallel processing
    - Optimized direct audio generation
    - Intelligent caching for frequently used responses
    - Advanced error handling and recovery
    \"\"\"
    
    def __init__(
        self,
        state_manager,
        stt_service,
        tts_service,
        llm_client,
        error_handler=None
    ):
        self.state_manager = state_manager
        self.stt_service = stt_service
        self.tts_service = tts_service
        self.llm_client = llm_client
        self.error_handler = error_handler
        self.logger = logging.getLogger("enhanced_stream")
        
        # Initialize cache
        self.cache_dir = "data/cache/stream"
        os.makedirs(self.cache_dir, exist_ok=True)
        self.audio_chunks_cache = {}
        
        self.logger.info("Enhanced Stream Processor initialized")
    
    async def process_streaming_audio_pipeline(
        self,
        session_id: str,
        audio_data: bytes,
        websocket
    ):
        \"\"\"
        Process audio with optimized pipeline.
        
        Args:
            session_id: Session identifier
            audio_data: Raw audio data
            websocket: WebSocket connection for sending responses
        \"\"\"
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
                self.logger.warning(f"STT timeout for session {session_id}")
                if self.error_handler:
                    await self.error_handler.handle_error(
                        "STT_ERROR",
                        session_id,
                        Exception("Speech transcription timed out"),
                        {"websocket": websocket}
                    )
                return
            
            # Check transcript result
            self.logger.info(f"Transcription: {transcript}")
            if not transcript.strip():
                await self.state_manager.transition_state(session_id, "WAITING", {
                    "message": "No speech detected, please try again"
                })
                return
            
            # 2. Update state and prepare for LLM processing
            await self.state_manager.transition_state(session_id, "PROCESSING", {
                "message": "Generating response",
                "transcript": transcript
            })
            
            # Get session context
            session = self.state_manager.get_session(session_id)
            if not session:
                self.logger.error(f"Session {session_id} not found")
                return
                
            context = session.get_context()
            
            # Determine interaction stage from metadata
            metadata = {}
            if hasattr(session, "metadata"):
                metadata = session.metadata.copy() if session.metadata else {}
                
            interaction_stage = metadata.get("stage", None)
            
            # If no explicit stage, try to infer it
            if not interaction_stage:
                if not context or len(context) <= 1:
                    interaction_stage = "introduction"
                elif len(context) > 10:
                    interaction_stage = "conclusion"
                else:
                    interaction_stage = "behavioral_assessment"
            
            # 3. Start TTS prewarming in parallel with LLM generation
            tts_prewarm_task = asyncio.create_task(self._prewarm_tts())
            tasks.append(tts_prewarm_task)
            
            # 4. Generate LLM response
            try:
                progress_callback = None  # No streaming progress in direct mode
                
                llm_future = asyncio.create_task(
                    asyncio.to_thread(
                        self.llm_client.generate_response,
                        transcript,
                        context,
                        None,  # default timeout
                        None,  # default retries
                        interaction_stage
                    )
                )
                tasks.append(llm_future)
                
                # Add a timeout for LLM processing
                response = await asyncio.wait_for(llm_future, timeout=12.0)
                
                # Remove completed task
                if llm_future in tasks:
                    tasks.remove(llm_future)
            except asyncio.TimeoutError:
                self.logger.warning(f"LLM timeout for session {session_id}")
                if self.error_handler:
                    await self.error_handler.handle_error(
                        "LLM_ERROR",
                        session_id,
                        Exception("LLM response generation timed out"),
                        {"websocket": websocket, "transcript": transcript}
                    )
                return
            
            # Add the exchange to session history
            session.add_interaction(transcript, response)
            
            # 5. Generate speech using direct API
            await self.state_manager.transition_state(session_id, "PROCESSING", {
                "message": "Converting response to speech"
            })
            
            # Use direct TTS processing
            await self._generate_standard_tts(session_id, response, websocket)
                
        except asyncio.CancelledError:
            # Handle cancellation
            self.logger.info(f"Pipeline cancelled for {session_id}")
            
            # Cancel all running tasks
            for task in tasks:
                if not task.done():
                    task.cancel()
                    
            # Always try to return to WAITING state
            try:
                await self.state_manager.transition_state(session_id, "WAITING", {
                    "message": "Processing cancelled"
                })
            except Exception:
                pass
                
        except Exception as e:
            self.logger.error(f"Error in pipeline: {e}")
            
            # Cancel all running tasks
            for task in tasks:
                if not task.done():
                    task.cancel()
                    
            # Try to use error handler
            if self.error_handler:
                await self.error_handler.handle_error(
                    "SYSTEM_ERROR",
                    session_id,
                    e,
                    {"websocket": websocket}
                )
            
            # Always try to get back to WAITING state
            try:
                await self.state_manager.transition_state(session_id, "WAITING", {
                    "message": "Ready for next input after error"
                })
            except Exception:
                pass
    
    # Streaming TTS methods removed - using only direct API
    
    async def _generate_standard_tts(self, session_id: str, text: str, websocket) -> None:
        \"\"\"
        Generate TTS response using standard (non-streaming) approach.
        
        Args:
            session_id: Session identifier
            text: Text to synthesize
            websocket: WebSocket connection
        \"\"\"
        try:
            # Generate speech with timeout
            tts_future = asyncio.create_task(
                asyncio.to_thread(self.tts_service.synthesize, text)
            )
            
            # Add timeout to prevent hanging
            audio_response = await asyncio.wait_for(tts_future, timeout=8.0)
            
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
            self.logger.warning(f"TTS timeout for session {session_id}")
            
            # Send text-only response as fallback
            fallback_message = {
                "type": "text_response",
                "session_id": session_id,
                "timestamp": time.time(),
                "text": text,
                "message": "Audio conversion timed out, showing text instead"
            }
            
            try:
                await websocket.send(json.dumps(fallback_message))
                
                # Update state
                await self.state_manager.transition_state(session_id, "WAITING", {
                    "message": "Waiting for user input after fallback"
                })
            except Exception as e:
                self.logger.error(f"Error sending fallback message: {e}")
                
        except Exception as e:
            self.logger.error(f"Error in standard TTS: {e}")
            
            # Try to send text-only response
            try:
                text_message = {
                    "type": "text_response",
                    "session_id": session_id,
                    "timestamp": time.time(),
                    "text": text,
                    "message": "Audio generation failed, showing text instead"
                }
                
                await websocket.send(json.dumps(text_message))
                
                # Update state
                await self.state_manager.transition_state(session_id, "WAITING", {
                    "message": "Waiting for user input after error"
                })
            except Exception as text_error:
                self.logger.error(f"Failed to send text fallback: {text_error}")
    
    async def _prewarm_tts(self) -> bool:
        \"\"\"
        Prewarm TTS engine to reduce cold-start latency.
        
        Returns:
            True if successful, False otherwise
        \"\"\"
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
"""
    
    # Write the file
    with open(target_file, 'w') as f:
        f.write(content)
    
    logger.info(f"Created {target_file} successfully.")

logger.info("Setup complete!")
