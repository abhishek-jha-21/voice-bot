import asyncio
import websockets
import base64
import json
from vosk import Model, KaldiRecognizer

model_path = "/var/www/voice-bot.v4edu.in/models/hindi"
model = Model(model_path)

async def handle_ws(websocket):
    recognizer = KaldiRecognizer(model, 16000)
    print("Client connected")

    try:
        async for message in websocket:
            try:
                data = json.loads(message)
            except:
                continue

            event = data.get("event")

            # -----------------------------
            # 1️⃣ START Event (Twilio)
            # -----------------------------
            if event == "start":
                print("Stream started")
                await websocket.send(json.dumps({"status": "ready"}))
                continue

            # -----------------------------
            # 2️⃣ MEDIA Event (audio frames)
            # -----------------------------
            if event == "media":
                payload = data["media"]["payload"]     # base64 string

                # base64 decode → PCM16 bytes
                try:
                    audio_bytes = base64.b64decode(payload)
                except Exception as e:
                    print("Decode error:", e)
                    continue

                # Feed into Vosk
                if recognizer.AcceptWaveform(audio_bytes):
                    result = recognizer.Result()
                    print("Final:", result)
                    await websocket.send(result)
                else:
                    partial = recognizer.PartialResult()
                    await websocket.send(partial)

                continue

            # -----------------------------
            # 3️⃣ STOP Event (call ended)
            # -----------------------------
            if event == "stop":
                print("Stream ended")
                await websocket.send(json.dumps({"status": "finished"}))
                break

            # Ignore unknown events
            # print("Unknown event:", event)

    except Exception as e:
        print("WebSocket error:", e)

    finally:
        print("Client disconnected")


async def main():
    print("Twilio WebSocket Server running on ws://0.0.0.0:9500/twilio-stream")
    async with websockets.serve(handle_ws, "0.0.0.0", 9500):
        await asyncio.Future()  # keep alive


if __name__ == "__main__":
    asyncio.run(main())
