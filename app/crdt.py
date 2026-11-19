"""Registros CRDT LWW por campo para los datos de cada evento."""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from typing import Any

from pycrdt import Doc, Map

_CAMPOS_EVENTO = (
    "titulo",
    "descripcion",
    "inicio",
    "fin",
    "todo_el_dia",
    "creador",
    "participantes",
    "estado",
    "version",
    "ultima_modificacion",
    "calendario_id",
)


def _jsonable(valor: Any) -> Any:
    if isinstance(valor, (datetime, date)):
        return valor.isoformat()
    if isinstance(valor, dict):
        return {str(clave): _jsonable(elemento) for clave, elemento in valor.items()}
    if isinstance(valor, (list, tuple)):
        return [_jsonable(elemento) for elemento in valor]
    return valor


def _ahora_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _mapa_evento(doc: Doc) -> Map:
    return doc.get("evento", type=Map)


def _marca(registro: Any) -> Any:
    if isinstance(registro, dict):
        return registro.get("ts", 0)
    return 0


def _clave_marca(ts: Any) -> tuple[int, Any]:
    """Compara marcas Lamport numéricas o marcas ISO normalizadas."""
    if isinstance(ts, (int, float)):
        return (0, ts)
    texto = str(ts or "")
    if texto.isdigit():
        return (0, int(texto))
    return (1, texto)


def crear_evento_crdt(datos: dict) -> Doc:
    """Crea un Doc con un registro LWW por campo y marca temporal ISO UTC.

    Cada valor del mapa incluye su marca `ts`; se puede usar un contador
    Lamport o una fecha ISO. La marca permite decidir de forma determinista
    qué escritura prevalece cuando llegan ediciones concurrentes.
    """
    doc = Doc()
    mapa = _mapa_evento(doc)
    ts = _ahora_iso()
    for campo in _CAMPOS_EVENTO:
        if campo in datos:
            valor = _jsonable(datos[campo])
        elif campo == "descripcion":
            valor = ""
        elif campo == "todo_el_dia":
            valor = False
        elif campo == "creador":
            valor = "anon"
        elif campo == "participantes":
            valor = []
        elif campo == "estado":
            valor = "propuesta"
        elif campo == "version":
            valor = 1
        elif campo == "ultima_modificacion":
            valor = ts
        else:
            valor = None
        mapa[campo] = {"value": valor, "ts": ts}
    return doc


def actualizar_evento_crdt(doc: Doc, cambios: dict, ts: str) -> Doc:
    """Actualiza los campos indicados con una nueva marca Lamport o ISO."""
    mapa = _mapa_evento(doc)
    for campo, valor in cambios.items():
        if campo in _CAMPOS_EVENTO:
            mapa[campo] = {"value": _jsonable(valor), "ts": ts}
    return doc


def fusionar_eventos(doc_a: Doc, doc_b: Doc) -> Doc:
    """Fusiona dos Docs usando LWW y aplica los ganadores en ambos sentidos.

    Las marcas Lamport numéricas se comparan como enteros y las marcas ISO
    como texto UTC ordenable. En caso de empate, el valor se desempata mediante
    su representación JSON para que ambos nodos converjan al mismo resultado.
    """
    mapa_a = _mapa_evento(doc_a)
    mapa_b = _mapa_evento(doc_b)
    valores_a = mapa_a.to_py()
    valores_b = mapa_b.to_py()
    ganadores = {}

    for campo in valores_a.keys() | valores_b.keys():
        registro_a = valores_a.get(campo)
        registro_b = valores_b.get(campo)
        clave_a = _clave_marca(_marca(registro_a))
        clave_b = _clave_marca(_marca(registro_b))
        if clave_a == clave_b and registro_a is not None and registro_b is not None:
            elegido = max(
                (registro_a, registro_b),
                key=lambda registro: json.dumps(
                    registro, sort_keys=True, ensure_ascii=False
                ),
            )
        elif registro_b is None or (
            registro_a is not None and clave_a > clave_b
        ):
            elegido = registro_a
        else:
            elegido = registro_b
        if elegido is not None:
            ganadores[campo] = elegido

    for campo, registro in ganadores.items():
        mapa_a[campo] = registro
        mapa_b[campo] = registro
    return doc_a


def doc_a_dict(doc: Doc) -> dict:
    """Desenvuelve los registros LWW y devuelve solo los valores del evento."""
    resultado = {}
    for campo, registro in _mapa_evento(doc).to_py().items():
        if isinstance(registro, dict) and "value" in registro:
            resultado[campo] = registro["value"]
        else:
            resultado[campo] = registro
    return resultado


def serialize_doc(doc: Doc) -> bytes:
    """Serializa el estado CRDT como una actualización binaria PyCRDT."""
    return doc.get_update()


def deserialize_doc(datos: bytes) -> Doc:
    """Reconstruye un Doc CRDT desde una actualización binaria PyCRDT."""
    doc = Doc()
    doc.apply_update(datos)
    return doc
