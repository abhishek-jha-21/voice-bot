import os
from dotenv import load_dotenv
from twilio.rest import Client

# Load environment variables from .env file
load_dotenv()

# Twilio credentials
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_NUMBER = os.getenv("TWILIO_NUMBER")

# Base URL of your application (used in Twilio webhooks)
BASE_URL = os.getenv("BASE_URL")

# Twilio client
if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_NUMBER, BASE_URL]):
    raise ValueError("Please set all environment variables in .env file.")

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
