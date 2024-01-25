
async def bot_rename (name, bot_token):
    headers = {
        'Authorization': f'Bot {bot_token}',
        'Content-Type': 'application/json'
    }

    # Replace 'NEW_BOT_NAME' with the desired name for your bot
    payload = {
        'username': f'{name}'
    }

    response = requests.patch('https://discord.com/api/v9/users/@me', headers=headers, json=payload)

    if response.status_code == 200:
        print("Bot name changed successfully")
    else:
        print("Failed to change bot name")
        print("Status Code:", response.status_code)
        print("Response:", response.json())
