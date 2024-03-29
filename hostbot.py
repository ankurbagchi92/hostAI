import discord
import os
import requests
import message_utils as msgs
import bot_config as bot
import ai_api as ai
import rag
import asyncio
import database

from discord.ext import commands
from dotenv import load_dotenv

# Create a Discord client instance and set the command prefix
intents = discord.Intents.all()
intents.messages = True
intents.guilds = True
#client = discord.Client(intents=intents)

load_dotenv()

class MyClient(discord.Client):
    async def  setup_hook(self) -> None:
        await database.init()
        await rag.init()
    async def close(self):
        await database._close()

client = MyClient(intents=intents)


channel_cooldowns = {}

def check_response_needed(conversation):
    systemprompt = bot.sp_crn + conversation;
    return ai.ask(systemprompt, bot.p_crn)

def converse(message, prompt, conversation):
    context = rag.lookup (prompt, message.guild.id)
    systemprompt = bot.sp_converse + conversation + f'\n\nHere is some relevant information from past conversations:\n{context}';
    return ai.ask(systemprompt, prompt)

# Build response:

async def build_response(message, content):
    conversation = msgs.get_conversation(message.channel.id)
    response = await converse(message, content, conversation)
    reply = response.replace(f"{bot.name}: ","",1)
    await message.channel.send(reply)
    channel_cooldowns[message.channel.id] = 8;
    return


# Set the confirmation message when the bot is ready
@client.event
async def on_ready():
    bot.name = client.user.display_name
    print(f'Logged in as {bot.name}')

@client.event
async def on_message(message):

    if message.channel.id not in channel_cooldowns:
        channel_cooldowns[message.channel.id] = 0

    #Remove bot mention from message

    content = msgs.clean_message (message, client.user.id, bot.name)

    await msgs.save_content(message, content)

    if message.author != client.user:

        #On reply

        if message.reference and message.reference.resolved:
            if message.reference.resolved.author == client.user:
                quote = await msgs.get_quoted_message(message)
                content = f'(Replying to {quote}) ' + content
                async with message.channel.typing():
                    await build_response (message, content)

        #On mention

        elif client.user.mentioned_in(message):
            # print ("SYSTEM MESSAGE: I got mentioned!")
            await build_response (message, content)

        #On heat (bot is actively being talked to)

        else:
            if (channel_cooldowns[message.channel.id] > 0):
                channel_cooldowns[message.channel.id] -= 1
                conversation = msgs.get_conversation(message.channel.id)
                reply = await check_response_needed (conversation) + content
                if 'yes' in reply.lower():
                    async with message.channel.typing():
                        await build_response(message, content)



# Retrieve token from the .env file



client.run(os.getenv('DISCORD'))
