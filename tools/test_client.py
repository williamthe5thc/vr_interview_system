#!/usr/bin/env python3
import asyncio
import websockets
import json
import base64
import argparse
import os
import time
from pydub import AudioSegment
from pydub.playback import play


async def test_client(server_url, audio_path):
    """
    Simple test client for the VR Interview WebSocket server
    
    Args:
        server_url: WebSocket server URL (e.g., ws://localhost:8765)
        audio_path: Path to audio file for testing
    """
    print(f"Connecting to {server_url}...")
    
    try:
        async with websockets.connect(server_url) as websocket:
            print("Connected to server")
            session_id = None
            
            # Set up message handler
            receive_task = asyncio.create_task(handle_messages(websocket))
            
            # Load audio file
            if os.path.exists(audio_path):
                print(f"Loading audio from {audio_path}")
                audio = AudioSegment.from_file(audio_path)
                
                # Wait for server to be ready
                await asyncio.sleep(2)
                
                # Send audio data
                print("Sending audio...")
                with open(audio_path, "rb") as f:
                    audio_data = f.read()
                    audio_message = {
                        "type": "audio_data",
                        "session_id": session_id,
                        "timestamp": time.time(),
                        "data": base64.b64encode(audio_data).decode('utf-8')
                    }
                    await websocket.send(json.dumps(audio_message))
                    print("Audio sent")
            else:
                print(f"Audio file not found: {audio_path}")
                
            # Keep the connection open
            await receive_task
            
    except (websockets.exceptions.ConnectionClosedError, 
            websockets.exceptions.ConnectionClosedOK) as e:
        print(f"Connection closed: {e}")
    except Exception as e:
        print(f"Error: {e}")


async def handle_messages(websocket):
    """
    Handle incoming messages from the server
    
    Args:
        websocket: WebSocket connection
    """
    try:
        while True:
            message = await websocket.recv()
            
            try:
                # Parse the message
                data = json.loads(message)
                msg_type = data.get("type")
                
                # Handle different message types
                if msg_type == "state_update":
                    handle_state_update(data)
                elif msg_type == "audio_response":
                    handle_audio_response(data)
                elif msg_type == "error":
                    handle_error(data)
                else:
                    print(f"Unknown message type: {msg_type}")
                    
            except json.JSONDecodeError:
                print("Received non-JSON message")
                
    except (websockets.exceptions.ConnectionClosedError, 
            websockets.exceptions.ConnectionClosedOK) as e:
        print(f"Connection closed while receiving: {e}")


def handle_state_update(data):
    """
    Handle state update messages
    
    Args:
        data: State update message data
    """
    previous = data.get("previous")
    current = data.get("current")
    metadata = data.get("metadata", {})
    
    print(f"State changed: {previous} → {current}")
    
    # Print additional info if available
    if "message" in metadata:
        print(f"Info: {metadata['message']}")
    if "transcript" in metadata:
        print(f"Transcript: {metadata['transcript']}")


def handle_audio_response(data):
    """
    Handle audio response messages
    
    Args:
        data: Audio response message data
    """
    print("Received audio response")
    
    # Decode audio data
    audio_bytes = base64.b64decode(data.get("data", ""))
    
    # Save to temporary file
    temp_file = "temp_response.mp3"
    with open(temp_file, "wb") as f:
        f.write(audio_bytes)
        
    # Play the audio
    try:
        audio = AudioSegment.from_file(temp_file)
        print("Playing audio response...")
        play(audio)
    except Exception as e:
        print(f"Error playing audio: {e}")
    finally:
        # Clean up
        if os.path.exists(temp_file):
            os.remove(temp_file)


def handle_error(data):
    """
    Handle error messages
    
    Args:
        data: Error message data
    """
    code = data.get("code")
    message = data.get("message")
    print(f"Error {code}: {message}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test client for VR Interview WebSocket server")
    parser.add_argument("--server", default="ws://localhost:8765", help="WebSocket server URL")
    parser.add_argument("--audio", default="D:\\vr-interview-server\\test_audio\\speech_sample_1.wav", help="Path to audio file for testing")
    
    args = parser.parse_args()
    
    asyncio.run(test_client(args.server, args.audio))
