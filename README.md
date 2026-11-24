# Kronos-Syncal

Calendario distribuido con almacenamiento local SQLite, API FastAPI e
intercambio de cambios entre nodos mediante ZeroMQ. Los campos de los eventos
se resuelven con registros CRDT LWW.

## Requisitos

Python 3.10 o posterior. Instala las dependencias del proyecto en tu entorno:

```bash
python -m pip install "fastapi[standard]" sqlalchemy pyzmq pycrdt authlib python-dateutil itsdangerous python-dotenv ray pytest httpx
```

## Configuración de Google OAuth

Crea un archivo `.env` en la raíz del proyecto y define estas variables:

```dotenv
GOOGLE_CLIENT_ID=tu-id-de-cliente
GOOGLE_CLIENT_SECRET=tu-secreto-de-cliente
SESSION_SECRET=una-clave-aleatoria-larga
```

Configura un cliente OAuth de tipo aplicación web en Google Cloud y registra
`http://localhost:8000/auth/callback` como URI de redirección autorizada para
desarrollo local. En producción, registra también la URI HTTPS de tu dominio
con la ruta `/auth/callback` y usa esa misma dirección pública al acceder a la
aplicación. Mantén el archivo `.env` y sus secretos fuera del control de
versiones. Inicia el flujo visitando `/auth/login`.

## Ejecución

Desde la raíz del repositorio:

```bash
uvicorn main:app --reload
```

Por defecto, la aplicación inicia un runtime local de Ray. Para conectar con
un clúster local iniciado manualmente, ejecuta en una terminal:

```bash
ray start --head
```

Y en otra terminal inicia la aplicación indicando que debe descubrir el
clúster:

```bash
RAY_ADDRESS=auto uvicorn main:app --reload
```

Abre `http://localhost:8000`. La base de datos `kronos.db` se crea en el
directorio de trabajo. Cada nodo que reciba sincronizaciones debe permitir
conexiones TCP entrantes en el puerto `5555`; la API HTTP usa el puerto `8000`.
La paralelización con Ray Core se describe en [docs/08_ray.md](docs/08_ray.md).

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

Incluye autenticación de usuarios con Google OAuth, calendarios, eventos,
invitaciones, consulta de disponibilidad, recurrencias con exclusiones
(`rrule` y `exdates`), privacidad por evento y sincronización delta con CRDT y
checkpoint temporal. El transporte de sincronización no cifra ni autentica sus
mensajes; úsalo solo en redes confiables. No incluye descubrimiento P2P ni
almacenamiento offline en el navegador. Consulta las demás limitaciones en
[docs/07_futuro.md](docs/07_futuro.md).
