@echo off
echo Initializing Aura AI Backend...
cd backend
call venv\Scripts\activate
uvicorn server.main:app --host 127.0.0.1 --port 8000 --reload
pause
