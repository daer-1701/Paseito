import os
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
GEMINI_THINKING = os.getenv("GEMINI_THINKING", "low")
GEMINI_MODEL_RESPALDO = os.getenv("GEMINI_MODEL_RESPALDO", "gemini-3.8-flash")
GEMINI_TIMEOUT_S = float(os.getenv("GEMINI_TIMEOUT_S", "25"))

# edge: voces neuronales de Microsoft (rápidas, sin cuota) | gemini: Gemini TTS (lento y con cuota baja)
TTS_MOTOR = os.getenv("TTS_MOTOR", "edge")
EDGE_TTS_VOZ = os.getenv("EDGE_TTS_VOZ", "es-BO-SofiaNeural")
EDGE_TTS_VELOCIDAD = os.getenv("EDGE_TTS_VELOCIDAD", "+0%")

GEMINI_TTS_MODELS = [m.strip() for m in os.getenv(
    "GEMINI_TTS_MODELS", "gemini-3.8-flash-lite-tts,gemini-3.8-flash-tts"
).split(",") if m.strip()]
GEMINI_TTS_VOZ = os.getenv("GEMINI_TTS_VOZ", "Kore")
GEMINI_TTS_TIMEOUT_S = float(os.getenv("GEMINI_TTS_TIMEOUT_S", "60"))

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'paseo.db'}")
ZONA_HORARIA = ZoneInfo("America/La_Paz")

CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]
# Carpeta del frontend que el backend sirve en "/" si existe. Vacío = no servir frontend (solo API).
_frontend = os.getenv("FRONTEND_DIR", str(BASE_DIR.parent / "frontend")).strip()
FRONTEND_DIR = Path(_frontend) if _frontend else None
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")

# Paseo Points (fidelización): base MySQL de otro equipo, solo lectura. Vacío = integración apagada.
PUNTOS_DATABASE_URL = os.getenv("PUNTOS_DATABASE_URL", "").strip()
_ca = os.getenv("PUNTOS_DB_CA", "").strip()
PUNTOS_DB_CA = (BASE_DIR / _ca).resolve() if _ca else None
PUNTOS_TIMEOUT_S = int(os.getenv("PUNTOS_TIMEOUT_S", "6"))
# API de Paseo Points (p. ej. http://localhost:4000): valida el QR de cliente sin que el secreto salga de su servidor.
PUNTOS_API_URL = os.getenv("PUNTOS_API_URL", "").strip().rstrip("/")
PUNTOS_API_KEY = os.getenv("PUNTOS_API_KEY", "").strip()
# Respaldo sin API: secreto propio del QR (HMAC-SHA256). Nunca el JWT_SECRET de sesiones de Paseo Points.
PUNTOS_QR_SECRET = os.getenv("PUNTOS_QR_SECRET", "").strip()
