@echo off
echo Installing required dependencies in the vr-interview conda environment...

REM Activate conda environment
call conda activate vr-interview

REM Install dependencies
pip install websockets
pip install numpy
pip install gtts
pip install pydub
pip install requests
pip install pyaudio
pip install openai-whisper

echo Dependencies installed. You can now use the system.
pause
