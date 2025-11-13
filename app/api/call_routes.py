from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse
from app.config import BASE_URL, TWILIO_NUMBER, client
import logging
import os

router = APIRouter()

# --- Setup logging ---
log_file = os.path.join(os.path.dirname(__file__), "call_logs.log")
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

@router.post("/call")
def make_call(to: str = Form(...)):
    try:
        call = client.calls.create(
            to=to,
            from_=TWILIO_NUMBER,
            url=f"{BASE_URL}/voice"
        )
        logging.info(f"Outbound call initiated to {to}, SID: {call.sid}")
        return {"call_sid": call.sid, "status": "initiated"}
    except Exception as e:
        logging.error(f"Failed to initiate call to {to}: {str(e)}")
        return JSONResponse({"error": "Failed to initiate call", "details": str(e)}, status_code=500)
