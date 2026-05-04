import os
import sys
import platform
import subprocess
import json
import time
import re
from google import genai
from dotenv import load_dotenv
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Load API Key
load_dotenv()

class VibeHandler(FileSystemEventHandler):
    def __init__(self, assistant):
        self.assistant = assistant
        self.last_processed = {} 

    def on_modified(self, event):
        if event.is_directory: return
        file_path = Path(event.src_path)
        # Added more extensions for versatility
        if file_path.suffix.lower() not in ['.py', '.js', '.ts', '.html', '.css', '.c', '.cpp', '.go', '.rs', '.php', '.java', '.pyi']:
            return
        
        # Debounce to prevent multiple triggers on a single save
        current_time = time.time()
        if str(file_path) in self.last_processed:
            if current_time - self.last_processed[str(file_path)] < 1.5:
                return
        
        self.last_processed[str(file_path)] = current_time
        self.process_vibe(file_path)

    def process_vibe(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            vibe_line_index = -1
            instruction = ""
            marker = "@gemini" + ' "'
            for i, line in enumerate(lines):
                if marker in line:
                    vibe_line_index = i
                    # Capture text between the double quotes after @gemini
                    try:
                        instruction = line.split(marker)[1].split('"')[0]
                    except IndexError:
                        instruction = ""
                    break
            
            if vibe_line_index == -1 or not instruction: return
            
            print(f"\n\033[94m[Vibe Detected]\033[0m Processing instruction in {file_path.name}...")
            
            # Request the updated implementation
            new_content = self.assistant.get_vibe_implementation(file_path, "".join(lines), instruction)
            
            if new_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"\033[92m[Vibe Applied]\033[0m {file_path.name}: {instruction}")
            else:
                print(f"\033[91m[Vibe Failed]\033[0m No content returned for {file_path.name}")

        except Exception as e:
            print(f"\033[91m[Vibe Error]\033[0m {e}")

class SeamlessAssistant:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.config_path = Path("assistant_config.json")
        self.active_mode = "auto"
        self.provider = "google" # google, ollama, local
        
        self.config = self.load_config()
        self.model_name = self.config.get("model", "gemini-3.1-flash-lite-preview")
        self.model_name_display = self.config.get("model_name_display", self.model_name)
        self.provider = self.config.get("provider", "google")
        
        if self.provider == "google":
            if not self.api_key:
                print("\033[91m[Error]\033[0m GEMINI_API_KEY not found.")
                sys.exit(1)
            self.client = genai.Client(api_key=self.api_key)
        
        self.system_info = {
            "os": platform.system(),
            "cwd": str(Path.cwd()),
            "files": [f.name for f in Path.cwd().glob('*') if f.is_file()][:30]
        }
        self.chat = None
        self.local_url = self.config.get("local_url", "http://localhost:11434")

    def load_config(self):
        default = {"model": "gemini-3.1-flash-lite-preview", "provider": "google"}
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            except: pass
        return default

    def save_config(self, model_name, provider=None):
        try:
            if provider is None:
                provider = self.provider
            with open(self.config_path, 'w') as f:
                json.dump({"model": model_name, "provider": provider}, f)
        except Exception as e:
            print(f"Failed to save config: {e}")


    def select_model(self, choice=None):
        try:
            if self.provider == "local":
                print("\n\033[93m[Local Provider]\033[0m To change local models or engines (vLLM / llama.cpp), close this and run:")
                print("  python local_llm_manager.py")
                return self.model_name
                
            if self.provider == "google":
                models = [m.name.replace('models/', '') for m in self.client.models.list() 
                         if 'generateContent' in m.supported_actions]
            else:
                models = []
            
            if not choice:
                if not models:
                    print(f"\nProvider '{self.provider}' does not support model listing.")
                    choice = input(f"Enter model name [current: {self.model_name}]: ").strip()
                else:
                    print("\nAvailable Models:")
                    for i, m in enumerate(models, 1):
                        star = "*" if m == self.model_name else " "
                        print(f"  {i}. {star} {m}")
                    
                    choice = input(f"\nSelect model [current: {self.model_name}]: ").strip()
            
            selected = self.model_name
            if not choice:
                return selected
            
            if choice.isdigit() and 1 <= int(choice) <= len(models):
                selected = models[int(choice)-1]
            elif choice in models or not models: # Allow manual entry if no model list
                selected = choice
            else:
                print(f"Invalid choice '{choice}', keeping {self.model_name}")
                return self.model_name

            self.save_config(selected, self.provider)
            print(f"\033[92m[Config]\033[0m Model switched to: {selected}")
            return selected
            
        except Exception as e:
            print(f"Error listing models: {e}. Using {self.model_name}")
            return self.model_name

    def setup_chat(self):
        # We need a system instruction that is compatible across providers
        self.system_instruction = f"""
        You are a Seamless OS Orchestrator. 
        Context: OS={self.system_info['os']}, CWD={self.system_info['cwd']}
        
        CRITICAL RULES:
        1. BE A DOER: In PLAN mode, provide the exact actions to fulfill the wish immediately.
        2. NO EMPTY PROMISES: Never use CHAT mode to describe what you *would* do. If action is needed, provide a PLAN.
        3. READ FILES: If the user asks how a script works and you don't have its content, your PLAN should include a command to display it (e.g., `type filename` on Windows).
        4. SAFE PATHS: On Windows, use raw strings r"C:\\path".
        5. POWERSHELL: When using variables in strings followed by colons, always use ${var}: or $($var): to avoid drive reference errors.
        6. WINDOWS: You are in a PowerShell environment. Do NOT prefix commands with 'powershell -Command'. Just write the PowerShell code directly.
        7. CLEANUP: Always include a final command to delete temporary scripts, UNLESS the user explicitly asks to keep them.
        8. WEB REQUESTS: On Windows, always use 'curl.exe' instead of 'curl' to bypass the problematic Invoke-WebRequest alias.

        Respond ONLY with a JSON object:
        {{
            "type": "chat" or "plan",
            "explanation": "Your direct answer (for chat) or summary of actions (for plan). Escape backslashes.",
            "actions": [
                {{ "type": "write_file", "path": "script.ext", "content": "CONTENT" }},
                {{ "type": "command", "content": "shell command", "is_dangerous": false }}
            ]
        }}
        """
        
        if self.provider == "google":
            self.chat = self.client.chats.create(
                model=self.model_name,
                config={
                    'system_instruction': self.system_instruction,
                    'response_mime_type': 'application/json'
                }
            )
        else:
            self.chat_history = [{"role": "system", "content": self.system_instruction}]

    def _call_local_llm(self, prompt):
        import requests
        import threading
        import itertools
        headers = {"Content-Type": "application/json"}
        
        # If the model name is a local file path (llama.cpp), we need to extract just the filename
        # or ask the server what model it is currently running.
        actual_model = self.model_name
        if actual_model and ("/" in actual_model or "\\" in actual_model):
            try:
                # Query the server for the loaded model name
                res = requests.get(f"{self.local_url}/v1/models")
                if res.status_code == 200:
                    models_data = res.json()
                    # llama-server returns a list directly or in a 'data' key
                    models = models_data.get("data", models_data) if isinstance(models_data, dict) else models_data
                    if models and isinstance(models, list):
                        actual_model = models[0].get("id", models[0].get("name", self.model_name))
            except:
                pass
                
        # Truncate prompt to prevent 400 errors from context overflow
        # Most local models have 4k-32k context. 12k chars is safe for ~3k-4k tokens.
        safe_prompt = prompt
        if len(safe_prompt) > 12000:
            safe_prompt = safe_prompt[:6000] + "\n... [TRUNCATED] ...\n" + safe_prompt[-6000:]

        payload = {
            "model": actual_model,
            "messages": self.chat_history + [{"role": "user", "content": safe_prompt}],
            "response_format": {"type": "json_object"}
        }
        
        # --- Loading Animation & Diagnostics ---
        stop_event = threading.Event()
        def spinner():
            chars = itertools.cycle(['|', '/', '-', '\\'])
            start_time = time.time()
            last_status_time = 0
            status_text = ""
            gpu_text = ""
            milestone_30 = False
            milestone_60 = False
            
            while not stop_event.is_set():
                current_time = time.time()
                elapsed = current_time - start_time
                
                # Poll every 2 seconds to not overwhelm the system
                if current_time - last_status_time > 2.0:
                    # 1. Check Tokens
                    try:
                        res = requests.get(f"{self.local_url}/slots", timeout=0.5)
                        if res.status_code == 200:
                            slots = res.json()
                            active = [s for s in slots if str(s.get('state', '0')) not in ['0', 'idle', '0.0']]
                            if active:
                                decoded = active[0].get('n_decoded', 0)
                                status_text = f" | Tokens: {decoded}"
                    except:
                        pass
                    
                    # 2. Check GPU (Hidden window on Windows)
                    try:
                        creationflags = 0
                        if platform.system() == "Windows":
                            creationflags = getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000)
                        result = subprocess.run(
                            ["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"],
                            capture_output=True, text=True, check=True, creationflags=creationflags
                        )
                        util = result.stdout.strip().split('\n')[0]
                        gpu_text = f" | GPU: {util}%"
                    except:
                        pass
                    
                    last_status_time = current_time

                # Auto-inform milestones
                if int(elapsed) == 30 and not milestone_30:
                    sys.stdout.write(f'\r\033[K\033[90m[System] The AI is working on a complex task. Still actively processing...{gpu_text}\033[0m\n')
                    milestone_30 = True
                if int(elapsed) == 60 and not milestone_60:
                    sys.stdout.write(f'\r\033[K\033[93m[System] This is taking longer than usual, but the engine is still responding...{status_text}\033[0m\n')
                    milestone_60 = True

                sys.stdout.write(f'\r\033[93m[*] AI Crunching ({int(elapsed)}s){status_text}{gpu_text} {next(chars)}\033[0m ')
                sys.stdout.flush()
                time.sleep(0.1)
            sys.stdout.write('\r\033[K') # Clear the line when done
            
        t = threading.Thread(target=spinner)
        t.start()
        
        try:
            res = requests.post(f"{self.local_url}/v1/chat/completions", json=payload, headers=headers)
            res.raise_for_status()
            data = res.json()
            content = data['choices'][0]['message']['content']
            self.chat_history.append({"role": "user", "content": safe_prompt})
            self.chat_history.append({"role": "assistant", "content": content})
            return content
        except Exception as e:
            return json.dumps({"type": "chat", "explanation": f"Local LLM Error: {e}"})
        finally:
            stop_event.set()
            t.join()

    def get_assistant_plan(self, user_input, is_followup=False):
        if self.chat is None:
            self.setup_chat()

        mode_instruction = ""
        if self.active_mode == "chat":
            mode_instruction = "FORCE MODE: CHAT. Do not propose actions."
        elif self.active_mode == "plan":
            mode_instruction = "FORCE MODE: PLAN. Always provide actions."

        context = f"Files in directory: {self.system_info['files']}\n{mode_instruction}"
        prompt = f"{context}\n\nUser Wish: \"{user_input}\"" if not is_followup else f"Command Output:\n{user_input}\n\nBased on this, fulfill original wish."

        content = ""
        if self.provider == "google":
            response = self.chat.send_message(prompt)
            content = response.text.strip()
        else:
            content = self._call_local_llm(prompt)
            
        # JSON extraction...
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif content.startswith("```"):
            content = content.split("```")[1].strip()
        
        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1:
            content = content[start:end+1]
        
        try:
            return json.loads(content)
        except:
            return {"type": "chat", "explanation": content}


    def get_vibe_implementation(self, file_path, full_content, instruction):
        # Specific instructions to the model to ensure the @gemini tag is consumed/removed
        prompt = (
            f"Expert coder task: Update '{file_path.name}' based on the instruction: '{instruction}'.\n"
            f"IMPORTANT: Return the FULL file content. Ensure the '@gemini' instruction line is removed from the output.\n"
            f"Do not include any preamble, only the raw file content.\n\n"
            f"Current File Content:\n{full_content}"
        )
        try:
            response = self.client.models.generate_content(model=self.model_name, contents=prompt)
            content = response.text.strip()
            # Remove Markdown code blocks if present
            if content.startswith("```"):
                lines = content.splitlines()
                if lines[0].startswith("```"): lines = lines[1:]
                if lines[-1].startswith("```"): lines = lines[:-1]
                content = "\n".join(lines)
            return content
        except Exception as e:
            print(f"Model Error: {e}")
            return None

    def execute_plan(self, plan):
        print(f"\n\033[95m[PLAN]\033[0m {plan['explanation']}")
        captured_output = []
        
        for i, action in enumerate(plan['actions'], 1):
            if action['type'] == 'command':
                print(f"  {i}. \033[94m[EXEC]\033[0m {action['content']}")
            elif action['type'] == 'write_file':
                print(f"  {i}. \033[94m[WRITE]\033[0m {action['path']}")
                # Show preview of file content
                lines = action['content'].splitlines()
                preview_lines = []
                for line in lines[:5]:
                    preview_lines.append(f"      | {line}")
                
                preview = "\n".join(preview_lines)
                if len(lines) > 5:
                    preview += f"\n      |\n      | ... ({len(lines)-5} more lines)"
                print(f"\033[90m{preview}\033[0m")

        confirm = input(f"\nExecute these steps? (Y/n): ").lower()
        if confirm not in ['y', '']:
            print("Aborted.")
            return None

        for action in plan['actions']:
            try:
                if action['type'] == 'command':
                    print(f"  [RUNNING] {action['content']}")
                    cmd = action['content']
                    
                    if platform.system() == 'Windows':
                        # Use -Command - to read from stdin, avoiding quoting/expansion issues
                        run_cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", "-"]
                        result = subprocess.run(run_cmd, input=cmd, capture_output=True, text=True)
                    else:
                        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                        
                    if result.stdout:
                        print(f"\033[32m{result.stdout}\033[0m")
                        captured_output.append(result.stdout)
                    if result.returncode != 0:
                        print(f"\033[91m[Command Failed]\033[0m\n{result.stderr}")
                        break
                elif action['type'] == 'write_file':
                    print(f"  [WRITING] {action['path']}")
                    with open(action['path'], 'w', encoding='utf-8') as f:
                        f.write(action['content'])
            except Exception as e:
                print(f"\033[91m[Execution Error]\033[0m {e}")
                break
        
        print("\033[92m✔ Task completed.\033[0m")
        return "\n".join(captured_output)

    def ensure_local_server(self):
        if self.provider != "local":
            return
            
        import requests
        try:
            res = requests.get(f"{self.local_url}/v1/models", timeout=1.0)
            if res.status_code == 200:
                return
        except requests.exceptions.RequestException:
            pass

        print("\n\033[93m[System]\033[0m Local AI server not responding. Launching it now...")
        
        if platform.system() == "Windows":
            subprocess.Popen(["cmd.exe", "/c", "start", "Local AI Engine", sys.executable, "local_llm_manager.py", "start"])
        else:
            subprocess.Popen(["x-terminal-emulator", "-e", sys.executable, "local_llm_manager.py", "start"])
            
        print("\033[90m[*] Waiting for server to initialize (you may need to answer prompts in the new window)...\033[0m")
        for _ in range(300):
            try:
                if requests.get(f"{self.local_url}/v1/models", timeout=1.0).status_code == 200:
                    print("\033[92m[System]\033[0m Server is fully loaded and ready!")
                    return
            except requests.exceptions.RequestException:
                pass
            time.sleep(2)
            
        print("\033[91m[Error]\033[0m Timed out waiting for the local server.")

    def run(self):
        print(f"\n=== Gemini Seamless Orchestrator ({self.system_info['os']}) ===")
        print("Watching directory for changes... (Add @gemini \"instruction\" to any file to trigger)")
        print("Commands: /model [n], /chat (force inquiry), /plan (force action), /auto (smart), /clear (reset memory), exit")

        observer = Observer()
        observer.schedule(VibeHandler(self), ".", recursive=True)
        observer.start()
        
        self.ensure_local_server()
        self.setup_chat()

        try:
            while True:
                mode_tag = f"[{self.active_mode.upper()}]" if self.active_mode != "auto" else ""
                wish = input(f"\n({self.model_name_display}){mode_tag} Wish > ").strip()
                if not wish: continue

                # Command Interceptor
                parts = wish.lower().split()
                cmd = parts[0]
                
                if cmd in ['/model', '/config', '/setup']:
                    arg = parts[1] if len(parts) > 1 else None
                    self.model_name = self.select_model(arg)
                    self.ensure_local_server()
                    self.setup_chat() # Reset memory for new model
                    continue
                
                if cmd in ['/clear', '/reset']:
                    self.setup_chat()
                    print("\033[92m[System]\033[0m Chat history cleared.")
                    continue
                
                if cmd in ['/chat', '/q']:
                    self.active_mode = "chat"
                    print("\033[94m[Mode]\033[0m Switched to CHAT (Question) mode.")
                    continue
                
                if cmd in ['/plan', '/p']:
                    self.active_mode = "plan"
                    print("\033[94m[Mode]\033[0m Switched to PLAN (Action) mode.")
                    continue
                
                if cmd in ['/auto', '/a']:
                    self.active_mode = "auto"
                    print("\033[94m[Mode]\033[0m Switched to AUTO (Smart) mode.")
                    continue

                if wish.lower() in ['exit', 'quit']: break

                # Main Orchestration Loop
                step_count = 0
                max_steps = 5
                
                is_followup = False
                current_prompt = wish
                
                while step_count < max_steps:
                    step_count += 1
                    plan = self.get_assistant_plan(current_prompt, is_followup=is_followup)
                    
                    if plan.get('type') == 'plan' and plan.get('actions'):
                        output = self.execute_plan(plan)
                        
                        if output is None: # Aborted by user
                            break
                            
                        if self.active_mode == 'plan':
                            break
                            
                        print("\033[90m[*] Analyzing output...\033[0m")
                        output_str = output if output.strip() else "(Command executed successfully with no output)"
                        
                        current_prompt = output_str
                        is_followup = True
                        
                        if step_count == max_steps:
                            cont = input(f"\n\033[93m[Warning]\033[0m Reached {max_steps} steps. Continue investigation? (Y/n): ").strip().lower()
                            if cont == 'y' or cont == '':
                                max_steps += 5
                            else:
                                print("\033[91m[Error]\033[0m Investigation halted by user.")
                                break
                    else:
                        explanation = plan.get('explanation')
                        if not explanation:
                            # Debug: what did the model actually return?
                            explanation = f"[Internal Error] Model returned 'chat' but no explanation. Plan: {json.dumps(plan)}"
                        
                        print(f"\n\033[94m[Assistant]\033[0m {explanation}")
                        break
        except KeyboardInterrupt:
            pass
        finally:
            observer.stop()
            observer.join()
            print("\nShutting down.")

if __name__ == "__main__":
    assistant = SeamlessAssistant()
    assistant.run()