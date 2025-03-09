import asyncio
import logging
import time
import json
from enum import Enum, auto


class States(Enum):
    """Enumeration of possible states for the conversation"""
    IDLE = auto()
    LISTENING = auto()
    PROCESSING = auto()
    RESPONDING = auto()
    WAITING = auto()
    ERROR = auto()


class StateManager:
    """
    Manages the state machine for conversation sessions.
    
    This class handles state transitions and ensures they follow the defined flow:
    IDLE → LISTENING → PROCESSING → RESPONDING → WAITING → (repeat)
    
    It also handles broadcasting state changes to connected clients.
    """
    
    def __init__(self):
        self.sessions = {}
        self.logger = logging.getLogger("state_manager")
        self._state_locks = {}  # Locks to prevent race conditions in state transitions
        
    def create_session(self, session_id, session):
        """Initialize a new session with IDLE state"""
        self.sessions[session_id] = session
        self._state_locks[session_id] = asyncio.Lock()
        self.logger.info(f"Created new session: {session_id}")
        
    def end_session(self, session_id):
        """Clean up session resources"""
        if session_id in self.sessions:
            del self.sessions[session_id]
        if session_id in self._state_locks:
            del self._state_locks[session_id]
        self.logger.info(f"Ended session: {session_id}")
        
    def get_session(self, session_id):
        """Get the session object for a session ID"""
        return self.sessions.get(session_id)
        
    def get_session_state(self, session_id):
        """Get the current state name for a session"""
        session = self.sessions.get(session_id)
        if not session:
            return None
        return session.state
        
    async def transition_state(self, session_id, new_state, metadata=None):
        """
        Transition session to a new state and broadcast the change.
        
        Uses locks to prevent race conditions in state transitions.
        """
        if session_id not in self.sessions:
            self.logger.error(f"Cannot transition state for unknown session: {session_id}")
            return False
            
        # Acquire lock to prevent concurrent state transitions
        async with self._state_locks[session_id]:
            session = self.sessions[session_id]
            previous_state = session.state
            
            # Validate the state transition
            if not self._is_valid_transition(previous_state, new_state):
                self.logger.warning(
                    f"Invalid state transition: {previous_state} → {new_state}"
                )
                return False
                
            # Update the session state
            session.state = new_state
            session.last_updated = time.time()
            
            # Add metadata if provided
            if metadata:
                session.metadata.update(metadata)
                
            self.logger.info(f"State transition: {session_id}: {previous_state} to {new_state}")
            
            # Broadcast state change
            await self._broadcast_state_change(session_id, previous_state, new_state, metadata)
            
            return True
            
    def _is_valid_transition(self, current, next_state):
        """
        Validate that a state transition follows the allowed flow.
        
        Valid transitions:
        - IDLE → LISTENING
        - LISTENING → PROCESSING
        - PROCESSING → RESPONDING
        - RESPONDING → WAITING
        - WAITING → LISTENING
        - Any state → ERROR
        - ERROR → IDLE (recovery)
        - Control messages can reset to IDLE from any state
        """
        # Allow resetting to IDLE from any state
        if next_state == "IDLE":
            return True
            
        # Any state can transition to ERROR
        if next_state == "ERROR":
            return True
            
        # Handle the normal flow
        valid_transitions = {
            "IDLE": ["LISTENING"],
            "LISTENING": ["PROCESSING"],
            "PROCESSING": ["RESPONDING", "PROCESSING"],  # Allow updates during processing
            "RESPONDING": ["WAITING"],
            "WAITING": ["LISTENING"],
            "ERROR": ["IDLE"]  # Recovery from error
        }
        
        return next_state in valid_transitions.get(current, [])
        
    async def _broadcast_state_change(self, session_id, previous, current, metadata):
        """Broadcast state change to the client"""
        session = self.sessions.get(session_id)
        if not session or not session.websocket:
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
