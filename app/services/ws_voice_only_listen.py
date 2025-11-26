import base64
import json
import websockets
import audioop
from vosk import Model, KaldiRecognizer
from app.services.voice_logger import log_voice_reply

# ==================== CONFIG ====================
VOSK_MODEL_PATH = "/var/www/voice-bot.v4edu.in/models/hindi"

import os
if not os.path.exists(VOSK_MODEL_PATH):
    raise Exception(f"Vosk model not found at {VOSK_MODEL_PATH}")

vosk_model = Model(VOSK_MODEL_PATH)


def decode_base64(payload: str) -> bytes:
    missing = len(payload) % 4
    if missing:
        payload += "=" * (4 - missing)
    return base64.b64decode(payload)


async def handle_ws_service(websocket: websockets.WebSocketServerProtocol):
    print("Client connected (Twilio)")
    log_voice_reply("Client connected (Twilio)")

    # --- Initialize Vosk recognizer ---
    recognizer = KaldiRecognizer(vosk_model, 16000)  # 16 kHz sampling for user speech

    async for message in websocket:
        try:
            data = json.loads(message)
        except:
            continue

        event = data.get("event")
        if event == "start":
            log_voice_reply("Twilio stream started")
            continue

        if event == "media":
            payload_b64 = data["media"]["payload"]
            mulaw_8khz = decode_base64(payload_b64)

            # Convert μ-law → linear PCM16
            linear = audioop.ulaw2lin(mulaw_8khz, 2)

            # Resample 8kHz → 16kHz for Vosk
            resampled = audioop.ratecv(linear, 2, 1, 8000, 16000, None)[0]

            # Recognize speech
            if recognizer.AcceptWaveform(resampled):
                result = json.loads(recognizer.Result())
                text = result.get("text", "").strip()
                if text:
                    log_voice_reply(f"User: {text}")
            else:
                # partial result if needed
                partial = json.loads(recognizer.PartialResult())
                if partial.get("partial", "").strip():
                    log_voice_reply(f"User (partial): {partial['partial']}")

        elif event == "stop":
            log_voice_reply("Twilio stream stopped")
            break

    print("Client disconnected")
    log_voice_reply("Client disconnected")