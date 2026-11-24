"""Transporte ligero REQ/REP y lotes delta para nodos Kronos-Syncal."""

from __future__ import annotations

import threading
from typing import Any, Callable
from urllib.parse import urlparse

import zmq

_SERVERS: dict[int, dict[str, Any]] = {}
_LOCK = threading.Lock()


def _normalizar_delta(cambios: dict) -> dict:
    if not isinstance(cambios, dict):
        raise ValueError("cambios debe ser un objeto JSON")
    inesperados = set(cambios) - {"eventos", "tombstones", "events"}
    if inesperados:
        raise ValueError("El lote solo puede contener eventos y tombstones")
    eventos = cambios.get("eventos", cambios.get("events", []))
    tombstones = cambios.get("tombstones", [])
    if not isinstance(eventos, list) or not isinstance(tombstones, list):
        raise ValueError("eventos y tombstones deben ser listas")
    eventos_normalizados = []
    for evento in eventos:
        if not isinstance(evento, dict):
            raise ValueError("cada evento debe ser un objeto JSON")
        evento_normalizado = dict(evento)
        evento_normalizado.setdefault("rrule", None)
        evento_normalizado.setdefault("exdates", [])
        evento_normalizado.setdefault("visibilidad", "publico")
        eventos_normalizados.append(evento_normalizado)
    eventos = eventos_normalizados
    return {"eventos": eventos, "tombstones": tombstones}


def _direccion_zmq(destino: str) -> str:
    if destino.startswith("tcp://"):
        return destino
    if destino.startswith(("http://", "https://")):
        parsed = urlparse(destino)
        if not parsed.hostname:
            raise ValueError("La URL de destino no contiene un host válido")
        return f"tcp://{parsed.hostname}:5555"
    if not destino:
        raise ValueError("El destino no puede estar vacío")
    return f"tcp://{destino}"


def iniciar_servidor_sync(
    puerto: int, callback: Callable[[dict], dict]
) -> threading.Thread:
    """Inicia un servidor REP en un hilo daemon que procesa deltas recibidos.

    El mensaje transporta solo las listas `eventos` y `tombstones`; el nodo
    receptor decide cómo aplicar su checkpoint y fusionar los cambios.
    """
    if not 1 <= puerto <= 65535:
        raise ValueError("El puerto debe estar entre 1 y 65535")
    with _LOCK:
        existente = _SERVERS.get(puerto)
        if existente and existente["thread"].is_alive():
            return existente["thread"]
        context = zmq.Context()
        listo = threading.Event()
        estado: dict[str, Any] = {}
        detener = threading.Event()

        def worker() -> None:
            socket = context.socket(zmq.REP)
            socket.setsockopt(zmq.LINGER, 0)
            try:
                socket.bind(f"tcp://*:{puerto}")
                listo.set()
                while not detener.is_set():
                    try:
                        if not socket.poll(100, zmq.POLLIN):
                            continue
                        mensaje = socket.recv_json()
                    except zmq.ContextTerminated:
                        break
                    except zmq.ZMQError as error:
                        if detener.is_set():
                            break
                        estado["error"] = str(error)
                        break
                    try:
                        delta = _normalizar_delta(mensaje)
                        resultado = callback(delta)
                        socket.send_json({"status": "ok", "payload": resultado})
                    except Exception as error:
                        socket.send_json({"status": "error", "error": str(error)})
            except Exception as error:
                estado["error"] = str(error)
                listo.set()
            finally:
                socket.close(linger=0)

        hilo = threading.Thread(target=worker, daemon=True, name=f"sync-rep-{puerto}")
        _SERVERS[puerto] = {
            "context": context,
            "thread": hilo,
            "ready": listo,
            "state": estado,
            "stop": detener,
        }
        hilo.start()
    listo.wait(timeout=2)
    if not listo.is_set():
        detener_servidor_sync(puerto)
        raise RuntimeError(f"No se pudo iniciar el servidor ZeroMQ en el puerto {puerto}")
    if "error" in estado:
        detener.set()
        hilo.join(timeout=2)
        context.term()
        raise RuntimeError(f"No se pudo iniciar el servidor ZeroMQ: {estado['error']}")
    return hilo


def detener_servidor_sync(puerto: int) -> None:
    """Detiene ordenadamente un servidor ZeroMQ local, si está iniciado."""
    with _LOCK:
        servidor = _SERVERS.pop(puerto, None)
    if servidor is None:
        return
    servidor["stop"].set()
    servidor["thread"].join(timeout=2)
    servidor["context"].term()


def enviar_cambios(
    destino: str, cambios: dict, timeout_ms: int = 2000
) -> dict:
    """Envía un delta de eventos y tombstones mediante ZeroMQ REQ/REP."""
    if timeout_ms <= 0:
        raise ValueError("timeout_ms debe ser mayor que cero")
    delta = _normalizar_delta(cambios)
    direccion = _direccion_zmq(destino)
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.setsockopt(zmq.LINGER, 0)
    socket.setsockopt(zmq.SNDTIMEO, timeout_ms)
    socket.setsockopt(zmq.RCVTIMEO, timeout_ms)
    try:
        socket.connect(direccion)
        socket.send_json(delta)
        return socket.recv_json()
    except zmq.Again:
        return {"status": "error", "error": "Tiempo de espera agotado al sincronizar"}
    finally:
        socket.close(linger=0)
        context.term()
