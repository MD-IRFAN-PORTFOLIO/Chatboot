# Build stage for Python backend
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install dependencies (from backend folder)
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend project
COPY backend/server ./server
COPY backend/static ./static

# Copy Frontend files into a dedicated directory
COPY Frontend ./frontend_dist

# Expose port
EXPOSE 8080

# Run uvicorn (Render provides $PORT env var)
CMD sh -c "uvicorn server.main:app --host 0.0.0.0 --port ${PORT:-8080}"
# Render Build Fix: 20-03-2026 15:49:51
