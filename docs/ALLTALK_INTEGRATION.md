# AllTalk TTS Integration Guide

This document provides detailed information about integrating AllTalk TTS with the VR Interview System, including how to set up streaming audio and troubleshoot common issues.

## Overview

AllTalk TTS is used in the VR Interview System to generate high-quality speech for the virtual interviewer. The system supports two methods of audio delivery:

1. **Direct Streaming**: Audio is streamed directly from AllTalk to the client
2. **File Generation**: Audio is generated as a file and then sent to the client

## Setup Requirements

1. Install AllTalk TTS following the instructions at [AllTalk TTS GitHub](https://github.com/erew123/alltalk_tts)
2. Configure the VR Interview System to use AllTalk:

```json
// In config/config.json
"alltalk": {
  "url": "http://127.0.0.1:7851",
  "voice": "YourPreferredVoice.wav",
  "format": "wav",
  "retries": 3,
  "timeout": 30,
  "direct_api_timeout": 40,
  "alltalk_dir": "D:/AllTalk/alltalk_tts",
  "default_language": "en"
}
```

3. Start AllTalk TTS using the provided batch file
4. Verify AllTalk is running by accessing http://127.0.0.1:7851/api/ready

## Streaming Integration Details

### Server-Side Implementation

The VR Interview System uses AllTalk's streaming API endpoint to deliver audio directly to the client:

```
GET http://127.0.0.1:7851/api/tts-generate-streaming
```

Parameters:
- `text`: The text to convert to speech (URL-encoded)
- `voice`: The voice file to use (e.g., `female_01.wav`)
- `language`: The language code (e.g., `en`)
- `output_file`: Base filename for the generated audio

The server generates this URL and sends it to the client in an `audio_stream_url` message:

```json
{
  "type": "audio_stream_url",
  "session_id": "uuid",
  "timestamp": 1646721387.23,
  "url": "http://127.0.0.1:7851/api/tts-generate-streaming?text=Hello&voice=female_01.wav&language=en&output_file=response_1234",
  "format": "wav"
}
```

### Client-Side Implementation

The Unity client receives this URL and uses UnityWebRequest to stream the audio:

```csharp
using (UnityWebRequest request = UnityWebRequestMultimedia.GetAudioClip(url, AudioType.WAV))
{
    yield return request.SendWebRequest();
    
    if (request.result == UnityWebRequest.Result.Success)
    {
        AudioClip clip = DownloadHandlerAudioClip.GetContent(request);
        // Play the audio
    }
}
```

### Fallback Mechanism

If streaming fails, the system falls back to direct audio delivery:

1. The server checks for the generated audio file in AllTalk's outputs directory
2. It sends the audio data directly in an `audio_response` message
3. If file retrieval fails, it sends a text-only response as a final fallback

## Timing Considerations

AllTalk can take significant time to generate audio, especially for longer texts:

- Short responses (~50 chars): 1-3 seconds
- Medium responses (~200 chars): 5-15 seconds
- Long responses (400+ chars): 30-60 seconds

The VR Interview System accounts for this with:
- Extended monitoring timeouts (up to 45 seconds)
- Progress updates during generation
- Parallel audio synthesis for faster fallback

## File Location and Naming

AllTalk saves generated audio files in its outputs directory with these naming patterns:

- Direct API: `{output_file}.wav` or `{output_file}.wav.wav`
- Streaming API: `{output_file}.wav`

The system checks multiple file path variations to handle these inconsistencies.

## Troubleshooting

### Common Issues

1. **Streaming URL Generation Fails**
   - Check AllTalk is running (`http://127.0.0.1:7851/api/ready`)
   - Verify the voice file exists in AllTalk
   - Check that the outputs directory is writable

2. **Audio File Not Found**
   - Check the AllTalk outputs directory for the generated file
   - Verify the file extensions (.wav vs .wav.wav)
   - Check permissions on the AllTalk directory

3. **Streaming Takes Too Long**
   - Increase the timeout settings in config.json
   - Reduce the length of text being synthesized
   - Consider using a faster TTS model in AllTalk

4. **Client Can't Play Streaming Audio**
   - Verify Unity can access the AllTalk server (firewall settings)
   - Check the URL format in the Unity logs
   - Ensure Unity has the correct AudioType set

### Diagnostic Steps

1. Enable verbose logging in config.json:
   ```json
   "server": {
     "log_level": "DEBUG"
   }
   ```

2. Check server logs for:
   - "Created AllTalk streaming URL" messages
   - File path checking attempts
   - Streaming status updates

3. Check Unity logs for:
   - StreamAudioFromUrl calls
   - Streaming progress updates
   - Connection status messages

## API Reference

### AllTalk API Endpoints

#### Streaming TTS Generation
```
GET /api/tts-generate-streaming
```

Required parameters:
- `text`: Text to convert to speech
- `voice`: Voice file to use
- `language`: Language code (e.g., "en")
- `output_file`: Filename for the generated audio

#### Server Status
```
GET /api/ready
```
Returns "Ready" if the server is available

#### Available Voices
```
GET /api/voices
```
Returns a list of available voice files

## Performance Optimization

To optimize AllTalk streaming performance:

1. Use shorter responses when possible
2. Enable DeepSpeed in AllTalk for faster generation
3. Pre-warm the TTS engine by sending a short test request at startup
4. Balance quality and speed by using an appropriate model
