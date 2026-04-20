# Gemini AI Assistant

A cross-platform assistant that lets you chat with Gemini in your browser or terminal. Supported on **macOS**, **Windows**, and **Ubuntu (Linux)**.

## 🚀 Easy Setup

### Windows
1.  Double-click **`setup.bat`**. This will set up your private environment and install everything automatically.
2.  Once finished, double-click **`start_assistant.bat`** to open the chat in your browser.

### macOS & Ubuntu
1.  Open your terminal in this folder.
2.  Run the setup script:
    ```bash
    bash setup.sh
    ```
3.  Start the assistant:
    ```bash
    ./start_assistant.sh
    ```

---

## 🔑 API Key Configuration

The first time you start the app, it will look for your API key.
- **Recommended:** Create a file named `.env` in this folder and paste your key inside like this:
  ```text
  GEMINI_API_KEY=your_key_here
  ```
- Alternatively, you can get a free key at [aistudio.google.com](https://aistudio.google.com/).

---

## 📖 How to Use

### Web Browser View (Recommended)
This is the easiest way to use the assistant.
- **Run:** `start_assistant.bat` (Windows) or `./start_assistant.sh` (macOS/Ubuntu).
- Your browser will open a clean chat interface.
- **Features:** 
    - Type and press **Enter** to send.
    - Click 📷 to attach images.
    - Switch AI models using the dropdown at the top right.

### Command Line View
For power users who prefer the terminal.
- **Run:** `.\.venv\Scripts\python.exe gemini_core.py chat` (Windows) or `./.venv/bin/python gemini_core.py chat`.
- **Image Attachments:** Type `attach` and press Enter to select an image file visually.

---

## 🛠️ Troubleshooting
- **Python not found:** Ensure you have Python 3.9+ installed. Download it from [python.org](https://www.python.org/).
- **Port 5000 busy:** If the web view won't open, ensure no other web apps are running on your computer.

---

## 📄 License

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.
