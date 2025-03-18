"""
WebSocket Timeout Extender for VR Interview System.

This module extends the timeouts for LLM processing and implements progressive updates
during long operations.
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, Optional, List, Callable
import base64

class WebSocketTimeoutExtender:
    """
    Enhances the WebSocket server to support extended timeouts and progressive updates.
    
    This is a non-invasive solution that can be added to the existing system without
    significant changes to the core architecture.
    """
    
    def __init__(self, websocket_server=None, logger=None):
        """Initialize the timeout extender."""
        self.websocket_server = websocket_server
        self.logger = logger or logging.getLogger("timeout_extender")
        self.active_tasks = {}  # session_id -> task
        
        self.logger.info("WebSocket Timeout Extender initialized")
    
    def register_with_server(self, websocket_server):
        """Register this extender with the WebSocket server."""
        self.websocket_server = websocket_server
        self.logger.info("Registered with WebSocket server")
    
    async def extend_timeout(self, session_id: str, websocket, timeout: float = 45.0,
                            task_type: str = "LLM", original_task = None):
        """
        Extend a timeout for a long-running operation.
        
        Args:
            session_id: Session identifier
            websocket: WebSocket connection
            timeout: Timeout in seconds (default: 45.0)
            task_type: Type of task (LLM, TTS, etc.)
            original_task: The original task to monitor
        
        Returns:
            True if successful, False otherwise
        """
        if session_id in self.active_tasks:
            self.logger.warning(f"Session {session_id} already has an active task")
            return False
        
        # Create a task to send progress updates
        update_task = asyncio.create_task(
            self._send_progress_updates(session_id, websocket, task_type)
        )
        
        # Store the task for cleanup
        self.active_tasks[session_id] = update_task
        
        try:
            # Wait for the original task or timeout
            if original_task:
                try:
                    # Wait with extended timeout
                    await asyncio.wait_for(original_task, timeout=timeout)
                    self.logger.info(f"{task_type} task completed within extended timeout")
                    return True
                except asyncio.TimeoutError:
                    self.logger.warning(f"{task_type} task timed out after extended timeout of {timeout}s")
                    
                    # We'll let the original task continue in the background
                    # and handle the result when it completes
                    if not original_task.done():
                        asyncio.create_task(
                            self._handle_delayed_completion(session_id, websocket, original_task, task_type)
                        )
                    return False
            else:
                # Just run the progress updates for the specified timeout
                await asyncio.sleep(timeout)
                return True
                
        finally:
            # Clean up the update task
            if session_id in self.active_tasks:
                update_task = self.active_tasks.pop(session_id)
                if not update_task.done():
                    update_task.cancel()
    
    async def _send_progress_updates(self, session_id: str, websocket, task_type: str):
        """Send progress updates during long-running operations."""
        # Different messages based on task type
        if task_type == "LLM":
            messages = [
                "I'm thinking about your question...",
                "Still processing your question...",
                "This is a complex question, giving it some thought...",
                "Almost ready with a response...",
                "Finalizing my thoughts on this..."
            ]
        elif task_type == "TTS":
            messages = [
                "Generating speech...",
                "Converting text to speech...",
                "Preparing audio response...",
                "Almost ready with the audio...",
                "Finalizing the audio response..."
            ]
        else:
            messages = [
                "Processing your request...",
                "Working on it...",
                "Almost ready...",
                "Finalizing the response..."
            ]
        
        try:
            # Send updates every 5 seconds
            for i in range(60):  # Maximum of 5 minutes
                await asyncio.sleep(5.0)
                
                if not websocket:
                    self.logger.warning(f"WebSocket connection lost during progress updates for {session_id}")
                    return
                
                # Create update message
                update_message = {
                    "type": "progress_update",
                    "session_id": session_id,
                    "timestamp": time.time(),
                    "message": messages[i % len(messages)]
                }
                
                # Send the update
                try:
                    await websocket.send(json.dumps(update_message))
                    self.logger.debug(f"Sent progress update to {session_id}: {update_message['message']}")
                except Exception as e:
                    self.logger.error(f"Error sending progress update: {e}")
                    return
        except asyncio.CancelledError:
            # Task was cancelled (normal)
            pass
        except Exception as e:
            self.logger.error(f"Error in progress updates: {e}")
    
    async def _handle_delayed_completion(self, session_id: str, websocket, task, task_type: str):
        """Handle delayed completion of a long-running task."""
        try:
            # Wait for the task to complete (no timeout)
            result = await task
            
            self.logger.info(f"Delayed {task_type} task completed for {session_id}")
            
            if not websocket:
                self.logger.warning(f"WebSocket connection lost during delayed completion for {session_id}")
                return
                
            # Handle the result based on task type
            if task_type == "LLM":
                # Send a notification about the delayed completion
                notification = {
                    "type": "system_message",
                    "session_id": session_id,
                    "timestamp": time.time(),
                    "message": "Delayed response received"
                }
                
                # Send the notification
                try:
                    await websocket.send(json.dumps(notification))
                except Exception as e:
                    self.logger.error(f"Error sending delayed notification: {e}")
                
                # Send the actual response if we have one
                if result:
                    response = {
                        "type": "transcript_update",
                        "session_id": session_id,
                        "timestamp": time.time(),
                        "transcript": result,
                        "source": "llm",
                        "delayed": True
                    }
                    
                    try:
                        await websocket.send(json.dumps(response))
                    except Exception as e:
                        self.logger.error(f"Error sending delayed response: {e}")
            
            # Other task types can be handled similarly
            
        except Exception as e:
            self.logger.error(f"Error handling delayed completion: {e}")
