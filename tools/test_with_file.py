#!/usr/bin/env python3
import asyncio
import argparse
import os
import sys

# Add the path to the test_client module
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# Import the test_client function
from test_client import test_client

async def main():
    parser = argparse.ArgumentParser(description="Test the VR Interview Server with a specified audio file")
    parser.add_argument("--server", default="ws://localhost:8765", help="WebSocket server URL")
    parser.add_argument("--file", type=str, required=True, help="Name of the audio file (without path)")
    
    args = parser.parse_args()
    
    # Set the path to the audio files
    audio_dir = "D:\\vr-interview-server\\test_audio"
    
    # Add .wav extension if not provided
    file_name = args.file
    if not file_name.endswith(".wav"):
        file_name += ".wav"
        
    audio_path = os.path.join(audio_dir, file_name)
    
    print(f"Using audio file: {audio_path}")
    
    # Run the test client with the specified file
    await test_client(args.server, audio_path)

if __name__ == "__main__":
    asyncio.run(main())
