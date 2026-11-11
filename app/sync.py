"""Sincronización básica entre nodos usando ZeroMQ.

La sincronización por delta consiste en enviar únicamente los cambios relevantes, no el estado completo, para reducir ancho de banda y facilitar la resolución de diferencias entre nodos. En una implementación futura se usarán tombstones para marcar borrados y reordenar eventos si es necesario.
"""

from __future__ import annotations

import json
import threading
from typing import Any, Dict

import zmq


_SERVERS = {}


def iniciar_servidor_sync(puerto: int):
    """Inicia un servicio de sincronización REP en segundo plano."""
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind(f"tcp://*:{puerto}")

    def worker():
        while True:
            try:
                mensaje = socket.recv_json()
                socket.send_json({"status": "ok", "payload": mensaje})
            except Exception:
                break

    hilo = threading.Thread(target=worker, daemon=True)
    hilo.start()
    _SERVERS[puerto] = (context, socket, hilo)
    return hilo


def enviar_cambios(destino: str, cambios: Dict[str, Any]):
    """Envía un lote de cambios a un nodo destino usando ZeroMQ REQ/REP."""
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect(f"tcp://{destino}:5555")
    socket.send_json({"cambios": cambios})
    respuesta = socket.recv_json()
    socket.close()
    context.term()
    return respuesta
