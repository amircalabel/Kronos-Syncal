# Reporte de estado del proyecto

Fecha del reporte: 23 de noviembre de 2026

## 1. Estado general

Kronos-Syncal es un calendario distribuido construido con FastAPI, SQLite, PyCRDT y ZeroMQ. La implementación actual incluye una API REST, calendarios y eventos, invitaciones, conflictos de disponibilidad, sincronización entre nodos, Google OAuth 2.0/OpenID Connect, recurrencias básicas y privacidad de eventos.

La rama de trabajo actual es `kronos_syncal_copilot`. El último commit registrado es `bd48fc2` con el mensaje `feat: autenticación OAuth con Google, recurrencia y privacidad`.

El repositorio debe conservarse sin cambios en el directorio `static/` salvo que exista una solicitud explícita posterior.

## 2. Backend

### Persistencia

- SQLite es la base de datos local mediante SQLAlchemy.
- Se crean tablas para calendarios, eventos, invitaciones y tombstones.
- Las relaciones foráneas se habilitan al abrir las conexiones.
- Las pruebas limpian las listas de invitaciones y los datos relacionados antes de aislar cada caso.
- Existe una compatibilidad ligera de arranque que añade las columnas nuevas de recurrencia y privacidad a bases SQLite existentes:
  - `rrule`
  - `exdates`
  - `visibilidad`

### Modelo de eventos

El modelo `Evento` incluye:

- Identificador UUID.
- Título y descripción.
- Fechas de inicio y fin.
- Evento de todo el día.
- Creador y participantes.
- Estado: propuesta, confirmado o cancelado.
- Versión y fecha de última modificación.
- Calendario asociado.
- Datos serializados para CRDT.
- `rrule`, `exdates` y `visibilidad`.

Las visibilidades disponibles son:

- `publico`: visible sin iniciar sesión.
- `privado`: visible solo para el creador.
- `solo_invitados`: visible para el creador y los participantes.

### Modelo de usuarios

El modelo `Usuario` utiliza `email` como clave primaria. También contiene:

- `nombre`.
- `google_sub`, con restricción única y nullable.

## 3. Google OAuth 2.0 y sesiones

La identidad está implementada con Authlib y `SessionMiddleware`.

Se añadió `app/auth.py` con:

- Instancia global `OAuth`.
- Registro del proveedor `google`.
- URL de metadatos de Google.
- Alcances `openid email profile`.
- Lectura de `GOOGLE_CLIENT_ID` y `GOOGLE_CLIENT_SECRET`.

`main.py` incorpora sesiones mediante `SESSION_SECRET`, con una clave aleatoria de desarrollo si la variable no está definida.

Las rutas añadidas en `app/routes/auth.py` son:

- `GET /auth/login`: inicia la autorización de Google.
- `GET /auth/callback`: obtiene el token, crea o actualiza el usuario y guarda la identidad en la sesión.
- `POST /auth/logout`: vacía la sesión.
- `GET /auth/me`: devuelve el usuario de sesión o 401.

La prueba de callback no abre Google: las pruebas usan una sesión precargada o usan clientes aislados.

## 4. Autorización de la API

Las operaciones protegidas exigen una sesión con correo electrónico:

- `POST /api/eventos`.
- `PUT /api/eventos/{id}`.
- `DELETE /api/eventos/{id}`.
- `POST /api/eventos/{id}/invitar`.
- `POST /api/eventos/{id}/responder`.

Las reglas implementadas son:

- Sin sesión: 401.
- `PUT` por usuario distinto del creador: 403.
- `DELETE` por usuario distinto del creador: 403.
- Invitación por usuario distinto del creador: 403.
- Respuesta por correo distinto al del campo `usuario`: 403.

El listado público solo muestra eventos `publico` para visitantes sin sesión. Los usuarios autenticados pueden ver eventos privados propios y eventos `solo_invitados` si son creador o participante.

`GET /api/eventos/{id}` aplica también la política de privacidad y devuelve 404 cuando el usuario no tiene acceso.

## 5. Invitaciones y conflictos

Se mantiene la relación `Invitacion` con respuestas:

- `pendiente`.
- `aceptado`.
- `rechazado`.

La API permite:

- Agregar participantes e invitaciones.
- Responder por una invitación propia.
- Detectar conflictos temporales.
- Confirmar eventos solo después de una aceptación.
- Forzar una aceptación si existen conflictos.

Las invitaciones también actualizan la lista persistida de participantes del evento.

## 6. Recurrencias

Los eventos pueden almacenar `rrule` y `exdates`.

`GET /api/eventos` usa `dateutil.rrule.rrulestr` para expandir recurrencias.

Las ocurrencias devuelven identificadores compuestos:

```text
f"{id_evento}::{occurrence_iso}"
```

Las excepciones presentes en `exdates` se excluyen del listado.

La expansión está limitada a cinco años hacia adelante si no se indican los filtros `desde` o `hasta`.

## 7. Sincronización CRDT

Ya existía una sincronización entre nodos basada en:

- PyCRDT.
- Registros LWW por campo.
- Transporte ZeroMQ REQ/REP.
- Checkpoints temporales.
- Tombstones para eliminaciones.
- Delta de eventos y eliminaciones.

Los endpoints existentes permiten consultar disponibilidad, enviar cambios y obtener deltas.

La sincronización actual no cifra ni autentica el transporte ZeroMQ y debe ejecutarse solamente en redes confiables.

## 8. Pruebas

Se creó `tests/conftest.py` con el fixture `cliente_autenticado`.

El fixture usa `TestClient` y una cookie de sesión firmada. No necesita iniciar el navegador ni llamar a Google.

Las pruebas añadidas cubren:

- Visitante sin sesión: solo eventos públicos.
- Usuario distinto del creador: 403 al modificar.
- Participante: puede ver un evento `solo_invitados`.
- Logout: elimina la sesión y `/auth/me` devuelve 401.

Las pruebas existentes que usaban operaciones libres fueron adaptadas mínimamente al fixture de sesión.

Resultado verificado:

- 13 pruebas aprobadas.
- 0 fallidas.
- 0 errores.
- El directorio `static/` quedó sin cambios.

## 9. Documentación completada

Se actualizó la documentación existente:

- `docs/02_base_de_datos.md`: esquema de `Usuario` y nuevos campos de `Evento`.
- `docs/05_api.md`: rutas de autenticación, permisos y privacidad.
- `docs/07_futuro.md`: OAuth registrado como ya implementado.

Documentos previos que describen el proyecto todavía pueden contener información parcial o obsoleta sobre autenticación, recurrencias o estructura.

## 10. Trabajo restante

### 10.1 Correcciones técnicas prioritarias

- Añadir `rrule`, `exdates` y `visibilidad` a `_CAMPOS_EVENTO` de `app/crdt.py`.
- Extender `_aplicar_campos` y el proceso de sincronización para conservar íntegramente esos tres campos.
- Extender `crear_evento_crdt` y `actualizar_evento_crdt` con la recurrencia y la privacidad.
- Verificar que los deltas de sincronización no pierdan exdates al recibir o fusionar eventos.
- Añadir migraciones formales para bases existentes, en vez de depender solo de `ALTER TABLE` al iniciar.
- Añadir una restricción o validación de base de datos para los valores permitidos de `visibilidad`.
- Revisar el intercambio CRDT de la recurrencia y las excepciones para evitar marcas temporales incompatibles.

### 10.2 Autenticación y seguridad

- Configurar los orígenes y URIs de redirección reales de Google para el entorno de producción.
- Definir una URL de sesión persistente para despliegues; la clave aleatoria debe ser reemplazada por `SESSION_SECRET` estable.
- Marcar cookies como seguras y adecuadas al despliegue mediante HTTPS.
- Añadir manejo explícito de errores y estados cancelados durante el flujo OAuth.
- Validar el identificador `iss` y el estado de `email_verified` aportado por Google.
- Definir políticas para cuentas con correos cambiados o identificadores de Google duplicados.
- Proteger el transporte ZeroMQ o limitarlo a redes confiables.
- Añadir CSRF, límites de intentos y cabeceras de seguridad si la aplicación se expone públicamente.

### 10.3 Comprobación de reglas de acceso

- Añadir pruebas de acceso para visitantes a eventos privados y `solo_invitados`.
- Añadir pruebas de participante que puede ver pero no modificar un evento ajeno.
- Añadir pruebas de actualización y eliminación por otros usuarios.
- Añadir pruebas de invitación por usuario distinto del creador.
- Añadir pruebas de respuesta con un usuario distinto del invitado.
- Añadir pruebas de inexistencia o privacidad para `GET /api/eventos/{id}`.
- Añadir pruebas de expansión RRULE y exdates.
- Añadir pruebas de recurrencia visible solo para participantes.
- Añadir pruebas de callback OAuth stubbed, sin navegador ni red externa.
- Añadir pruebas de sesión expirada o cookie inválida.

### 10.4 Documentación pendiente

- Actualizar `docs/01_estructura.md`: ahora existen módulos de autenticación y recurrencias.
- Actualizar `docs/02_base_de_datos.md`: eliminar la limitación antigua que afirma que no existe autenticación ni privacidad.
- Actualizar `README.md`: añadir Authlib, python-dateutil, itsdangerous y variables de entorno OAuth.
- Actualizar `README.md`: retirar afirmaciones antiguas de que las recurrencias y el flujo completo de autenticación siguen sin existir.
- Actualizar `docs/07_futuro.md`: resumir separadamente lo implementado y lo pendiente sin afirmar que la recurrencia sigue sin existir.
- Actualizar `docs/04_sincronizacion.md`: documentar cómo se sincronizan `rrule`, `exdates`, `visibilidad` y usuarios.
- Añadir instrucciones concretas de Google Cloud Console: credenciales OAuth, URI autorizado y URI de callback.
- Documentar que `/auth/logout` usa `POST` y no `GET`.

### 10.5 Funcionalidades futuras previstas

- Descubrimiento P2P de nodos.
- Confirmación remota de checkpoints.
- Reintentos automáticos en segundo plano.
- Mejora del protocolo de sincronización para autenticación y cifrado.
- Mini-agente de lenguaje natural.
- Soporte offline del navegador mediante IndexedDB.
- Caché de aplicación y funcionamiento con pérdida de conexión.
- Paginación en listas de eventos.
- Auditoría completa de cambios y eliminaciones.
- Mecanismo formal de migraciones.
- Interfaz del flujo OAuth, aunque no se debe tocar `static/` sin una solicitud específica posterior.

## 11. Riesgos conocidos

- La migración de esquema solo añade las nuevas columnas al arrancar; no sustituye una estrategia completa de versiones de base de datos.
- Las condiciones de privacidad pueden ser inconsistentes si se alteran los datos durante sincronización remota.
- Los datos remotos pueden contener visibilidad o recurrencias no sincronizados por el CRDT actual.
- Los secretos OAuth no deben almacenarse ni distribuirse fuera de variables de entorno.
- El transporte ZeroMQ sigue abierto a cambios no autenticados.
- La documentación contiene referencias históricas que aún pueden contradecir el estado implementado.

## 12. Resumen ejecutivo

El núcleo funcional ya está implementado: API REST, persistencia, CRDT, sincronización, invitaciones, OAuth con Google, permisos básicos, privacidad y recurrencias. La mayor deuda actual está en la integración completa de los nuevos campos con el CRDT y la sincronización, junto con la endurecimiento de seguridad, las pruebas adicionales y la actualización documental.
