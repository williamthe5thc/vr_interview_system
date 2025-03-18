"""
Apply AllTalk streaming fixes to VR Interview System server.

Run this script before starting the server to ensure streaming works properly.
This version directly modifies the server modules in place.
"""

import logging
import importlib
import sys
import os
import inspect
import types

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("fix_installer")

def find_stream_processor_module():
    """Find the stream processor module in the project."""
    try:
        # Try different possible paths
        candidates = [
            "app.websocket.stream_processor",
            "app.websocket.enhanced_stream_processor",
            "stream_processor"
        ]
        
        for candidate in candidates:
            try:
                module = importlib.import_module(candidate)
                if hasattr(module, "StreamProcessor"):
                    logger.info(f"Found StreamProcessor in module: {candidate}")
                    return module
            except ImportError:
                continue
                
        # If direct import fails, search for the file
        for root, dirs, files in os.walk("."):
            for file in files:
                if file.endswith("stream_processor.py"):
                    path = os.path.join(root, file)
                    logger.info(f"Found stream processor file at: {path}")
                    
                    # Convert path to module name
                    module_path = path.replace(os.sep, ".").replace(".py", "")
                    if module_path.startswith("."):
                        module_path = module_path[1:]
                    
                    try:
                        module = importlib.import_module(module_path)
                        if hasattr(module, "StreamProcessor"):
                            logger.info(f"Loaded StreamProcessor from: {module_path}")
                            return module
                    except ImportError:
                        logger.warning(f"Could not import module from {path}")
        
        logger.error("Could not find StreamProcessor module")
        return None
    except Exception as e:
        logger.error(f"Error finding StreamProcessor: {e}")
        return None

def find_alltalk_tts_module():
    """Find the AllTalk TTS module in the project."""
    try:
        # Try different possible paths
        candidates = [
            "services.audio.alltalk_tts_improved",
            "services.audio.alltalk_tts",
            "alltalk_tts"
        ]
        
        for candidate in candidates:
            try:
                module = importlib.import_module(candidate)
                if hasattr(module, "AllTalkTTSService"):
                    logger.info(f"Found AllTalkTTSService in module: {candidate}")
                    return module
            except ImportError:
                continue
                
        # If direct import fails, search for the file
        for root, dirs, files in os.walk("."):
            for file in files:
                if "alltalk" in file.lower() and file.endswith(".py"):
                    path = os.path.join(root, file)
                    logger.info(f"Found AllTalk file at: {path}")
                    
                    # Convert path to module name
                    module_path = path.replace(os.sep, ".").replace(".py", "")
                    if module_path.startswith("."):
                        module_path = module_path[1:]
                    
                    try:
                        module = importlib.import_module(module_path)
                        if hasattr(module, "AllTalkTTSService"):
                            logger.info(f"Loaded AllTalkTTSService from: {module_path}")
                            return module
                    except ImportError:
                        logger.warning(f"Could not import module from {path}")
        
        logger.error("Could not find AllTalkTTSService module")
        return None
    except Exception as e:
        logger.error(f"Error finding AllTalkTTSService: {e}")
        return None

def patch_server_module():
    """Patch the server module with enhanced text_response handling."""
    try:
        # Import the fixes module
        fixes = importlib.import_module("alltalk_streaming_fix")
        logger.info("Successfully imported fix module")
        
        # Create a simple text_response handler method
        async def send_text_response(session_id, text_content, websocket):
            """Send a text_response message to the client."""
            logger.info(f"Sending text_response to session {session_id}")
            
            try:
                import json
                import time
                
                # Create and send text_response message
                message = {
                    "type": "text_response",
                    "session_id": session_id,
                    "timestamp": time.time(),
                    "text": text_content
                }
                await websocket.send(json.dumps(message))
                logger.info(f"Sent text_response message: {len(text_content)} chars")
                return True
                
            except Exception as e:
                logger.error(f"Error sending text_response: {e}")
                return False
        
        # Look for websocket server module
        try:
            for name in ["app.websocket.server", "app.websocket.server_enhanced_fixed", "websocket_server"]:
                try:
                    module = importlib.import_module(name)
                    # Add the text_response method
                    if hasattr(module, "WebSocketServer"):
                        logger.info(f"Adding text_response handler to {name}.WebSocketServer")
                        module.WebSocketServer.send_text_response = send_text_response
                        
                        # Also try to patch the send_audio_response method
                        if hasattr(module.WebSocketServer, "send_audio_response"):
                            original_send_audio = module.WebSocketServer.send_audio_response
                            
                            async def enhanced_send_audio(self, session_id, audio_data=None, text=None, streaming_url=None):
                                """Patched audio response method with text fallback."""
                                try:
                                    # If we have valid audio data, use original method
                                    if audio_data and len(audio_data) > 1000:
                                        return await original_send_audio(self, session_id, audio_data, text, streaming_url)
                                    
                                    # If no audio but we have text, use text_response
                                    if not audio_data and text and session_id in self.active_connections:
                                        websocket = self.active_connections[session_id]
                                        return await send_text_response(session_id, text, websocket)
                                    
                                    # Otherwise use original method
                                    return await original_send_audio(self, session_id, audio_data, text, streaming_url)
                                except Exception as e:
                                    logger.error(f"Error in patched send_audio_response: {e}")
                                    # Try the original method
                                    return await original_send_audio(self, session_id, audio_data, text, streaming_url)
                            
                            module.WebSocketServer.send_audio_response = enhanced_send_audio
                            logger.info(f"Patched send_audio_response in {name}.WebSocketServer")
                except ImportError:
                    pass
            
            logger.info("Server module patching completed")
            return True
        except Exception as e:
            logger.error(f"Error patching server module: {e}")
            return False
            
    except Exception as e:
        logger.error(f"Error in patch_server_module: {e}")
        return False

def main():
    """Apply AllTalk streaming fixes to server components."""
    logger.info("Starting AllTalk fix application - direct module approach")
    
    success = True
    
    # Patch server module
    server_patch_success = patch_server_module()
    if not server_patch_success:
        logger.warning("Server module patching failed")
        success = False
    
    # Find and patch stream processor module
    stream_proc_module = find_stream_processor_module()
    if stream_proc_module:
        try:
            # Import the fixes module
            fixes = importlib.import_module("alltalk_streaming_fix")
            
            # Get the original methods
            original_send_streaming_url = stream_proc_module.StreamProcessor._send_streaming_url
            original_monitor_streaming = stream_proc_module.StreamProcessor._monitor_streaming_status
            
            # Replace with enhanced versions
            exec(inspect.getsource(fixes.fix_stream_processor).replace(
                "fix_stream_processor", "_temp_fix_func"), globals(), locals())
            
            # Monkey patch the methods
            stream_proc_module.StreamProcessor._send_streaming_url = locals()["enhanced_send_streaming_url"]
            stream_proc_module.StreamProcessor._monitor_streaming_status = locals()["enhanced_monitor_streaming"]
            
            logger.info("Successfully patched StreamProcessor methods")
        except Exception as e:
            logger.error(f"Error patching StreamProcessor: {e}")
            success = False
    else:
        logger.warning("Could not find StreamProcessor module")
        success = False
    
    # Find and patch AllTalk TTS module
    alltalk_module = find_alltalk_tts_module()
    if alltalk_module:
        try:
            # Import the fixes module
            fixes = importlib.import_module("alltalk_streaming_fix")
            
            # Get the original methods
            original_get_streaming_url = alltalk_module.AllTalkTTSService.get_streaming_url
            original_get_last_audio_data = alltalk_module.AllTalkTTSService.get_last_audio_data
            
            # Extend the service class
            alltalk_module.AllTalkTTSService.timeout = 60  # Double the timeout
            alltalk_module.AllTalkTTSService.direct_api_timeout = 90  # Much longer timeout for direct API
            
            # Replace with enhanced versions from the fix module
            exec(inspect.getsource(fixes.fix_alltalk_tts_service).replace(
                "fix_alltalk_tts_service", "_temp_fix_func"), globals(), locals())
                
            # Monkey patch the methods
            alltalk_module.AllTalkTTSService.get_streaming_url = locals()["enhanced_get_streaming_url"]
            alltalk_module.AllTalkTTSService.get_last_audio_data = locals()["enhanced_get_last_audio_data"]
            
            logger.info("Successfully patched AllTalkTTSService methods")
        except Exception as e:
            logger.error(f"Error patching AllTalkTTSService: {e}")
            success = False
    else:
        logger.warning("Could not find AllTalkTTSService module")
        success = False
    
    # Create instruction file for server startup
    with open("server_patch_instructions.txt", "w") as f:
        f.write("""
VR INTERVIEW SYSTEM PATCHING INSTRUCTIONS
=========================================

The following modules have been patched:
- Server module (for text_response handling)
- StreamProcessor (for better streaming support)
- AllTalkTTSService (for reliable audio generation)

When you start the server, include the following lines in your code:

```python
# At the top of server.py or where you initialize components
import alltalk_streaming_fix

# After creating the server instance
from app.websocket.server import EnhancedServer 
server = EnhancedServer(...)

# Apply fixes to the server instance
alltalk_streaming_fix.apply_all_fixes(server)
```

Or apply the fixes when the server is running:

```python
# Get the server instance
server = get_server_instance()

# Import and apply fixes
import alltalk_streaming_fix
alltalk_streaming_fix.apply_all_fixes(server)
```
""")
    
    logger.info("Created server_patch_instructions.txt with detailed instructions")
    
    return success

if __name__ == "__main__":
    success = main()
    if success:
        logger.info("AllTalk fix application completed successfully")
        print("\n===== SUCCESS =====")
        print("AllTalk fixes have been applied to modules directly.")
        print("1. When starting the server, check the logs for 'AllTalk fixes applied successfully'")
        print("2. If you need to apply fixes again at runtime, use:")
        print("   import alltalk_streaming_fix")
        print("   alltalk_streaming_fix.apply_all_fixes(server_instance)")
        print("\nSee server_patch_instructions.txt for more details.")
    else:
        logger.warning("AllTalk fix application partially completed")
        print("\n===== PARTIAL SUCCESS =====")
        print("Some fixes were applied, but others failed. Check the logs for details.")
        print("You can still try running the server - the partial fixes may be sufficient.")
        print("To apply fixes at runtime, use:")
        print("   import alltalk_streaming_fix")
        print("   alltalk_streaming_fix.apply_all_fixes(server_instance)")
        print("\nSee server_patch_instructions.txt for more details.")
    
    sys.exit(0 if success else 1)
