# Trabajo futuro

## Qué se hizo

Se dejaron identificadas como fases posteriores la detección P2P, el flujo completo de invitaciones, recurrencias RRULE, el mini-agente de lenguaje natural y el cliente offline-first basado en IndexedDB. El mini-agente no forma parte de esta implementación.

## Por qué se hizo así

Estas funciones requieren decisiones adicionales de privacidad, identidad, modelo de recurrencia y sincronización sin conexión en el cliente. Mantenerlas fuera del primer corte permite que el backend y las operaciones básicas sean ejecutables ahora.

## Limitaciones

No se envían ni aceptan invitaciones con estados por participante. No se expanden eventos recurrentes, no hay descubrimiento P2P y no se interpreta texto natural. La interfaz depende de la API en línea, aunque la base local del servidor sigue disponible.
