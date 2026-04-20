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

echo.
echo --- Setup Complete! ---
echo To start the assistant, run: start_assistant.bat
echo.
pause
