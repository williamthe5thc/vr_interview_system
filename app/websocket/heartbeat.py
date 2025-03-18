import asyncio
import json
import logging
import time


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
