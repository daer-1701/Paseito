import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session

from . import agente
from .config import CORS_ORIGINS, FRONTEND_DIR, GEMINI_MODEL
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


@app.get("/kiosco", include_in_schema=False)
def kiosco():
    return RedirectResponse("/")


@app.get("/prueba-voz", include_in_schema=False)
def prueba_voz():
    return RedirectResponse("/prueba-voz.html")


class FrontendSinCache(StaticFiles):
    """El navegador revalida cada archivo (304 si no cambió): el kiosco nunca se queda con JS viejo."""

    async def get_response(self, path, scope):
        respuesta = await super().get_response(path, scope)
        respuesta.headers["Cache-Control"] = "no-cache"
        return respuesta


# Comodidad para desarrollo y para el kiosco: si el frontend está al lado, se sirve en la raíz.
# Va al final para que las rutas de la API tengan prioridad.
if FRONTEND_DIR and FRONTEND_DIR.is_dir():
    app.mount("/", FrontendSinCache(directory=FRONTEND_DIR, html=True), name="frontend")
