# GoogleClaw: Seamless OS Orchestration & AI Vision

GoogleClaw is an agent-first workspace designed for autonomous OS orchestration and intelligent computer vision. It leverages the Gemini 3.1 model family to plan, execute, and verify complex technical missions across Windows, Linux, and macOS.

## 🚀 Core Features

### 1. Smart CLI Orchestrator (`gemini_assistant.py`)
A reactive terminal assistant that understands your "Wishes."
*   **Hybrid Modes**: Toggle between `/chat` (analysis) and `/plan` (action) modes.
*   **Safe Execution**: Previews every script and command with a confirmation prompt.
*   **Vibe Coding**: Automatically updates code based on `@gemini` tags in your source files.
*   **Persistence**: Remembers your preferred model and provider.

### 2. Local AI Orchestration (`local_llm_manager.py`)
Run state-of-the-art models entirely on your hardware for 100% privacy and zero cost.
*   **App Store Experience**: Curated menu of optimized Unsloth GGUF models (DeepSeek, Gemma, Qwen, Llama).
*   **Dual Engines**: Supports **vLLM** (max performance) and **llama.cpp** (max efficiency).
*   **Smart Downloader**: Automatically fetches the required engine binaries and model weights.
*   **Hardware Control**: Interactive choice to offload models fully to GPU or split across CPU/RAM.

### 3. AI Vision Suite
High-performance computer vision scripts optimized for NVIDIA RTX hardware.
*   **`detect_humans_filehistory.py`**: A specialized high-speed scanner for large video archives.
    *   **Optimization**: Uses frame-striding and FP16 half-precision for 10x faster processing.
    *   **Sorting**: Processes the most recent footage first.
    *   **Reporting**: Generates comprehensive CSV logs of human detection events.

### 4. Web UI (`gemini_core.py`)
A browser-based interface for those who prefer visual orchestration and plan management.

## 🛠 Setup & Installation

1.  **Environment**: Ensure you have Python 3.13+ and a virtual environment.
2.  **GPU Support (Optional but Recommended)**:
    ```powershell
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
    ```
3.  **Dependencies**:
    ```powershell
    pip install ultralytics opencv-python pandas flask python-dotenv google-genai huggingface_hub requests
    ```
4.  **API Key**: Add your `GEMINI_API_KEY` to a `.env` file for Cloud mode. For Local mode, add `HF_TOKEN` to access gated models.

## 📖 Usage

### Running the Assistant
```powershell
./start_assistant.bat
```
*This will automatically guide you through local AI setup if configured for local mode.*

**CLI Commands**:
*   `/model`: Switch models (Cloud) or access the Local AI Manager instructions.
*   `/chat`: Switch to inquiry-only mode.
*   `/plan`: Switch to action-oriented mode.

### Managing Local AI
```powershell
python local_llm_manager.py
```
*Use this to download new models or switch between model families like DeepSeek or Gemma.*

### Running Human Detection
```powershell
python detect_humans_filehistory.py
```
*The script targets `~/Downloads/reolink` by default and uses your GPU automatically if available.*

---
Made with ❤️ in California
