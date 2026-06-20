import gdb
import random
HOST = "172.24.16.1:2345"

# MAY_BATTLE = 529
MAX_TRAINERS = 855

def BattleToStart():
    # return random.randint(0, MAX_TRAINERS - 1)
    return 999 #Way outside the array.  Fuck it.

def addressof(symbol):
    return int(gdb.parse_and_eval(f"&{symbol}").address)

# def write(symbol, value):
#     addr = addressof(symbol)
#     inferior = gdb.selected_inferior()

#     value_bytes = value.to_bytes(4, byteorder='little')
#     inferior.write_memory(addr, value)

def simpleWrite(symbol, value):
    print(f"Setting {symbol} to {value}...")
    gdb.execute(f"set {symbol} = {value}")

class BattleStartBreakpoint(gdb.Breakpoint):
    def __init__(self, expression):
        # Initialize the watchpoint
        super().__init__(expression, type=gdb.BP_WATCHPOINT, wp_class=gdb.WP_WRITE)
        
        # 2. THIS IS CRITICAL. It stops GDB from fetching UI data.
        self.silent = True 

    def stop(self):
        # We can safely put our payload here once the lag is gone!
        return False  

# 3. PRE-CALCULATE THE RAW ADDRESS
# We get the raw memory address so GDB doesn't do scope-checking
addr_val = gdb.parse_and_eval("&gTrainerBattleOpponent_A")

# Format it as a raw memory cast. 
# (Assuming the opponent ID is a 16-bit short. If it's a 32-bit int, use 'int')
raw_watch_expr = f"*((short*){int(addr_val)})"

print(f"Setting raw hardware watchpoint on: {raw_watch_expr}")

# Instantiate the breakpoint with the raw expression
BattleStartBreakpoint(raw_watch_expr)
# Break on battle start
# gdb.execute("watch gTrainerBattleOpponent_A")


# And go
# gdb.execute("detach")
gdb.execute(f"target remote {HOST}")
gdb.execute("continue")