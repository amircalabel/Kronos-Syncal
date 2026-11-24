# Kronos-Syncal

**Kronos-Syncal** es un calendario distribuido y *local-first* diseñado para gestionar eventos personales y reuniones grupales sin depender de un servidor central único. Cada nodo mantiene su propia base de datos local en SQLite, sincroniza cambios mediante **ZeroMQ (REQ/REP)**, resuelve conflictos de manera determinista mediante **CRDTs (Last-Writer-Wins)** y paraleliza cálculos de disponibilidad y expansión de recurrencias con **Ray Core**.

El proyecto está pensado para ejecutarse en entornos con recursos limitados (4 GB de RAM y almacenamiento reducido), evitando contenedores, orquestadores o dependencias pesadas.

---

## Características principales

- **Almacenamiento local-first:** cada nodo opera sobre su propia instancia de SQLite (`kronos.db`) con claves foráneas y restricciones de integridad.
- **Resolución automática de conflictos (CRDT):** uso de `pycrdt` con semántica *Last-Writer-Wins* (LWW) y marcas temporales lógicas/ISO para campos de eventos, además de *tombstones* (`EventoTombstone`) para propagar eliminaciones sin resurrección de datos.
- **Sincronización delta entre nodos:** intercambio incremental de eventos y eliminaciones mediante ZeroMQ (`REQ/REP`) usando *checkpoints* temporales.
- **Paralelización con Ray Core:** ejecución distribuida/paralela mediante tareas sin estado (`@ray.remote` y `ray.get`) para el cálculo de disponibilidad grupal y la expansión de eventos recurrentes, sin recurrir a herramientas que oculten decisiones de diseño distribuido.
- **Autenticación con Google OAuth 2.0 (OIDC):** inicio de sesión con cuenta de Google (`Authlib` + sesiones firmadas) y control de permisos por rol (creador vs. participante).
- **Gestión completa de calendario:**
  - Creación, edición y cancelación de eventos (`propuesta`, `confirmado`, `cancelado`).
  - Flujo de invitaciones por participante (`pendiente`, `aceptado`, `rechazado`) con detección de conflictos de horario (HTTP `409` y opción `forzar`).
  - Consulta de disponibilidad entre múltiples usuarios.
  - Eventos recurrentes mediante reglas `RRULE` (RFC 5545) y exclusiones puntuales (`EXDATE`).
  - Niveles de privacidad por evento (`publico`, `privado`, `solo_invitados`).

---

## Arquitectura

```text
┌───────────────────────────┐         ZeroMQ (REQ/REP)         ┌───────────────────────────┐
│          Nodo A           │ ◄────────── Delta Sync ────────► │          Nodo B           │
│  FastAPI + SQLite + CRDT  │          (puerto TCP 5555)       │  FastAPI + SQLite + CRDT  │
└─────────────┬─────────────┘                                  └─────────────┬─────────────┘
              │                                                              │
              ▼                                                              ▼
   ┌─────────────────────┐                                        ┌─────────────────────┐
   │      Ray Core       │                                        │      Ray Core       │
   │ (@ray.remote Tasks) │                                        │ (@ray.remote Tasks) │
   └─────────────────────┘                                        └─────────────────────┘

```

* **Backend:** FastAPI + SQLAlchemy + SQLite.
* **Sincronización y convergencia:** `pycrdt` (LWW) + `pyzmq`.
* **Cómputo paralelo:** Ray Core (`@ray.remote` para tareas deterministas y tolerantes a fallos por reconstrucción de linaje).
* **Autenticación:** Google OAuth 2.0 mediante `Authlib` y `Starlette SessionMiddleware`.
* **Frontend:** interfaz ligera en HTML + Alpine.js (sin *build steps* ni Node.js; actualmente en fase inicial mientras se consolida la capa distribuida).

---

## Estructura del proyecto

```text
kronos-syncal/
├── main.py                  # Punto de entrada de FastAPI y ciclo de vida de Ray Core
├── app/
│   ├── auth.py              # Configuración del cliente OAuth de Google
│   ├── database.py          # Motor SQLAlchemy y conexión a SQLite
│   ├── models.py            # Modelos: Usuario, Calendario, Evento, Invitacion, EventoTombstone
│   ├── crdt.py              # Lógica CRDT LWW y fusión de estados
│   ├── sync.py              # Servidor/cliente ZeroMQ y sincronización delta
│   └── routes/
│       ├── auth.py          # Rutas /auth/login, /auth/callback, /auth/logout, /auth/me
│       └── calendar.py      # Endpoints REST de calendarios, eventos, invitaciones y disponibilidad
├── static/
│   ├── index.html           # Interfaz web ligera (Alpine.js)
│   └── app.js               # Lógica de cliente HTTP
├── docs/                    # Documentación técnica del proyecto
└── test/                    # Suite de pruebas automatizadas con pytest

```

---

## Requisitos e instalación

* **Python 3.10 o superior** (recomendado 3.11 o 3.12).

1. **Clona el repositorio y sitúate en la rama activa:**
```bash
git clone [https://github.com/](https://github.com/)<tu-usuario>/kronos-syncal.git
cd kronos-syncal
git checkout kronos-syncal-ray

```


2. **Crea y activa un entorno virtual:**
```bash
python3 -m venv .venv
source .venv/bin/activate

```


3. **Instala las dependencias:**
```bash
python -m pip install "fastapi[standard]" sqlalchemy pyzmq pycrdt authlib python-dateutil itsdangerous python-dotenv ray pytest httpx

```



---

## Configuración de Google OAuth

1. En **Google Cloud Console**, configura la pantalla de consentimiento OAuth (tipo *Externo* y agrega los correos de prueba necesarios).
2. Crea credenciales de tipo **Aplicación web** y registra como URI de redirección autorizada:
```text
http://localhost:8000/auth/callback

```


3. Crea un archivo `.env` en la raíz del proyecto (asegúrate de que esté incluido en `.gitignore`):
```dotenv
GOOGLE_CLIENT_ID=tu-id-de-cliente.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=tu-secreto-de-cliente
SESSION_SECRET=una-clave-aleatoria-larga

```



---

## Ejecución

### Modo local (inicia Ray Core automáticamente)

```bash
uvicorn main:app --reload

```

### Modo clúster local con Ray Core

1. En una terminal, inicia el nodo cabecera de Ray:
```bash
ray start --head

```


2. En otra terminal, inicia la aplicación conectándose al clúster:
```bash
RAY_ADDRESS=auto uvicorn main:app --reload

```



### Puertos y acceso

* **API REST e interfaz web:** `http://localhost:8000`
* **Documentación interactiva (Swagger):** `http://localhost:8000/docs`
* **Health check:** `http://localhost:8000/api/health`
* **Sincronización ZeroMQ entre nodos:** puerto TCP `5555` (configurable por nodo).
* **Base de datos local:** `kronos.db` (generada automáticamente al iniciar).

---

## Pruebas

Para ejecutar la suite completa de pruebas (22 pruebas unitarias y de integración, incluyendo fusión CRDT, control de acceso, recurrencias y tareas paralelas en Ray Core):

```bash
pytest -v

```

---

## Documentación técnica

En la carpeta `docs/` se detalla el diseño y las decisiones técnicas del sistema:

* [`docs/00_resumen.md`](https://www.google.com/search?q=docs/00_resumen.md) — Visión general y arquitectura del sistema.
* [`docs/01_estructura.md`](https://www.google.com/search?q=docs/01_estructura.md) — Organización de módulos y archivos.
* [`docs/02_base_de_datos.md`](https://www.google.com/search?q=docs/02_base_de_datos.md) — Esquema relacional, usuarios, privacidad y *tombstones*.
* [`docs/03_crdt.md`](https://www.google.com/search?q=docs/03_crdt.md) — Modelo CRDT *Last-Writer-Wins* y resolución de conflictos.
* [`docs/04_sincronizacion.md`](https://www.google.com/search?q=docs/04_sincronizacion.md) — Protocolo ZeroMQ REQ/REP y sincronización delta.
* [`docs/05_api.md`](https://www.google.com/search?q=docs/05_api.md) — Especificación de endpoints REST.
* [`docs/06_frontend.md`](https://www.google.com/search?q=docs/06_frontend.md) — Estructura de la interfaz ligera.
* [`docs/07_futuro.md`](https://www.google.com/search?q=docs/07_futuro.md) — Alcance pendiente y trabajo futuro.
* [`docs/08_ray.md`](https://www.google.com/search?q=docs/08_ray.md) — Paralelización con Ray Core, tolerancia a fallos y limitaciones.

---

## Limitaciones conocidas

* **Transporte ZeroMQ sin cifrado:** los mensajes entre nodos viajan en texto plano sobre TCP; debe ejecutarse en redes confiables o sobre túneles seguros.
* **Descubrimiento manual de pares:** los nodos remotos se indican explícitamente al sincronizar (no existe descubrimiento automático P2P).
* **Interfaz web básica:** el frontend en `static/` cubre las operaciones fundamentales; las vistas avanzadas de invitaciones, recurrencia y modo *offline* en navegador (IndexedDB) forman parte de fases posteriores.


---

### Qué mejora respecto al anterior

1. **Coherencia con el estado real:** refleja las 22 pruebas, el modelo `Invitacion`, OAuth, recurrencia, privacidad y Ray Core real.
2. **Transparencia académica:** explica por qué se usa **Ray Core** (`@ray.remote`) en lugar de frameworks que automaticen decisiones distribuidas, alineado con los criterios de evaluación de la asignatura.
3. **Honestidad sobre el frontend y las limitaciones:** deja claro que la interfaz web es mínima y que la seguridad de transporte ZeroMQ y el descubrimiento P2P están documentados como limitaciones, evitando inconsistencias al revisar el repositorio.

```
