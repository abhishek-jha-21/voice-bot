import base64
import json
import websockets
import audioop
from vosk import Model, KaldiRecognizer
from app.services.voice_logger import log_voice_reply
from gtts import gTTS
from pydub import AudioSegment
import os
import io
from app.config import client

# ==================== CONFIG ====================
VOSK_MODEL_PATH = "/var/www/voice-bot.v4edu.in/models/hindi"
if not os.path.exists(VOSK_MODEL_PATH):
    raise Exception(f"Vosk model not found at {VOSK_MODEL_PATH}")

vosk_model = Model(VOSK_MODEL_PATH)


# ----------------- AUDIO UTILITIES -----------------
def decode_base64_audio(payload: str) -> bytes:
    """Decode base64 payload to bytes"""
    missing = len(payload) % 4
    if missing:
        payload += "=" * (4 - missing)
    return base64.b64decode(payload)


def mulaw_to_pcm16(mulaw_bytes: bytes) -> bytes:
    """Convert μ-law 8-bit → PCM16"""
    return audioop.ulaw2lin(mulaw_bytes, 2)


def resample_audio(pcm16: bytes, in_rate=8000, out_rate=16000) -> bytes:
    """Resample audio from 8kHz → 16kHz for ASR"""
    return audioop.ratecv(pcm16, 2, 1, in_rate, out_rate, None)[0]


# ----------------- SPEECH RECOGNITION -----------------
def init_recognizer(sample_rate=16000):
    """Initialize Vosk recognizer"""
    return KaldiRecognizer(vosk_model, sample_rate)


def recognize_audio(recognizer, audio_chunk: bytes) -> dict:
    """Recognize audio chunk; returns final or partial transcript"""
    if recognizer.AcceptWaveform(audio_chunk):
        return json.loads(recognizer.Result())
    return json.loads(recognizer.PartialResult())


# ----------------- TEXT TO SPEECH -----------------
def text_to_twilio_audio(text: str) -> str:
    """Generate μ-law 8-bit Base64 audio for Twilio from text"""
    tts = gTTS(text=text, lang="hi")
    mp3_fp = io.BytesIO()
    tts.write_to_fp(mp3_fp)
    mp3_fp.seek(0)

    audio = AudioSegment.from_file(mp3_fp, format="mp3")
    audio = audio.set_frame_rate(8000).set_channels(1).set_sample_width(2)
    pcm16 = audio.raw_data
    mulaw = audioop.lin2ulaw(pcm16, 2)
    return base64.b64encode(mulaw).decode("utf-8")


# ----------------- TWILIO -----------------
def reply_call_twilio(call_sid: str, text: str):
    """Send Twilio <Say> reply using REST API"""
    log_voice_reply(f"Send reply via Twilio REST API: {text}")
    twiml = f"<Response><Say language='hi-IN'>{text}</Say></Response>"
    client.calls(call_sid).update(twiml=twiml)


# ----------------- WEBSOCKET HANDLER -----------------
async def handle_ws_service(websocket: websockets.WebSocketServerProtocol):
    log_voice_reply("Client connected (Twilio)")
    call_sid = None
    recognizer = init_recognizer()

    async for message in websocket:
        try:
            data = json.loads(message)
        except:
            continue

        event = data.get("event")

        if event == "start":
            call_sid = data.get("start", {}).get("callSid")
            log_voice_reply(f"Stream started, call_sid={call_sid}")
            continue

        if event == "media":
            audio_bytes = decode_base64_audio(data["media"]["payload"])
            pcm16 = mulaw_to_pcm16(audio_bytes)
            resampled = resample_audio(pcm16)

            result = recognize_audio(recognizer, resampled)

            if result.get("text"):
                log_voice_reply(f"User: {text.strip()}")
                text = result.get("text")
                if text and text.strip():
                    if call_sid:
                        reply_call_twilio(call_sid, f"आपने कहा: {text.strip()}")
            else:
                text = result.get("partial")
                log_voice_reply(f"Partial: {text.strip()}")

        elif event == "stop":
            log_voice_reply("Twilio stream stopped")
            break

    log_voice_reply("Client disconnected")
