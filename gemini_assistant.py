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
        self.active_mode = "auto" # Modes: auto, chat, plan
        
        if not self.api_key:
            print("\033[91m[Error]\033[0m GEMINI_API_KEY not found in environment.")
            sys.exit(1)
        
        try:
            self.client = genai.Client(api_key=self.api_key)
        except Exception as e:
            print(f"\033[91m[Error]\033[0m Failed to initialize Gemini client: {e}")
            sys.exit(1)
            
        self.model_name = self.load_config()
        self.system_info = {
            "os": platform.system(),
            "cwd": str(Path.cwd()),
            "files": [f.name for f in Path.cwd().glob('*') if f.is_file()][:30]
        }

    def load_config(self):
        default = 'gemini-3.1-flash-lite-preview'
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    return config.get("model", default)
            except:
                pass
        return default

    def save_config(self, model_name):
        try:
            with open(self.config_path, 'w') as f:
                json.dump({"model": model_name}, f)
        except Exception as e:
            print(f"Failed to save config: {e}")

    def select_model(self, choice=None):
        try:
            models = [m.name.replace('models/', '') for m in self.client.models.list() 
                     if 'generateContent' in m.supported_actions]
            
            if not choice:
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
            elif choice in models:
                selected = choice
            else:
                print(f"Invalid choice '{choice}', keeping {self.model_name}")
                return self.model_name

            self.save_config(selected)
            print(f"\033[92m[Config]\033[0m Model switched to: {selected}")
            return selected
            
        except Exception as e:
            print(f"Error listing models: {e}. Using {self.model_name}")
            return self.model_name

    def get_assistant_plan(self, user_input):
        mode_instruction = ""
        if self.active_mode == "chat":
            mode_instruction = "FORCE MODE: CHAT. Do not propose actions. Only explain/answer."
        elif self.active_mode == "plan":
            mode_instruction = "FORCE MODE: PLAN. Always provide actions, even for questions (e.g. read the file)."

        prompt = f"""
        You are a Seamless OS Orchestrator. 
        Context: OS={self.system_info['os']}, CWD={self.system_info['cwd']}
        Files in directory: {self.system_info['files']}
        {mode_instruction}

        User Wish: "{user_input}"
        
        MODES:
        1. CHAT: Use ONLY if you can answer the user's wish completely using only the provided context. Do NOT say "I will read" or "I will check"—if you need to do that, use PLAN mode.
        2. PLAN: Use if you need to execute commands, write files, or READ existing files (using 'type' or 'cat') to fulfill the wish.

        CRITICAL RULES:
        1. BE A DOER: In PLAN mode, provide the exact actions to fulfill the wish immediately.
        2. NO EMPTY PROMISES: Never use CHAT mode to describe what you *would* do. If action is needed, provide a PLAN.
        3. READ FILES: If the user asks how a script works and you don't have its content, your PLAN should include a command to display it (e.g., `type filename` on Windows).
        4. SAFE PATHS: On Windows, use raw strings r"C:\\path".
        5. POWERSHELL: When using variables in strings followed by colons, always use ${var}: or $($var): to avoid drive reference errors (e.g., "PID ${id}:").
        6. CLEANUP: Always include a final command to delete temporary scripts, UNLESS the user explicitly asks to keep them.

        Respond ONLY with a JSON object:
        {{
            "type": "chat" or "plan",
            "explanation": "Your direct answer (for chat) or summary of actions (for plan). IMPORTANT: Escape all backslashes properly (e.g., C:\\\\Path).",
            "actions": [
                {{ "type": "write_file", "path": "script.ext", "content": "CONTENT" }},
                {{ "type": "command", "content": "shell command", "is_dangerous": false }}
            ]
        }}
        """
        try:
            response = self.client.models.generate_content(model=self.model_name, contents=prompt)
            content = response.text.strip()
            
            # Robust JSON extraction
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif content.startswith("```"):
                content = content.split("```")[1].strip()
            
            # Find the actual JSON object
            start = content.find("{")
            end = content.rfind("}")
            if start != -1 and end != -1:
                content = content[start:end+1]
            
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                if "Invalid \\escape" in str(e):
                    # Attempt to fix common Windows path escaping issues
                    # Escape backslashes that are not followed by a valid escape char
                    
                    # This is a broad fix: escape all backslashes, then fix already-escaped ones
                    fixed = content.replace("\\", "\\\\")
                    # Fix common legitimate escapes that we just doubled
                    fixed = fixed.replace("\\\\\"", "\\\"").replace("\\\\n", "\\n").replace("\\\\r", "\\r").replace("\\\\t", "\\t")
                    try:
                        return json.loads(fixed)
                    except:
                        pass
                raise e

        except Exception as e:
            return {"type": "chat", "explanation": f"Failed to generate response: {e}", "actions": []}

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

        confirm = input(f"\nExecute these steps? (y/n): ").lower()
        if confirm != 'y':
            print("Aborted.")
            return None

        for action in plan['actions']:
            try:
                if action['type'] == 'command':
                    print(f"  [RUNNING] {action['content']}")
                    result = subprocess.run(action['content'], shell=True, capture_output=True, text=True)
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

    def run(self):
        print(f"\n=== Gemini Seamless Orchestrator ({self.system_info['os']}) ===")
        print("Watching directory for changes... (Add @gemini \"instruction\" to any file to trigger)")
        print("Commands: /model [n], /chat (force inquiry), /plan (force action), /auto (smart), exit")

        observer = Observer()
        observer.schedule(VibeHandler(self), ".", recursive=True)
        observer.start()

        try:
            while True:
                mode_tag = f"[{self.active_mode.upper()}]" if self.active_mode != "auto" else ""
                wish = input(f"\n({self.model_name}){mode_tag} Wish > ").strip()
                if not wish: continue

                # Command Interceptor
                parts = wish.lower().split()
                cmd = parts[0]
                
                if cmd in ['/model', '/config', '/setup']:
                    arg = parts[1] if len(parts) > 1 else None
                    self.model_name = self.select_model(arg)
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
                current_wish = wish
                step_count = 0
                max_steps = 5
                
                while step_count < max_steps:
                    step_count += 1
                    plan = self.get_assistant_plan(current_wish)
                    
                    if plan.get('type') == 'plan' and plan.get('actions'):
                        output = self.execute_plan(plan)
                        
                        if output is None: # Aborted by user
                            break
                            
                        if self.active_mode == 'plan':
                            break
                            
                        print("\033[90m[*] Analyzing output...\033[0m")
                        output_str = output if output.strip() else "(Command executed successfully with no output)"
                        current_wish = (
                            f"Original request: '{wish}'.\n\n"
                            f"We have executed some steps. Command output:\n{output_str}\n\n"
                            "Based on this output, can you now fulfill the original request? "
                            "If yes, respond with type 'chat' and a comprehensive explanation. "
                            "If you need to perform more actions (like reading a specific file mentioned in the output), respond with type 'plan'."
                        )
                    else:
                        explanation = plan.get('explanation')
                        if not explanation:
                            # Debug: what did the model actually return?
                            explanation = f"[Internal Error] Model returned 'chat' but no explanation. Plan: {json.dumps(plan)}"
                        
                        print(f"\n\033[94m[Assistant]\033[0m {explanation}")
                        break
                
                if step_count >= max_steps:
                    print("\033[91m[Error]\033[0m Reached maximum number of steps for this request.")
        except KeyboardInterrupt:
            pass
        finally:
            observer.stop()
            observer.join()
            print("\nShutting down.")


if __name__ == "__main__":
    assistant = SeamlessAssistant()
    assistant.run()