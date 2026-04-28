# Seamless Assistant: Local & Cloud Setup Guide

The Seamless Assistant allows you to control your computer and write code using powerful AI models. You can use either **Google's cloud AI** (for best performance) or **your own local computer** (for privacy and offline use).

---

## 1. Choose Your Mode

### Option A: Google Cloud AI (Easiest)
Use this if you have an internet connection and want the most advanced AI features.
1.  Get your **Gemini API Key** from [Google AI Studio](https://aistudio.google.com/).
2.  Create a file named `.env` in the project folder.
3.  Add this line to the file: `GEMINI_API_KEY=your_key_here`.

### Option B: Local AI (Privacy & Offline)
Use this to run high-performance AI models (DeepSeek, Gemma, Llama) directly on your hardware. We provide a built-in manager to handle the complex setup for you.

1.  **Requirement**: An NVIDIA GPU with at least 8GB VRAM is highly recommended.
2.  **Authentication**: Get a Hugging Face token from [hf.co/settings/tokens](https://huggingface.co/settings/tokens) and add it to your `.env` file as `HF_TOKEN=your_token`.
3.  **Automatic Setup**: The first time you run `start_assistant.bat` in local mode, it will open the **Local AI Model Downloader**. 

---

## 2. Configure the Assistant

Open the `assistant_config.json` file in your project folder and set your preferences.

### For Cloud Mode:
```json
{
  "model": "gemini-3.1-flash-lite-preview",
  "provider": "google"
}
```

### For Local Mode:
```json
{
  "provider": "local"
}
```
*Note: The local downloader will automatically populate the rest of the configuration once you pick a model.*

---

## 3. The Local AI App Store

We recommend using the curated models from **Unsloth** available in our interactive manager. To access the manager manually:

```powershell
python local_llm_manager.py
```

### Supported Model Families:
*   **DeepSeek R1**: The gold standard for logic and coding tasks.
*   **Google Gemma (2/3/4)**: Excellent for creative work and general assistance.
*   **Meta Llama 3**: Highly reliable all-around performance.
*   **Alibaba Qwen 2.5**: Fast, capable, and great for multilingual support.

### Hardware Offloading
When starting a local model, you can choose to:
*   **Full GPU**: Offload all AI "layers" to your graphics card for maximum speed.
*   **Split Mode**: Share the load between your GPU and standard RAM (allows running large 32B models on smaller GPUs).

---

## 3. How to Use

1.  **Start the Assistant:** Double-click `start_assistant.bat`.
2.  **Wish List:** When you see `Wish >`, type what you want to do. 
    *   *Example:* "Find all duplicate files in this folder."
    *   *Example:* "Monitor network traffic for the browser."
3.  **Modes:**
    *   `/chat`: Just talk to the AI.
    *   `/plan`: The AI will suggest steps to fix a problem, then you can approve them.
    *   `/auto`: The AI will automatically decide when to just talk or when to take action.

---

## 4. Pro-Tips
*   **Vibe Coding:** You can add `@gemini "instruction"` to the top of any `.py`, `.js`, or `.ts` file. Save the file, and the assistant will automatically update your code to follow your instruction.
*   **Need help?** Type `/help` or ask the assistant directly: "How do I use this?"
*   **Running out of memory?** Type `/clear` to reset the assistant's memory.
