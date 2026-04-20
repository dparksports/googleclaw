#!/bin/bash
echo "--- Gemini AI Assistant Setup (macOS/Ubuntu) ---"

if ! command -v python3 &> /dev/null
then
    echo "Error: Python3 is not installed. Please install it using your package manager."
    exit 1
fi

echo "Creating virtual environment..."
python3 -m venv .venv

echo "Installing dependencies..."
./.venv/bin/python -m pip install -r requirements.txt

chmod +x start_assistant.sh

echo ""
echo "--- Setup Complete! ---"
echo "To start the assistant, run: ./start_assistant.sh"
echo ""
