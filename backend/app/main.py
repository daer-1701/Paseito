import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session

from . import agente
from .config import CORS_ORIGINS, GEMINI_MODEL
from .db import crear_tablas, engine
from .rutas import admin, analitica, catalogo, chat
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
)

app.include_router(chat.router)
app.include_router(catalogo.router)
app.include_router(admin.router)
app.include_router(analitica.router)


@app.get("/salud", tags=["sistema"])
def salud():
    return {"ok": True, "modelo": GEMINI_MODEL, "ia_configurada": agente.ia_configurada()}
