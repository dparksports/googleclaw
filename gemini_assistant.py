import os
import sys
import platform
import subprocess
import json
import time
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
        if not self.api_key:
            print("\033[91m[Error]\033[0m GEMINI_API_KEY not found in environment.")
            sys.exit(1)
        
        try:
            self.client = genai.Client(api_key=self.api_key)
        except Exception as e:
            print(f"\033[91m[Error]\033[0m Failed to initialize Gemini client: {e}")
            sys.exit(1)
            
        self.model_name = self.select_model()
        self.system_info = {
            "os": platform.system(),
            "cwd": str(Path.cwd()),
            "files": [f.name for f in Path.cwd().glob('*') if f.is_file()][:30]
        }

    def select_model(self):
        try:
            models = [m.name.replace('models/', '') for m in self.client.models.list() 
                     if 'generateContent' in m.supported_actions]
            
            # Prioritize a default if available, else let user choose
            default_model = 'gemini-3.1-pro-preview'
            if default_model not in models:
                default_model = models[0] if models else None

            print("\nAvailable Models:")
            for i, m in enumerate(models, 1):
                print(f"  {i}. {m}")
            
            choice = input(f"\nSelect model [default {default_model}]: ").strip()
            if not choice:
                return default_model
            
            if choice.isdigit() and 1 <= int(choice) <= len(models):
                return models[int(choice)-1]
            elif choice in models:
                return choice
            else:
                print(f"Invalid choice, using {default_model}")
                return default_model
        except Exception as e:
            print(f"Error listing models: {e}. Using gemini-2.0-flash.")
            return 'gemini-2.0-flash'

    def get_assistant_plan(self, user_input):
        prompt = f"""
        You are a Seamless OS Orchestrator. 
        Context: OS={self.system_info['os']}, CWD={self.system_info['cwd']}
        Files in directory: {self.system_info['files']}

        User Wish: "{user_input}"
        Goal: Provide a complete, automated plan to fulfill this wish. 

        CRITICAL RULES:
        1. BE A DOER: Provide the actions to execute the solution immediately.
        2. SCRIPTS: For logic, write a complete script (Python, Bash, or PowerShell).
        3. PLATFORM SPECIFIC: Use PowerShell for Windows and Bash for Linux/Mac.
        4. ROBUSTNESS: When installing dependencies, check if they exist first. Avoid hardcoded `--index-url` or specific CUDA versions unless absolutely necessary for hardware compatibility. Prefer standard `pip install`.
        5. CLEANUP: Always include a final command to delete any temporary scripts created.

        Respond ONLY with a JSON object:
        {{
            "explanation": "Summary of approach",
            "actions": [
                {{ "type": "write_file", "path": "script.ext", "content": "CONTENT" }},
                {{ "type": "command", "content": "shell command", "is_dangerous": false }},
                {{ "type": "command", "content": "rm script.ext", "is_dangerous": false }}
            ]
        }}
        """
        try:
            response = self.client.models.generate_content(model=self.model_name, contents=prompt)
            content = response.text.strip()
            if content.startswith("```json"): content = content[7:-3].strip()
            return json.loads(content)
        except Exception as e:
            return {"explanation": f"Failed to generate plan: {e}", "actions": []}

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
        
        for i, action in enumerate(plan['actions'], 1):
            if action['type'] == 'command':
                print(f"  {i}. \033[94m[EXEC]\033[0m {action['content']}")
            elif action['type'] == 'write_file':
                print(f"  {i}. \033[94m[WRITE]\033[0m {action['path']}")
                # Show preview of file content
                lines = action['content'].splitlines()
                preview = "\n".join([f"      | {l}" for l in lines[:5]])
                if len(lines) > 5: preview += f"\n      | ... ({len(lines)-5} more lines)"
                print(f"\033[90m{preview}\033[0m")

        confirm = input(f"\nExecute these steps? (y/n): ").lower()
        if confirm != 'y':
            print("Aborted.")
            return

        for action in plan['actions']:
            try:
                if action['type'] == 'command':
                    print(f"  [RUNNING] {action['content']}")
                    result = subprocess.run(action['content'], shell=True, capture_output=True, text=True)
                    if result.stdout: print(f"\033[32m{result.stdout}\033[0m")
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

    def run(self):
        print(f"\n=== Gemini Seamless Orchestrator ({self.system_info['os']}) ===")
        print("Watching directory for changes... (Add @gemini \"instruction\" to any file to trigger)")
        print("Commands: /model (change model), exit (quit)")

        observer = Observer()
        observer.schedule(VibeHandler(self), ".", recursive=True)
        observer.start()

        try:
            while True:
                wish = input(f"\nWish > ").strip()
                if not wish: continue

                # Command Interceptor
                if wish.lower() in ['/model', '/config', '/setup']:
                    self.model_name = self.select_model()
                    continue

                if wish.lower() in ['exit', 'quit']: break

                plan = self.get_assistant_plan(wish)
                if plan.get('actions'):
                    self.execute_plan(plan)
                else:
                    print(f"\nAssistant: {plan.get('explanation', 'I cannot fulfill that wish.')}")
        except KeyboardInterrupt:
            pass
        finally:
            observer.stop()
            observer.join()
            print("\nShutting down.")


if __name__ == "__main__":
    assistant = SeamlessAssistant()
    assistant.run()