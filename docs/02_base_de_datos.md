# Base de datos

## Qué se hizo

`Calendario` registra nombre y propietario. `Evento` conserva título, descripción, fechas, estado, participantes, versión, calendario asociado y los registros CRDT serializados como JSON. `EventoTombstone` identifica una eliminación, quién la realizó y cuándo ocurrió. Las fechas se almacenan en SQLite como UTC sin zona horaria.
`Usuario` identifica cuentas mediante `email` como clave primaria, conserva `nombre` y el identificador único de Google `google_sub`. `Evento` incluye `rrule`, `exdates` y `visibilidad` (`publico`, `privado` o `solo_invitados`).

## Por qué se hizo así

SQLite guarda un archivo local por instalación, ofrece transacciones sin servidor adicional y es adecuado para equipos modestos. Las claves foráneas se activan al abrir cada conexión. Los tombstones evitan que la sincronización interprete una eliminación como ausencia de datos y restaure el evento desde otro nodo.

## Limitaciones

No se incluyen migraciones automáticas para bases creadas con esquemas anteriores. Un evento cancelado se conserva y no aparece en el listado predeterminado; se puede consultar con `estado=cancelado`. No hay autenticación ni políticas de acceso por propietario.
