import logging


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
