# Estructura del proyecto

## Qué se hizo

```text
main.py                 Entrada FastAPI y ciclo de vida
app/
  database.py           Motor SQLite y dependencia de sesión
  models.py             Calendarios, eventos y tombstones
  crdt.py               Registros LWW con PyCRDT
  sync.py               Transporte ZeroMQ REQ/REP
  routes/calendar.py    API REST y aplicación de deltas
static/
  index.html            Interfaz en español
  app.js                Estado y acciones Alpine.js
docs/                   Guías del proyecto
test/test_basico.py     Pruebas API y CRDT
```

## Por qué se hizo así

La separación mantiene juntas las responsabilidades de persistencia, resolución de conflictos, transporte, endpoints y presentación. No requiere compilación del frontend ni servicios auxiliares.

## Limitaciones

La estructura es intencionalmente pequeña. No hay módulos separados para autenticación, invitaciones, recurrencias ni almacenamiento de checkpoints por nodo.
