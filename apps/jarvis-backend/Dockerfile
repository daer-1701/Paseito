FROM python:3.11.11-slim-bookworm
ENV PYTHONUNBUFFERED=1 JARVIS_HOST=0.0.0.0 JARVIS_DB=/data/jarvis.sqlite3
WORKDIR /app
COPY apps/jarvis-backend/jarvis ./jarvis
COPY apps/jarvis-backend/web ./web
COPY apps/jarvis-backend/data ./data
RUN useradd --uid 10001 --create-home jarvis && mkdir /data && chown jarvis:jarvis /data
USER jarvis
EXPOSE 8000
CMD ["python", "-m", "jarvis.bootstrap"]
