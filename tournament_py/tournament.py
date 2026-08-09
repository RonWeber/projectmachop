#!/usr/bin/python

import json
from dataclasses import dataclass, field
from tournament_py.trainer_class_names import trainer_class_names
import string

MON_DATA_FILE = "mondata/out_json.json"
PAST_OUTCOMES_FILE = "ipc/past_outcomes.json"

@dataclass
class TournamentData:
    outcomes_per_event: dict[int, int] = field(default_factory=dict)
    current_player_json: dict = field(default_factory=dict)
    current_opponent_json: dict = field(default_factory=dict)
    last_player_json: dict = field(default_factory=dict)
    last_opponent_json: dict = field(default_factory=dict)
    last_winner_json: dict = field(default_factory=dict)
    last_loser_json: dict = field(default_factory=dict)
    streak_by_index: dict[int, int] = field(default_factory=dict)
    current_streak: int = 0

mon_data = {}
with open(MON_DATA_FILE, 'r') as f:
    mon_data = json.load(f)

def ReadPastOutcomes():
    past_outcomes = {}
    with open(PAST_OUTCOMES_FILE, 'r') as f:
        past_outcomes = json.load(f)
    return past_outcomes

def TrainerData(index):
    global mon_data
    return mon_data[index]

def ParseTournamentData(past_outcomes):
    playerIndexInList = 0
    opponentIndexInList = 1
    pastOutcomeIndex = 1
    result = TournamentData()
    lastPlayerIndexInList = 0
    lastOpponentIndexInList = 1
    lastWinnerIndex = 0
    lastLoserIndex = 0
    while str(pastOutcomeIndex) in past_outcomes["outcomes"]:
        lastPlayerIndexInList = playerIndexInList
        lastOpponentIndexInList = opponentIndexInList
        outcome = past_outcomes["outcomes"][str(pastOutcomeIndex)]
        result.outcomes_per_event[pastOutcomeIndex] = outcome
        if outcome == 1:
            # -- Player won. Move on to the next opponent.
            # print(TrainerData(playerIndexInList)["name"] + " won against opponent " + TrainerData(opponentIndexInList)["name"] + " in event " + str(pastOutcomeIndex))
            lastWinnerIndex = playerIndexInList
            lastLoserIndex = opponentIndexInList
            result.streak_by_index[playerIndexInList] = result.streak_by_index.get(playerIndexInList, 0) + 1
            opponentIndexInList = 1 + pastOutcomeIndex
        elif outcome == 2:
            # -- Player lost. Opponent becomes the next player, and the next opponent is chosen.
            # print(TrainerData(opponentIndexInList)["name"] + " won against player " + TrainerData(playerIndexInList)["name"] + " in event " + str(pastOutcomeIndex))
            lastWinnerIndex = opponentIndexInList
            lastLoserIndex = playerIndexInList
            result.streak_by_index[opponentIndexInList] = result.streak_by_index.get(opponentIndexInList, 0) + 1
            playerIndexInList = opponentIndexInList
            opponentIndexInList = 1 + pastOutcomeIndex
        else:
            print("Invalid outcome for event " + str(pastOutcomeIndex) + ": " + str(outcome))

        pastOutcomeIndex += 1
    result.current_player_json = TrainerData(playerIndexInList)
    result.current_opponent_json = TrainerData(opponentIndexInList)
    result.last_player_json = TrainerData(lastPlayerIndexInList)
    result.last_opponent_json = TrainerData(lastOpponentIndexInList)
    result.last_winner_json = TrainerData(lastWinnerIndex)
    result.last_loser_json = TrainerData(lastLoserIndex)
    result.current_streak = result.streak_by_index.get(playerIndexInList, 0)
    return result

def TrainerFullName(trainer_json):
    class_id = trainer_json["trainer_class"]
    class_name = trainer_class_names.get(class_id, "Pokemon Trainer")
    return string.capwords(f"{class_name} {trainer_json['character_name']}")