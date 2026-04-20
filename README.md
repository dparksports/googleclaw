# 🌟 Gemini Seamless Assistant

The easiest way to use AI on your computer. No complex commands, no technical jargon—just tell the AI what you want to do, and it helps you get it done.

---

## 🚀 How to Get Started

### 1. Set Up (Only once)
*   **Windows:** Double-click `setup.bat`.
*   **Mac / Linux:** Run `bash setup.sh` in your terminal.

### 2. Add your "Brain" (API Key)
The assistant needs a key from Google to work.
1.  Get a free key at [aistudio.google.com](https://aistudio.google.com/).
2.  Create a simple text file named `.env` in this folder.
3.  Paste this inside: `GEMINI_API_KEY=your_key_here`

### 3. Start the Assistant
*   **Windows:** Double-click `start_smart_assistant.bat`.
*   **Mac / Linux:** Run `./start_smart_assistant.sh`.

---

## 💡 How to Use (For Everyone)

### Option A: The "Wish" Box (Terminal)
When you start the assistant, you'll see a `Wish >` prompt. Just type what you want in plain English:

*   **Organize files:** *"Find all my photos and move them into a folder named 'MyPictures'."*
*   **Create things:** *"Write a simple Python script that reminds me to drink water every hour."*
*   **System Help:** *"How much space is left on my hard drive?"*
*   **Batch Tasks:** *"Find every text file in this folder and change the word 'Apple' to 'Orange'."*

The assistant will explain its plan. If it needs to run a command, it will ask for your permission first!

### Option B: "Vibe Coding" (Inside your Editor)
If you are writing code in an editor (like VS Code or Notepad++), you don't even need to switch back to the assistant.

1.  Keep the assistant running in the background.
2.  In your code file, just write a comment like this:
    `# @gemini create a function that calculates the area of a circle`
3.  **Save the file.**
4.  Magic! The assistant will see your comment and automatically replace it with the actual code.

---

## 🛠️ Frequently Asked Questions

**"Is it safe?"**
Yes. The assistant will always describe what it's about to do. If a task could delete or change important files, it will explicitly ask: *"Run this command? (y/n)"*.

**"Do I need to know how to code?"**
Not at all. You can use it just to manage your files, ask questions about your computer, or learn how things work.

**"What files can I use 'Vibe Coding' in?"**
It works in almost any code file: Python (.py), JavaScript (.js), HTML, CSS, C++, and more.

---

## 📄 License
This project is open-source under the Apache License 2.0.
