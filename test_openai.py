# test_openai.py
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(dotenv_path=".env")

api_key = os.getenv("OPENAI_API_KEY")
print("Using key prefix:", (api_key or "")[:8])

client = OpenAI(api_key=api_key)

resp = client.chat.completions.create(
    model="gpt-4o-mini",  # or "gpt-4.1-mini" if your account supports it
    messages=[
        {"role": "system", "content": "You are a test assistant."},
        {"role": "user", "content": "Say hello in one short sentence."},
    ],
    max_tokens=20,
)

print("Response:", resp.choices[0].message.content)
