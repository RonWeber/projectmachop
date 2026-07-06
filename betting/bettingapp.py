from twitchAPI.twitch import Twitch
from twitchAPI.oauth import UserAuthenticator
from twitchAPI.type import AuthScope, ChatEvent
from twitchAPI.chat import Chat, EventData, ChatMessage, ChatSub, ChatCommand
import asyncio
import os
import dotenv
from db import *

dotenv.load_dotenv()

APP_ID = os.getenv('TWITCH_CLIENT_ID')
APP_SECRET = os.getenv('TWITCH_CLIENT_SECRET')
USER_SCOPE = [AuthScope.CHAT_READ, AuthScope.CHAT_EDIT]
TARGET_CHANNEL = 'ProjectMachop'
CHEAT_ACCOUNTS = ['ProjectMachop', 'Bratmon']  # The accounts that can use the !givemoney command

# Called when the bot successfully starts up
async def on_ready(ready_event: EventData):
    print(f'Bot is ready! Joining {TARGET_CHANNEL}...')
    await ready_event.chat.join_room(TARGET_CHANNEL)

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

# Setup and run the bot
async def run():
    # Initialize Twitch API and authenticate
    twitch = await Twitch(APP_ID, APP_SECRET)
    auth = UserAuthenticator(twitch, USER_SCOPE, force_verify=False)
    
    # This will open a browser window for you to log into your bot account
    token, refresh_token = await auth.authenticate()
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
    chat.register_command('givemoney', givemoney_command)
    chat.register_command('addmoney', givemoney_command)

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
    asyncio.run(run())