from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from server.routes import admin, chat
from server.database import init_db
from fastapi.staticfiles import StaticFiles
import os

# Ensure static directories exist
os.makedirs("static/uploads/faculty", exist_ok=True)

app = FastAPI(
    title="Hybrid College Chatbot API",
    description="A chatbot backend that queries MongoDB first, falling back to Gemini API.",
    version="1.0.0"
)

# CORS enabled
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def on_startup():
    await init_db()

# Static Path Resolution
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) 
potential_paths = [
    os.path.join(BASE_DIR, "frontend_dist"), # Docker
    os.path.join(os.path.dirname(BASE_DIR), "frontend"), # Local
    "frontend_dist",
    "../frontend"
]
FRONTEND_PATH = next((p for p in potential_paths if os.path.exists(p)), None)

# Mount API Routers FIRST
app.include_router(chat.router)
app.include_router(admin.router)

# Mount static files (Uploading/Faculty Photos)
# Note: This is mounted at /static
app.mount("/static", StaticFiles(directory="static"), name="static")

# Mount Frontend files at the root /
# This ensures index.html is served at the base URL
if FRONTEND_PATH:
    app.mount("/", StaticFiles(directory=FRONTEND_PATH, html=True), name="frontend")
else:
    @app.get("/")
    async def root():
        return {"message": "Backend Live. Frontend folder not found!"}
