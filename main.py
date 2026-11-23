from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine
from app.models import Calendario, Evento, EventoTombstone, Invitacion  # noqa: F401
from app.routes.calendar import aplicar_delta_sync, router
from app.sync import detener_servidor_sync, iniciar_servidor_sync

BASE_DIR = Path(__file__).resolve().parent


@asynccontextmanager
async def lifespan(_application: FastAPI):
    Base.metadata.create_all(bind=engine)
    iniciar_servidor_sync(5555, aplicar_delta_sync)
    try:
        yield
    finally:
        detener_servidor_sync(5555)


app = FastAPI(title="Kronos-Syncal", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.include_router(router)


@app.get("/", include_in_schema=False)
def inicio():
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.get("/api/health")
def salud():
    return {"status": "ok"}
