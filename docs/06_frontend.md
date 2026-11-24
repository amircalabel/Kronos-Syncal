# Interfaz web

## Qué se hizo

`static/index.html` contiene una página adaptable en español y carga Alpine.js desde CDN. `static/app.js` define `calendarioApp()` con eventos, calendarios, formulario y dirección remota. La interfaz permite crear, editar y eliminar eventos, y sincronizar deltas con un nodo.

## Por qué se hizo así

Alpine.js añade interactividad directamente en HTML sin compilador, servidor Node ni framework pesado. Las peticiones `fetch` usan la API del mismo origen; el endpoint de disponibilidad también puede consumirse desde otros clientes.

## Limitaciones

La página necesita conectividad para cargar Alpine.js desde el CDN y no implementa caché de aplicación ni edición offline con IndexedDB. El checkpoint del envío se conserva en `localStorage` del navegador.
