import requests
import json

# Parameters to be sent in the request
payload = {
    "text_input": "This is a test of the AllTalk TTS system",
    "text_filtering": "standard",
    "character_voice_gen": "female_01.wav",
    "narrator_enabled": "false",
    "language": "en",
    "output_file_name": "test_output",
    "output_file_timestamp": "true",
    "autoplay": "true",
    "autoplay_volume": "0.8"
}

# Send the POST request
response = requests.post(
    "http://127.0.0.1:7851/api/tts-generate",
    data=payload
)

# Parse the JSON response
result = response.json()

# Print out the response content
print(f"Response: {response.text}")