from fastapi import APIRouter, Request
from fastapi.responses import Response
from app.services.neet_service import predict_neet_rank
from app.config import BASE_URL
import logging
import os

router = APIRouter()

# --- Setup logging ---
log_file = os.path.join(os.path.dirname(__file__), "voice_errors.log")
logging.basicConfig(
    filename=log_file,
    level=logging.ERROR,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

@router.post("/voice")
async def voice():
    twiml = f"""
    <Response>
        <Say voice="Polly.Aditi-Neural" language="hi-IN" rate="medium" pitch="medium">
            नमस्ते! मैं आपका NEET भविष्यवक्ता सहायक हूँ। 
        </Say>
        <Pause length="1"/>
        <Say voice="Polly.Aditi-Neural" language="hi-IN">
            कृपया मुझे अपना NEET स्कोर बताइए ताकि मैं आपका अनुमानित रैंक बता सकूँ।
        </Say>
        <Pause length="1"/>
        <Gather input="speech" action="{BASE_URL}/handle-response" method="POST" timeout="7">
            <Say voice="Polly.Aditi-Neural" language="hi-IN">
                अब अपना स्कोर बोलें। उदाहरण के लिए: एक सौ पचास।
            </Say>
        </Gather>
        <Say voice="Polly.Aditi-Neural" language="hi-IN">
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
            try:
                # Convert spoken number words to digits if needed
                marks = int(''.join(filter(str.isdigit, speech)))
                rank = predict_neet_rank(marks)
                reply = f"आपके {marks} स्कोर के आधार पर आपका अनुमानित रैंक {rank} है। शुभकामनाएँ!"
            except ValueError:
                reply = "माफ़ कीजिये, मैं आपका स्कोर समझ नहीं पाया। कृपया फिर से प्रयास करें।"
        else:
            reply = "हमें कोई प्रतिक्रिया नहीं मिली। कृपया पुनः कॉल करें।"

    except Exception as e:
        # Log error to file
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
