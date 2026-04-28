@echo off
setlocal enabledelayedexpansion

:: Check if provider is local in config
set "is_local=0"
if exist "assistant_config.json" (
    findstr /C:"\"provider\": \"local\"" "assistant_config.json" >nul
    if !errorlevel! equ 0 (
        set "is_local=1"
    )
)

if !is_local! equ 1 (
    echo [Setup] Local provider detected.
    
    :: Run interactive setup FIRST in the main window (downloads model, picks engine)
    .\.venv\Scripts\python.exe local_llm_manager.py
    
    echo.
    echo Starting Inference Server in the background...
    start "Local LLM Server" cmd /k ".\.venv\Scripts\python.exe local_llm_manager.py start"
    
    echo Waiting for server to initialize...
    timeout /t 10 /nobreak >nul
)

echo Starting Assistant...
.\.venv\Scripts\python.exe gemini_assistant.py

pause