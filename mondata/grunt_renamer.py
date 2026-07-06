#!/usr/bin/python

import json
import re

EMERALD_TRAINERS_FILEPATH = "C:\\Users\\ROnni\\Programming\\projectmachop\\mondata\\emerald_trainers.h"


def parse_trainer_list(file_content):
    trainers = {}
    trainer_class_pattern = r"trainerClass\s*=\s*(\w*),"
    trainer_name_pattern = r"trainerName\s*=\s*_\(\")(.*?)(\"\),"
    party_pattern = r"party\s*=\s*\w*\((\w*)\),"
    trainer_pattern = re.compile(
        r"(\[(\w+)\]\s+=\s*\{.*?" + 
        trainer_class_pattern + ".*?" +
        trainer_name_pattern + ".*?" +
        party_pattern +
        r"\s*},)", re.DOTALL
    )

    i = 0
    grunt_count_per_class_name = {}

    def rename_grunt(match):
        nonlocal i
        nonlocal grunt_count_per_class_name
        all_pre_name = match.group(1)
        unique_name = match.group(2)
        class_name = match.group(3)
        character_name = match.group(4)
        all_post_name = match.group(5)
        party_id = match.group(6)
        new_character_name = character_name
        # print(f"Match {i}: unique_name={unique_name}, class_name={class_name}, character_name={character_name}, party_id={party_id}")
        if character_name == "GRUNT":
            if class_name not in grunt_count_per_class_name:
                grunt_count_per_class_name[class_name] = 0
            grunt_count_per_class_name[class_name] += 1
            new_character_name = f"GRUNT {grunt_count_per_class_name[class_name]}"
            print("Renaming grunt: ", unique_name, class_name, character_name, party_id, "->", new_character_name)
         
        i += 1
        return f"{all_pre_name}{new_character_name}{all_post_name}"
    
    replacement = trainer_pattern.sub(rename_grunt, file_content)
    # print(replacement)
    return replacement

if __name__ == "__main__":
    with open(EMERALD_TRAINERS_FILEPATH, 'r') as f:
        c_file_data = f.read()
        replacement = parse_trainer_list(c_file_data)
    with open(EMERALD_TRAINERS_FILEPATH, 'w') as f:
        f.write(replacement)
        
