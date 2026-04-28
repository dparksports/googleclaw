# 🤖 Seamless Local AI Guide

This project allows you to run world-class AI models (like DeepSeek, Gemma, and Llama) entirely on your own computer. This ensures total privacy, offline access, and zero subscription fees.

---

## 🚀 Quick Start (Easiest Way)

1.  **Open the Project Folder:** Navigate to the folder where you installed the Seamless Assistant.
2.  **Launch the Assistant:** Double-click `start_assistant.bat`.
3.  **Follow the Wizard:** 
    *   If you haven't configured a local model yet, a menu will appear.
    *   **Choose a Model:** Pick from the list (e.g., DeepSeek for coding, Gemma for writing).
    *   **Login:** If prompted, paste your Hugging Face token (found at [hf.co/settings/tokens](https://huggingface.co/settings/tokens)).
    *   **Wait for Download:** The script will automatically download the model and the inference engine.
4.  **Start Chatting:** Once the server says "Ready!", the chat window will open and you can begin typing your wishes.

---

## 🛠️ Advanced Configuration

### Changing Models
If you want to try a different model (e.g., switching from a fast 8B model to a "Genius" 32B model):
1. Close all active assistant windows.
2. Open a terminal (PowerShell) in the project folder.
3. Run: `python local_llm_manager.py`
4. Select your new model. The assistant will update your configuration automatically.

### Running Custom Unsloth Models
If you have fine-tuned your own model or found a specific one on Hugging Face:
1. Run `python local_llm_manager.py`.
2. Choose option **5. [Advanced] Custom Hugging Face Link**.
3. Provide the **Repo ID** (e.g., `unsloth/DeepSeek-R1-Distill-Llama-8B-GGUF`) and the **Filename** (e.g., `DeepSeek-R1-Distill-Llama-8B-Q4_K_M.gguf`).

---

## 🖥️ Hardware & Performance (GPU vs CPU)

When you start a model, the system will ask if you want to **"Offload all layers to GPU"**.

### Option A: Yes (All on GPU) - RECOMMENDED
*   **Speed:** Extremely fast (Real-time responses).
*   **Requirement:** Your GPU (e.g., RTX 3060, 4090) must have enough **VRAM** to hold the entire model.
*   **Use this if:** The model description says "needs 6GB VRAM" and you have 8GB or more.

### Option B: No (Split between GPU and CPU)
*   **Speed:** Slower (The more it spills into CPU/RAM, the slower it gets).
*   **Requirement:** Uses your standard system RAM if your GPU isn't big enough.
*   **Use this if:** You want to run a massive model (like a 32B model) but only have a medium-sized GPU (like 8GB or 12GB).

---

## ❓ Troubleshooting

*   **"WinError 10061":** This means the main assistant started before the local AI server was ready. Wait a few seconds and try again, or check the "Local LLM Server" window for errors.
*   **Hugging Face Login:** If a download fails, ensure you have "Accepted the Terms" for that model on the Hugging Face website (common for Gemma and Llama models).
*   **Slow Responses:** Ensure you are using the GPU option. If you are already using it, your model might be too large for your GPU. Try a smaller version (e.g., switch from 14B to 8B).
