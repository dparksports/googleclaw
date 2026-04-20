import os
import json
import pathlib
import sys
import tkinter as tk
import webbrowser
from threading import Timer
from tkinter import filedialog
from platformdirs import user_config_dir
import google.generativeai as genai
from PIL import Image
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
# Configuration
APP_NAME = "gemini-cli"
CONFIG_DIR = pathlib.Path(user_config_dir(APP_NAME))
CONFIG_FILE = CONFIG_DIR / "config.json"

# Cached model instance
_model = None

def get_config():
    if not CONFIG_FILE.exists():
        return {"model": "gemini-1.5-flash", "api_key": ""}
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def set_config(key, value):
    config = get_config()
    config[key] = value
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    # Persist the API key provided by the user
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

# Fallback to a stable default model
from dotenv import load_dotenv

# Load environment variables from .env if it exists
load_dotenv()

def get_model():
    global _model
    if _model: return _model
    
    config = get_config()
    # Priority: Environment Var (which includes .env) > Saved Config
    api_key = os.environ.get("GEMINI_API_KEY") or config.get("api_key")
        
    if not api_key: 
        print("API Key not found in environment or config.")
        return None
    
    genai.configure(api_key=api_key)
    try:
        model_name = config.get("model", "gemini-1.5-flash")
        _model = genai.GenerativeModel(model_name)
        return _model
    except Exception as e:
        print(f"Error initializing model {model_name}: {e}")
        return None

# Web Routes
@app.route('/')
def index(): return render_template('index.html')

@app.route('/models', methods=['GET'])
def get_models():
    model = get_model()
    if not model: return jsonify([])
    # Note: get_model already configured the client
    models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    return jsonify(models)

@app.route('/set-model', methods=['POST'])
def set_model_route():
    model_name = request.json.get('model')
    set_config("model", model_name)
    global _model
    _model = None # Force re-init on next chat
    return jsonify({"status": "success"})

@app.route('/chat', methods=['POST'])
def chat_route():
    prompt = request.form.get('prompt', '')
    image = request.files.get('image')
    model = get_model()
    if not model: return jsonify({"response": "Error: Not configured."}), 400
    
    contents = [prompt]
    if image:
        img = Image.open(image.stream)
        contents = [prompt, img]
    
    response = model.generate_content(contents)
    return jsonify({"response": response.text})

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
    model = get_model()
    if not model: 
        print("Not configured. Run the app once to set up.")
        return
    chat = model.start_chat()
    print(f"--- Chatting (Type 'exit' to quit) ---")
    while True:
        user_input = input("You: ")
        if user_input.lower() == 'exit': break
        # ... (rest of logic unchanged)
