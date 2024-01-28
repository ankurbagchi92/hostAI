import os
from dotenv import load_dotenv
import requests

load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI')

async def ask (systemprompt, prompt):
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
