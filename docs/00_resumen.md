# Resumen

## Qué se hizo

Kronos-Syncal es un calendario distribuido con API REST, almacenamiento local y una interfaz web en español. Permite crear, editar y cancelar eventos, administrar calendarios, consultar disponibilidad y enviar cambios a otros nodos. Los campos del evento usan registros CRDT LWW para resolver ediciones concurrentes.

```text
 Navegador (HTML + Alpine.js)
              │ HTTP
              ▼
       FastAPI ───── ZeroMQ REQ/REP ───── FastAPI de otro nodo
          │                                      │
        SQLite                                 SQLite
          └──────── CRDT LWW por campo ─────────┘
```

Stack: Python, FastAPI, SQLAlchemy, SQLite, PyCRDT, ZeroMQ y Alpine.js.

## Por qué se hizo así

SQLite evita un servicio de base de datos separado y mantiene los datos disponibles localmente. PyCRDT conserva marcas por campo y ZeroMQ ofrece un transporte ligero entre instalaciones. Alpine.js permite una interfaz sin proceso de compilación.

## Limitaciones

La aplicación proporciona sincronización explícita entre direcciones conocidas, no descubrimiento P2P ni operación sin conexión en el navegador. El mini-agente de lenguaje natural queda como función futura. El CDN de Alpine.js requiere conexión para cargar la interfaz.
