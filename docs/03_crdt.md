# CRDT y resolución de conflictos

## Qué se hizo

Cada campo del evento se guarda en un mapa PyCRDT como `{ "value": ..., "ts": ... }`. La función de fusión compara la marca temporal por campo, elige el registro más reciente y escribe el ganador en ambos documentos.

```text
Nodo A: titulo = {value: "Reunión", ts: 10}
Nodo B: titulo = {value: "Revisión", ts: 12}
Resultado: titulo = {value: "Revisión", ts: 12}
```

Las marcas admiten contadores Lamport numéricos o fechas ISO ordenables; los empates se desempatan por representación JSON para converger. Los documentos se pueden transportar como actualizaciones binarias y el estado usado por la API se persiste como JSON.

## Por qué se hizo así

Un registro LWW por atributo conserva cambios independientes: editar el título no sobrescribe la descripción. PyCRDT proporciona el documento compartido y la serialización de actualizaciones.

## Limitaciones

No hay un servicio de reloj Lamport distribuido ni detección de deriva de relojes. En instalaciones que usan ISO, se recomienda que los nodos mantengan relojes UTC sincronizados. La política de desempate garantiza determinismo, no intención del usuario.
