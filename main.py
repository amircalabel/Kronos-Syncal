from contextlib import asynccontextmanager
import os
import secrets
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv

load_dotenv()

from app.database import Base, asegurar_columnas_compatibilidad, engine
from app.models import Calendario, Evento, EventoTombstone, Invitacion, Usuario  # noqa: F401
from app.routes.auth import router as auth_router
from app.routes.calendar import aplicar_delta_sync, router
from app.sync import detener_servidor_sync, iniciar_servidor_sync

BASE_DIR = Path(__file__).resolve().parent


@asynccontextmanager
async def lifespan(_application: FastAPI):
    Base.metadata.create_all(bind=engine)
    asegurar_columnas_compatibilidad()
    iniciar_servidor_sync(5555, aplicar_delta_sync)
    try:
        yield
    finally:
        detener_servidor_sync(5555)


app = FastAPI(title="Kronos-Syncal", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET", secrets.token_hex(32)),
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.include_router(router)
app.include_router(auth_router)


@app.get("/", include_in_schema=False)
def inicio():
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.get("/api/health")
def salud():
    return {"status": "ok"}
