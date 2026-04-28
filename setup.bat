@echo off
echo --- Gemini AI Assistant Setup (Windows) ---

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: Python is not installed. Please install it from python.org.
    pause
    exit /b
)

echo Creating virtual environment...
python -m venv .venv

echo Installing dependencies...
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

echo Downloading Local AI Engine (llama.cpp) for Windows...
.\.venv\Scripts\python.exe -c "import local_llm_manager; local_llm_manager.download_llama_cpp()"

echo.
echo --- Setup Complete! ---
echo To start the assistant, run: start_assistant.bat
echo.
pause
