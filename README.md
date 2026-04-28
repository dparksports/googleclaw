# 🦅 GoogleClaw: Seamless OS Orchestration & AI Vision

**GoogleClaw** is a powerful, agent-first workspace designed for autonomous OS orchestration and intelligent computer vision. It leverages cloud models (like Gemini 3.1) and highly-optimized local models (like DeepSeek, Gemma, and Llama) to plan, execute, and verify complex technical missions across your local system.

Whether you need a smart terminal assistant that safely executes PowerShell commands, a high-speed video processing pipeline for security footage, or a totally private local AI environment, GoogleClaw handles it all natively.

---

## 🚀 Core Features

### 1. 💻 Smart CLI Orchestrator (`gemini_assistant.py`)
A reactive terminal assistant that understands your "Wishes" and directly interfaces with your operating system.
*   **Hybrid Modes**: Instantly toggle between `/chat` (pure analysis) and `/plan` (action-oriented execution) modes.
*   **Safe Execution**: The agent drafts scripts and commands, but always previews them with a confirmation prompt before running.
*   **Vibe Coding**: Automatically updates your code! Add an `@gemini "instruction"` tag as a comment in any supported file, and the assistant will rewrite the code for you upon saving.
*   **Seamless Persistence**: Remembers your preferred models, API keys, and execution environments automatically.

### 2. 🧠 Local AI "App Store" (`local_llm_manager.py`)
Run state-of-the-art models entirely on your hardware for 100% privacy, zero latency, and zero subscription costs.
*   **Curated App Store**: An interactive UI featuring curated, highly-optimized Unsloth GGUF exports of DeepSeek R1, Google Gemma (2, 3, & 4), Meta Llama 3, and Alibaba Qwen 2.5.
*   **Smart Downloader**: Automatically downloads and configures required engine binaries (`llama-server.exe`) and Hugging Face model weights seamlessly in the background.
*   **Hardware Control**: Pick your engine (vLLM for raw speed, llama.cpp for VRAM efficiency). Offload models entirely to your GPU, or split them across CPU/RAM to run massive 32B models on consumer hardware.
*   **Build From Source**: Automatically detects CMake and CUDA toolchains to offer on-the-fly binary compilation for maximum hardware optimization.

### 3. 👁️ AI Vision Suite
High-performance computer vision scripts optimized for NVIDIA RTX hardware.
*   **`detect_humans_filehistory.py`**: A specialized high-speed scanner for large video archives.
    *   **Optimization**: Uses frame-striding and FP16 half-precision for up to 10x faster processing.
    *   **Sorting**: Prioritizes processing the most recent footage first.
    *   **Reporting**: Generates comprehensive CSV logs of human detection events.

### 4. 🛡️ Windows Security Hardening
Built-in PowerShell scripts and guides to lock down your Windows environment:
*   Identify and terminate rogue BackgroundTaskHost processes.
*   Enforce Web Components lockdowns (WebView2 / Widgets).
*   Create strict Outbound firewall rules to prevent unauthorized CDN communication.

---

## 🛠 Setup & Installation

### Option 1: Automatic Setup (Windows)
Simply run the setup script to create a virtual environment, install dependencies, and download the local AI engine.
```powershell
./setup.bat
```

### Option 2: Manual Installation
1.  **Environment**: Ensure you have Python 3.13+ installed. Create and activate a virtual environment:
    ```powershell
    python -m venv .venv
    .\.venv\Scripts\activate
    ```
2.  **GPU Support (Optional but Highly Recommended)**:
    ```powershell
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
    ```
3.  **Dependencies**:
    ```powershell
    pip install -r requirements.txt
    ```
4.  **Authentication**: Create a `.env` file in the root directory.
    *   **Cloud Mode**: Add `GEMINI_API_KEY=your_key_here`
    *   **Local Mode**: Add `HF_TOKEN=your_token_here` (to download gated models like Gemma/Llama).

---

## 📖 Usage Guides

### Start the AI Orchestrator
```powershell
./start_assistant.bat
```
*If your configuration is set to "local", this batch script will smoothly guide you through downloading a local model before launching the assistant.*

**CLI Commands**:
*   `/model`: Switch cloud models or access the Local AI Manager instructions.
*   `/chat` or `/q`: Force the assistant into Question/Analysis mode.
*   `/plan` or `/p`: Force the assistant into Action/Execution mode.
*   `/auto` or `/a`: Let the assistant intelligently decide between chatting and acting.

### Manage Local AI Models
```powershell
python local_llm_manager.py
```
*Launch the interactive model downloader to switch between model families (DeepSeek, Gemma, etc.) or input custom Unsloth Hugging Face URLs.*

---

## 📚 Documentation
For detailed guides on utilizing specific features, refer to the included markdown docs:
*   [Local AI Setup Guide](LOCAL_AI_GUIDE.md) - Deep dive into running local models and managing VRAM.
*   [Security Guide](SECURITY_GUIDE.md) - How to protect against rogue background tasks.
*   [Firewall Guide](FIREWALL_GUIDE.md) - Blocking malicious outbound traffic.
*   [WebView2 Lockdown Guide](WEBVIEW2_FIREWALL_GUIDE.md) - Securing Windows 11 Widgets and Search.

---
*Made with ❤️ in California*