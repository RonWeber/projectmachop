#!/usr/bin/python

import json
import re

EMERALD_TP_FILEPATH = "C:\\Users\\ROnni\\Programming\\projectmachop\\mondata\\emerald_trainer_parties.h"
EMERALD_SPECIES_FILEPATH = "C:\\Users\\ROnni\\Programming\\projectmachop\\mondata\\species_info.h"
OUT_JSON_FILEPATH = "C:\\Users\\ROnni\\Programming\\projectmachop\\mondata\\out_json.json"

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

    totaled_paries = []
    for pname, party in trainer_parties.items():
        grandTotal = 0
        newParty = []
        for pkmn in party:
            statTotals = CalculateMonStatTotal(species_data, pkmn["species"], pkmn["iv"], pkmn["lvl"])
            pkmn.update(statTotals)
            newParty.append(pkmn)
            grandTotal += statTotals["statTotal"]
        totaled_paries.append({"name": pname,  "grandTotal": grandTotal, "party": newParty})
    
    totaled_paries.sort(key=lambda x: x["grandTotal"])



    # Pretty print the resulting dictionary map
    with open(OUT_JSON_FILEPATH, 'w') as f:
        f.write(json.dumps(totaled_paries, indent=4))  

