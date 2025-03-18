#!/usr/bin/env python3
"""
AllTalk Test Script

This script tests the AllTalk TTS server with multiple approaches to identify
which API endpoints are working correctly.
"""

import requests
import time
import json
import sys
import os
import urllib.parse

ALLTALK_URL = "http://127.0.0.1:7851"
TEST_TEXT = "This is a test of the AllTalk TTS system integration."
TEST_VOICE = "alloy"  # Change to a voice you know exists on your system

def log_info(message):
    """Log an informational message"""
    print(f"[INFO] {message}")

def log_error(message):
    """Log an error message"""
    print(f"[ERROR] {message}")

def log_success(message):
    """Log a success message"""
    print(f"[SUCCESS] {message}")

def check_server_availability():
    """Check if AllTalk server is available"""
    log_info(f"Testing connection to AllTalk at {ALLTALK_URL}")
    
    try:
        response = requests.get(f"{ALLTALK_URL}/api/ready", timeout=5)
        if response.status_code == 200:
            log_success("AllTalk server is available")
            return True
        else:
            log_error(f"AllTalk server returned status code {response.status_code}")
            return False
    except Exception as e:
        log_error(f"Error connecting to AllTalk server: {e}")
        return False

def test_voices_api():
    """Test the voices API endpoint"""
    log_info("Testing voices API endpoint...")
    
    try:
        response = requests.get(f"{ALLTALK_URL}/api/voices", timeout=5)
        if response.status_code == 200:
            voices_data = response.json()
            voices = voices_data.get('voices', [])
            log_success(f"Found {len(voices)} voices")
            return True
        else:
            log_error(f"Voices API returned status code {response.status_code}")
            return False
    except Exception as e:
        log_error(f"Error testing voices API: {e}")
        return False

def test_streaming_api():
    """Test the streaming API endpoint"""
    log_info("Testing streaming API (POST)...")
    
    try:
        timestamp = int(time.time())
        test_file = f"test_stream_{timestamp}"
        
        response = requests.post(
            f"{ALLTALK_URL}/api/tts-generate-streaming",
            data={
                "text": TEST_TEXT,
                "voice": TEST_VOICE,
                "language": "en",
                "output_file": test_file
            },
            stream=True,
            timeout=5
        )
        
        if response.status_code == 200:
            # Don't read the full response, just check status
            response.close()
            log_success("Streaming API (POST) is working")
            return True
        else:
            log_error(f"Streaming API (POST) returned status code {response.status_code}")
            return False
    except Exception as e:
        log_error(f"Error testing streaming API (POST): {e}")
        return False

def test_streaming_api_get():
    """Test the streaming API with GET method"""
    log_info("Testing streaming API (GET)...")
    
    try:
        timestamp = int(time.time())
        test_file = f"test_stream_get_{timestamp}"
        encoded_text = urllib.parse.quote(TEST_TEXT)
        
        url = f"{ALLTALK_URL}/api/tts-generate-streaming?text={encoded_text}&voice={TEST_VOICE}&language=en&output_file={test_file}"
        
        response = requests.get(
            url,
            stream=True,
            timeout=5
        )
        
        if response.status_code == 200:
            # Don't read the full response, just check status
            response.close()
            log_success("Streaming API (GET) is working")
            return True
        else:
            log_error(f"Streaming API (GET) returned status code {response.status_code}")
            return False
    except Exception as e:
        log_error(f"Error testing streaming API (GET): {e}")
        return False

def test_tts_generate_api():
    """Test the tts-generate API endpoint"""
    log_info("Testing tts-generate API...")
    
    try:
        timestamp = int(time.time())
        test_file = f"test_direct_{timestamp}"
        
        response = requests.post(
            f"{ALLTALK_URL}/api/tts-generate",
            data={
                "text_input": TEST_TEXT,
                "character_voice_gen": TEST_VOICE,
                "output_file_name": test_file,
                "format": "wav"
            },
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            timeout=10
        )
        
        if response.status_code == 200:
            if len(response.content) > 100:
                log_success(f"tts-generate API is working, received {len(response.content)} bytes")
                
                # Save to file for verification
                os.makedirs("test_output", exist_ok=True)
                with open(f"test_output/tts_generate_test.wav", "wb") as f:
                    f.write(response.content)
                log_info(f"Saved output to test_output/tts_generate_test.wav")
                
                return True
            else:
                log_error(f"tts-generate API returned empty response")
                return False
        else:
            log_error(f"tts-generate API returned status code {response.status_code}")
            return False
    except Exception as e:
        log_error(f"Error testing tts-generate API: {e}")
        return False

def test_synthesize_api():
    """Test the synthesize API endpoint"""
    log_info("Testing synthesize API...")
    
    try:
        response = requests.post(
            f"{ALLTALK_URL}/api/synthesize",
            data={
                "text": TEST_TEXT,
                "voice": TEST_VOICE,
                "format": "wav"
            },
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            timeout=10
        )
        
        if response.status_code == 200:
            if len(response.content) > 100:
                log_success(f"synthesize API is working, received {len(response.content)} bytes")
                
                # Save to file for verification
                os.makedirs("test_output", exist_ok=True)
                with open(f"test_output/synthesize_test.wav", "wb") as f:
                    f.write(response.content)
                log_info(f"Saved output to test_output/synthesize_test.wav")
                
                return True
            else:
                log_error(f"synthesize API returned empty response")
                return False
        else:
            log_error(f"synthesize API returned status code {response.status_code}")
            return False
    except Exception as e:
        log_error(f"Error testing synthesize API: {e}")
        return False

def test_tts_api():
    """Test the tts API endpoint"""
    log_info("Testing tts API...")
    
    try:
        response = requests.post(
            f"{ALLTALK_URL}/api/tts",
            json={
                "text": TEST_TEXT,
                "voice": TEST_VOICE,
                "format": "wav"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            if len(response.content) > 100:
                log_success(f"tts API is working, received {len(response.content)} bytes")
                
                # Save to file for verification
                os.makedirs("test_output", exist_ok=True)
                with open(f"test_output/tts_test.wav", "wb") as f:
                    f.write(response.content)
                log_info(f"Saved output to test_output/tts_test.wav")
                
                return True
            else:
                log_error(f"tts API returned empty response")
                return False
        else:
            log_error(f"tts API returned status code {response.status_code}")
            return False
    except Exception as e:
        log_error(f"Error testing tts API: {e}")
        return False

def test_file_permissions():
    """Test file system permissions"""
    log_info("Testing file system permissions...")
    
    alltalk_dir = "D:/AllTalk/alltalk_tts"
    outputs_dir = os.path.join(alltalk_dir, "outputs")
    
    # Test root directory
    log_info(f"Checking AllTalk root directory: {alltalk_dir}")
    if os.path.exists(alltalk_dir):
        log_success(f"AllTalk directory exists: {alltalk_dir}")
    else:
        log_error(f"AllTalk directory does not exist: {alltalk_dir}")
        
    # Test outputs directory
    log_info(f"Checking outputs directory: {outputs_dir}")
    if os.path.exists(outputs_dir):
        log_success(f"Outputs directory exists: {outputs_dir}")
    else:
        log_error(f"Outputs directory does not exist: {outputs_dir}")
        try:
            os.makedirs(outputs_dir, exist_ok=True)
            log_success(f"Created outputs directory: {outputs_dir}")
        except Exception as e:
            log_error(f"Failed to create outputs directory: {e}")
            
    # Test file write permission
    try:
        test_file = os.path.join(outputs_dir, f"test_permission_{int(time.time())}.txt")
        with open(test_file, "w") as f:
            f.write("Test file for permission checking")
        log_success(f"Successfully wrote test file: {test_file}")
        
        # Try to read it back
        with open(test_file, "r") as f:
            content = f.read()
        log_success(f"Successfully read test file: {len(content)} bytes")
        
        # Clean up
        os.remove(test_file)
        log_success(f"Successfully removed test file")
        
        return True
    except Exception as e:
        log_error(f"File permission test failed: {e}")
        return False

def main():
    """Main function"""
    print("=" * 60)
    print("AllTalk TTS Integration Test")
    print("=" * 60)
    
    # Create results dictionary
    results = {}
    
    # Check server availability
    results["server_available"] = check_server_availability()
    if not results["server_available"]:
        log_error("Server not available, cannot continue testing")
        sys.exit(1)
        
    # Test voice API
    results["voices_api"] = test_voices_api()
    
    # Test streaming API (POST)
    results["streaming_api_post"] = test_streaming_api()
    
    # Test streaming API (GET)
    results["streaming_api_get"] = test_streaming_api_get()
    
    # Test tts-generate API
    results["tts_generate_api"] = test_tts_generate_api()
    
    # Test synthesize API
    results["synthesize_api"] = test_synthesize_api()
    
    # Test tts API
    results["tts_api"] = test_tts_api()
    
    # Test file permissions
    results["file_permissions"] = test_file_permissions()
    
    # Print summary
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    all_passed = True
    for test, result in results.items():
        status = "PASSED" if result else "FAILED"
        if not result:
            all_passed = False
        print(f"{test:20s}: {status}")
        
    print("=" * 60)
    if all_passed:
        print("All tests PASSED!")
        print("AllTalk should be working correctly with your VR Interview System")
    else:
        print("Some tests FAILED")
        print("Review the logs above for more information")
        
    print("=" * 60)
    
    # Recommendations
    print("\nRecommendations:")
    if not results["server_available"]:
        print("- Make sure AllTalk server is running and accessible at", ALLTALK_URL)
        
    if not results["voices_api"]:
        print("- Check if voices are properly loaded in AllTalk")
        
    if not results["streaming_api_post"] and not results["streaming_api_get"]:
        print("- Streaming API is not working. Check AllTalk server configuration")
        
    if not results["tts_generate_api"] and not results["synthesize_api"] and not results["tts_api"]:
        print("- No direct TTS API is working. Check AllTalk server configuration")
        
    if not results["file_permissions"]:
        print("- File permission issues detected. Check that your application has write access to the outputs directory")
        
    if all_passed:
        print("- Everything looks good! If you're still having issues, check your server.py configuration")
        print("- Make sure your server is using the correct URL and voice settings")
    
if __name__ == "__main__":
    main()
