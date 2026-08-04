import json
import obsws_python as obs
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

cl = obs.ReqClient(host='localhost', port=4455, password='7HQugdW469QBf8l8', timeout=3)

class PastOutcomesHandler(FileSystemEventHandler):
    def on_modified(self, event=None):
        try:
            with open("ipc/past_outcomes.json", 'r') as f:
                past_outcomes_content = json.load(f)
            
            # Update the OBS text source with the new past outcomes
            cl.set_text_gdi_plus(source="Past Outcomes", text=json.dumps(past_outcomes_content, indent=2))
        except Exception as e:
            print(f"Error reading past outcomes file: {e}")
            raise e

if __name__ == "__main__":
    event_handler = PastOutcomesHandler()
    observer = Observer()
    observer.schedule(event_handler, path='ipc', recursive=False)
    observer.start()