import base64
import json
import websockets
import audioop
from vosk import Model, KaldiRecognizer
from app.services.voice_logger import log_voice_reply
from gtts import gTTS
from pydub import AudioSegment
import io
import os

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
    """Resample audio from 8kHz → 16kHz"""
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
def text_to_ws_audio(text: str) -> str:
    """Convert text → μ-law Base64 audio for Twilio WS streaming"""
    tts = gTTS(text=text, lang="hi")
    mp3_fp = io.BytesIO()
    tts.write_to_fp(mp3_fp)
    mp3_fp.seek(0)

    audio = AudioSegment.from_file(mp3_fp, format="mp3")
    audio = audio.set_frame_rate(8000).set_channels(1).set_sample_width(2)
    pcm16 = audio.raw_data
    mulaw = audioop.lin2ulaw(pcm16, 2)
    return base64.b64encode(mulaw).decode("utf-8")

# ----------------- WS RESPONSE SENDER -----------------
async def send_ws_response(websocket, stream_sid, text, sequence_number, chunk_number, timestamp):
    """Send a Twilio MediaStream-compliant audio message"""
    audio_b64 = text_to_ws_audio(text)
    await websocket.send(json.dumps({
        "event": "media",
        "streamSid": stream_sid,
        "media": {
            "payload": audio_b64,
            "track": "outbound",
            "chunk": str(chunk_number),
            "timestamp": str(timestamp)
        },
        "sequenceNumber": str(sequence_number)
    }))
    sequence_number += 1
    chunk_number += 1
    timestamp += 20
    return sequence_number, chunk_number, timestamp

# ----------------- PROCESS RECOGNITION RESULT -----------------
async def process_recognition_result(websocket, stream_sid, result, sequence_number, chunk_number, timestamp):
    """
    Handles Vosk recognition result.
    Sends TTS reply only for final transcript, partials are logged.
    """
    partial = result.get("partial", "").strip()
    final = result.get("text", "").strip()

    if partial and not final:
        log_voice_reply(f"Partial: {partial}")

    if final:
        log_voice_reply(f"User: {final}")
        reply_text = f"आपने कहा: {final}"
        sequence_number, chunk_number, timestamp = await send_ws_response(
            websocket,
            stream_sid,
            reply_text,
            sequence_number,
            chunk_number,
            timestamp
        )

    return sequence_number, chunk_number, timestamp

# ----------------- WEBSOCKET HANDLER -----------------
async def handle_ws_service(websocket: websockets.WebSocketServerProtocol):
    log_voice_reply("Client connected (Twilio)")
    stream_sid = None
    recognizer = init_recognizer()
    sequence_number = 1
    chunk_number = 1
    timestamp = 0

    async for message in websocket:
        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            continue

        event = data.get("event")

        if event == "start":
            stream_sid = data.get("start", {}).get("streamSid")
            log_voice_reply(f"Stream started, stream_sid={stream_sid}")
            continue

        if event == "media":
            audio_bytes = decode_base64_audio(data["media"]["payload"])
            pcm16 = mulaw_to_pcm16(audio_bytes)
            resampled = resample_audio(pcm16)

            result = recognize_audio(recognizer, resampled)

            sequence_number, chunk_number, timestamp = await process_recognition_result(
                websocket,
                stream_sid,
                result,
                sequence_number,
                chunk_number,
                timestamp
            )

        elif event == "stop":
            log_voice_reply("Twilio stream stopped")
            break

    log_voice_reply("Client disconnected")
