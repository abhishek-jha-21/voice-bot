import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv("/var/www/voice-bot.v4edu.in/.env")
api_key = os.getenv("OPENAI_API_KEY")

print("API KEY:", api_key)

client = OpenAI(api_key=api_key)

with open("assets/greet.mp3", "rb") as audio_file:
    response = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        language="hi"
    )

print("\nTranscription:")
print(response.text)
