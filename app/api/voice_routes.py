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

@router.post("/voice1")
async def voice():
    twiml = f"""
    <Response>
        <!-- Play the pre-recorded human-like greeting -->
        <Play>{BASE_URL}/assets/greet.mp3</Play>
        <Pause length="1"/>
        <Gather 
            input="speech" 
            language="hi-IN"
            action="{BASE_URL}/handle-response" 
            method="POST" 
            timeout="10" 
            actionOnEmptyResult="true"
        >

            <Say language="hi-IN">
                कृपया अपना NEET स्कोर बोलें। उदाहरण के लिए: एक सौ पचास।
            </Say>
        </Gather>
        <Say language="hi-IN">
            हमें आपकी प्रतिक्रिया नहीं मिली। धन्यवाद!
        </Say>
    </Response>
    """
    return Response(content=twiml, media_type="application/xml")


@router.post("/handle-response")
async def handle_response(request: Request):
    try:
        form = await request.form()
        speech = form.get("SpeechResult", "")

        if speech:
            reply = speech
            log_voice_reply(speech)
        else:
            reply = "हमें कोई प्रतिक्रिया नहीं मिली। कृपया पुनः प्रयास करें।"

    except Exception as e:
        logging.error("Error in handle-response: %s", str(e))
        reply = "क्षमा करें, कुछ त्रुटि हुई है। बाद में पुनः प्रयास करें।"

    twiml = f"""
    <Response>
        <Say voice="Polly.Aditi" language="hi-IN" rate="medium" pitch="medium">
            {reply}
        </Say>
        <Pause length="1"/>
        <Say voice="Polly.Aditi" language="hi-IN">
            NEET भविष्यवक्ता सहायक का उपयोग करने के लिए धन्यवाद। अलविदा!
        </Say>
        <Hangup/>
    </Response>
    """
    return Response(content=twiml, media_type="application/xml")


@router.post("/voice")
async def voice():
    twiml = f"""
    <Response>
        <Start>
            <Stream url="wss://voice-bot.v4edu.in/twilio-stream"/>
        </Start>
        <Say language="hi-IN">आप कैसे हैं??</Say>
    </Response>
    """
    return Response(content=twiml, media_type="application/xml")