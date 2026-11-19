# API

## Qué se hizo

| Método | Ruta | Cuerpo o parámetros | Respuesta |
|---|---|---|---|
| GET | `/api/health` | — | `{status: "ok"}` |
| GET | `/api/eventos` | Filtros opcionales: `calendario_id`, `estado`, `desde`, `hasta` | Lista de eventos |
| GET | `/api/eventos/{id}` | — | Evento o 404 |
| POST | `/api/eventos` | Título, fechas y campos opcionales | Evento creado (201) |
| PUT | `/api/eventos/{id}` | Campos parciales del evento | Evento actualizado |
| DELETE | `/api/eventos/{id}` | `eliminado_por` opcional | Confirmación y tombstone |
| GET | `/api/calendarios` | — | Lista de calendarios |
| POST | `/api/calendarios` | `nombre`, `propietario` | Calendario creado (201) |
| GET | `/api/disponibilidad` | `inicio`, `fin`, `usuarios` opcional (CSV) | Intervalos ocupados y libres |
| GET | `/api/sync/delta` | `desde` opcional (checkpoint ISO) | Eventos, tombstones y checkpoint |
| POST | `/api/sync/enviar` | `{destino, cambios, timeout_ms?}`; cambios contiene listas `eventos` y `tombstones` | Resultado ZeroMQ |

Las fechas usan ISO 8601. Se rechazan intervalos inválidos y estados fuera de propuesta, confirmado o cancelado.

## Por qué se hizo así

La API REST es compatible con el navegador y permite a otros clientes consultar calendarios. Los esquemas Pydantic validan las entradas antes de persistirlas.

## Limitaciones

No hay autenticación, paginación ni permisos. El endpoint de envío reporta fallos de transporte como tiempo de espera HTTP.
