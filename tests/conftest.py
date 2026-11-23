import base64
import json
import os

import pytest
from fastapi.testclient import TestClient
from itsdangerous import TimestampSigner

from main import app


EMAIL_PRUEBA = "usuario@test.local"


@pytest.fixture
def cliente_autenticado():
    secret = os.getenv("SESSION_SECRET", "secreto-de-pruebas")
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
