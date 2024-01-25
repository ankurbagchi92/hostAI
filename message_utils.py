import re
import discord


# Clean up messages:

def clean_message(message):
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

# Dictionary to store the last 10 messages for each channel
channel_messages = {}

def save_content(message, content):

    channel_id = message.channel.id

    if channel_id not in channel_messages:
        channel_messages[channel_id] = []

    channel_messages[channel_id].append(content)

    # Keep only the last 10 messages per channel
    if len(channel_messages[channel_id]) > 8:
        channel_messages[channel_id].pop(0)

    return content

def get_conversation(channel_id):
    conversation = ""
    messages = channel_messages.get(channel_id, [])

    for msg in messages:
        conversation += msg + "\n"

    return conversation
