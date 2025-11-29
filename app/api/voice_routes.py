from fastapi import APIRouter, Request
from fastapi.responses import Response
from app.services.neet_service import predict_neet_rank
from app.config import BASE_URL
import logging
import os
from app.services.voice_logger import log_voice_reply


router = APIRouter()

log_file = os.path.join(os.path.dirname(__file__), "voice_errors.log")
logging.basicConfig(
    filename=log_file,
    level=logging.ERROR,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

@router.post("/voice")
async def voice():
    twiml = """
    <Response>
        <Start>
            <Stream url="wss://voice-bot.v4edu.in/twilio-stream"/>
        </Start>
        <Say language="hi-IN">आप कैसे हैं?</Say>
    </Response>
    """
    return Response(content=twiml, media_type="application/xml")
