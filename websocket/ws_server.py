import asyncio
import websockets
from app.services.ws_voice_stream import handle_ws_service


async def handle_ws(websocket):
    return await handle_ws_service(websocket)

async def main():
    print("Twilio WebSocket Server running on ws://0.0.0.0:9500/twilio-stream")
    async with websockets.serve(handle_ws, "0.0.0.0", 9500):
        await asyncio.Future()  # keep alive


if __name__ == "__main__":
    asyncio.run(main())
