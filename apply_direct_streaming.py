"""
Apply direct streaming integration to VR Interview System.

This script modifies the server to use the fast direct streaming
approach validated in TestStream.py.
"""

import logging
import sys
import importlib
import os
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("streaming_installer")

def main():
    """Apply the direct streaming fix to the server."""
    logger.info("Starting direct streaming integration")
    
    # First, verify AllTalk API is accessible
    try:
        import requests
        test_response = requests.get("http://127.0.0.1:7851/api/ready", timeout=5)
        if test_response.status_code != 200:
            logger.error("AllTalk API is not available at http://127.0.0.1:7851")
            print("\n===== ERROR =====")
            print("AllTalk API is not available. Please make sure AllTalk is running.")
            print("Run TestStream.py first to verify AllTalk is functioning properly.")
            return False
        logger.info("AllTalk API is accessible")
    except Exception as e:
        logger.error(f"Error checking AllTalk API: {e}")
        print("\n===== ERROR =====")
        print("Failed to connect to AllTalk API. Please make sure AllTalk is running.")
        print("Run TestStream.py first to verify AllTalk is functioning properly.")
        return False
    
    # Create server wrapper file to easily integrate the direct streaming fix
    wrapper_path = "direct_stream_server.py"
    with open(wrapper_path, "w") as f:
        f.write("""
'''
Direct streaming server wrapper for VR Interview System.

This wrapper starts the standard server but applies the direct streaming fix.
'''

import logging
import sys
import os
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("direct_streaming_server")

def main():
    logger.info("Starting direct streaming server wrapper")
    
    # Import direct streaming fix
    import alltalk_direct_streaming_fix
    
    # Import the normal server
    import server
    
    # Get server instance after it's created
    for _ in range(30):  # Try for 30 seconds
        if hasattr(server, 'get_server_instance'):
            server_instance = server.get_server_instance()
            if server_instance:
                # Apply fixes
                alltalk_direct_streaming_fix.apply_server_fixes(server_instance)
                logger.info("Direct streaming fixes applied to server instance")
                break
        import time
        time.sleep(1)
    
    logger.info("Server wrapper initialization complete")
    
    # No need to keep running this script - the server is already running
    # on the imported server module

if __name__ == "__main__":
    main()
""")
    
    logger.info(f"Created direct streaming server wrapper at {wrapper_path}")
    
    # Create an easy startup batch file
    bat_path = "start_direct_streaming_server.bat"
    with open(bat_path, "w") as f:
        f.write("""@echo off
echo Starting VR Interview System with Direct Streaming support
echo =======================================================
echo.
python direct_stream_server.py
echo.
if %ERRORLEVEL% NEQ 0 (
  echo There was an error starting the server
  pause
)
""")
    
    logger.info(f"Created startup batch file at {bat_path}")
    
    # Create instructions for Unity integration
    unity_path = "unity_integration_instructions.txt"
    with open(unity_path, "w") as f:
        f.write("""
VR INTERVIEW SYSTEM - UNITY INTEGRATION INSTRUCTIONS
===================================================

1. Make sure the MessageHandlerExtensions.cs file has been added to your project
   at: D:\\VRSystemTest\\Assets\\Scripts\\Network\\MessageHandlerExtensions.cs

2. Make sure the MessageHandlerPatcher.cs file has been added to your project
   at: D:\\VRSystemTest\\Assets\\Scripts\\Network\\MessageHandlerPatcher.cs

3. In Unity, add the MessageHandlerPatcher component to the GameObject
   that has your MessageHandler component. This component will automatically
   patch the MessageHandler to handle text_response messages.

To start the server with direct streaming support:
-------------------------------------------------
1. Make sure AllTalk is running
2. Run the TestStream.py script to verify AllTalk is working
3. Run start_direct_streaming_server.bat or python direct_stream_server.py

Troubleshooting:
---------------
- If you encounter errors, check the logs for specific error messages
- Make sure AllTalk is running and responding to API requests
- Verify the server is correctly connecting to AllTalk
- Check that Unity correctly received and applied the MessageHandler patches

For fast audio streaming and more reliable operation:
---------------------------------------------------
This integration uses the AllTalk streaming API which is extremely fast,
but falls back to direct audio or text responses if streaming isn't available.
""")
    
    logger.info(f"Created Unity integration instructions at {unity_path}")
    
    # Report success
    print("\n===== SUCCESS =====")
    print("Direct streaming integration has been set up successfully.")
    print("")
    print("To start the server with direct streaming support:")
    print("1. Make sure AllTalk is running")
    print("2. Run: python direct_stream_server.py")
    print("   or use the start_direct_streaming_server.bat file")
    print("")
    print("See unity_integration_instructions.txt for Unity client setup details.")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
