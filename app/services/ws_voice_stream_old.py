import base64
import numpy as np
import json
from vosk import Model, KaldiRecognizer
from app.services.voice_logger import log_voice_reply
from faster_whisper import WhisperModel

model_path = "/var/www/voice-bot.v4edu.in/models/hindi"

model = WhisperModel("medium", device="cpu")  # use cuda for GPU

def decode_base64(payload):
    missing = len(payload) % 4
    if missing:
        payload += "=" * (4 - missing)
    return base64.b64decode(payload)

async def process_audio(audio_bytes):
    # Convert 8-bit mulaw (Twilio default) to PCM float32
    pcm = np.frombuffer(audio_bytes, dtype=np.int8).astype(np.float32) / 128.0

    segments, info = model.transcribe(
        pcm,
        beam_size=1,
        language="hi",
        vad_filter=True,
        temperature=0.0
    )

    final_text = ""
    for seg in segments:
        final_text += seg.text.strip() + " "

    final_text = final_text.strip()

    log_voice_reply(final_text)
    print("Recognized:", final_text)

    return json.dumps({"text": final_text})


async def handle_ws_service(websocket):
    print("Client connected")
    log_voice_reply("Client connected")

    # recognizer = KaldiRecognizer(model, 16000)

    try:
        async for message in websocket:

            try:
                data = json.loads(message)
            except:
                continue

            event = data.get("event")

            if event == "start":
                recognizer.Reset()
                print("Stream started")
                log_voice_reply("Stream started")
                await websocket.send(json.dumps({"status": "ready"}))
                continue

            if event == "media":
                payload = data["media"]["payload"]

                try:
                    audio_bytes = decode_base64(payload)
                except Exception as e:
                    print("Decode error:", e)
                    continue

                print("Frame length:", len(audio_bytes))

                response = await process_audio(audio_bytes)
                await websocket.send(response)
                continue

            if event == "stop":
                print("Stream ended")
                log_voice_reply("Stream ended")
                await websocket.send(json.dumps({"status": "finished"}))
                break

    except Exception as e:
        print("WebSocket error:", e)
        log_voice_reply(f"WS Error: {e}")

    finally:
        print("Client disconnected")
        log_voice_reply("Client disconnected")
