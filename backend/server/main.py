from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from server.routes import admin, chat
from server.database import init_db
from fastapi.staticfiles import StaticFiles
import os

# Ensure static directories exist before mounting
os.makedirs("static/uploads/faculty", exist_ok=True)

app = FastAPI(
    title="Hybrid College Chatbot API",
    description="A chatbot backend that queries MongoDB first, falling back to Gemini API.",
    version="1.0.0"
)

# CORS enabled
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with specific origins
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def on_startup():
    await init_db()

# Mount static files (Uploading/Faculty Photos)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Mount Frontend files
if os.path.exists("../frontend"):
    app.mount("/ui", StaticFiles(directory="../frontend", html=True), name="frontend")
elif os.path.exists("frontend_dist"): # For container structure
    app.mount("/ui", StaticFiles(directory="frontend_dist", html=True), name="frontend")

# Include Routers
app.include_router(chat.router)
app.include_router(admin.router)

@app.get("/", tags=["Root"])
async def root():
    return {"message": "Welcome to Hybrid College Chatbot API. Access /docs for API documentation."}
