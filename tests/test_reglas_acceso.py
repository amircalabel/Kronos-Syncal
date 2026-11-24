import base64
import json
import os
from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from itsdangerous import TimestampSigner

from main import app


def crear_cliente_sesion(email: str) -> TestClient:
    secret = os.getenv("SESSION_SECRET", "secreto-de-pruebas")
    client = TestClient(app)
    contenido = base64.b64encode(
        json.dumps(
            {
                "user": {
                    "email": email,
                    "name": email,
                    "sub": f"google-sub-{email}",
                }
            }
        ).encode("utf-8")
    )
    cookie = TimestampSigner(secret).sign(contenido).decode("utf-8")
    client.cookies.set("session", cookie)
    return client


def crear_evento(client: TestClient, **campos) -> dict:
    inicio = campos.pop("inicio", datetime.now() + timedelta(days=1))
    datos = {
        "titulo": campos.pop("titulo", "Evento de prueba"),
        "inicio": inicio.isoformat(),
        "fin": (inicio + timedelta(hours=1)).isoformat(),
        **campos,
    }
    respuesta = client.post("/api/eventos", json=datos)
    assert respuesta.status_code == 201
    return respuesta.json()


def test_visitante_no_puede_ver_evento_privado(cliente_autenticado):
    evento = crear_evento(cliente_autenticado, visibilidad="privado")

    visitante = TestClient(app)
    respuesta = visitante.get(f"/api/eventos/{evento['id']}")

    assert respuesta.status_code == 404


def test_participante_solo_invitados_puede_ver_pero_no_modificar(
    cliente_autenticado,
):
    participante = "participante@test.local"
    evento = crear_evento(
        cliente_autenticado,
        participantes=[participante],
        visibilidad="solo_invitados",
    )
    client = crear_cliente_sesion(participante)

    consulta = client.get(f"/api/eventos/{evento['id']}")
    actualizacion = client.put(
        f"/api/eventos/{evento['id']}",
        json={"titulo": "Cambio no autorizado"},
    )
    eliminacion = client.delete(f"/api/eventos/{evento['id']}")

    assert consulta.status_code == 200
    assert actualizacion.status_code == 403
    assert eliminacion.status_code == 403


def test_no_creador_no_puede_invitar_participantes(cliente_autenticado):
    evento = crear_evento(cliente_autenticado)
    client = crear_cliente_sesion("otro@test.local")

    respuesta = client.post(
        f"/api/eventos/{evento['id']}/invitar",
        json={"participantes": ["nuevo@test.local"]},
    )

    assert respuesta.status_code == 403


def test_no_se_puede_responder_por_otro_usuario(cliente_autenticado):
    evento = crear_evento(cliente_autenticado)
    invitado = "invitado@test.local"
    invitacion = cliente_autenticado.post(
        f"/api/eventos/{evento['id']}/invitar",
        json={"participantes": [invitado]},
    )
    assert invitacion.status_code == 200

    respuesta = cliente_autenticado.post(
        f"/api/eventos/{evento['id']}/responder",
        json={"usuario": invitado, "respuesta": "aceptado"},
    )

    assert respuesta.status_code == 403


def test_rrule_expande_tres_ocurrencias_y_exdates_excluye_una(
    cliente_autenticado,
):
    inicio = datetime.now().replace(microsecond=0) + timedelta(days=1)
    evento = crear_evento(
        cliente_autenticado,
        inicio=inicio,
        rrule="FREQ=DAILY;COUNT=3",
    )

    ocurrencias = cliente_autenticado.get("/api/eventos").json()
    ocurrencias_evento = [
        ocurrencia
        for ocurrencia in ocurrencias
        if ocurrencia["id"].startswith(f"{evento['id']}::")
    ]
    assert len(ocurrencias_evento) == 3

    actualizacion = cliente_autenticado.put(
        f"/api/eventos/{evento['id']}",
        json={"exdates": [inicio.isoformat()]},
    )
    assert actualizacion.status_code == 200

    ocurrencias = cliente_autenticado.get("/api/eventos").json()
    ocurrencias_evento = [
        ocurrencia
        for ocurrencia in ocurrencias
        if ocurrencia["id"].startswith(f"{evento['id']}::")
    ]
    assert len(ocurrencias_evento) == 2
