# File: app/services/ws_voice_stream.py
# 🚀 Full Speech-to-Speech AI Voice Bot (Twilio <-> OpenAI Voice Streaming)

import os
import json
import asyncio
import aiohttp
from app.services.voice_logger import log_voice_reply

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise Exception("❌ OPENAI_API_KEY missing from environment")

URL = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01"


async def handle_ws_service(websocket):
    log = lambda msg: log_voice_reply(f"[VOICE-AI] {msg}")

    stream_sid = None
    is_generating = False

    log("📞 Twilio call connected")

    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(
            URL,
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "OpenAI-Beta": "realtime=v1",
            },
        ) as oai:

            # 🔥 Configure Real-Time Speech-to-Speech Mode
            await oai.send_json({
                "type": "session.update",
                "session": {
                    "modalities": ["audio", "text"],   # REQUIRED
                    "instructions": (
                        "तुम एक दोस्ताना हिंदी बोलने वाले असिस्टेंट हो। "
                        "हमेशा सिर्फ हिंदी में जवाब दो, आवाज में। "
                        "जवाब छोटा, मीठा और मददगार हो।"
                    ),
                    "voice": "alloy",                   # Works if speech is enabled
                    "input_audio_format": "g711_ulaw",
                    "output_audio_format": "g711_ulaw", # Twilio compatible
                    "turn_detection": {
                        "type": "server_vad",
                        "threshold": 0.5,
                        "prefix_padding_ms": 300,
                        "silence_duration_ms": 600,
                    },
                    "input_audio_transcription": {      # Whisper ASR
                        "model": "whisper-1",
                        "language": "hi",
                    },
                }
            })

            # 🔄 Handle OpenAI → Twilio streaming
            async def openai_to_twilio():
                nonlocal is_generating

                async for msg in oai:
                    if msg.type != aiohttp.WSMsgType.TEXT:
                        continue

                    data = json.loads(msg.data)
                    event_type = data.get("type")

                    if event_type == "input_audio_buffer.speech_started":
                        log("🎙 User started speaking")

                    elif event_type == "input_audio_buffer.speech_stopped":
                        log("🛑 User stopped — generating reply")
                        await oai.send_json({
                            "type": "response.create",
                            "response": {
                                "modalities": ["audio", "text"],
                                "max_output_tokens": 200,
                            },
                        })
                        is_generating = True

                    elif event_type == "response.audio.delta":
                        if stream_sid:
                            await websocket.send(json.dumps({
                                "event": "media",
                                "streamSid": stream_sid,
                                "media": {"payload": data["delta"]}
                            }))
                            log(f"🔊 Sending audio chunk ({len(data['delta'])} bytes)")

                    elif event_type == "response.text.delta":
                        log(f"💬 AI (text): {data.get('delta')}")

                    elif event_type == "response.completed":
                        log("✔ OpenAI finished speaking")
                        is_generating = False

                    elif event_type == "error":
                        log(f"🚨 OPENAI ERROR: {json.dumps(data.get('error'), ensure_ascii=False)}")

            forward_task = asyncio.create_task(openai_to_twilio())

            # 🎯 Handle Twilio → OpenAI audio incoming
            async for message in websocket:
                data = json.loads(message)
                event = data.get("event")

                if event == "start":
                    stream_sid = data["start"]["streamSid"]
                    log(f"🟢 Twilio Stream Started — SID={stream_sid}")

                elif event == "media":
                    await oai.send_json({
                        "type": "input_audio_buffer.append",
                        "audio": data["media"]["payload"],
                    })

                elif event == "stop":
                    await oai.send_json({"type": "input_audio_buffer.commit"})
                    log("📵 Call ended")
                    break

            forward_task.cancel()

    log("🏁 Call session closed")
