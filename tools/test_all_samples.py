#!/usr/bin/env python3
import asyncio
import os
import argparse
import time
from test_client import test_client

async def test_all_samples(server_url):
    """
    Test all sample audio files in the test_audio directory
    
    Args:
        server_url: WebSocket server URL
    """
    audio_dir = "D:\\vr-interview-server\\test_audio"
    
    # Find all .wav files in the directory
    audio_files = [f for f in os.listdir(audio_dir) if f.endswith('.wav')]
    
    print(f"Found {len(audio_files)} audio samples to test")
    
    for i, file_name in enumerate(audio_files, 1):
        print(f"\n==== Testing sample {i}/{len(audio_files)}: {file_name} ====\n")
        
        audio_path = os.path.join(audio_dir, file_name)
        
        try:
            # Wait a moment between tests
            if i > 1:
                print("Waiting 3 seconds before next test...")
                await asyncio.sleep(3)
                
            # Run the test client with this file
            await test_client(server_url, audio_path)
            
        except Exception as e:
            print(f"Error testing {file_name}: {e}")
        
        print(f"\n==== Completed testing {file_name} ====\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test all audio samples with the VR Interview Server")
    parser.add_argument("--server", default="ws://localhost:8765", help="WebSocket server URL")
    
    args = parser.parse_args()
    
    asyncio.run(test_all_samples(args.server))
