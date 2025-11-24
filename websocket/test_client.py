import asyncio
import websockets
import json
import base64
import audioop

async def test():
    uri = "wss://voice-bot.v4edu.in/twilio-stream"
    async with websockets.connect(uri) as ws:
        print("Connected to local stream")

        # 1. Send "start" event (Twilio always sends this first)
        await ws.send(json.dumps({
            "event": "start",
            "start": {"callSid": "TEST-CALL"}
        }))

        print("Sent start event")

        # 2. Create FAKE μ-law audio (a simple beep at 8kHz)
        pcm = (b"\x00\x10" * 1000)  # fake PCM
        mulaw = audioop.lin2ulaw(pcm, 2)
        payload = base64.b64encode(mulaw).decode()

        # 3. Send a fake "media" event
        await ws.send(json.dumps({
            "event": "media",
            "media": {
                "payload": payload
            }
        }))
        print("Sent fake audio")

        # 4. Receive reply from your server
        reply = await ws.recv()
        print("Received:", reply)

        # 5. Send stop
        await ws.send(json.dumps({"event": "stop"}))
        print("Sent stop event")

asyncio.run(test())
