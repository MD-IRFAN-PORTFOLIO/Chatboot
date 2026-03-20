from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import asyncio

# These must be imported after app creation if they use the app, 
# but here they are standard APIRouters.
from server.routes import admin, chat
from server.database import init_db, client

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

# ==========================================
# HIGH PRIORITY DIAGNOSTIC ROUTES
# ==========================================

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "Backend is running"}

@app.get("/debug-paths")
async def debug_paths():
    db_status = "Unknown"
    db_error = None
    try:
        # Quick ping to test DB connection (2s timeout)
        await asyncio.wait_for(client.admin.command('ping'), timeout=2.0)
        db_status = "Connected"
    except Exception as e:
        db_status = "Failed"
        db_error = str(e)

    # Static Path Resolution
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) 
    potential_paths = [
        os.path.join(BASE_DIR, "frontend_dist"), 
        os.path.join(os.path.dirname(BASE_DIR), "frontend"), 
        "frontend_dist",
        "/app/frontend_dist"
    ]
    found_path = next((p for p in potential_paths if os.path.exists(p)), "NOT_FOUND")

    return {
        "status": "online",
        "mongodb": {
            "status": db_status,
            "error": db_error,
            "url_provided": "YES" if os.getenv("MONGODB_URL") else "NO"
        },
        "cwd": os.getcwd(),
        "base_dir": BASE_DIR,
        "frontend_path": found_path,
        "cwd_files": os.listdir(".")
    }

# ==========================================
# STARTUP LOGIC
# ==========================================

@app.on_event("startup")
async def on_startup():
    # Run DB init in background so it doesn't block app startup
    asyncio.create_task(init_db())

# ==========================================
# MOUNTING (Order Matters!)
# ==========================================

# 1. API Routers
app.include_router(chat.router)
app.include_router(admin.router)

# 2. Static Assets (Photos/Uploads)
app.mount("/static", StaticFiles(directory="static"), name="static")

# 3. Frontend (Catch-all at the end)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) 
FRONTEND_PATH = os.path.join(BASE_DIR, "frontend_dist") if os.path.exists(os.path.join(BASE_DIR, "frontend_dist")) else os.path.join(os.path.dirname(BASE_DIR), "frontend")

if os.path.exists(FRONTEND_PATH):
    app.mount("/", StaticFiles(directory=FRONTEND_PATH, html=True), name="frontend")
else:
    @app.get("/")
    async def root_fallback():
        return {"message": "Backend OK, but Frontend folder missing!", "diagnostics": "/debug-paths"}
