import re
import discord
import rag
import database
import asyncio

# Clean up messages:

def clean_message(message, userID, botname):
    message.content = message.content.replace(f'<@{userID}>', f'{botname}').replace(f'<@!{userID}>', f'{botname}').strip()
    content = discord.utils.remove_markdown(message.content)
    content = replace_mentions_with_names(message.content, message.guild.members)
    content = f"{message.author.display_name}: {message.content}"
    return content

def replace_mentions_with_names(message_content, members):
    def replace_mention(match):
        user_id = int(match.group(1))  # Extract the user ID from the mention
        member = discord.utils.get(members, id=user_id)
        return member.display_name if member else match.group(0)  # Replace with username or keep the original mention

    # Regular expression to find mentions in the format <@!user_id> or <@user_id>
    mention_pattern = re.compile(r'<@!?(\d+)>')
    return mention_pattern.sub(replace_mention, message_content)

# get the full text of quoted message:

async def get_quoted_message (message):
    referenced_message = message.reference.resolved

    # If the referenced message is not cached, fetch it
    if referenced_message is None:
        try:
            referenced_message = await message.channel.fetch_message(message.reference.message_id)
            return clean_message(referenced_message)
        except discord.NotFound:
            # Message not found or inaccessible
            return ""

    else:
        return clean_message(referenced_message)


# Dictionary to store the last 10 messages for each channel
channel_messages = {}

async def store_content (server_id, filecontent):
    await database.add_log(server_id, filecontent)
    rag.add_to_db(filecontent, server_id)


async def save_content(message, content):

    channel_id = message.channel.id
    server_id = message.guild.id # IDEA:

    if channel_id not in channel_messages:
        channel_messages[channel_id] = []

    channel_messages[channel_id].append(content)

    # Keep only the last 10 messages per channel
    if len(channel_messages[channel_id]) > 8:
        channel_messages[channel_id].pop(0)

    filecontent = f'[Channel: {channel_id}] ' + content + "\n"

    await store_content(server_id, filecontent)

    return content

def get_conversation(channel_id):
    conversation = ""
    messages = channel_messages.get(channel_id, [])

    for msg in messages:
        conversation += msg + "\n"

    return conversation
