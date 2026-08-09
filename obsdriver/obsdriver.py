import json
import string
import obsws_python as obs
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
from pathlib import Path
from betting.outcomefile import start_watching, add_on_files_changed_callback
from tournament_py.trainer_class_names import trainer_class_names
from tournament_py.tournament import TrainerFullName
from tournament_py.trainer_sprites_by_class import SpritePerClassTable

cl = obs.ReqClient(host='localhost', port=4455, password='7HQugdW469QBf8l8', timeout=3)
PAST_OUTCOMES_FILE_NAME = "ipc\\past_outcomes.json"
CURRENT_PATH = Path(__file__).resolve().parent.parent
SPRITES_PATH = str(CURRENT_PATH / "sprites")
    
def TrainerNameNewline(trainer_json):
    class_id = trainer_json["trainer_class"]
    class_name = trainer_class_names.get(class_id, "Pokemon Trainer")
    return f"{string.capwords(class_name)}\n{string.capwords(trainer_json['character_name'])}"

def ChangeImage(source_name, new_image_path):
    try:
        settings = {"file": new_image_path}
        cl.set_input_settings(name=source_name, settings=settings, overlay=True)
    except Exception as e:
        print(f"Error updating image source '{source_name}': {e}")

def ChangeText(source_name, new_text):
    try:
        settings = {"text": new_text}
        cl.set_input_settings(name=source_name, settings=settings, overlay=True)
    except Exception as e:
        print(f"Error updating text source '{source_name}': {e}")

def Update(_, tournament_data):
    print(f"Player name: {TrainerFullName(tournament_data.current_player_json)}")
    ChangeText("Player", TrainerNameNewline(tournament_data.current_player_json))
    ChangeText("Opponent", TrainerNameNewline(tournament_data.current_opponent_json))
    playerPic = tournament_data.current_player_json['trainer_pic']
    opponentPic = tournament_data.current_opponent_json['trainer_pic']
    print(f"Player pic: {playerPic}, Opponent pic: {opponentPic}")
    print(f"Player sprite: {SpritePerClassTable.get(playerPic, 'ASDsasda')}, Opponent sprite: {SpritePerClassTable.get(opponentPic, 'xsas')}")
    playerImagePath = SPRITES_PATH + "/" + SpritePerClassTable.get(playerPic, "")
    opponentImagePath = SPRITES_PATH + "/" + SpritePerClassTable.get(opponentPic, "")
    ChangeImage("PlayerImage", playerImagePath)
    ChangeImage("OpponentImage", opponentImagePath)
    ChangeText("WinStreak", str(tournament_data.current_streak))

# class PastOutcomesHandler(FileSystemEventHandler):
#     def on_modified(self, event=None):
#         print(f"Detected change in past_outcomes.json: {event.src_path if event else 'No event'}")
#         if event and event.src_path != PAST_OUTCOMES_FILE_NAME:
#             return  # Ignore events that are not for the past outcomes file
#         try:
#             with open(PAST_OUTCOMES_FILE_NAME, 'r') as f:
#                 past_outcomes_content = json.load(f)

#             textSettings = {"text": "YOOOOOOO!"}
#             # Update the OBS text source with the new past outcomes
#             cl.set_input_settings(name="Player", settings=textSettings, overlay=True)
#         except Exception as e:
#             print(f"Error reading past outcomes file: {e}")
#             raise e

def Initialize():
    print("Initializing OBS driver...")
    add_on_files_changed_callback(Update)

if __name__ == "__main__":
    Initialize()
