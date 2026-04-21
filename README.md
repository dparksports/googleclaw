# GoogleClaw: Seamless OS Orchestration & AI Vision

GoogleClaw is an agent-first workspace designed for autonomous OS orchestration and intelligent computer vision. It leverages the Gemini 3.1 model family to plan, execute, and verify complex technical missions across Windows, Linux, and macOS.

## 🚀 Core Features

### 1. Smart CLI Orchestrator (`gemini_assistant.py`)
A reactive terminal assistant that understands your "Wishes."
*   **Hybrid Modes**: Toggle between `/chat` (analysis) and `/plan` (action) modes.
*   **Safe Execution**: Previews every script and command with a confirmation prompt.
*   **Vibe Coding**: Automatically updates code based on `@gemini` tags in your source files.
*   **Persistence**: Remembers your preferred model (e.g., `gemini-3.1-flash-lite-preview`).

### 2. AI Vision Suite
High-performance computer vision scripts optimized for NVIDIA RTX hardware.
*   **`detect_humans_filehistory.py`**: A specialized high-speed scanner for large video archives.
    *   **Optimization**: Uses frame-striding and FP16 half-precision for 10x faster processing.
    *   **Sorting**: Processes the most recent footage first.
    *   **Reporting**: Generates comprehensive CSV logs of human detection events.

### 3. Web UI (`gemini_core.py`)
A browser-based interface for those who prefer visual orchestration and plan management.

## 🛠 Setup & Installation

1.  **Environment**: Ensure you have Python 3.13+ and a virtual environment.
2.  **GPU Support (Optional but Recommended)**:
    ```powershell
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
    ```
3.  **Dependencies**:
    ```powershell
    pip install ultralytics opencv-python pandas flask python-dotenv google-genai
    ```
4.  **API Key**: Add your `GEMINI_API_KEY` to a `.env` file in the root directory.

## 📖 Usage

### Running the Assistant
```powershell
python gemini_assistant.py
```
**Commands**:
*   `/model [number]`: Quickly switch Gemini models.
*   `/chat`: Switch to inquiry-only mode.
*   `/plan`: Switch to action-oriented mode.

### Running Human Detection
```powershell
python detect_humans_filehistory.py
```
*The script targets `~/Downloads/reolink` by default and uses your GPU automatically if available.*

---
*Created with 🤖 Antigravity IDE*
