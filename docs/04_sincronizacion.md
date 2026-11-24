# Sincronización

## Qué se hizo

El nodo escucha ZeroMQ REP en el puerto TCP 5555 y procesa lotes con las listas `eventos` y `tombstones`. El emisor usa REQ con tiempos límite configurables. `GET /api/sync/delta?desde=...` obtiene cambios posteriores a un checkpoint temporal; `POST /api/sync/enviar` los envía. El receptor fusiona CRDT y registra tombstones.

## Por qué se hizo así

REQ/REP es un patrón pequeño de solicitud y respuesta. Un checkpoint temporal evita reenviar en cada operación eventos sin cambios; al fallar el envío, el cliente no avanza el checkpoint y puede reintentar.

## Limitaciones

El transporte no cifra ni autentica conexiones: debe limitarse a redes confiables. El checkpoint pertenece al navegador y se mantiene por dirección remota. No hay descubrimiento automático, confirmación de checkpoint remoto ni reintentos en segundo plano. Los nodos deben exponer el puerto 5555 además de la API HTTP.

## Recurrencia y privacidad en los deltas

Los deltas generados desde el checkpoint incluyen `rrule`, `exdates` y `visibilidad` en cada evento, junto con `crdt_data`, y el emisor los conserva en el lote JSON que envía por ZeroMQ. En el documento CRDT, cada campo se representa como un registro LWW `{value, ts}`. Al fusionar documentos, prevalece el registro con la marca temporal más reciente y los nodos convergen al mismo valor.

`rrule` contiene la regla de recurrencia, `visibilidad` contiene `publico`, `privado` o `solo_invitados`, y `exdates` se trata como una única lista LWW completa: cuando hay conflicto, se reemplaza toda la lista en lugar de combinar elementos uno a uno. Al recibir un delta, el receptor fusiona los registros remotos con el documento local, aplica los valores ganadores al modelo y los persiste en SQLite. De este modo, recurrencia y privacidad sobreviven al transporte por ZeroMQ y a las fusiones posteriores del evento.
