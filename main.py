from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api import voice_routes, call_routes
import os


app = FastAPI(debug=True)
app.mount("/assets", StaticFiles(directory="assets"), name="assets")

@app.get("/")
def root():
    return {"status": "Voice bot running 🚀"}

app.include_router(voice_routes.router)
app.include_router(call_routes.router)
