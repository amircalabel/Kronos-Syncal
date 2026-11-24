# Base de datos

## Qué se hizo

`Calendario` registra nombre y propietario. `Evento` conserva título, descripción, fechas, estado, participantes, versión, calendario asociado y los registros CRDT serializados como JSON. También incluye `rrule` para la regla de recurrencia, `exdates` para las fechas excluidas y `visibilidad`, restringida a `publico`, `privado` o `solo_invitados`. Las fechas se almacenan en SQLite como UTC sin zona horaria.

`Usuario` representa las cuentas autenticadas con Google: usa `email` como clave primaria y conserva el nombre y el identificador único de Google (`google_sub`). La privacidad se aplica en la API: los eventos privados solo son visibles para su creador; los de solo invitados, para el creador y sus participantes.

## Por qué se hizo así

SQLite guarda un archivo local por instalación, ofrece transacciones sin servidor adicional y es adecuado para equipos modestos. Las claves foráneas se activan al abrir cada conexión. Los tombstones evitan que la sincronización interprete una eliminación como ausencia de datos y restaure el evento desde otro nodo.

## Limitaciones

No se incluyen migraciones automáticas generales para bases creadas con esquemas anteriores; el arranque solo añade compatibilidad para las columnas de recurrencia y visibilidad. La autenticación de usuarios se realiza mediante Google OAuth. Un evento cancelado se conserva y no aparece en el listado predeterminado; se puede consultar con `estado=cancelado`.
