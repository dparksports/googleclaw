import os
import sys
import platform
import subprocess
import json
import time
import threading
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
        if file_path.suffix not in ['.py', '.js', '.ts', '.html', '.css', '.c', '.cpp', '.go', '.rs']:
            return
        
        # Debounce
        current_time = time.time()
        if str(file_path) in self.last_processed:
            if current_time - self.last_processed[str(file_path)] < 2:
                return
        
        self.last_processed[str(file_path)] = current_time
        self.process_vibe(file_path)

    def process_vibe(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            vibe_line_index = -1
            instruction = ""
            for i, line in enumerate(lines):
                if "@gemini" in line:
                    vibe_line_index = i
                    instruction = line.split("@gemini")[1].strip()
                    break
            
            if vibe_line_index == -1: return
            
            # Implementation logic
            new_content = self.assistant.get_vibe_implementation(file_path, "".join(lines), instruction)
            if new_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"\n\033[92m[Vibe Applied]\033[0m {file_path.name}: {instruction}")

        except Exception: pass

class SeamlessAssistant:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            print("\033[91m[Error]\033[0m GEMINI_API_KEY not found.")
            sys.exit(1)
        
        try:
            self.client = genai.Client(api_key=self.api_key)
        except Exception as e:
            print(f"\033[91m[Error]\033[0m Failed to initialize Gemini client: {e}")
            sys.exit(1)
            
        self.model_name = 'gemini-1.5-flash'
        self.system_info = {
            "os": platform.system(),
            "cwd": str(Path.cwd()),
            "files": [f.name for f in Path.cwd().glob('*') if f.is_file()][:20] # Context
        }

    def get_assistant_plan(self, user_input):
        prompt = f"""
        You are a Seamless OS Orchestrator. 
        Context: OS={self.system_info['os']}, CWD={self.system_info['cwd']}
        Files in directory: {self.system_info['files']}

        User Wish: "{user_input}"

        Goal: Provide a complete, automated plan to fulfill this wish. 
        
        CRITICAL RULES:
        1. BE A DOER: If a user asks "how to" or for a solution, ALWAYS provide the actions to execute it. Never just explain.
        2. COMPLEX TASKS: For tasks like finding duplicates, resizing images, or log analysis, WRITE A SCRIPT (Python, PowerShell, or Bash) and then add a COMMAND to run it.
        3. PLATFORM SPECIFIC: Use PowerShell (`powershell.exe -ExecutionPolicy Bypass -File ...`) for Windows scripts and Bash for Linux/Mac.
        4. CLEANUP: If you create a temporary script, the last action should be a command to delete it.

        Respond ONLY with a JSON object:
        {{
            "explanation": "A high-level summary of the approach",
            "actions": [
                {{ "type": "write_file", "path": "script_name.ext", "content": "FULL SCRIPT CONTENT" }},
                {{ "type": "command", "content": "shell command to run the script", "is_dangerous": false }},
                {{ "type": "command", "content": "command to delete the script", "is_dangerous": false }}
            ]
        }}
        """
        try:
            response = self.client.models.generate_content(model=self.model_name, contents=prompt)
            content = response.text.strip()
            if content.startswith("```json"): content = content[7:-3].strip()
            return json.loads(content)
        except Exception as e:
            return {"explanation": f"Error: {e}", "actions": []}

    def get_vibe_implementation(self, file_path, full_content, instruction):
        prompt = f"Expert coder task: Update {file_path.name} based on '@gemini {instruction}'. Respond with FULL file content only.\n\n{full_content}"
        try:
            response = self.client.models.generate_content(model=self.model_name, contents=prompt)
            content = response.text.strip()
            if content.startswith("```"):
                lines = content.splitlines()
                if lines[0].startswith("```"): lines = lines[1:]
                if lines[-1].startswith("```"): lines = lines[:-1]
                content = "\n".join(lines)
            return content
        except Exception: return None

    def execute_plan(self, plan):
        print(f"\n\033[95m[PROPOSED ORCHESTRATION PLAN]\033[0m")
        print(f"Summary: {plan['explanation']}")
        
        print(f"\n\033[94mThe following actions will be performed:\033[0m")
        for i, action in enumerate(plan['actions'], 1):
            if action['type'] == 'command':
                danger = " \033[91m[DANGEROUS]\033[0m" if action.get('is_dangerous') else ""
                print(f"  {i}. [EXECUTE] `{action['content']}`{danger}")
            elif action['type'] == 'write_file':
                print(f"  {i}. [CREATE] `{action['path']}`")
                # Show a preview of the script being written
                preview = action['content'].splitlines()
                preview_snippet = "\n      ".join(preview[:5])
                if len(preview) > 5: preview_snippet += "\n      ..."
                print(f"      \033[90mContent Preview:\n      {preview_snippet}\033[0m")

        confirm = input(f"\nDo you want to proceed? (y/n): ").lower()
        if confirm != 'y':
            print("\033[93mOrchestration aborted.\033[0m")
            return

        for action in plan['actions']:
            if action['type'] == 'command':
                cmd = action['content']
                print(f"\033[93mRunning:\033[0m {cmd}")
                subprocess.run(cmd, shell=True)
            
            elif action['type'] == 'write_file':
                path = action['path']
                print(f"\033[92mWriting:\033[0m {path}")
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(action['content'])
        
        print("\n\033[92m✔ All tasks completed successfully.\033[0m")

    def run(self):
        print(f"\n=== Gemini Seamless Orchestrator ({self.system_info['os']}) ===")
        print("I can run commands, write scripts, and watch your code for @gemini tags.")
        print("Type your wish or 'exit' to quit.\n")

        # Start Background Vibe Watcher
        observer = Observer()
        observer.schedule(VibeHandler(self), ".", recursive=True)
        observer.start()

        try:
            while True:
                wish = input(f"Wish > ").strip()
                if not wish: continue
                if wish.lower() in ['exit', 'quit']: break
                
                plan = self.get_assistant_plan(wish)
                if plan['actions']:
                    self.execute_plan(plan)
                else:
                    print(f"\n{plan['explanation']}")
                print()
        except KeyboardInterrupt:
            pass
        finally:
            observer.stop()
            observer.join()
            print("\nGoodbye!")

if __name__ == "__main__":
    assistant = SeamlessAssistant()
    assistant.run()
