"""One server configuration; environment overrides root .env."""
import os
from pathlib import Path
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / '.env')
FRONTEND_DIR = Path(os.getenv('FRONTEND_DIR', ROOT / 'frontend'))
CORS_ORIGINS = [s.strip() for s in os.getenv('CORS_ORIGINS', '').split(',') if s.strip()]
ZONA_HORARIA = ZoneInfo('America/La_Paz')
PUNTOS_DATABASE_URL = os.getenv('PUNTOS_DATABASE_URL', '').strip()
_ca = os.getenv('PUNTOS_DB_CA', '').strip()
PUNTOS_DB_CA = Path(_ca).resolve() if _ca else None
PUNTOS_TIMEOUT_S = max(1, min(6, int(os.getenv('PUNTOS_TIMEOUT_S', '3'))))
