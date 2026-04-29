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
        return {"model": "gemini-3.1-pro-preview", "api_key": ""}
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

@app.route('/api/packet-stats')
def packet_stats():
    ip = request.args.get('ip', '52.110.4.23')
    csv_file = f'packet_stats_{ip.replace(".", "_")}.csv'
    
    if not os.path.exists(csv_file):
        return jsonify({"labels": [], "sent": [], "received": []})
    
    import csv
    with open(csv_file, 'r') as f:
        reader = csv.reader(f)
        lines = list(reader)
        
    if len(lines) <= 1:
        return jsonify({"labels": [], "sent": [], "received": []})
        
    data_lines = lines[1:] # Skip header
    data_lines = data_lines[-60:] # Last 60 points
    
    labels = []
    sent = []
    received = []
    
    for row in data_lines:
        if len(row) >= 4:
            # Timestamp, TargetIP, RxPackets, TxPackets, RxBytes, TxBytes for raw
            # Timestamp, Target_IP, Packets_Sent, Packets_Received for scapy
            labels.append(row[0].split(' ')[1]) # Just the time
            
            # Handle both CSV formats
            if len(row) == 6: 
                # monitor_packets_raw.py format
                sent.append(int(row[3]))
                received.append(int(row[2]))
            else:
                # monitor_packets.py format
                sent.append(int(row[2]))
                received.append(int(row[3]))
                
    return jsonify({
        "labels": labels,
        "sent": sent,
        "received": received
    })

import glob

@app.route('/api/monitored-ips')
def monitored_ips():
    files = glob.glob('packet_stats_*.csv')
    ips = []
    for f in files:
        base = f.replace('packet_stats_', '').replace('.csv', '')
        ip = base.replace('_', '.')
        ips.append(ip)
    return jsonify({"ips": list(set(ips))})

@app.route('/api/start-monitor', methods=['POST'])
def start_monitor():
    target = request.json.get('ip', '').strip()
    if not target:
        return jsonify({"status": "error", "message": "No IP or Process Name provided"}), 400
    
    # 1. Check for Admin Privileges (Required for raw sockets)
    is_admin = False
    try:
        import ctypes
        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        pass
    
    if not is_admin:
        return jsonify({
            "status": "error", 
            "message": "Administrator privileges required. Please restart the Web Server as Administrator."
        }), 403

    # 2. Resolve Process Name to IPs if needed
    ips_to_monitor = []
    if any(c.isalpha() for c in target): # Likely a process name
        try:
            ps_cmd = f"Get-NetTCPConnection -OwningProcess (Get-Process {target}).Id | Where-Object {{ $_.RemoteAddress -notmatch '0.0.0.0|127.0.0.1' }} | Select-Object -ExpandProperty RemoteAddress"
            res = subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True, text=True)
            ips = list(set([line.strip() for line in res.stdout.splitlines() if line.strip()]))
            if not ips:
                return jsonify({"status": "error", "message": f"No active connections found for process '{target}'"}), 404
            ips_to_monitor = ips
        except Exception as e:
            return jsonify({"status": "error", "message": f"Could not find process '{target}': {str(e)}"}), 404
    else:
        ips_to_monitor = [target]

    # 3. Start Monitoring for each IP
    started = []
    try:
        for ip in ips_to_monitor:
            cmd = [sys.executable, 'monitor_packets_raw.py', ip]
            # Use CREATE_NO_WINDOW to keep it clean, but Popen will run it
            subprocess.Popen(cmd, creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0)
            started.append(ip)
        
        return jsonify({
            "status": "success", 
            "message": f"Started monitoring: {', '.join(started)}"
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

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
    model_name = config.get("model", "gemini-3.1-pro-preview")
    
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
            config={'system_instruction': system_instruction, 'response_mime_type': 'application/json'}
        )
        text = response.text.strip()
        
        try:
            # Strip markdown if needed
            json_text = text
            if "```json" in json_text:
                json_text = json_text.split("```json")[1].split("```")[0].strip()
            elif json_text.startswith("```"):
                json_text = json_text.split("```")[1].strip()
            
            # Extract actual JSON object
            start = json_text.find("{")
            end = json_text.rfind("}")
            if start != -1 and end != -1:
                json_text = json_text[start:end+1]
            
            try:
                data = json.loads(json_text)
            except json.JSONDecodeError as e:
                if "Invalid \\escape" in str(e):
                    # Fix common Windows path issues
                    fixed = json_text.replace("\\", "\\\\")
                    fixed = fixed.replace("\\\\\"", "\\\"").replace("\\\\n", "\\n").replace("\\\\r", "\\r").replace("\\\\t", "\\t")
                    data = json.loads(fixed)
                else:
                    raise e

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
    model_name = config.get("model", "gemini-3.1-pro-preview")
    
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
