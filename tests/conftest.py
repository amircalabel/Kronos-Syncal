import base64
import json
import os

from dotenv import load_dotenv

load_dotenv()

import pytest
from fastapi.testclient import TestClient
from itsdangerous import TimestampSigner
from app.database import SessionLocal
from app.models import Evento, EventoTombstone, Invitacion, Usuario, Calendario

from main import app


EMAIL_PRUEBA = "usuario@test.local"


@pytest.fixture
def cliente_autenticado():
    secret = os.getenv("SESSION_SECRET", "secreto-de-pruebas")
    db = SessionLocal()
    db.query(Invitacion).delete()
    db.query(EventoTombstone).delete()
    db.query(Evento).delete()
    db.query(Usuario).delete()
    db.query(Calendario).delete()
    db.commit()
    db.close()
    with TestClient(app) as client:
        contenido = base64.b64encode(
            json.dumps(
                {
                    "user": {
                        "email": EMAIL_PRUEBA,
                        "name": "Usuario de prueba",
                        "sub": "google-sub-prueba",
                    }
                }
            ).encode("utf-8")
        )
        cookie = TimestampSigner(secret).sign(contenido).decode("utf-8")
        client.cookies.set("session", cookie)
        yield client
