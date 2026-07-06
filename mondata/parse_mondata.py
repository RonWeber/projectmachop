#!/usr/bin/python

import json
import re

EMERALD_TP_FILEPATH = "C:\\Users\\ROnni\\Programming\\projectmachop\\mondata\\emerald_trainer_parties.h"
EMERALD_SPECIES_FILEPATH = "C:\\Users\\ROnni\\Programming\\projectmachop\\mondata\\species_info.h"
EMERALD_TRAINERS_FILEPATH = "C:\\Users\\ROnni\\Programming\\projectmachop\\mondata\\emerald_trainers.h"
OUT_JSON_FILEPATH = "C:\\Users\\ROnni\\Programming\\projectmachop\\mondata\\out_json.json"
PROBLEM_TRAINERS_JSON_FILEPATH = "C:\\Users\\ROnni\\Programming\\projectmachop\\mondata\\problem_trainers.json"
POTENTIAL_REFIGHTS_JSON_FILEPATH = "C:\\Users\\ROnni\\Programming\\projectmachop\\mondata\\potential_refights.json"

STATS = ["HP", "Attack", "Defense", "Speed", "SpAttack", "SpDefense"]

def parse_trainer_parties(file_content):
    parties = {}

    # Regex to find each trainer block and capture the struct name and its inner content
    # Looks for 'struct ... struct_name[] = { inner_content };'
    struct_pattern = re.compile(
        r"struct\s+\w+\s+(\s*\w+)\s*\[\]\s*=\s*\{(.*?)\};", re.DOTALL
    )

    # Regex to capture individual pokemon blocks inside a struct
    mon_pattern = re.compile(r"\{([^}]+)\}", re.DOTALL)

    # Regexes to extract specific fields within a pokemon block
    iv_pattern = re.compile(r"\.iv\s*=\s*(\d+)")
    lvl_pattern = re.compile(r"\.lvl\s*=\s*(\d+)")
    species_pattern = re.compile(r"\.species\s*=\s*([A-Z0-9_]+)")

    # Find all trainer structs in the file
    for struct_match in struct_pattern.finditer(file_content):
        struct_name = struct_match.group(1).strip()
        inner_content = struct_match.group(2)

        parties[struct_name] = []

        # Find all individual Pokémon blocks within this trainer's struct
        for mon_match in mon_pattern.finditer(inner_content):
            mon_data = mon_match.group(1)

            # Extract fields (defaulting to None or 0 if missing)
            iv_match = iv_pattern.search(mon_data)
            lvl_match = lvl_pattern.search(mon_data)
            species_match = species_pattern.search(mon_data)

            if species_match:  # Only add if we found a valid species
                pokemon = {
                    "species": species_match.group(1),
                    "lvl": int(lvl_match.group(1)) if lvl_match else None,
                    "iv": int(iv_match.group(1)) if iv_match else 0,
                }
                parties[struct_name].append(pokemon)

    return parties

def parse_mon(file_content):
    mon = {}
    poke_pattern = re.compile(
        r"\[(\w+)\]\s*=\s*\{(.*?noFlip = (TRUE|FALSE),\s*)\}", re.DOTALL
    )

    stat_patterns = {}

    for stat in STATS:
        stat_patterns[stat] = re.compile(r"\.base" + stat + r"\s*=\s*(\d+)")


    for poke_match in poke_pattern.finditer(file_content):
        name = poke_match.group(1)
        inner_content = poke_match.group(2)
        mon[name] = {}
        for stat, pattern in stat_patterns.items():
            match = pattern.search(inner_content)
            if not match:
                raise RuntimeError("No match")
            mon[name][stat] = int(match.group(1))

    return mon

def parse_trainer_list(file_content):
    trainers = {}
    description_pattern = r"// Description:\s*\"(.*?)\""
    trainer_class_pattern = r"trainerClass\s*=\s*(\w*),"
    trainer_name_pattern = r"trainerName\s*=\s*_\(\"(.*?)\"\),"
    party_pattern = r"party\s*=\s*\w*\((\w*)\),"
    trainer_pattern = re.compile(
        r"\[(\w+)\]\s+=\s*\{.*?" + 
        description_pattern + ".*?" +
        trainer_class_pattern + ".*?" +
        trainer_name_pattern + ".*?" +
        party_pattern +
        r"\s*\},", re.DOTALL
    )

    i = 0
    for match in trainer_pattern.finditer(file_content):
        # print(match.group(0))
        print(i, i - 855 + 89, match.group(1), match.group(2), match.group(3), match.group(4), match.group(5))
        unique_name = match.group(1)
        description = match.group(2)
        class_name = match.group(3)
        character_name = match.group(4)
        party_id = match.group(5)
        trainers[party_id] = {
            "id": unique_name,
            "description": description,
            "class_name": class_name,
            "character_name": character_name,
            "party_id": party_id,
            "index": i,
            "problems": [],
        }
        i += 1
    if len(trainers) != 1509:
        print("Warning: Expected 1509 trainers, but found", len(trainers))
    return trainers
        
def CalculateMonStatTotal(speciesList, species, iv, lvl):
    specData = speciesList[species]
    statTotal = 0
    result = {}
    for stat in STATS:
        if stat == "HP":
            n = 2 * specData[stat] + iv;
            valInStat = ((n * lvl) // 100) + lvl + 10
        else:
            valInStat = (((2 * specData[stat] + iv) * lvl) // 100) + 5
        result[stat] = valInStat
        statTotal += valInStat
    result["statTotal"] = statTotal
    return result


if __name__ == "__main__":
    with open(EMERALD_TP_FILEPATH, 'r') as f:
        c_file_data = f.read()
        trainer_parties = parse_trainer_parties(c_file_data)

    with open(EMERALD_SPECIES_FILEPATH, 'r') as f:
        emerald_file_data = f.read()
        species_data = parse_mon(emerald_file_data)  

    with open(EMERALD_TRAINERS_FILEPATH, 'r') as f:
        trainers = parse_trainer_list(f.read()) 

    class_name_desc_counts = {}
    trainer_numbers_list = {}
    trainer_number_match = re.compile(r"(\w*?)_(\d+)$")
    for trainer in trainers.values():
        class_name = trainer["class_name"] + " " + trainer["character_name"] + " " + trainer["description"]
        if class_name not in class_name_desc_counts:
            class_name_desc_counts[class_name] = 0
        class_name_desc_counts[class_name] += 1

        match = trainer_number_match.match(trainer["id"])
        if match:
            base_name = match.group(1)
            number = int(match.group(2))
            if base_name not in trainer_numbers_list:
                trainer_numbers_list[base_name] = []
            trainer_numbers_list[base_name].append(number)

    trainer_numbers_list = dict(sorted(trainer_numbers_list.items(), key=lambda x: len(x[1]), reverse=True))

    with open(POTENTIAL_REFIGHTS_JSON_FILEPATH, 'w') as f:
        print("Numbered Trainers: ", len(trainer_numbers_list))
        f.write(json.dumps(trainer_numbers_list, indent=4))
    parties_missing_trainer_info = []

    totaled_paries = []
    for pname, party in trainer_parties.items():
        grandTotal = 0
        newParty = []
        for pkmn in party:
            statTotals = CalculateMonStatTotal(species_data, pkmn["species"], pkmn["iv"], pkmn["lvl"])
            pkmn.update(statTotals)
            newParty.append(pkmn)
            grandTotal += statTotals["statTotal"]
        if pname not in trainers:
            parties_missing_trainer_info.append(pname)
        else:
            if not party:
                trainers[pname]["problems"].append("empty_party")
            trainers[pname]["has_party"] = True
        if trainers[pname]["description"] != "SKIP":
            totaled_paries.append({
                "name": pname,
                "trainer_id": trainers[pname]["id"] if pname in trainers else None,
                "description": trainers[pname]["description"] if pname in trainers else "",
                "index": trainers[pname]["index"],
                "grandTotal": grandTotal,
                "party": newParty})
    
    totaled_paries.sort(key=lambda x: x["grandTotal"])

    for tparty, trainer in trainers.items():
        class_name = trainer["class_name"] + " " + trainer["character_name"] + " " + trainer["description"]
        if class_name_desc_counts[class_name] > 1:
            trainer["problems"].append("redundant_class_name_desc")
        if tparty in parties_missing_trainer_info:
            trainer["problems"].append("no_party_info")
        if "has_party" not in trainer:
            trainer["problems"].append("no_party_info")

    problematic_trainers = [trainer for trainer in trainers.values() if trainer["problems"] and trainer["description"] != "SKIP"]
    print("Problematic Trainers: ", len(problematic_trainers))

    problematic_trainers.sort(key=lambda x: x["character_name"])

    # Pretty print the resulting dictionary map
    with open(OUT_JSON_FILEPATH, 'w') as f:
        f.write(json.dumps(totaled_paries, indent=4))  

    with open(PROBLEM_TRAINERS_JSON_FILEPATH, 'w') as f:
        f.write(json.dumps(problematic_trainers, indent=4))  
