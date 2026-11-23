# API

## Qué se hizo

| Método | Ruta | Cuerpo o parámetros | Respuesta |
|---|---|---|---|
| GET | `/api/health` | — | `{status: "ok"}` |
| GET | `/api/eventos` | Filtros opcionales: `calendario_id`, `estado`, `desde`, `hasta` | Lista de eventos |
| GET | `/api/eventos/{id}` | — | Evento o 404 |
| POST | `/api/eventos` | Título, fechas y campos opcionales | Evento creado (201) |
| PUT | `/api/eventos/{id}` | Campos parciales del evento | Evento actualizado |
| POST | `/api/eventos/{id}/invitar` | `{participantes: ["a", "b"]}` | Evento con invitaciones pendientes |
| POST | `/api/eventos/{id}/responder` | `{usuario, respuesta, forzar?}`; respuesta es `aceptado` o `rechazado` | Evento actualizado; 409 si hay conflictos y no se fuerza |
| GET | `/api/eventos/{id}/conflictos` | `usuario` | Lista de otros eventos no cancelados que se solapan |
| DELETE | `/api/eventos/{id}` | `eliminado_por` opcional | Confirmación y tombstone |
| GET | `/api/calendarios` | — | Lista de calendarios |
| POST | `/api/calendarios` | `nombre`, `propietario` | Calendario creado (201) |
| GET | `/api/disponibilidad` | `inicio`, `fin`, `usuarios` opcional (CSV) | Intervalos ocupados y libres |
| GET | `/api/sync/delta` | `desde` opcional (checkpoint ISO) | Eventos, tombstones y checkpoint |
| POST | `/api/sync/enviar` | `{destino, cambios, timeout_ms?}`; cambios contiene listas `eventos` y `tombstones` | Resultado ZeroMQ |

Las fechas usan ISO 8601. Se rechazan intervalos inválidos y estados fuera de propuesta, confirmado o cancelado. Las invitaciones comienzan como `pendiente`; solo se puede confirmar un evento mediante `PUT` después de que al menos un participante lo haya aceptado. `forzar: true` permite aceptar pese a los conflictos informados. La API aún no autentica la identidad del creador o de los participantes.

Las respuestas del evento incluyen `invitaciones`, con `usuario`, `respuesta` y `respondido_en`. Los intervalos se consideran superpuestos cuando comparten tiempo (el fin de uno igual al inicio del otro no cuenta como conflicto). Un `409` al aceptar incluye en `detail.conflictos` los eventos en conflicto; `forzar: true` permite continuar y registrar la aceptación.

## Por qué se hizo así

La API REST es compatible con el navegador y permite a otros clientes consultar calendarios. Los esquemas Pydantic validan las entradas antes de persistirlas.

## Limitaciones

No hay autenticación, paginación ni permisos. El endpoint de envío reporta fallos de transporte como tiempo de espera HTTP.
