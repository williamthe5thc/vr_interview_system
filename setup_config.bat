@echo off
echo VR Interview System Configuration Setup
echo =====================================
echo.
echo Available profiles:
echo  1. Development (more logging, debug features)
echo  2. Production (optimized performance, minimal logging)
echo  3. Minimal (reduced resource usage)
echo.

set /p profile="Select profile (1-3, default: 1): "

if "%profile%"=="2" (
    python tools\setup_config.py --profile production
) else if "%profile%"=="3" (
    python tools\setup_config.py --profile minimal
) else (
    python tools\setup_config.py --profile development
)

echo.
echo Configuration setup complete.
echo You can now start the server with "python server.py"
echo.
pause
