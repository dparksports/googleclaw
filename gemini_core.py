import os
import json
import pathlib
import sys
import platform
import subprocess
import tkinter as tk
import webbrowser
from threading import Timer
from tkinter import filedialog
from platformdirs import user_config_dir
from google import genai
from PIL import Image
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
# Configuration
APP_NAME = "gemini-cli"
CONFIG_DIR = pathlib.Path(user_config_dir(APP_NAME))
CONFIG_FILE = CONFIG_DIR / "config.json"

# Cached client instance
_client = None

def get_config():
    if not CONFIG_FILE.exists():
        return {"model": "gemini-2.0-flash", "api_key": ""}
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def set_config(key, value):
    config = get_config()
    config[key] = value
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

from dotenv import load_dotenv
load_dotenv()

def get_client():
    global _client
    if _client: return _client
    
    config = get_config()
    api_key = os.environ.get("GEMINI_API_KEY") or config.get("api_key")
        
    if not api_key: 
        print("API Key not found in environment or config.")
        return None
    
    try:
        _client = genai.Client(api_key=api_key)
        return _client
    except Exception as e:
        print(f"Error initializing client: {e}")
        return None

# Web Routes
@app.route('/')
def index(): return render_template('index.html')

@app.route('/models', methods=['GET'])
def get_models():
    client = get_client()
    if not client: return jsonify([])
    models = [m.name for m in client.models.list() if 'generateContent' in m.supported_actions]
    return jsonify(models)

@app.route('/set-model', methods=['POST'])
def set_model_route():
    model_name = request.json.get('model')
    set_config("model", model_name)
    return jsonify({"status": "success"})

@app.route('/chat', methods=['POST'])
def chat_route():
    prompt = request.form.get('prompt', '')
    image = request.files.get('image')
    client = get_client()
    if not client: return jsonify({"response": "Error: Not configured."}), 400
    
    config = get_config()
    model_name = config.get("model", "gemini-2.0-flash")
    
    system_instruction = f"""
    You are a Seamless OS Orchestrator. 
    Current OS: {platform.system()}
    Current Directory: {os.getcwd()}
    
    CRITICAL RULES:
    1. BE A DOER: If a user asks "how to" do something or "find" something on their OS, ALWAYS respond with a JSON PLAN. Never just explain.
    2. PLAN FORMAT: Respond ONLY with a JSON object if the wish involves an OS task:
    {{
        "type": "plan",
        "explanation": "Briefly describe what this plan will accomplish",
        "actions": [
            {{ "type": "command", "content": "shell command", "is_dangerous": true/false }},
            {{ "type": "write_file", "path": "filename", "content": "file content" }}
        ]
    }}
    3. CHAT MODE: If (and only if) the user is just saying hello, asking a general knowledge question, or chatting about non-OS topics, respond with a simple JSON:
    {{
        "response": "Your text response here"
    }}
    4. SCRIPTING: For complex tasks (like finding duplicates), WRITE A SCRIPT (Python/PowerShell/Bash) and then add a COMMAND to run it.
    5. ROBUSTNESS: When installing dependencies, check if they exist first. Avoid hardcoded `--index-url` or specific CUDA versions unless absolutely necessary. Prefer standard `pip install`.
    6. WINDOWS: Use PowerShell for all Windows commands.
    """
    
    contents = [prompt]
    if image:
        img = Image.open(image.stream)
        contents = [prompt, img]
    
    try:
        response = client.models.generate_content(
            model=model_name, 
            contents=contents,
            config={'system_instruction': system_instruction}
        )
        text = response.text.strip()
        
        # Try to parse as JSON
        try:
            # Strip markdown if needed
            json_text = text
            if "```json" in json_text:
                json_text = json_text.split("```json")[1].split("```")[0].strip()
            elif json_text.startswith("```"):
                json_text = json_text.split("```")[1].strip()
            
            data = json.loads(json_text)
            if data.get("type") == "plan":
                return jsonify(data)
            if data.get("response"):
                return jsonify({"response": data["response"]})
        except:
            pass # Fallback to raw text if JSON parsing fails
            
        return jsonify({"response": response.text})
    except Exception as e:
        return jsonify({"response": str(e)}), 500

@app.route('/execute', methods=['POST'])
def execute_route():
    actions = request.json.get('actions', [])
    results = []
    
    for action in actions:
        if action['type'] == 'command':
            cmd = action['content']
            try:
                res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                results.append({
                    "action": f"Run `{cmd}`",
                    "stdout": res.stdout,
                    "stderr": res.stderr,
                    "success": res.returncode == 0
                })
            except Exception as e:
                results.append({"action": f"Run `{cmd}`", "error": str(e), "success": False})
        
        elif action['type'] == 'write_file':
            path = action['path']
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(action['content'])
                results.append({"action": f"Write `{path}`", "success": True})
            except Exception as e:
                results.append({"action": f"Write `{path}`", "error": str(e), "success": False})
                
    return jsonify({"results": results})

def run_web():
    def open_browser(): webbrowser.open("http://127.0.0.1:5000")
    Timer(1, open_browser).start()
    app.run(port=5000)

def select_file():
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    file_path = filedialog.askopenfilename(
        title="Select an image",
        filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.gif *.webp")]
    )
    root.destroy()
    return file_path

def interactive_chat():
    client = get_client()
    if not client: 
        print("Not configured. Run the app once to set up.")
        return
    config = get_config()
    model_name = config.get("model", "gemini-2.0-flash")
    
    print(f"--- Chatting with {model_name} (Type 'exit' to quit) ---")
    while True:
        user_input = input("You: ")
        if user_input.lower() == 'exit': break
        
        response = client.models.generate_content(model=model_name, contents=user_input)
        print(f"Gemini: {response.text}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg == "web":
            run_web()
        elif arg == "chat":
            interactive_chat()
        else:
            print(f"Unknown argument: {arg}. Use 'web' or 'chat'.")
    else:
        run_web()
