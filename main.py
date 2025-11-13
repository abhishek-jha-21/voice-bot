from fastapi import FastAPI, Form
from fastapi.responses import Response
from twilio.rest import Client
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# --- Environment variables ---
ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_NUMBER = os.getenv("TWILIO_NUMBER")
BASE_URL = os.getenv("BASE_URL")

# --- Initialize Twilio client ---
client = Client(ACCOUNT_SID, AUTH_TOKEN)

@app.get("/")
def root():
    return {"status": "Voice bot running 🚀"}

# --- Webhook for incoming/outgoing call ---
@app.post("/voice")
def voice():
    twiml = f"""
    <Response>
        <Say voice="Polly.Aditi">
            Hello! I am your NEET Predictor assistant.
            Please tell me your NEET score to know your college prediction.
        </Say>
        <Pause length="2"/>
        <Say>Would you like to subscribe for full prediction? Press 1 for Yes.</Say>
        <Gather numDigits="1" action="{BASE_URL}/handle-key">
            <Say>Press 1 to subscribe or 2 to exit.</Say>
        </Gather>
    </Response>
    """
    return Response(content=twiml, media_type="application/xml")

# --- Handle keypad input (DTMF) ---
@app.post("/handle-key")
def handle_key(Digits: str = Form(...)):
    if Digits == "1":
        message = "Thank you. Our team will contact you soon for subscription details."
    else:
        message = "Thank you for your time. Have a great day!"
    twiml = f"<Response><Say>{message}</Say><Hangup/></Response>"
    return Response(content=twiml, media_type="application/xml")

# --- API to make an outbound call manually ---
@app.post("/call")
def make_call(to: str = Form(...)):
    call = client.calls.create(
        to=to,
        from_=TWILIO_NUMBER,
        url=f"{BASE_URL}/voice"
    )
    return {"call_sid": call.sid, "status": "initiated"}
