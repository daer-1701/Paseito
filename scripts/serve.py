"""Cross-platform launcher for the single application."""
import sys
from pathlib import Path
root = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root / 'backend'))
sys.path.insert(0,str(root / 'apps' / 'jarvis-backend'))
from app.main import run
run()
