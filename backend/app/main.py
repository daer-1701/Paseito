import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session

from . import agente
from .config import CORS_ORIGINS, GEMINI_MODEL
from .db import crear_tablas, engine
from .rutas import admin, analitica, catalogo, chat, voz
from .seed import sembrar

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(_: FastAPI):
    crear_tablas()
    with Session(engine) as db:
        if sembrar(db):
            logging.getLogger("jarvis").info("Base de datos sembrada con los datos del Paseo")
    yield


app = FastAPI(
    title="Paseito API",
    description="Backend de Paseito, la asistente inteligente del Paseo Aranjuez.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Modelo-Voz"],
)

app.include_router(chat.router)
app.include_router(catalogo.router)
app.include_router(admin.router)
app.include_router(analitica.router)
app.include_router(voz.router)


@app.get("/salud", tags=["sistema"])
def salud():
    return {"ok": True, "modelo": GEMINI_MODEL, "ia_configurada": agente.ia_configurada()}


ESTATICOS = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=ESTATICOS), name="static")


@app.get("/kiosco", include_in_schema=False)
def kiosco():
    return FileResponse(ESTATICOS / "kiosco.html")


@app.get("/prueba-voz", include_in_schema=False)
def prueba_voz():
    return FileResponse(ESTATICOS / "prueba-voz.html")
