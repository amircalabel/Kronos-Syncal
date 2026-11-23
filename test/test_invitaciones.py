from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def crear_evento(
    client,
    *,
    creador=None,
    inicio="2035-01-01T10:00:00",
    fin="2035-01-01T11:00:00",
):
    respuesta = client.post(
        "/api/eventos",
        json={
            "titulo": "Evento de invitaciones",
            "inicio": inicio,
            "fin": fin,
            "creador": creador or f"creador-{uuid4()}",
        },
    )
    assert respuesta.status_code == 201
    return respuesta.json()


def test_invitar_agrega_participantes_pendientes(client):
    evento = crear_evento(client)
    usuarios = [f"usuario-{uuid4()}", f"usuario-{uuid4()}"]

    respuesta = client.post(
        f"/api/eventos/{evento['id']}/invitar",
        json={"participantes": usuarios},
    )

    assert respuesta.status_code == 200
    actualizado = respuesta.json()
    assert actualizado["participantes"] == usuarios
    assert {
        invitacion["usuario"]: invitacion["respuesta"]
        for invitacion in actualizado["invitaciones"]
    } == {usuario: "pendiente" for usuario in usuarios}
    assert all(
        invitacion["respondido_en"] is None
        for invitacion in actualizado["invitaciones"]
    )


def test_aceptar_invitacion_sin_conflicto(client):
    evento = crear_evento(client)
    usuario = f"usuario-{uuid4()}"
    client.post(
        f"/api/eventos/{evento['id']}/invitar",
        json={"participantes": [usuario]},
    )

    respuesta = client.post(
        f"/api/eventos/{evento['id']}/responder",
        json={"usuario": usuario, "respuesta": "aceptado"},
    )

    assert respuesta.status_code == 200
    invitacion = respuesta.json()["invitaciones"][0]
    assert invitacion["respuesta"] == "aceptado"
    assert invitacion["respondido_en"] is not None
    assert respuesta.json()["estado"] == "propuesta"


def test_aceptar_con_conflicto_devuelve_409_y_no_cambia_respuesta(client):
    usuario = f"usuario-{uuid4()}"
    conflicto = crear_evento(client, creador=usuario)
    evento = crear_evento(client)
    client.post(
        f"/api/eventos/{evento['id']}/invitar",
        json={"participantes": [usuario]},
    )

    consulta = client.get(
        f"/api/eventos/{evento['id']}/conflictos",
        params={"usuario": usuario},
    )
    assert consulta.status_code == 200
    assert [item["id"] for item in consulta.json()] == [conflicto["id"]]

    respuesta = client.post(
        f"/api/eventos/{evento['id']}/responder",
        json={"usuario": usuario, "respuesta": "aceptado"},
    )

    assert respuesta.status_code == 409
    assert respuesta.json()["detail"]["conflictos"][0]["id"] == conflicto["id"]
    evento_actualizado = client.get(f"/api/eventos/{evento['id']}").json()
    assert evento_actualizado["invitaciones"][0]["respuesta"] == "pendiente"
    assert evento_actualizado["invitaciones"][0]["respondido_en"] is None


def test_aceptar_con_conflicto_y_forzar(client):
    usuario = f"usuario-{uuid4()}"
    crear_evento(client, creador=usuario)
    evento = crear_evento(client)
    client.post(
        f"/api/eventos/{evento['id']}/invitar",
        json={"participantes": [usuario]},
    )

    respuesta = client.post(
        f"/api/eventos/{evento['id']}/responder",
        json={"usuario": usuario, "respuesta": "aceptado", "forzar": True},
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["invitaciones"][0]["respuesta"] == "aceptado"


def test_confirmar_requiere_una_invitacion_aceptada(client):
    evento = crear_evento(client)
    usuario = f"usuario-{uuid4()}"
    client.post(
        f"/api/eventos/{evento['id']}/invitar",
        json={"participantes": [usuario]},
    )

    sin_aceptacion = client.put(
        f"/api/eventos/{evento['id']}",
        json={"estado": "confirmado"},
    )
    assert sin_aceptacion.status_code == 409
    assert client.get(f"/api/eventos/{evento['id']}").json()["estado"] == "propuesta"

    aceptada = client.post(
        f"/api/eventos/{evento['id']}/responder",
        json={"usuario": usuario, "respuesta": "aceptado"},
    )
    assert aceptada.status_code == 200
    confirmacion = client.put(
        f"/api/eventos/{evento['id']}",
        json={"estado": "confirmado"},
    )
    assert confirmacion.status_code == 200
    assert confirmacion.json()["estado"] == "confirmado"
