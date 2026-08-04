#!/usr/bin/python

import json

MON_DATA_FILE = "mondata/out_json.json"
PAST_OUTCOMES_FILE = "ipc/past_outcomes.json"

mon_data = {}
with open(MON_DATA_FILE, 'r') as f:
    mon_data = json.load(f)

def ReadPastOutcomes():
    past_outcomes = {}
    with open(PAST_OUTCOMES_FILE, 'r') as f:
        past_outcomes = json.load(f)
    return past_outcomes
