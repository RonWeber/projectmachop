from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import json

from tournament_py.tournament import ParseTournamentData

CURRENT_EVENT_FILE_NAME = "ipc\\current_event.txt"
PAST_OUTCOMES_FILE_NAME = "ipc\\past_outcomes.json"

on_files_changed = []

def add_on_files_changed_callback(callback):
    global on_files_changed
    on_files_changed.append(callback)

class CurrentEventHandler(FileSystemEventHandler):
    def on_modified(self, event=None):
        if event and event.src_path != CURRENT_EVENT_FILE_NAME:
            return  # Ignore events that are not for the current event file
        try:
            with open(CURRENT_EVENT_FILE_NAME, 'r') as f:
                current_event_content = f.read()
            
            with open(PAST_OUTCOMES_FILE_NAME, 'r') as f:
                past_outcomes_content = json.load(f)
                tournament_data = ParseTournamentData(past_outcomes_content)
            
            if on_files_changed:
                for callback in on_files_changed:
                    callback(current_event_content, tournament_data)
        except Exception as e:
            print(f"Error reading files: {e}")
            raise e


def start_watching():
    event_handler = CurrentEventHandler()
    observer = Observer()
    observer.schedule(event_handler, path='ipc', recursive=False)
    observer.start()
    event_handler.on_modified(event=None)  # Trigger the handler once to read the initial state
    return observer

