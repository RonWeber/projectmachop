json = require("json")

PAST_OUTCOMES_FILE = BasePath .. "ipc/past_outcomes.json"

MON_DATA_FILE = BasePath .. "mondata/out_json.json"
Mondata = {}
CHEAT_OFFSET = 119

local monDataFile = io.open(MON_DATA_FILE, "r")
if monDataFile then
    local content = monDataFile:read("*all")
    Mondata = json.decode(content)
    monDataFile:close()
else
    console:log("Error: Mondata file not found. Please ensure the file exists at the specified path.")
end

PastOutcomes = {}

function ReadPastOutcomes()
    local file = io.open(PAST_OUTCOMES_FILE, "r")
    if file then
        local content = file:read("*all")
        PastOutcomes = json.decode(content)
        file:close()
    else
        console:log("Error: Past outcomes file not found. Starting with an empty list.")
        PastOutcomes = {}
    end
end

ReadPastOutcomes()


function CurrentMatchup()
    local playerIndexInROM = Mondata[1]["index"]
    local opponentIndexInROM = Mondata[2]["index"]
    local playerIndexInList = 1
    local opponentIndexInList = 2
    local pastOutcomeIndex = 1
    local cheatOffset = CHEAT_OFFSET or 0
    -- console:log("Past outcomes: " .. dump(PastOutcomes))
    while PastOutcomes["outcomes"][tostring(pastOutcomeIndex)] ~= nil do
        local outcome = PastOutcomes["outcomes"][tostring(pastOutcomeIndex)]
        if outcome == 1 then
            -- console:log("Player won against opponent at index " .. pastOutcomeIndex .. ". Moving to next opponent.")
            -- Player won. Move on to the next opponent.
            opponentIndexInList = 2 + pastOutcomeIndex + cheatOffset
            opponentIndexInROM = Mondata[opponentIndexInList]["index"]
        elseif outcome == 2 then
            -- console:log("Player lost against opponent at index " .. pastOutcomeIndex .. ". Switching player and opponent.")
            -- Player lost. Opponent becomes the next player, and the next opponent is chosen.
            playerIndexInROM = opponentIndexInROM
            playerIndexInList = opponentIndexInList
            opponentIndexInList = 2 + pastOutcomeIndex + cheatOffset
            opponentIndexInROM = Mondata[opponentIndexInList]["index"]
        else
            console:log("Invalid outcome value: " .. tostring(outcome) .. ". Expected 1 (win) or 2 (loss).")
        end

        pastOutcomeIndex = pastOutcomeIndex + 1
    end
    playerName = Mondata[playerIndexInList]["trainer_class"] .. " " .. Mondata[playerIndexInList]["character_name"]
    opponentName = Mondata[opponentIndexInList]["trainer_class"] .. " " .. Mondata[opponentIndexInList]["character_name"]
    console:log(string.format("Battle %d", pastOutcomeIndex))
    console:log(string.format("Current matchup: Player: %s (Index in ROM: %d) vs Opponent: %s (Index in ROM: %d)", playerName, playerIndexInROM, opponentName, opponentIndexInROM))
    return {
        player = playerIndexInROM,
        opponent = opponentIndexInROM,
        index = pastOutcomeIndex
    }
end

function EndCurrentMatchup(outcome)
    local currentMatchup = CurrentMatchup()
    local pastOutcomeIndex = currentMatchup["index"]
    PastOutcomes["outcomes"][tostring(pastOutcomeIndex)] = outcome

    -- Save the updated outcomes back to the file
    local file = io.open(PAST_OUTCOMES_FILE, "w")
    if file then
        local content = json.encode(PastOutcomes)
        file:write(content)
        file:close()
    else
        console:log("Error: Could not open past outcomes file for writing.")
    end
end