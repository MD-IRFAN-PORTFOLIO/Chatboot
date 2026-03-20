from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, JSONResponse
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

# ==========================================
# DIAGNOSTIC LOGGING (Visible in Render Logs)
# ==========================================
print("--- STARTING PATH DIAGNOSTICS ---")
print(f"Current Working Directory: {os.getcwd()}")
print(f"Files in CWD: {os.listdir('.')}")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) 
print(f"BASE_DIR (calculated from __file__): {BASE_DIR}")
if os.path.exists(BASE_DIR):
    print(f"Files in BASE_DIR: {os.listdir(BASE_DIR)}")

potential_paths = [
    os.path.join(BASE_DIR, "frontend_dist"), 
    os.path.join(os.path.dirname(BASE_DIR), "frontend"), 
    "frontend_dist",
    "../frontend",
    "/app/frontend_dist"
]

FRONTEND_PATH = None
for p in potential_paths:
    exists = os.path.exists(p)
    print(f"Checking path '{p}': {'EXISTS' if exists else 'not found'}")
    if exists and not FRONTEND_PATH:
        FRONTEND_PATH = p

print(f"FINAL FRONTEND_PATH: {FRONTEND_PATH}")
print("--- END PATH DIAGNOSTICS ---")

# ==========================================
# ROUTES
# ==========================================

@app.get("/debug-paths")
async def debug_paths():
    return {
        "cwd": os.getcwd(),
        "cwd_files": os.listdir("."),
        "base_dir": BASE_DIR,
        "base_dir_files": os.listdir(BASE_DIR) if os.path.exists(BASE_DIR) else "NOT_FOUND",
        "frontend_path": FRONTEND_PATH,
        "is_p_exists": os.path.exists(FRONTEND_PATH) if FRONTEND_PATH else False
    }

# Mount API Routers
app.include_router(chat.router)
app.include_router(admin.router)

# Mount static files (Uploading/Faculty Photos)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Mount Frontend files at the root /
if FRONTEND_PATH:
    app.mount("/", StaticFiles(directory=FRONTEND_PATH, html=True), name="frontend")
else:
    @app.get("/")
    async def root_fallback():
        return JSONResponse(content={
            "status": "online",
            "message": "Backend OK, but Frontend folder missing!",
            "diagnostics": "/debug-paths"
        })
