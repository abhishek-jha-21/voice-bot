import base64
import json
import asyncio
import websockets
import audioop
from openai import OpenAI
from app.services.voice_logger import log_voice_reply

# ==================== CONFIG ====================
OPENAI_API_KEY = "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"
REALTIME_MODEL = "gpt-4o-realtime-preview-2024-10-01"

client = OpenAI(api_key=OPENAI_API_KEY)


def decode_base64(payload: str) -> bytes:
    missing = len(payload) % 4
    if missing:
        payload += "=" * (4 - missing)
    return base64.b64decode(payload)


async def handle_ws_service(websocket: websockets.WebSocketServerProtocol):
    print("Client connected (Twilio)")
    log_voice_reply("Client connected (Twilio)")

    ws_url = f"wss://api.openai.com/v1/realtime?model={REALTIME_MODEL}"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "OpenAI-Beta": "realtime=v1",
    }

    conn = None
    try:
        conn = await websockets.connect(
            ws_url,
            additional_headers=headers,
            max_size=None,
            ping_interval=20,
            ping_timeout=60,
        )

        # Session config
        await conn.send(json.dumps({
            "type": "session.update",
            "session": {
                "modalities": ["text", "audio"],
                "instructions": "You are a super fast, friendly phone assistant. Keep replies extremely short and natural.",
                "voice": "alloy",
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
            }
        }))

        print("Connected to OpenAI Realtime API")
        log_voice_reply("Connected to OpenAI Realtime API")

        # Forward OpenAI → Twilio + log transcript
        async def forward_openai():
            try:
                async for message in conn:
                    event = json.loads(message)
                    typ = event.get("type")

                    # ---- Audio from OpenAI ----
                    if typ == "response.audio.delta":
                        audio_b64 = event.get("delta", "")
                        if audio_b64:
                            await websocket.send(json.dumps({
                                "event": "media",
                                "media": {"payload": audio_b64}
                            }))

                    # ---- Text from OpenAI ----
                    elif typ == "response.output_text.delta":
                        text = event.get("text", "")
                        if text:
                            await websocket.send(json.dumps({"event": "text", "text": text}))
                            log_voice_reply(f"AI: {text}")

                    elif typ == "response.done":
                        log_voice_reply("AI finished speaking")

            except Exception as e:
                log_voice_reply(f"OpenAI listener error: {e}")

        asyncio.create_task(forward_openai())

        # Handle Twilio → OpenAI
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
                try:
                    linear = audioop.ulaw2lin(mulaw_8khz, 2)
                    if isinstance(linear, tuple):
                        linear = linear[0]
                except Exception:
                    linear = audioop.ulaw2lin(mulaw_8khz, 2)

                # Resample 8kHz → 24kHz
                resampled = audioop.ratecv(linear, 2, 1, 8000, 24000, None)[0]

                # --- Log user speech via OpenAI STT ---
                try:
                    transcript = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=resampled  # raw PCM16 bytes
                    )
                    if transcript and transcript.text:
                        log_voice_reply(f"User: {transcript.text}")
                except Exception as e:
                    log_voice_reply(f"STT error: {e}")

                # Send audio to OpenAI Realtime
                await conn.send(json.dumps({
                    "type": "input_audio_buffer.append",
                    "audio": resampled.hex()
                }))

            elif event == "stop":
                log_voice_reply("Twilio stream stopped")
                break

    except Exception as e:
        log_voice_reply(f"Fatal error: {e}")
    finally:
        if conn:
            await conn.close()
        log_voice_reply("Client disconnected")


async def main():
    server = await websockets.serve(handle_ws_service, "0.0.0.0", 9500, ping_interval=None)
    await server.wait_closed()


if __name__ == "__main__":
    asyncio.run(main())