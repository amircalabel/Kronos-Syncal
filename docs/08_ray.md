# Paralelización con Ray Core

## Elección de Ray Core

Kronos-Syncal usa primitivas explícitas de Ray Core para ejecutar trabajo en
paralelo. No usa Ray Serve: Serve automatiza el despliegue y escalado de
servicios, mientras que aquí se requiere que el código de la aplicación
controle directamente qué operaciones se distribuyen y cómo se combinan sus
resultados. Esta decisión también respeta la restricción del proyecto de no
delegar decisiones de diseño distribuido a herramientas de automatización.

Al iniciar FastAPI, `main.py` conecta con el clúster indicado por
`RAY_ADDRESS` mediante `ray.init(address="auto")`, o inicia Ray localmente si
la variable no está definida. Al cerrar la aplicación, llama a
`ray.shutdown()`.

## Tasks y Actors

Una **Task** ejecuta una función sin estado que devuelve un resultado. Un
**Actor** mantiene estado entre llamadas y serializa operaciones sobre ese
estado. La expansión de una recurrencia y el cálculo de ocupación de un usuario
son operaciones independientes: reciben sus datos, producen resultados y no
necesitan conservar estado entre solicitudes. Por eso se implementan como
Ray Tasks; no se necesita un Actor para estos endpoints.

`GET /api/disponibilidad` crea una Task por usuario y combina los intervalos
ocupados devueltos en la aplicación. `GET /api/eventos` envía a Tasks los
eventos recurrentes y vuelve a colocar sus ocurrencias expandidas en el orden
de eventos del resultado. Los eventos sin recurrencia no requieren expansión.

## Verificación

La ejecución con Ray Core real se verificó en el entorno local: una Task remota
de prueba devolvió el resultado esperado y `ray.shutdown()` cerró el runtime.
También se ejecutó la suite completa con el runtime Ray activo: las 22 pruebas
pasaron, incluidas las comprobaciones de disponibilidad paralela y expansión
de tres eventos recurrentes. Estas pruebas usan `@ray.remote`, `.remote()` y
`ray.get()` reales, sin reemplazos síncronos.

## Tolerancia a fallos y determinismo

Ray conserva el linaje de las Tasks para poder reconstruir resultados perdidos
volviendo a ejecutar el trabajo y sus dependencias disponibles. Ante un fallo
de worker, las Tasks pueden reintentarse según la política de reintentos de
Ray; no se debe asumir que una ejecución tiene efectos exactamente una vez.
Las Tasks de este proyecto son de solo lectura y devuelven valores, por lo que
su repetición no modifica la base de datos.

Las Tasks son sin estado y deben ser deterministas respecto a sus entradas y a
los datos consultados. Si la base cambia entre un intento y otro, el resultado
puede diferir; por ello, no se realizan escrituras de negocio desde estas
funciones. En un clúster remoto, todos los workers necesitan el código y las
dependencias del proyecto, además de acceso a la base indicada por la URL. La
base SQLite local no se comparte automáticamente entre nodos, por lo que su
ruta solo funciona en workers que tengan acceso al mismo archivo. Un clúster
con nodos independientes requiere una base de datos accesible por todos ellos.
