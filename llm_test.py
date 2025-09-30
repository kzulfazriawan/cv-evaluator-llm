# scripts/test_openrouter.py
import json
import requests
from decouple import config

KEY = config("OPENROUTER_API_KEY")
CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"
HEADERS = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}

messages = [
    {"role": "system", "content": "You are an assistant that returns only JSON."},
    {"role": "user", "content": "Return only: {\"ok\": true}"}
]

payload = {
    "model": "x-ai/grok-4-fast:free",   # replace with a slug you find in dashboard
    "messages": messages,
    "temperature": 0.0,
    "max_tokens": 200,
    "response_format": {"type": "json_object"}
}

r = requests.post(CHAT_URL, headers=HEADERS, json=payload, timeout=60)
print(r.status_code, r.text)
