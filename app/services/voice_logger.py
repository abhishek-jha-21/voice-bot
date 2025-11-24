from sqlalchemy import text
from app.database import engine
import traceback


def log_voice_reply(speech: str):
    try:
        query = text("INSERT INTO voice_logs (speech_text) VALUES (:speech)")
        with engine.begin() as conn:
            conn.execute(query, {"speech": speech})
        print("LOG INSERTED")
    except Exception as e:
        print("DB Logging Error:", e)
        print(traceback.format_exc())