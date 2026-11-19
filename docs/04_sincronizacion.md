# Sincronización

## Qué se hizo

El nodo escucha ZeroMQ REP en el puerto TCP 5555 y procesa lotes con las listas `eventos` y `tombstones`. El emisor usa REQ con tiempos límite configurables. `GET /api/sync/delta?desde=...` obtiene cambios posteriores a un checkpoint temporal; `POST /api/sync/enviar` los envía. El receptor fusiona CRDT y registra tombstones.

## Por qué se hizo así

REQ/REP es un patrón pequeño de solicitud y respuesta. Un checkpoint temporal evita reenviar en cada operación eventos sin cambios; al fallar el envío, el cliente no avanza el checkpoint y puede reintentar.

## Limitaciones

El transporte no cifra ni autentica conexiones: debe limitarse a redes confiables. El checkpoint pertenece al navegador y se mantiene por dirección remota. No hay descubrimiento automático, confirmación de checkpoint remoto ni reintentos en segundo plano. Los nodos deben exponer el puerto 5555 además de la API HTTP.
