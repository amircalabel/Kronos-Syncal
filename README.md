# Kronos-Syncal

**Kronos-Syncal** es un calendario distribuido y offline-first construido con FastAPI, SQLite y CRDTs. Permite crear eventos, gestionar invitaciones y consultar disponibilidad incluso sin conexión, sincronizando cambios entre nodos mediante ZeroMQ y resolviendo conflictos de forma automática.

El proyecto está diseñado para funcionar en hardware modesto (4 GB de RAM, 11 GB de disco) y prioriza la simplicidad, la ligereza y el aprendizaje de conceptos fundamentales de sistemas distribuidos.

---

## 🎯 Objetivo

Construir un sistema de calendario distribuido que:

- Permita a varios usuarios (nodos) crear, editar y eliminar eventos.
- Gestione invitaciones y reuniones de grupo.
- Consulte disponibilidad y detecte conflictos de horario.
- Funcione **offline** y sincronice cambios al reconectar.
- Resuelva conflictos de forma automática mediante **CRDTs** (Conflict-free Replicated Data Types).
- Ofrezca controles de privacidad.
- Diferencie entre propuesta, invitación aceptada y evento confirmado.

---

## 🧠 ¿Por qué es difícil?

Un calendario distribuido parece sencillo, pero esconde problemas complejos:

- **Consistencia:** Si dos usuarios editan el mismo evento sin conexión, ¿qué pasa al reconectar?
- **Offline-first:** Los cambios deben aplicarse localmente de inmediato y sincronizarse después.
- **Recurrencia:** Un evento semanal con excepciones ("la reunión del 15 de mayo se cancela") es complejo de modelar.
- **Conflictos:** No hay un servidor central que decida quién gana. Los nodos deben converger por sí solos.
- **Privacidad:** No todos los eventos son visibles para todos los usuarios.

Kronos-Syncal aborda estos problemas usando **CRDTs** y **relojes lógicos** para garantizar que todos los nodos lleguen al mismo estado, sin importar el orden en que lleguen los cambios.

---

## 🏗️ Arquitectura

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Nodo 1     │◄───►│  Nodo 2     │◄───►│  Nodo 3     │
│  (SQLite)   │     │  (SQLite)   │     │  (SQLite)   │
│  (CRDT)     │     │  (CRDT)     │     │  (CRDT)     │
└─────────────┘     └─────────────┘     └─────────────┘
       ▲                   ▲                   ▲
       │                   │                   │
       └───────────────────┴───────────────────┘
                    ZeroMQ (sincronización)
```

- **Cada nodo** tiene su propia base de datos SQLite local.
- **CRDTs** garantizan que los cambios converjan sin coordinador central.
- **ZeroMQ** se usa para la comunicación entre nodos (mensajes ligeros y rápidos).
- **FastAPI** expone una API REST para el frontend y para la sincronización.
- **Alpine.js** se usa para el frontend (ligero, sin build steps).

---

## 🛠️ Stack tecnológico

| Capa | Tecnología | Por qué |
|------|------------|---------|
| Backend | **FastAPI** | Ligero, rápido, ideal para APIs REST. |
| Base de datos | **SQLite** | Cero configuración, un archivo por nodo. |
| ORM | **SQLAlchemy** | Manejo de datos con objetos Python. |
| Sincronización | **ZeroMQ** | Mensajería ultraligera entre nodos. |
| CRDTs | **PyCRDT** | Resolución automática de conflictos. |
| Frontend | **HTML + Alpine.js** | Sin build steps, sin Node.js, sin React. |
| Pruebas | **pytest** | Pruebas unitarias y de integración. |

---

## 📁 Estructura del proyecto

```
kronos-syncal/
├── main.py                  # Punto de entrada de FastAPI
├── requirements.txt         # Dependencias del proyecto
├── docs/                    # Documentación y notas de aprendizaje
│   ├── semana1.md
│   ├── semana2.md
│   └── ...
├── app/
│   ├── __init__.py
│   ├── database.py          # Configuración de SQLAlchemy
│   ├── models.py            # Modelos de datos (Evento, Calendario, etc.)
│   ├── crdt.py              # Lógica de CRDTs para eventos
│   ├── sync.py              # Sincronización entre nodos (ZeroMQ)
│   └── routes/
│       ├── __init__.py
│       └── calendar.py      # Endpoints de la API
├── static/
│   ├── index.html           # Frontend con Alpine.js
│   └── app.js
└── test/
    └── test_basico.py       # Pruebas
```

---

## 🚀 Instalación

### Requisitos

- **Python 3.10+** (idealmente 3.11 o 3.12).
- **pip** (viene con Python).
- **SQLite** (incluido en Python).

### Pasos

1. **Clona el repositorio:**

   ```bash
   git clone https://github.com/tu-usuario/kronos-syncal.git
   cd kronos-syncal
   ```

2. **Crea un entorno virtual (recomendado):**

   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. **Instala las dependencias:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Ejecuta la aplicación:**

   ```bash
   uvicorn main:app --reload
   ```

5. **Abre tu navegador** en `http://127.0.0.1:8000`.

---

## 📚 Documentación

La carpeta `docs/` contiene las notas del **learning path** de 6 semanas que guía el desarrollo del proyecto:

- `semana1.md` — Local-First y escenarios de conflicto.
- `semana2.md` — CRDTs y modelo de datos.
- `semana3.md` — Relojes lógicos (HLC).
- `semana4.md` — Modelado de datos y recurrencia (iCalendar/RFC 5545).
- `semana5.md` — Sincronización, Delta Sync y Tombstones.
- `semana6.md` — Mini-agente para parsear lenguaje natural (futuro).

---

## 🧪 Pruebas

Para ejecutar las pruebas:

```bash
pytest
```

---

## 🗺️ Roadmap

- [x] Semana 1: Local-First y escenarios de conflicto.
- [ ] Semana 2: CRDTs y modelo de datos.
- [ ] Semana 3: Relojes lógicos (HLC).
- [ ] Semana 4: Modelado de datos y recurrencia.
- [ ] Semana 5: Sincronización entre nodos.
- [ ] Semana 6: Mini-agente (opcional, futuro).
- [ ] Frontend con Alpine.js.
- [ ] Pruebas de integración.
- [ ] Documentación final.

---

## 🤝 Contribuciones

Este es un proyecto académico, pero las sugerencias y mejoras son bienvenidas. Si encuentras un bug o tienes una idea, abre un issue o un pull request.

---

## 📄 Licencia

Este proyecto está bajo la licencia MIT. Consulta el archivo `LICENSE` para más detalles.

---

## 🙏 Agradecimientos

- A Martin Kleppmann por su trabajo en Local-First Software y CRDTs.
- A la comunidad de FastAPI, SQLAlchemy, ZeroMQ y PyCRDT.
- A los profesores y compañeros del curso de Sistemas Distribuidos.

---

**Kronos-Syncal** — Porque el tiempo es lo único que no se puede sincronizar sin conflictos.
```
