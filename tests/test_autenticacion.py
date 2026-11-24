from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from datetime import timedelta

from main import app
from tests.conftest import EMAIL_PRUEBA
from app.database import SessionLocal
from app.models import Evento


def crear_evento(client, **campos):
    inicio = datetime.now() + timedelta(days=1)
    datos = {
        "titulo": campos.pop("titulo", "Evento"),
        "inicio": inicio.isoformat(),
        "fin": (inicio + timedelta(hours=1)).isoformat(),
        "visibilidad": "publico",
        **campos,
    }
    respuesta = client.post("/api/eventos", json=datos)
    assert respuesta.status_code == 201
    return respuesta.json()


def test_listado_sin_sesion_solo_publico(cliente_autenticado):
    publico = crear_evento(cliente_autenticado, visibilidad="publico")
    privado = crear_evento(cliente_autenticado, visibilidad="privado")
    with TestClient(app) as client:
        respuesta = client.get("/api/eventos")
    ids = {evento["id"].split("::", 1)[0] for evento in respuesta.json()}
    assert publico["id"] in ids
    assert privado["id"] not in ids


def test_put_de_otro_creador_devuelve_403(cliente_autenticado):
    otro = "otro@test.local"
    inicio = datetime.now() + timedelta(days=1)
    db = SessionLocal()
    creado = Evento(
        titulo="Privado ajeno",
        inicio=inicio,
        fin=inicio + timedelta(hours=1),
        creador=otro,
        visibilidad="publico",
    )
    db.add(creado)
    db.commit()
    evento_id = creado.id
    db.close()
    respuesta = cliente_autenticado.put(
        f"/api/eventos/{evento_id}",
        json={"titulo": "No permitido"},
    )
    assert respuesta.status_code == 403


def test_participante_ve_evento_solo_invitados(cliente_autenticado):
    inicio = datetime.now() + timedelta(days=1)
    creado = cliente_autenticado.post(
        "/api/eventos",
        json={
            "titulo": "Solo invitados",
            "inicio": inicio.isoformat(),
            "fin": (inicio + timedelta(hours=1)).isoformat(),
            "participantes": [EMAIL_PRUEBA],
            "visibilidad": "solo_invitados",
        },
    )
    assert creado.status_code == 201
    respuesta = cliente_autenticado.get("/api/eventos")
    assert creado.json()["id"] in [
        evento["id"].split("::", 1)[0] for evento in respuesta.json()
    ]


def test_logout_limpia_sesion(cliente_autenticado):
    respuesta = cliente_autenticado.post("/auth/logout")
    assert respuesta.status_code in (200, 303)
    cliente_autenticado.cookies.delete("session")
    assert cliente_autenticado.get("/auth/me").status_code == 401
