import discord
import os
import requests
import message_utils as msg
from discord.ext import commands
from dotenv import load_dotenv

# Create a Discord client instance and set the command prefix
intents = discord.Intents.all()
intents.messages = True
intents.guilds = True
client = discord.Client(intents=intents)

load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI')

botname = "DostGPT"

channel_cooldowns = {}

async def check_response_needed(conversation):
    systemprompt = msgs.check_response_needed_system_prompt + conversation;
    return ask_ai_api(msgs.systemprompt, msgs.check_response_needed_prompt)

async def converse(prompt, conversation):
    systemprompt = msgs.converse_prompt + conversation;
    return ask_ai_api(systemprompt, prompt)


async def ask_ai_api (systemprompt, prompt):
    url = "https://api.openai.com/v1/chat/completions"
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {
                "role": "system",
                "content": f"{systemprompt}"
            },
            {
                "role": "user",
                "content": f"{prompt}"
            }
        ],
        "temperature": 1,
        "max_tokens": 256,
        "top_p": 1,
        "frequency_penalty": 0,
        "presence_penalty": 0
    }
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "content-type": "application/json"
    }
    response = requests.post(url, json=payload, headers=headers)
    return response.json()['choices'][0]['message']['content'].strip()

# Build response:

async def build_response(message, content):
    conversation = msgs.get_conversation(message.channel.id)
    response = converse(content, conversation)
    reply = response.replace(f"{botname}: ","",1)
    await message.channel.send(reply)
    channel_cooldowns[message.channel.id] = 8;
    return

async def get_quoted_message (message):
    referenced_message = message.reference.resolved

    # If the referenced message is not cached, fetch it
    if referenced_message is None:

        try:
            referenced_message = await message.channel.fetch_message(message.reference.message_id)
            # print (f'referenced: {referenced_message.content}')
            return msgs.clean_message(referenced_message)
        except discord.NotFound:
            # Message not found or inaccessible
            return ""

    else:
        return msgs.clean_message(referenced_message)

# Set the confirmation message when the bot is ready
@client.event
async def on_ready():
    botname = client.user.display_name
    print(f'Logged in as {botname}')

@client.event
async def on_message(message):

    if message.channel.id not in channel_cooldowns:
        channel_cooldowns[message.channel.id] = 0

    #Remove bot mention from message

    message.content = message.content.replace(f'<@{client.user.id}>', f'{botname}').replace(f'<@!{client.user.id}>', f'{botname}').strip()

    content = msgs.clean_message (message)

    if message.author != client.user:

        #On reply

        if message.reference and message.reference.resolved:
            if message.reference.resolved.author == client.user:
                # print ("SYSTEM MESSAGE: I got replied to!")
                quote = await get_quoted_message(message)
                content = f'(Replying to {quote}) ' + content
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
                    await build_response(message, content)

    msgs.save_content(message, content)

# Retrieve token from the .env file
client.run(os.getenv('TOKEN'))
