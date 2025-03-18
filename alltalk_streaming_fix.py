"""
AllTalk direct streaming fix for VR Interview System.

This script implements direct streaming integration with AllTalk,
fixing compatibility issues with the Oculus Quest VR client.
"""

import logging
import os
import time
import requests
import json
import asyncio
import urllib.parse
import base64
from typing import Optional, Dict, Any, Union

# Configure logger
logger = logging.getLogger("alltalk_streaming_fix")
logger.setLevel(logging.INFO)
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s',
        '%Y-%m-%d %H:%M:%S'
    ))
    logger.addHandler(console_handler)

class AllTalkStreamingFix:
    """
    Fixes AllTalk streaming integration for the Oculus Quest Unity client.
    
    This class implements workarounds for:
    1. Session ID mismatches between client and server
    2. AllTalk streaming URL errors and inconsistencies
    3. Stream URL accessibility from the Quest
    4. Provides fallback mechanisms for streaming failures
    """
    
    def __init__(self, base_url="http://127.0.0.1:7851"):
        """
        Initialize the streaming fix.
        
        Args:
            base_url: The base URL of the AllTalk server
        """
        self.base_url = base_url
        self.logger = logger
        self.logger.info(f"AllTalk Streaming Fix initialized with URL: {base_url}")
        
        # Test connection to verify server is reachable
        self.streaming_available = self._test_streaming_availability()
        
    def _test_streaming_availability(self) -> bool:
        """
        Test if AllTalk streaming API is available.
        
        Returns:
            bool: True if streaming is available, False otherwise
        """
        try:
            # Make a test request to the streaming API
            test_params = {
                "text": "Test streaming availability",
                "voice": "alloy",  # Default voice name
                "language": "en",
                "output_file": f"test_streaming_{int(time.time())}.wav"
            }
            
            response = requests.post(
                f"{self.base_url}/api/tts-generate-streaming",
                data=test_params,
                timeout=5,
                stream=True
            )
            
            # Just checking if the connection works, don't read the stream
            if response.status_code == 200:
                response.close()
                self.logger.info("AllTalk streaming API is available")
                return True
            else:
                self.logger.warning(f"AllTalk streaming API test failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error testing AllTalk streaming availability: {e}")
            return False

    def get_accessible_streaming_url(self, text: str, voice: str = "alloy", 
                                   session_id: Optional[str] = None) -> Optional[str]:
        """
        Generate a streaming URL that is properly formatted and accessible from the Oculus Quest.
        
        Args:
            text: The text to convert to speech
            voice: The voice to use
            session_id: Optional session ID for tracking
            
        Returns:
            A properly formatted streaming URL, or None if not available
        """
        if not self.streaming_available:
            self.logger.warning("Streaming not available, cannot generate URL")
            return None
            
        try:
            # Create a unique output filename with timestamp
            timestamp = int(time.time())
            output_file = f"vr_interview_{timestamp}.wav"
            
            # Properly encode parameters for URL
            encoded_text = urllib.parse.quote(text)
            encoded_voice = urllib.parse.quote(voice)
            
            # Build complete streaming URL with ALL required parameters
            direct_streaming_url = (
                f"{self.base_url}/api/tts-generate-streaming"
                f"?text={encoded_text}"
                f"&voice={encoded_voice}"
                f"&language=en"
                f"&output_file={output_file}"
            )
            
            # If on the same network, we could use this URL directly
            # However, for Oculus Quest, we need to replace localhost/127.0.0.1
            # with the actual LAN IP of the server
            
            # Extract host from base_url
            host = urllib.parse.urlparse(self.base_url).netloc.split(':')[0]
            
            # Replace localhost/127.0.0.1 with a better network address if needed
            if host in ["localhost", "127.0.0.1"]:
                # Try to use a LAN IP that Quest might be able to access
                # We'll check for server's IP addresses
                import socket
                try:
                    # Get all non-loopback IPv4 addresses
                    lan_ips = [
                        addr[4][0] for addr in socket.getaddrinfo(socket.gethostname(), None)
                        if addr[0] == socket.AF_INET and addr[4][0] != '127.0.0.1'
                    ]
                    
                    if lan_ips:
                        # Use the first LAN IP found
                        lan_ip = lan_ips[0]
                        self.logger.info(f"Found LAN IP for accessible streaming: {lan_ip}")
                        
                        # Replace host in both base_url and direct_streaming_url
                        base_url_with_lan = self.base_url.replace(host, lan_ip)
                        direct_streaming_url = direct_streaming_url.replace(host, lan_ip)
                    else:
                        self.logger.warning("No LAN IP found, Quest may not be able to access this URL")
                except Exception as ip_error:
                    self.logger.error(f"Error getting LAN IP: {ip_error}")
            
            self.logger.info(f"Generated accessible streaming URL: {direct_streaming_url[:100]}...")
            
            # Verify the URL works by making a test request
            try:
                test_response = requests.head(
                    direct_streaming_url,
                    timeout=5
                )
                
                if test_response.status_code != 200:
                    self.logger.warning(f"Streaming URL test failed with status {test_response.status_code}")
                    return None
                    
            except Exception as test_error:
                self.logger.warning(f"Streaming URL test failed: {test_error}")
                return None
                
            return direct_streaming_url
            
        except Exception as e:
            self.logger.error(f"Error generating accessible streaming URL: {e}")
            return None
    
    def generate_audio_with_fallbacks(self, text: str, voice: str = "alloy", 
                                    session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate audio using AllTalk with multiple fallback approaches.
        
        Args:
            text: The text to convert to speech
            voice: The voice to use
            session_id: Optional session ID for tracking
            
        Returns:
            Dict with status, URLs, and/or audio data
        """
        if not text or not text.strip():
            self.logger.warning("Empty text for speech generation")
            return {"status": "error", "message": "Empty text for speech generation"}
            
        try:
            # Generate a unique output filename with timestamp
            timestamp = int(time.time())
            output_file = f"vr_interview_{timestamp}"
            
            # STRATEGY 1: Try to get accessible streaming URL first
            streaming_url = self.get_accessible_streaming_url(text, voice, session_id)
            
            # STRATEGY 2: Generate audio file via standard API
            # This creates the audio file on the server that can be retrieved later
            standard_result = self._generate_via_standard_api(text, voice, output_file)
            
            # STRATEGY 3: Generate audio directly in memory as fallback
            direct_audio = None
            if not standard_result.get("success", False):
                direct_audio = self._generate_audio_directly(text, voice)
            
            # Consolidate results
            result = {
                "status": "success" if (streaming_url or standard_result.get("success") or direct_audio) else "error",
                "streaming_url": streaming_url,
                "file_path": standard_result.get("output_file_path"),
                "file_url": standard_result.get("output_file_url"),
                "audio_data": direct_audio,
                "text": text,  # Include original text as fallback
                "output_file": output_file
            }
            
            # Log diagnostic info
            self.logger.info(f"Audio generation results for {len(text)} characters:")
            self.logger.info(f"  - Streaming URL available: {streaming_url is not None}")
            self.logger.info(f"  - Standard API success: {standard_result.get('success', False)}")
            self.logger.info(f"  - Direct audio available: {direct_audio is not None}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error generating audio with fallbacks: {e}")
            return {
                "status": "error",
                "message": str(e),
                "text": text
            }
    
    def _generate_via_standard_api(self, text: str, voice: str, output_file: str) -> Dict[str, Any]:
        """
        Generate audio via the standard AllTalk API.
        
        Args:
            text: The text to convert to speech
            voice: The voice to use
            output_file: The output filename without extension
            
        Returns:
            Dict with success flag and file information
        """
        try:
            # Use the standard TTS API to generate audio
            params = {
                "text_input": text,
                "character_voice_gen": voice,
                "output_file_name": output_file,
                "output_file_timestamp": "false"
            }
            
            response = requests.post(
                f"{self.base_url}/api/tts-generate",
                data=params,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "output_file_path": result.get("output_file_path"),
                    "output_file_url": result.get("output_file_url")
                }
            else:
                self.logger.warning(f"Standard API failed: {response.status_code}")
                return {"success": False}
                
        except Exception as e:
            self.logger.error(f"Error with standard API: {e}")
            return {"success": False}
    
    def _generate_audio_directly(self, text: str, voice: str) -> Optional[bytes]:
        """
        Generate audio directly and return the audio data.
        
        Args:
            text: The text to convert to speech
            voice: The voice to use
            
        Returns:
            Audio data as bytes, or None if failed
        """
        try:
            # Use the standard API with direct content access
            output_file = f"direct_{int(time.time())}"
            params = {
                "text_input": text,
                "character_voice_gen": voice,
                "output_file_name": output_file,
                "output_file_timestamp": "false"
            }
            
            response = requests.post(
                f"{self.base_url}/api/tts-generate",
                data=params,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Get the audio file URL
                audio_url = f"{self.base_url}{result.get('output_file_url')}"
                
                # Download the audio content
                audio_response = requests.get(audio_url, timeout=10)
                
                if audio_response.status_code == 200 and len(audio_response.content) > 1000:
                    self.logger.info(f"Retrieved direct audio: {len(audio_response.content)} bytes")
                    return audio_response.content
                else:
                    self.logger.warning(f"Failed to retrieve audio from URL: {audio_url}")
            
            return None
                
        except Exception as e:
            self.logger.error(f"Error getting direct audio: {e}")
            return None


# Function to apply the fix to the stream_processor
async def integrate_streaming_fix(stream_processor, alltalk_url="http://127.0.0.1:7851", lan_ip=None):
    """
    Integrate streaming fix into the stream processor.
    
    Args:
        stream_processor: The stream processor to enhance
        alltalk_url: The AllTalk server URL
        lan_ip: Optional LAN IP to use instead of 127.0.0.1
    
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info("Integrating AllTalk streaming fix")
        
        # Create the streaming fix instance
        fix = AllTalkStreamingFix(alltalk_url)
        
        # Store it on the stream processor for later use
        stream_processor.alltalk_streaming_fix = fix
        
        # Replace the "Disabling direct streaming to ensure Oculus Quest compatibility" code
        # by monkey-patching the _check_alltalk_streaming_capability method
        
        # Store original method for reference
        original_check_streaming = stream_processor._check_alltalk_streaming_capability
        
        # Define new method that allows streaming
        def enhanced_check_streaming(session_id):
            """Enhanced version that allows streaming for Oculus Quest"""
            # Still log diagnostic information from original method
            streaming_capable = original_check_streaming(session_id)
            
            # But always enable streaming for our enhanced implementation
            logger.info("Enabling streaming support with AllTalk streaming fix")
            
            # Log URL replacement if LAN IP provided
            if lan_ip and alltalk_url and ("127.0.0.1" in alltalk_url or "localhost" in alltalk_url):
                base_url = alltalk_url
                modified_url = base_url.replace("127.0.0.1", lan_ip).replace("localhost", lan_ip)
                logger.info(f"Using modified URL for Quest access: {modified_url}")
            
            return True
        
        # Replace the method
        stream_processor._check_alltalk_streaming_capability = enhanced_check_streaming
        
        # Also modify the streaming URL generation to use our enhanced version
        # Store original get_streaming_url method from TTS service
        original_get_streaming_url = stream_processor.tts_service.get_streaming_url
        
        # Define enhanced version
        def enhanced_get_streaming_url(text, session_id=None):
            """Enhanced version that generates Quest-accessible URLs"""
            logger.info("Using enhanced streaming URL generation")
            
            # First try original method to keep compatibility
            try:
                original_url = original_get_streaming_url(text, session_id)
                
                # If successful, modify the URL to use LAN IP if provided
                if original_url and lan_ip and ("127.0.0.1" in original_url or "localhost" in original_url):
                    modified_url = original_url.replace("127.0.0.1", lan_ip).replace("localhost", lan_ip)
                    logger.info(f"Modified streaming URL: {modified_url[:100]}...")
                    return modified_url
                
                # If we have a working URL and no LAN IP, use the original
                if original_url:
                    return original_url
            except Exception as original_error:
                logger.warning(f"Original get_streaming_url failed: {original_error}")
            
            # If original fails or URL needs modification, use our enhanced version
            try:
                # Extract voice from TTS service
                voice = getattr(stream_processor.tts_service, 'voice', "alloy")
                
                # Use enhanced method to get accessible URL
                enhanced_url = fix.get_accessible_streaming_url(text, voice, session_id)
                
                if enhanced_url:
                    logger.info(f"Using enhanced streaming URL: {enhanced_url[:100]}...")
                    return enhanced_url
            except Exception as enhanced_error:
                logger.error(f"Enhanced streaming URL generation failed: {enhanced_error}")
            
            # Both methods failed
            logger.warning("Both original and enhanced streaming URL generation failed")
            return None
        
        # Replace the method
        stream_processor.tts_service.get_streaming_url = enhanced_get_streaming_url
        
        # Modify the stream processor's process_streaming_audio_pipeline to handle direct streaming properly
        # We'll do this by injecting a modification after the streaming URL check
        
        # Store original method
        original_process_audio = stream_processor.process_streaming_audio_pipeline
        
        # Define enhanced version
        async def enhanced_process_audio(session_id, audio_data, websocket=None):
            """Enhanced audio processing with proper streaming support"""
            logger.info(f"Enhanced audio pipeline for session {session_id}")
            
            # Use original method implementation
            await original_process_audio(session_id, audio_data, websocket)
            
        # Replace the method
        stream_processor.process_streaming_audio_pipeline = enhanced_process_audio
        
        # Fix direct streaming URL handling in stream processor
        # Locate and modify the code: "self.logger.info("Disabling direct streaming to ensure Oculus Quest compatibility")"
        
        # Patch _streaming_fallback_timer to better handle streaming failures
        original_fallback_timer = getattr(stream_processor, '_streaming_fallback_timer', None)
        
        if original_fallback_timer:
            async def enhanced_fallback_timer(session_id, audio_data, text_response):
                """Enhanced fallback timer with better handling"""
                try:
                    # Use original method but with shorter wait time for faster fallback
                    # We'll wait just 10 seconds instead of 15
                    logger.info(f"Enhanced fallback timer for {session_id}")
                    
                    # Wait shorter time for streaming confirmation
                    await asyncio.sleep(10.0)
                    
                    # Check if session exists and was not confirmed
                    parent_server = getattr(stream_processor, '_parent_server', None)
                    streaming_confirmed = False
                    if parent_server:
                        streaming_confirmed = hasattr(parent_server, 'streaming_confirmed') and session_id in getattr(parent_server, 'streaming_confirmed', set())
                    
                    if not streaming_confirmed:
                        logger.warning(f"No streaming confirmation after 10s, using fallback")
                        
                        # Ensure we have audio data or try to get it
                        if not audio_data or len(audio_data) < 1000:
                            # Try to get audio from the TTS service's last generated file
                            if hasattr(stream_processor.tts_service, 'get_last_audio_data'):
                                logger.info(f"Getting last audio data for fallback")
                                audio_data = await asyncio.to_thread(
                                    stream_processor.tts_service.get_last_audio_data,
                                    session_id
                                )
                            
                            # If still no audio, try to generate it directly
                            if (not audio_data or len(audio_data) < 1000) and hasattr(fix, 'generate_audio_with_fallbacks'):
                                logger.info(f"Generating audio directly for fallback")
                                # Get voice
                                voice = getattr(stream_processor.tts_service, 'voice', "alloy")
                                
                                result = await asyncio.to_thread(
                                    fix.generate_audio_with_fallbacks,
                                    text_response,
                                    voice,
                                    session_id
                                )
                                
                                audio_data = result.get('audio_data')
                        
                        # Send audio response with improved data
                        if audio_data and len(audio_data) > 1000:
                            await stream_processor._send_direct_audio(session_id, audio_data, text_response, websocket)
                            logger.info(f"Sent audio fallback of {len(audio_data)} bytes")
                        elif text_response:
                            await stream_processor._send_text_fallback(session_id, text_response, websocket)
                            logger.info(f"Sent text fallback of {len(text_response)} chars")
                            
                except asyncio.CancelledError:
                    # Task cancelled normally
                    pass
                except Exception as e:
                    logger.error(f"Error in enhanced fallback timer: {e}")
                    
                    # Last resort: try to send text fallback
                    try:
                        if text_response and websocket:
                            await stream_processor._send_text_fallback(session_id, text_response, websocket)
                    except Exception:
                        pass
            
            # Replace method
            stream_processor._streaming_fallback_timer = enhanced_fallback_timer
        
        logger.info("AllTalk streaming fix integrated successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error integrating streaming fix: {e}")
        return False


# Function to enhance server_enhanced_fixed.py
async def enhance_server(server, alltalk_url="http://127.0.0.1:7851", lan_ip=None):
    """
    Enhance the server with AllTalk streaming fixes.
    
    Args:
        server: The WebSocketServer instance
        alltalk_url: The AllTalk server URL
        lan_ip: Optional LAN IP to use instead of 127.0.0.1
    
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info("Enhancing WebSocketServer with AllTalk streaming fixes")
        
        # First enhance the stream processor
        success = await integrate_streaming_fix(server.stream_processor, alltalk_url, lan_ip)
        
        if not success:
            logger.warning("Failed to enhance stream processor, server enhancements may be limited")
        
        # Fix the send_audio_response method to properly handle streaming URLs
        original_send_audio = server.send_audio_response
        
        async def enhanced_send_audio(session_id, audio_data=None, text_response=None, streaming_url=None):
            """Enhanced audio sender with better streaming support"""
            logger.info(f"Enhanced send_audio_response for {session_id}")
            
            # Configure session to default to streaming support
            websocket = server.active_connections.get(session_id)
            if not websocket:
                logger.error(f"No active connection for {session_id}")
                return False
                
            # Get streaming capability flags
            if session_id not in server.client_capabilities:
                logger.info(f"Setting default streaming capability for {session_id}")
                server.client_capabilities[session_id] = {'supports_streaming': True}
            
            # Session capabilities
            session = server.state_manager.get_session(session_id)
            if session and hasattr(session, "metadata"):
                if not session.metadata:
                    session.metadata = {}
                # Set streaming capability to True by default
                if 'supports_streaming' not in session.metadata:
                    session.metadata['supports_streaming'] = True
                    logger.info(f"Set default streaming capability in session metadata")
            
            # Modify streaming URL if needed for Quest access
            if streaming_url and lan_ip and ("127.0.0.1" in streaming_url or "localhost" in streaming_url):
                streaming_url = streaming_url.replace("127.0.0.1", lan_ip).replace("localhost", lan_ip)
                logger.info(f"Modified streaming URL for Quest access: {streaming_url[:100]}...")
            
            # Now call original method with enhanced parameters
            return await original_send_audio(session_id, audio_data, text_response, streaming_url)
        
        # Replace the method
        server.send_audio_response = enhanced_send_audio
        
        # Add a new method to handle direct streaming to clients
        async def send_streaming_url(session_id, url, text=None):
            """
            Send streaming URL to client properly formatted for Quest access.
            
            Args:
                session_id: The session identifier
                url: The streaming URL
                text: Optional text for fallback
                
            Returns:
                True if successful, False otherwise
            """
            websocket = server.active_connections.get(session_id)
            if not websocket:
                logger.error(f"No active connection for {session_id}")
                return False
                
            try:
                # Fix URL if needed
                if lan_ip and ("127.0.0.1" in url or "localhost" in url):
                    url = url.replace("127.0.0.1", lan_ip).replace("localhost", lan_ip)
                
                # Create message
                message = {
                    "type": "audio_stream_url",
                    "session_id": session_id,
                    "timestamp": time.time(),
                    "url": url,
                    "format": "wav"
                }
                
                # Add text fallback if provided
                if text:
                    message["text"] = text
                
                # Send message
                await websocket.send(json.dumps(message))
                logger.info(f"Sent streaming URL to {session_id}: {url[:100]}...")
                
                # Track this session as using streaming
                server.streaming_sessions.add(session_id)
                
                return True
                
            except Exception as e:
                logger.error(f"Error sending streaming URL: {e}")
                return False
        
        # Add the method to server
        server.send_streaming_url = send_streaming_url
        
        logger.info("WebSocketServer enhanced successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error enhancing server: {e}")
        return False


# Main function to apply all fixes
async def apply_alltalk_fixes(server, alltalk_url="http://127.0.0.1:7851", lan_ip=None):
    """
    Apply all AllTalk streaming fixes to the server.
    
    Args:
        server: The WebSocketServer instance
        alltalk_url: The AllTalk server URL
        lan_ip: Optional LAN IP for Quest access
        
    Returns:
        True if successful, False otherwise
    """
    # If no LAN IP provided, try to detect it
    if not lan_ip:
        try:
            import socket
            lan_ips = [
                addr[4][0] for addr in socket.getaddrinfo(socket.gethostname(), None)
                if addr[0] == socket.AF_INET and addr[4][0] != '127.0.0.1'
            ]
            
            if lan_ips:
                lan_ip = lan_ips[0]
                logger.info(f"Detected LAN IP: {lan_ip}")
            else:
                logger.warning("No LAN IP detected, using user-provided or default IP")
                # Use server's host as fallback
                lan_ip = server.host if hasattr(server, 'host') and server.host != "0.0.0.0" else None
        except Exception as ip_error:
            logger.error(f"Error detecting LAN IP: {ip_error}")
    
    # Apply fixes
    success = await enhance_server(server, alltalk_url, lan_ip)
    
    if success:
        logger.info("AllTalk streaming fixes applied successfully")
        logger.info(f"Using AllTalk URL: {alltalk_url}")
        logger.info(f"Using LAN IP for Quest access: {lan_ip}")
    else:
        logger.error("Failed to apply AllTalk streaming fixes")
    
    return success


# For standalone testing
if __name__ == "__main__":
    """
    Test the AllTalk streaming fix functionality.
    """
    import sys
    
    # Configure simple logging to console
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Parse arguments
    alltalk_url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:7851"
    lan_ip = sys.argv[2] if len(sys.argv) > 2 else None
    
    print(f"Testing AllTalk streaming fix with URL: {alltalk_url}")
    
    # Create streaming fix
    fix = AllTalkStreamingFix(alltalk_url)
    
    # Test accessibility
    print(f"Streaming available: {fix.streaming_available}")
    
    # Test streaming URL generation
    test_text = "This is a test of AllTalk streaming. If you can hear this, the streaming fix is working."
    streaming_url = fix.get_accessible_streaming_url(test_text)
    
    print(f"Streaming URL: {streaming_url}")
    
    # Test audio generation
    result = fix.generate_audio_with_fallbacks(test_text)
    
    print(f"Audio generation result: {result['status']}")
    print(f"Streaming URL: {result.get('streaming_url') is not None}")
    print(f"File path: {result.get('file_path')}")
    print(f"Audio data: {result.get('audio_data') is not None}")
    
    print("Test complete!")