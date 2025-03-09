import json
import logging

logger = logging.getLogger("protocol")

def encode_message(message):
    """
    Encode a message dictionary to a JSON string for sending over WebSocket
    
    Args:
        message (dict): The message to encode
        
    Returns:
        str: JSON encoded message
    """
    try:
        return json.dumps(message)
    except Exception as e:
        logger.error(f"Error encoding message: {e}")
        return json.dumps({
            "type": "error",
            "message": "Error encoding message"
        })

def decode_message(raw_message):
    """
    Decode a raw WebSocket message to a dictionary
    
    Args:
        raw_message (str): The raw message from WebSocket
        
    Returns:
        dict: Decoded message as dictionary
        
    Raises:
        ValueError: If message cannot be decoded as JSON
    """
    try:
        if isinstance(raw_message, bytes):
            # Binary message, likely raw audio
            return {
                "type": "audio_data",
                "data": raw_message
            }
        else:
            # Text message, should be JSON
            return json.loads(raw_message)
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding message: {e}")
        raise ValueError(f"Invalid JSON message: {e}")

def validate_message(message):
    """
    Validate that a message has the required fields and structure
    
    Args:
        message (dict): The message to validate
        
    Returns:
        bool: True if message is valid, False otherwise
    """
    if not isinstance(message, dict):
        logger.error(f"Message is not a dictionary: {type(message)}")
        return False
        
    # All messages must have a type
    if "type" not in message:
        logger.error("Message missing required 'type' field")
        return False
        
    # Validate different message types
    msg_type = message.get("type")
    
    if msg_type == "audio_data":
        # Audio data must have data field
        if "data" not in message:
            logger.error("Audio message missing 'data' field")
            return False
    elif msg_type == "ping":
        # Ping is always valid
        pass
    elif msg_type == "control":
        # Control messages must have an action
        if "action" not in message:
            logger.error("Control message missing 'action' field")
            return False
        if message["action"] not in ["start", "stop", "reset"]:
            logger.error(f"Invalid control action: {message['action']}")
            return False
    else:
        # Unknown message type
        logger.warning(f"Unknown message type: {msg_type}")
        return False
        
    return True
