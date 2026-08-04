-- Upon a command being used.
BasePath = ""
if BasePath == "" then
    local pathLookup = debug.getinfo(1, "S").source:sub(2)
    BasePath = pathLookup:match("(.*[/\\])") or ""
    console:log("BasePath: " .. BasePath)
end
LIB_PATH = BasePath .. ""
-- EXEC_SUFFEX = " & pause"
EXEC_SUFFEX = ""
DidSetupChecks = false
MAP_PATH = BasePath .. "copyin/pokeemerald_modern.map"
BETTING_PATH = BasePath .. "ipc/current_event.txt"
SAVE_STATE_PATH = BasePath .. "savestate.ss0"
-- US_OVERRIDE = 265 -- Roxanne
-- THEM_OVERRIDE = 267 -- Wattson
FR_FIRST_TRAINER = 855 - 89
MAX_TRAINERS = 742 + FR_FIRST_TRAINER 
-- US_OVERRIDE = 1352
-- THEM_OVERRIDE = 1230 
FRAMES_TO_WAIT_AFTER_BATTLE = 100
MAX_INPUTS_UNTIL_SPEEDUP = 200

dofile(LIB_PATH .. "memory.lua")
dofile(LIB_PATH .. "tournament.lua")

function FileExists(name)
   local f=io.open(name,"r")
   if f~=nil then io.close(f) return true else return false end
end


function dump(o)
    if type(o) == 'table' then
       local s = '{ '
       for k,v in pairs(o) do
          if type(k) ~= 'number' then k = '"'..k..'"' end
          s = s .. '['..k..'] = ' .. dump(v) .. ','
       end
       return s .. '} '
    else if type(o) == 'string' then
        return '"' .. o .. '"'
    else
       return tostring(o)
    end
 end
end

local function get_symbol_addresses(map_path, symbols)
    local file = io.open(map_path, "r")
    
    if not file then
        console:log("Error: Could not open map file. Check the path.")
        return nil
    end

    symbol_search_patterns = {}
    for _, symbol_name in ipairs(symbols) do
        -- Create a search pattern for each symbol and store it in a table
        -- Pattern looks for a hex address (0x...), whitespace, and the exact symbol name
        -- The %s*$ ensures we don't accidentally match a symbol with a longer suffix
        symbol_search_patterns[symbol_name] = "(0x%x+)%s+" .. symbol_name .. "%s*$"
    end

    result = {}

    for line in file:lines() do
        for symbol_name, search_pattern in pairs(symbol_search_patterns) do

            local hex_match = string.match(line, search_pattern)
            if hex_match then
                -- Convert the string "0x02038BCA" into a Lua integer
                target_address = tonumber(hex_match)
                result[symbol_name] = target_address
                break
            end
        end
    end

    file:close()
    
    return result
end

NEEDED_SYMBOLS = {
    "gTrainerBattleOpponent_A",
    "gTrainerIdToCopyIn",
    "gR_ShouldChooseMoveItemPoke",
    "gR_ChosenItemId",
    "gR_MoveSelectLock",
    "gR_BattleOutcome",
    "gRngValue"
}
symbol_addresses = get_symbol_addresses(MAP_PATH, NEEDED_SYMBOLS)
for symbol_name, address in pairs(symbol_addresses) do
    if address then
        console:log(string.format("Symbol '%s' found at address: 0x%X", symbol_name, address))
    else
        console:log(string.format("Symbol '%s' not found in map file.", symbol_name))
    end
end
gTrainerBattleOpponent_A = symbol_addresses["gTrainerBattleOpponent_A"]
gTrainerIdToCopyIn = symbol_addresses["gTrainerIdToCopyIn"]
gR_ShouldChooseMoveItemPoke = symbol_addresses["gR_ShouldChooseMoveItemPoke"]
gR_ChosenItemId = symbol_addresses["gR_ChosenItemId"]
gR_MoveSelectLock = symbol_addresses["gR_MoveSelectLock"]
-- 0 = Battle ongoing, 1 = Player won, 2 = Player lost
gR_BattleOutcome = symbol_addresses["gR_BattleOutcome"]
gRngValue = symbol_addresses["gRngValue"]

betIsRunning = false
function WriteBettingFile(toWrite)
    console:log("Writing to betting file: " .. toWrite)
    local file = io.open(BETTING_PATH, "w")
    if file then
        file:write(toWrite)
        file:close()
    else
        console:log("Error: Could not open betting file for writing. Check the path.")
    end
end


-- We'll just say 1-3 = Move, item, poke, 4-7 is the move, 8-11 is the item, and 12-17 is the Pokemon
-- 18 is "Mash A, we're at a YES/NO we don't expect"
-- 19 is "We don't have a valid item, panic (And maybe bail out of the item menu)"
movementPrograms = {
    [0] = "",
    [1] = "a",
    [2] = "ra",
    [3] = "da",
    [4] = "a",
    [5] = "ra",
    [6] = "da",
    [7] = "rda",
    [8] = "a",
    [9] = "da",
    [10] = "dda",
    [11] = "ddda",
    [18] = "a",
    [19] = "bla",
}
DEFAULT_MOVEMENT_SUB_PROGRAMS = {
    {time = 42, btnDown = false},
    {time = 10, btnDown = true},
    {time = 1, btnDown = false},
}
STRUGGLEBUS_MOVEMENT_SUB_PROGRAMS = {
    {time = 2, btnDown = false},
    {time = 10, btnDown = true},
    {time = 1, btnDown = false},
}
movementSubPrograms = DEFAULT_MOVEMENT_SUB_PROGRAMS

movementProgramState = {
    currentProgramId = 0,
    currentCharIndex = 1,
    currentSubCharIndex = 1,
    currentTimeInSubIndex = 0,
}

function GetKeyForChar(char)
    if (char == "a") then
        return 0
    elseif (char == "b") then
        return 1
    elseif (char == "l") then
        return 5
    elseif (char == "r") then
        return 4
    elseif (char == "u") then
        return 6
    elseif (char == "d") then
        return 7
    end

    return nil

end

function StartMovementProgram(programId)
    movementProgramState.currentProgramId = programId
    movementProgramState.currentCharIndex = 1
    movementProgramState.currentSubCharIndex = 1
    movementProgramState.currentTimeInSubIndex = 0
end

function ExecuteMovementIfNeeded(mps)
    local program = movementPrograms[mps.currentProgramId]
    if not program then
        return
    end
    if mps.currentCharIndex > #program then
        return
    end
    local currentChar = program:sub(mps.currentCharIndex, mps.currentCharIndex)
    local key = GetKeyForChar(currentChar)
    local currentSubProgram = movementSubPrograms[mps.currentSubCharIndex]
    if currentSubProgram.btnDown then
        emu:addKey(key)
    else
        emu:clearKey(key)
    end
    mps.currentTimeInSubIndex = mps.currentTimeInSubIndex + 1
    if mps.currentTimeInSubIndex >= currentSubProgram.time then
        mps.currentTimeInSubIndex = 0
        mps.currentSubCharIndex = mps.currentSubCharIndex + 1
        if mps.currentSubCharIndex > #movementSubPrograms then
            mps.currentSubCharIndex = 1
            mps.currentCharIndex = mps.currentCharIndex + 1
        end
    end
end

Reentrant = false
ReProblemLogged = false
lastTrainerId = -1
lastMoveSelectLock = -1
lastBattleOutcome = 0
framesAfterBattleEnd = 0
completeInputsSinceBattleEnd = 0
lastRngValue = 0
function ResetState()
    lastTrainerId = -1
    lastMoveSelectLock = -1
    lastBattleOutcome = 0
    framesAfterBattleEnd = 0
    completeInputsSinceBattleEnd = 0
    lastRngValue = 0
    movementSubPrograms = DEFAULT_MOVEMENT_SUB_PROGRAMS
end
function OnFrame()
    if Reentrant then
        if not ReProblemLogged then
            console:log("Crash in OnFrame!")
            ReProblemLogged = true
        end
        return
    end
    Reentrant = true

    currentTrainerId = emu:read16(gTrainerBattleOpponent_A)
    if currentTrainerId ~= lastTrainerId then
        currentMatchup = CurrentMatchup()
        currentTrainerId = currentMatchup["opponent"]
        if THEM_OVERRIDE then
            currentTrainerId = THEM_OVERRIDE
        end
        emu:write16(gTrainerBattleOpponent_A, currentTrainerId)
        lastTrainerId = currentTrainerId
        newPlayerTrainerId = currentMatchup["player"]
        if US_OVERRIDE then
            newPlayerTrainerId = US_OVERRIDE
        end
        emu:write16(gTrainerIdToCopyIn, newPlayerTrainerId)
    end
    lastTrainerId = currentTrainerId

    currentMoveSelectLock = emu:read8(gR_MoveSelectLock)
    if currentMoveSelectLock ~= lastMoveSelectLock then
        -- console:log(string.format("MoveSelectLock changed: %d -> %d", lastMoveSelectLock, currentMoveSelectLock))
        -- console:log(string.format("ShouldChooseMoveItemPoke: %d", emu:read16(gR_ShouldChooseMoveItemPoke)))
        completeInputsSinceBattleEnd = completeInputsSinceBattleEnd + 1
        if completeInputsSinceBattleEnd >= MAX_INPUTS_UNTIL_SPEEDUP then
            -- console:log(string.format("Complete inputs since battle end: %d", completeInputsSinceBattleEnd))
            console:log("Speeding up movement sub-programs due to too many inputs since battle end.")
            movementSubPrograms = STRUGGLEBUS_MOVEMENT_SUB_PROGRAMS
        end
        StartMovementProgram(emu:read8(gR_ShouldChooseMoveItemPoke))
        if lastMoveSelectLock > 0 and currentMoveSelectLock > 0 and betIsRunning then
            console:log("First move was made - stop bets!")
            WriteBettingFile("")
            betIsRunning = false
        end
    end
    lastMoveSelectLock = currentMoveSelectLock
    ExecuteMovementIfNeeded(movementProgramState)

    currentBattleOutcome = emu:read8(gR_BattleOutcome)
    if lastBattleOutcome ~= currentBattleOutcome then
        -- emu:saveStateFile(SAVE_STATE_PATH)
        if currentBattleOutcome == 1 then
            console:log("Player won the battle.")
            EndCurrentMatchup(1)
        elseif currentBattleOutcome == 2 then
            console:log("Player lost the battle.")
            EndCurrentMatchup(2)
        end
        -- Start the next bet right away
        newCurrentMatchup = CurrentMatchup()
        WriteBettingFile(newCurrentMatchup["index"])
        betIsRunning = true
        lastBattleOutcome = currentBattleOutcome
    else
        if currentBattleOutcome ~= 0 then
            framesAfterBattleEnd = framesAfterBattleEnd + 1
            if framesAfterBattleEnd >= FRAMES_TO_WAIT_AFTER_BATTLE then
                -- Reset Everything!
                emu:loadStateFile(SAVE_STATE_PATH)
                -- New random number so that we have a different battlefield next time (Yes, it's only for that)
                local newRng = math.random(0, 0xFFFFFFFF)
                emu:write32(gRngValue, newRng)
                ResetState()
                console:log("Resetting state after battle outcome.")
            end
        end
    end

    Reentrant = false
end
CallBackId = callbacks:add("frame", OnFrame)

function Echo(...)
    console:log(...)
end

console:log("Good luck.")