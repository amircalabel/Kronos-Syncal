from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.crdt import (
    actualizar_evento_crdt,
    crear_evento_crdt,
    deserialize_doc,
    doc_a_dict,
    fusionar_eventos,
    serialize_doc,
)
from main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_salud(client):
    respuesta = client.get("/api/health")
    assert respuesta.status_code == 200
    assert respuesta.json() == {"status": "ok"}


def test_crear_listar_y_eliminar_evento(client):
    inicio = datetime.now() + timedelta(days=1)
    fin = inicio + timedelta(hours=1)
    respuesta = client.post(
        "/api/eventos",
        json={
            "titulo": "Prueba de calendario",
            "descripcion": "Evento de integración",
            "inicio": inicio.isoformat(),
            "fin": fin.isoformat(),
        },
    )
    assert respuesta.status_code == 201
    evento_id = respuesta.json()["id"]
    assert evento_id

    listado = client.get("/api/eventos")
    assert listado.status_code == 200
    assert any(evento["id"] == evento_id for evento in listado.json())

    eliminado = client.delete(f"/api/eventos/{evento_id}")
    assert eliminado.status_code == 200
    assert eliminado.json()["evento_id"] == evento_id
    assert client.get(f"/api/eventos/{evento_id}").json()["estado"] == "cancelado"


def test_fusion_crdt_elige_la_marca_mas_reciente():
    doc_a = crear_evento_crdt({"titulo": "Título inicial"})
    doc_b = crear_evento_crdt({"titulo": "Título concurrente"})
    actualizar_evento_crdt(doc_a, {"titulo": "Edición antigua"}, "10")
    actualizar_evento_crdt(doc_b, {"titulo": "Edición reciente"}, "20")

    fusionado = fusionar_eventos(doc_a, doc_b)

    assert doc_a_dict(fusionado)["titulo"] == "Edición reciente"
    assert doc_a_dict(doc_b)["titulo"] == "Edición reciente"


def test_serializacion_crdt_conserva_los_registros():
    original = crear_evento_crdt({"titulo": "Persistente"})
    restaurado = deserialize_doc(serialize_doc(original))

    assert doc_a_dict(restaurado)["titulo"] == "Persistente"
