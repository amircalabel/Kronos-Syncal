"""Módulo de CRDT para eventos.

El enfoque es un LWW-Register por campo: cada valor lleva una marca temporal y, si dos nodos escriben el mismo atributo al mismo tiempo, gana el valor con la marca más reciente. Esto permite que campos como `titulo` o `inicio` se resuelvan sin conflicto de forma determinista.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

try:  # pragma: no cover
    from pycrdt import Doc, Map as PyMap
except Exception:  # pragma: no cover
    Doc = None
    PyMap = None


def _timestamp_ms() -> int:
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def _normalizar_campos(datos: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "titulo": datos.get("titulo"),
        "descripcion": datos.get("descripcion"),
        "inicio": datos.get("inicio"),
        "fin": datos.get("fin"),
        "todo_el_dia": datos.get("todo_el_dia", False),
        "creador": datos.get("creador", "anon"),
        "participantes": datos.get("participantes", []),
        "estado": datos.get("estado", "propuesta"),
        "version": datos.get("version", 1),
        "ultima_modificacion": datos.get("ultima_modificacion") or datetime.now(timezone.utc),
    }


def _valor_con_tiempo(valor: Any) -> Dict[str, Any]:
    return {"value": valor, "timestamp": _timestamp_ms()}


def crear_evento_crdt(datos: Dict[str, Any]):
    """Crea un mapa CRDT para un evento dentro de un documento base."""
    payload = _normalizar_campos(datos)

    if Doc is not None and PyMap is not None:
        doc = Doc()
        mapa = doc.get_map("evento")
        for clave, valor in payload.items():
            mapa.set(clave, _valor_con_tiempo(valor))
        return doc

    evento = {}
    for clave, valor in payload.items():
        evento[clave] = _valor_con_tiempo(valor)
    return evento


def actualizar_evento_crdt(doc: Any, cambios: Dict[str, Any]):
    """Actualiza un documento CRDT con un conjunto de cambios."""
    if Doc is not None and PyMap is not None:
        mapa = doc.get_map("evento")
        for clave, valor in cambios.items():
            mapa.set(clave, _valor_con_tiempo(valor))
        return doc

    for clave, valor in cambios.items():
        doc[clave] = _valor_con_tiempo(valor)
    return doc


def fusionar_eventos(doc1: Any, doc2: Any):
    """Fusiona dos documentos CRDT usando regla LWW por timestamp."""
    if Doc is not None and PyMap is not None:
        base = doc1
        evento = base.get_map("evento")
        otro = doc2.get_map("evento")
        for clave in set(evento.keys()) | set(otro.keys()):
            actual = evento.get(clave)
            nuevo = otro.get(clave)
            if actual is None:
                evento.set(clave, nuevo)
            elif nuevo is not None and isinstance(actual, dict) and isinstance(nuevo, dict):
                if nuevo.get("timestamp", 0) >= actual.get("timestamp", 0):
                    evento.set(clave, nuevo)
        return base

    merged = dict(doc1)
    for clave, valor in dict(doc2).items():
        actual = merged.get(clave)
        if actual is None:
            merged[clave] = valor
        elif isinstance(actual, dict) and isinstance(valor, dict):
            merged[clave] = valor if valor.get("timestamp", 0) >= actual.get("timestamp", 0) else actual
        else:
            merged[clave] = valor
    return merged
