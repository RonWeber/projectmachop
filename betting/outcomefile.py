from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import json

CURRENT_EVENT_FILE_NAME = "current_event.txt"
PAST_OUTCOMES_FILE_NAME = "past_outcomes.json"

on_files_changed = None

def set_on_files_changed_callback(callback):
    global on_files_changed
    on_files_changed = callback


class CurrentEventHandler(FileSystemEventHandler):
    def on_modified(self, event=None):
        try:
            with open(CURRENT_EVENT_FILE_NAME, 'r') as f:
                current_event_content = f.read()
            
            with open(PAST_OUTCOMES_FILE_NAME, 'r') as f:
                past_outcomes_content = json.load(f)
            
            if on_files_changed:
                on_files_changed(current_event_content, past_outcomes_content)
        except Exception as e:
            print(f"Error reading files: {e}")
            raise e


def start_watching():
    event_handler = CurrentEventHandler()
    observer = Observer()
    observer.schedule(event_handler, path='.', recursive=False)
    observer.start()
    event_handler.on_modified(event=None)  # Trigger the handler once to read the initial state
    return observer

