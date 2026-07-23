from twitchAPI.twitch import Twitch
from twitchAPI.oauth import UserAuthenticator
from twitchAPI.type import AuthScope, ChatEvent
from twitchAPI.chat import Chat, EventData, ChatMessage, ChatSub, ChatCommand
import asyncio
import os
import dotenv
import json
import threading
from db import *
from outcomefile import start_watching, set_on_files_changed_callback


dotenv.load_dotenv()

APP_ID = os.getenv('TWITCH_CLIENT_ID')
APP_SECRET = os.getenv('TWITCH_CLIENT_SECRET')
USER_SCOPE = [AuthScope.CHAT_READ, AuthScope.CHAT_EDIT]
TARGET_CHANNEL = 'ProjectMachop'
CHEAT_ACCOUNTS = ['ProjectMachop', 'Bratmon']  # The accounts that can use the !givemoney command
TOKEN_PATH = os.getenv('TWITCH_TOKEN_PATH', 'twitch_user_token.json')

event_id = None
event_id_lock = threading.Lock()

global_chat_function = lambda msg: None  # Placeholder for the global chat function

def get_event_id():
    global event_id
    with event_id_lock:
        return event_id
    
def set_event_id(new_event_id):
    global event_id
    with event_id_lock:
        event_id = new_event_id

# Called when the bot successfully starts up
async def on_ready(ready_event: EventData):
    print(f'Bot is ready! Joining {TARGET_CHANNEL}...')
    await ready_event.chat.join_room(TARGET_CHANNEL)

def load_saved_tokens():
    if not os.path.exists(TOKEN_PATH):
        return None, None
    with open(TOKEN_PATH, 'r', encoding='utf-8') as token_file:
        token_data = json.load(token_file)
    return token_data.get('access_token'), token_data.get('refresh_token')

def save_tokens(access_token: str, refresh_token: str):
    with open(TOKEN_PATH, 'w', encoding='utf-8') as token_file:
        json.dump(
            {'access_token': access_token, 'refresh_token': refresh_token},
            token_file,
            ensure_ascii=True,
            indent=2
        )

# Called whenever a message is sent in the channel
async def on_message(msg: ChatMessage):
    print(f'[{msg.room.name}] {msg.user.name}: {msg.text}')

# Called whenever someone subscribes
async def on_sub(sub: ChatSub):
    print(f'New subscription in {sub.room.name}:\n'
          f'  Type: {sub.sub_plan}\n'
          f'  Message: {sub.sub_message}')

# Called whenever the !reply command is issued
async def test_command(cmd: ChatCommand):
    if len(cmd.parameter) == 0:
        await cmd.reply('You did not tell me what to reply with!')
    else:
        await cmd.reply(f'{cmd.user.name}: {cmd.parameter}')

async def givemoney_command(cmd: ChatCommand):
    if len(cmd.parameter) == 0:
        await cmd.reply('You did not specify a username to give money to!')
    splitCommand = cmd.parameter.split()
    moneyToGive = 1000  # Default amount to give
    if len(splitCommand) > 1:
        try:
            moneyToGive = int(splitCommand[1])
        except ValueError:
            await cmd.reply('The amount of money must be a valid integer.')
            return
    if cmd.user.name.lower() in [account.lower() for account in CHEAT_ACCOUNTS]:
        add_money(splitCommand[0], moneyToGive)
        await cmd.reply(f'{splitCommand[0]} has been given {moneyToGive} money. They now have {get_user_money(splitCommand[0])} money.')
    else:
        await cmd.reply('You do not have permission to use this command.')

async def getbalance_command(cmd: ChatCommand):
    balance = get_user_money(cmd.user.name)
    print(f'User {cmd.user.name} has {balance} money.')
    await cmd.reply(f'You have {balance} money.')

class InvalidInputError(Exception):
    """Custom exception for invalid input."""
    pass
async def bet_command(cmd: ChatCommand):
    splitCommand = cmd.parameter.split()
    try:
        money = 1000
        if (len(splitCommand) == 0 or len(splitCommand) > 2):
            raise InvalidInputError("Invalid number of arguments.")
        if len(splitCommand) == 2:
            try:
                money = int(splitCommand[1])
            except ValueError:
                raise InvalidInputError("The amount of money must be a valid integer.")
        outcome = 0
        if splitCommand[0].lower() == "player":
            outcome = 1
        elif splitCommand[0].lower() == "opponent":
            outcome = 2
        else:
            raise InvalidInputError("Invalid outcome. Must be 'player' or 'opponent'.")
        if get_event_id() is None:
            await cmd.reply('No active event to place a bet on.')
            return
        result = place_bet(cmd.user.name, money, get_event_id(), outcome)
        print(f'User {cmd.user.name} placed a bet of {result["money_bet"]} money on {splitCommand[0]}.')
        if result["all_in"]:
            await cmd.reply('You went ALL IN!')
        await cmd.reply(f'You have placed a bet of {result["money_bet"]} money on {splitCommand[0]}.')
    except InvalidInputError as e:
        await cmd.reply('Bet with either "!bet player <amount>" or "!bet opponent <amount>"')
        return
    
async def cancelevent_command(cmd: ChatCommand):
    if cmd.user.name.lower() not in [account.lower() for account in CHEAT_ACCOUNTS]:
        await cmd.reply('You do not have permission to use this command.')
        return
    splitCommand = cmd.parameter.split()
    eventToCancel = get_event_id()
    if len(splitCommand) == 0:
        cancel_bets(eventToCancel)
        await cmd.reply(f'All bets for event {eventToCancel} have been canceled.')
    elif len(splitCommand) == 1:
        try:
            eventToCancel = int(splitCommand[0])
            cancel_bets(eventToCancel)
            await cmd.reply(f'All bets for event {eventToCancel} have been canceled.')
        except ValueError:
            await cmd.reply('The event ID must be a valid integer.')

def on_files_changed(current_event_content, past_outcomes_content):
    current_event_id = get_event_id()
    file_content = current_event_content.strip()
    print(f"Detected change in current_event.txt: {file_content}")
    new_event_id = int(file_content) if file_content else None
    print(f"Current event ID: {current_event_id}, New event ID: {new_event_id}")
    if new_event_id != current_event_id:
        set_event_id(new_event_id)
        print(f"Event ID updated to: {file_content}")
        handle_past_outcomes(past_outcomes_content["outcomes"])  # Call the function to handle past outcomes

def handle_past_outcomes(past_outcomes_content):
    for event in events_with_bets():
        if str(event) in past_outcomes_content:
            winning_outcome = past_outcomes_content[str(event)]
            result = payout_bets(event, winning_outcome)
            print(f"Payouts processed for event {event} with winning outcome {winning_outcome}.")
            winning_outcome_str = "player" if winning_outcome == 1 else "opponent"
            global_chat_function(f'Event {event} has concluded! The winning outcome is {winning_outcome_str}. A grand total of {result["Total"]} has been distributed.')
        else:
            print(f"No outcome found for event {event} in past outcomes.")


# Setup and run the bot
async def run():
    # Initialize Twitch API and authenticate
    twitch = await Twitch(APP_ID, APP_SECRET)
    auth = UserAuthenticator(twitch, USER_SCOPE, force_verify=False)
    
    # This will open a browser window for you to log into your bot account
    token, refresh_token = load_saved_tokens()
    if token is None or refresh_token is None:
        auth = UserAuthenticator(twitch, USER_SCOPE, force_verify=False)
        # First run requires browser login, then tokens are reused.
        token, refresh_token = await auth.authenticate()
        save_tokens(token, refresh_token)
        print(f'Saved Twitch user token to {TOKEN_PATH}')

    await twitch.set_user_authentication(token, USER_SCOPE, refresh_token)

    # Create chat instance
    chat = await Chat(twitch)

    # Register event handlers
    chat.register_event(ChatEvent.READY, on_ready)
    chat.register_event(ChatEvent.MESSAGE, on_message)
    chat.register_event(ChatEvent.SUB, on_sub)

    # Register commands
    chat.register_command('reply', test_command)
    chat.register_command('balance', getbalance_command)
    chat.register_command('getbalance', getbalance_command)
    chat.register_command('money', getbalance_command)
    chat.register_command('getmoney', getbalance_command)
    chat.register_command('givemoney', givemoney_command)
    chat.register_command('addmoney', givemoney_command)
    chat.register_command('bet', bet_command)
    chat.register_command('cancelevent', cancelevent_command)

    global global_chat_function
    main_loop = asyncio.get_event_loop()
    def send_message_to_chat(msg):
        print(f"Sending message to chat: {msg}")
        asyncio.run_coroutine_threadsafe(chat.send_message(TARGET_CHANNEL, msg), main_loop)

    global_chat_function = send_message_to_chat

    # Start the chat bot
    chat.start()

    # Keep the bot running safely without blocking the async loop
    try:
        print("\n>>> Bot is running! Press Ctrl+C in the terminal to stop. <<<\n")
        while True:
            await asyncio.sleep(3600)
    finally:
        # Clean up links smoothly
        chat.stop()
        await twitch.close()
        print("Bot has been shut down.")

# Run the async loop
if __name__ == '__main__':
    set_on_files_changed_callback(on_files_changed)
    start_watching()
    asyncio.run(run())
