import os
import json
import time
import shutil
import logging
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configuration
HISTORY_DIR = Path(os.environ.get('USERPROFILE', '')) / '.gemini' / 'tmp' / 'googleclaw' / 'chats'
PROCESSED_DIR = Path(r'C:\Users\honey\googleclaw\processed_chats')

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

if not PROCESSED_DIR.exists():
    PROCESSED_DIR.mkdir(parents=True)

class ChatLogHandler(FileSystemEventHandler):
    def __init__(self):
        super().__init__()
        # Track the number of messages processed per file to avoid duplicates
        self.processed_message_counts = {}

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.json'):
            self.handle_event(event.src_path)

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith('.json'):
            self.handle_event(event.src_path)

    def handle_event(self, file_path):
        # Brief sleep to allow the OS to release the file lock after writing
        time.sleep(0.2)
        self.process_log(file_path)

    def process_log(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if 'messages' not in data:
                return

            messages = data['messages']
            file_name = os.path.basename(file_path)
            base_name = os.path.splitext(file_name)[0]
            
            # Determine starting point (where we left off for console logging)
            last_count = self.processed_message_counts.get(file_name, 0)
            new_messages = messages[last_count:]
            self.processed_message_counts[file_name] = len(messages)

            # Process new message pairs for console
            current_user_prompt = None
            for msg in new_messages:
                msg_type = msg.get('type')
                text = self._extract_text(msg)

                if msg_type == 'user':
                    current_user_prompt = text
                elif msg_type == 'gemini' and current_user_prompt:
                    if text.strip():
                        print(f"\n--- New Interaction (Session: {file_name}) ---")
                        print(f"Prompt: {current_user_prompt}")
                        print(f"Response: {text}")
                        print(f"-----------------------")
                        current_user_prompt = None
            
            # --- Readability Enhancements ---
            
            # 1. Save Pretty-Printed JSON
            json_dest = PROCESSED_DIR / file_name
            with open(json_dest, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, sort_keys=True)

            # 2. Generate/Update Markdown File
            md_dest = PROCESSED_DIR / f"{base_name}.md"
            self._write_markdown(data, md_dest)
            
        except json.JSONDecodeError:
            pass
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")

    def _extract_text(self, msg):
        content_list = msg.get('content', [])
        text = ""
        if isinstance(content_list, list):
            for item in content_list:
                if isinstance(item, dict) and 'text' in item:
                    text += item['text']
        elif isinstance(content_list, str):
            text = content_list
        return text

    def _write_markdown(self, data, md_path):
        messages = data.get('messages', [])
        session_id = data.get('sessionId', 'Unknown')
        start_time = data.get('startTime', 'Unknown')
        
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(f"# Gemini Session: {session_id}\n")
            f.write(f"**Started:** {start_time}\n\n---\n\n")
            
            for msg in messages:
                msg_type = msg.get('type').capitalize()
                text = self._extract_text(msg)
                
                if msg_type == 'User':
                    f.write(f"### 👤 User\n{text}\n\n")
                elif msg_type == 'Gemini':
                    if text.strip():
                        f.write(f"### 🤖 Gemini\n{text}\n\n")
                        f.write("---\n\n")
                    elif msg.get('toolCalls'):
                        # Optionally log tool calls
                        for tool in msg.get('toolCalls', []):
                            f.write(f"*🔧 Calling Tool: {tool.get('name')}*\n\n")

if __name__ == '__main__':
    if not HISTORY_DIR.exists():
        logger.error(f"History directory not found: {HISTORY_DIR}")
    else:
        event_handler = ChatLogHandler()
        observer = Observer()
        observer.schedule(event_handler, str(HISTORY_DIR), recursive=False)
        observer.start()
        
        print(f"Monitoring {HISTORY_DIR}...")
        print(f"Copying updates to {PROCESSED_DIR}...")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()
