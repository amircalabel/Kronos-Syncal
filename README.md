# Kronos-Syncal

Calendario distribuido con almacenamiento local SQLite, API FastAPI e
intercambio de cambios entre nodos mediante ZeroMQ. Los campos de los eventos
se resuelven con registros CRDT LWW.

## Requisitos

Python 3.10 o posterior. Instala las dependencias del proyecto en tu entorno:

```bash
python -m pip install "fastapi[standard]" sqlalchemy pyzmq pycrdt pytest httpx
```

## Ejecución

Desde la raíz del repositorio:

```bash
uvicorn main:app --reload
```

Abre `http://localhost:8000`. La base de datos `kronos.db` se crea en el
directorio de trabajo. Cada nodo que reciba sincronizaciones debe permitir
conexiones TCP entrantes en el puerto `5555`; la API HTTP usa el puerto `8000`.

Para ejecutar las pruebas:

```bash
pytest
```

## Uso y API

La interfaz permite crear, editar y eliminar eventos, elegir un calendario y
enviar cambios a otro nodo. La documentación de rutas y cuerpos está en
[docs/05_api.md](docs/05_api.md). La guía de inicio y arquitectura está en
[docs/00_resumen.md](docs/00_resumen.md).

## Alcance actual

Incluye calendarios, eventos, consulta de disponibilidad, tombstones y delta
sync con checkpoint temporal. La sincronización no cifra ni autentica los
mensajes; úsala solo en redes confiables. No incluye descubrimiento P2P,
flujo completo de invitaciones, recurrencias, mini-agente de lenguaje natural
ni almacenamiento offline en el navegador; estas funciones quedan para fases
futuras descritas en [docs/07_futuro.md](docs/07_futuro.md).
