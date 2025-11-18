from fastapi import FastAPI
from app.api import voice_routes, call_routes
from fastapi.staticfiles import StaticFiles


app = FastAPI(title="NEET Voice Bot")
app.mount("/assets", StaticFiles(directory="assets"), name="assets")
@app.get("/")
def root():
    return {"status": "Voice bot running 🚀"}

# include all routers
app.include_router(voice_routes.router)
app.include_router(call_routes.router)