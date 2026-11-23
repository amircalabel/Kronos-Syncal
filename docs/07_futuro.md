# Trabajo futuro

## Qué se hizo

Se dejaron identificadas como fases posteriores la detección P2P, recurrencias RRULE, el mini-agente de lenguaje natural y el cliente offline-first basado en IndexedDB. El mini-agente no forma parte de esta implementación.

## Por qué se hizo así

Estas funciones requieren decisiones adicionales de privacidad, identidad, modelo de recurrencia y sincronización sin conexión en el cliente. Mantenerlas fuera del primer corte permite que el backend y las operaciones básicas sean ejecutables ahora.

## Limitaciones

No se expanden eventos recurrentes, no hay descubrimiento P2P y no se interpreta texto natural. La API de invitaciones y conflictos aún no autentica las identidades de los participantes. La interfaz depende de la API en línea, aunque la base local del servidor sigue disponible.

## Estado de pruebas

Verificación: 4 pruebas aprobadas, 0 fallidas, 0 errores y 0 omitidas. Las rutas de salud y eventos superaron la prueba manual; la fusión CRDT conservó la edición con la marca temporal más reciente.
