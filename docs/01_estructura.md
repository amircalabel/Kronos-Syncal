# Estructura del proyecto

## Qué se hizo

```text
main.py                 Entrada FastAPI y ciclo de vida
app/
  auth.py               Registro del cliente OAuth de Google
  database.py           Motor SQLite y dependencia de sesión
  models.py             Calendarios, eventos y tombstones
  crdt.py               Registros LWW con PyCRDT
  sync.py               Transporte ZeroMQ REQ/REP
  routes/calendar.py    API REST y aplicación de deltas
  routes/auth.py        Login, callback y cierre de sesión OAuth
static/
  index.html            Interfaz en español
  app.js                Estado y acciones Alpine.js
tests/
  conftest.py           Fixture de cliente autenticado para pruebas
  test_*.py             Pruebas de API, acceso y CRDT
test/
  test_*.py             Pruebas básicas e invitaciones
docs/                   Guías del proyecto
```

## Por qué se hizo así

La separación mantiene juntas las responsabilidades de persistencia, resolución de conflictos, transporte, endpoints y presentación. No requiere compilación del frontend ni servicios auxiliares.

## Limitaciones

La estructura es intencionalmente pequeña. OAuth se separa entre el registro del cliente y sus rutas; las invitaciones y la lógica de recurrencia permanecen dentro de `routes/calendar.py`, no en módulos independientes. Tampoco hay almacenamiento de checkpoints por nodo.
