FROM python:3.11.11-slim-bookworm
ENV PYTHONUNBUFFERED=1 JARVIS_HOST=0.0.0.0 JARVIS_DB=/data/jarvis.sqlite3 PYTHONPATH=/app/backend:/app/apps/jarvis-backend
WORKDIR /app
COPY backend/requirements.txt ./backend/requirements.txt
COPY apps/jarvis-backend/requirements.txt ./apps/jarvis-backend/requirements.txt
RUN pip install --no-cache-dir -r apps/jarvis-backend/requirements.txt
COPY backend/app ./backend/app
COPY apps/jarvis-backend/jarvis ./apps/jarvis-backend/jarvis
COPY apps/jarvis-backend/data ./apps/jarvis-backend/data
COPY frontend ./frontend
RUN useradd --uid 10001 --create-home jarvis && mkdir /data && chown jarvis:jarvis /data
USER jarvis
EXPOSE 8000
CMD ["python", "-m", "app.main"]
