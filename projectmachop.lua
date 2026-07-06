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
-- US_OVERRIDE = 265 -- Roxanne
-- THEM_OVERRIDE = 267 -- Wattson
FR_FIRST_TRAINER = 855 - 89
MAX_TRAINERS = 742 + FR_FIRST_TRAINER 
-- US_OVERRIDE = 1352
-- THEM_OVERRIDE = 1230 

dofile(LIB_PATH .. "memory.lua")

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
movementSubPrograms = {
    {time = 45, btnDown = false},
    {time = 10, btnDown = true},
    {time = 1, btnDown = false},
}

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
        currentTrainerId = math.random(1, MAX_TRAINERS) - 1
        if THEM_OVERRIDE then
            currentTrainerId = THEM_OVERRIDE
        end
        emu:write16(gTrainerBattleOpponent_A, currentTrainerId)
        lastTrainerId = currentTrainerId
        newPlayerTrainerId = math.random(1, MAX_TRAINERS) - 1
        if US_OVERRIDE then
            newPlayerTrainerId = US_OVERRIDE
        end
        emu:write16(gTrainerIdToCopyIn, newPlayerTrainerId)
    end
    lastTrainerId = currentTrainerId

    currentMoveSelectLock = emu:read8(gR_MoveSelectLock)
    if currentMoveSelectLock ~= lastMoveSelectLock then
        console:log(string.format("MoveSelectLock changed: %d -> %d", lastMoveSelectLock, currentMoveSelectLock))
        console:log(string.format("ShouldChooseMoveItemPoke: %d", emu:read16(gR_ShouldChooseMoveItemPoke)))
        StartMovementProgram(emu:read8(gR_ShouldChooseMoveItemPoke))
    end
    lastMoveSelectLock = currentMoveSelectLock
    ExecuteMovementIfNeeded(movementProgramState)

    Reentrant = false
end
CallBackId = callbacks:add("frame", OnFrame)

function Echo(...)
    console:log(...)
end

console:log("Good luck.")