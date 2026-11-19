from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy.orm import Session

from app import sync
from app.crdt import (
    actualizar_evento_crdt,
    crear_evento_crdt,
    doc_a_dict,
    fusionar_eventos,
)
from app.database import SessionLocal, get_db
from app.models import Calendario, Evento, EventoTombstone

router = APIRouter(prefix="/api")
EstadosEvento = Literal["propuesta", "confirmado", "cancelado"]


class CalendarioCrear(BaseModel):
    nombre: str = Field(min_length=1, max_length=200)
    propietario: str = Field(default="local", min_length=1, max_length=200)


class CalendarioRespuesta(BaseModel):
    id: str
    nombre: str
    propietario: str

    model_config = ConfigDict(from_attributes=True)


class EventoCrear(BaseModel):
    titulo: str = Field(min_length=1, max_length=500)
    descripcion: str = ""
    inicio: datetime
    fin: datetime
    todo_el_dia: bool = False
    creador: str = "anon"
    participantes: list[str] = Field(default_factory=list)
    estado: EstadosEvento = "propuesta"
    calendario_id: str | None = None

    @model_validator(mode="after")
    def validar_intervalo(self):
        if _fecha_comparable(self.fin) <= _fecha_comparable(self.inicio):
            raise ValueError("fin debe ser posterior a inicio")
        return self


class EventoActualizar(BaseModel):
    titulo: str | None = Field(default=None, min_length=1, max_length=500)
    descripcion: str | None = None
    inicio: datetime | None = None
    fin: datetime | None = None
    todo_el_dia: bool | None = None
    creador: str | None = None
    participantes: list[str] | None = None
    estado: EstadosEvento | None = None
    calendario_id: str | None = None


class EventoRespuesta(BaseModel):
    id: str
    titulo: str
    descripcion: str
    inicio: datetime
    fin: datetime
    todo_el_dia: bool
    creador: str
    participantes: list[str]
    estado: EstadosEvento
    version: int
    ultima_modificacion: datetime
    calendario_id: str | None

    model_config = ConfigDict(from_attributes=True)


def _fecha_comparable(fecha: datetime) -> datetime:
    if fecha.tzinfo is not None:
        return fecha.astimezone(timezone.utc).replace(tzinfo=None)
    return fecha


class EnviarSync(BaseModel):
    destino: str = Field(min_length=1)
    cambios: dict
    timeout_ms: int = Field(default=2000, gt=0, le=60000)


def _sin_zona(fecha: datetime) -> datetime:
    if fecha.tzinfo is not None:
        return fecha.astimezone(timezone.utc).replace(tzinfo=None)
    return fecha


def _parsear_fecha(valor: datetime | str) -> datetime:
    if isinstance(valor, str):
        return datetime.fromisoformat(valor.replace("Z", "+00:00"))
    return valor


def _crear_doc_evento(evento: Evento):
    if evento.crdt_data:
        from pycrdt import Doc, Map

        doc = Doc()
        doc.get("evento", type=Map).update(evento.crdt_data)
        return doc
    return crear_evento_crdt(evento.to_dict())


def _aplicar_campos(evento: Evento, valores: dict) -> None:
    for campo in (
        "titulo",
        "descripcion",
        "todo_el_dia",
        "creador",
        "participantes",
        "estado",
        "calendario_id",
    ):
        if campo in valores:
            setattr(evento, campo, valores[campo])
    for campo in ("inicio", "fin", "ultima_modificacion"):
        if campo in valores and valores[campo] is not None:
            setattr(evento, campo, _sin_zona(_parsear_fecha(valores[campo])))
    if "version" in valores and valores["version"] is not None:
        evento.version = int(valores["version"])


def _calendario_predeterminado(db: Session) -> Calendario:
    calendario = db.query(Calendario).order_by(Calendario.id).first()
    if calendario is None:
        calendario = Calendario(nombre="Personal", propietario="local")
        db.add(calendario)
        db.flush()
    return calendario


@router.get("/eventos", response_model=list[EventoRespuesta])
def listar_eventos(
    calendario_id: str | None = None,
    estado: EstadosEvento | None = None,
    desde: datetime | None = None,
    hasta: datetime | None = None,
    db: Session = Depends(get_db),
):
    """Lista eventos y filtra por calendario, estado o intervalo superpuesto."""
    consulta = db.query(Evento)
    if calendario_id:
        consulta = consulta.filter(Evento.calendario_id == calendario_id)
    if estado:
        consulta = consulta.filter(Evento.estado == estado)
    else:
        consulta = consulta.filter(Evento.estado != "cancelado")
    if desde:
        consulta = consulta.filter(Evento.fin > _sin_zona(desde))
    if hasta:
        consulta = consulta.filter(Evento.inicio < _sin_zona(hasta))
    return consulta.order_by(Evento.inicio).all()


@router.get("/eventos/{evento_id}", response_model=EventoRespuesta)
def obtener_evento(evento_id: str, db: Session = Depends(get_db)):
    evento = db.get(Evento, evento_id)
    if evento is None:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    return evento


@router.post(
    "/eventos",
    response_model=EventoRespuesta,
    status_code=status.HTTP_201_CREATED,
)
def crear_evento(datos: EventoCrear, db: Session = Depends(get_db)):
    valores = datos.model_dump()
    calendario_id = valores["calendario_id"]
    if calendario_id:
        if db.get(Calendario, calendario_id) is None:
            raise HTTPException(status_code=404, detail="Calendario no encontrado")
    else:
        calendario_id = _calendario_predeterminado(db).id

    ahora = datetime.now(timezone.utc).replace(tzinfo=None)
    evento = Evento(
        id=str(uuid4()),
        **{
            **valores,
            "inicio": _sin_zona(valores["inicio"]),
            "fin": _sin_zona(valores["fin"]),
            "calendario_id": calendario_id,
            "ultima_modificacion": ahora,
            "version": 1,
        },
    )
    evento.crdt_data = doc_a_dict(crear_evento_crdt(evento.to_dict()))
    db.add(evento)
    db.commit()
    db.refresh(evento)
    return evento


@router.put("/eventos/{evento_id}", response_model=EventoRespuesta)
def actualizar_evento(
    evento_id: str, cambios: EventoActualizar, db: Session = Depends(get_db)
):
    evento = db.get(Evento, evento_id)
    if evento is None:
        raise HTTPException(status_code=404, detail="Evento no encontrado")

    valores = cambios.model_dump(exclude_unset=True)
    if any(valor is None for valor in valores.values()):
        raise HTTPException(status_code=422, detail="Los campos enviados no pueden ser nulos")
    if "calendario_id" in valores and db.get(Calendario, valores["calendario_id"]) is None:
        raise HTTPException(status_code=404, detail="Calendario no encontrado")
    if "inicio" in valores:
        valores["inicio"] = _sin_zona(valores["inicio"])
    if "fin" in valores:
        valores["fin"] = _sin_zona(valores["fin"])
    inicio_final = valores.get("inicio", evento.inicio)
    fin_final = valores.get("fin", evento.fin)
    if fin_final <= inicio_final:
        raise HTTPException(status_code=422, detail="fin debe ser posterior a inicio")

    ahora = datetime.now(timezone.utc).replace(tzinfo=None)
    valores["version"] = evento.version + 1
    valores["ultima_modificacion"] = ahora
    doc = _crear_doc_evento(evento)
    actualizar_evento_crdt(doc, valores, ahora.replace(tzinfo=timezone.utc).isoformat())
    _aplicar_campos(evento, doc_a_dict(doc))
    evento.crdt_data = doc_a_dict(doc)
    db.commit()
    db.refresh(evento)
    return evento


@router.delete("/eventos/{evento_id}")
def eliminar_evento(
    evento_id: str,
    eliminado_por: str = Query(default="local", min_length=1),
    db: Session = Depends(get_db),
):
    """Registra un tombstone y marca el evento cancelado sin borrarlo físicamente."""
    evento = db.get(Evento, evento_id)
    if evento is None:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    ahora = datetime.now(timezone.utc).replace(tzinfo=None)
    evento.estado = "cancelado"
    evento.version += 1
    evento.ultima_modificacion = ahora
    doc = _crear_doc_evento(evento)
    actualizar_evento_crdt(
        doc,
        {"estado": evento.estado, "version": evento.version, "ultima_modificacion": ahora},
        ahora.replace(tzinfo=timezone.utc).isoformat(),
    )
    evento.crdt_data = doc_a_dict(doc)
    tombstone = EventoTombstone(
        evento_id=evento.id, eliminado_por=eliminado_por, timestamp=ahora
    )
    db.add(tombstone)
    db.commit()
    return {"status": "ok", "evento_id": evento.id, "tombstone": tombstone.to_dict()}


@router.get("/calendarios", response_model=list[CalendarioRespuesta])
def listar_calendarios(db: Session = Depends(get_db)):
    return db.query(Calendario).order_by(Calendario.nombre).all()


@router.post(
    "/calendarios",
    response_model=CalendarioRespuesta,
    status_code=status.HTTP_201_CREATED,
)
def crear_calendario(datos: CalendarioCrear, db: Session = Depends(get_db)):
    calendario = Calendario(**datos.model_dump())
    db.add(calendario)
    db.commit()
    db.refresh(calendario)
    return calendario


@router.get("/disponibilidad")
def consultar_disponibilidad(
    inicio: datetime,
    fin: datetime,
    usuarios: str = "",
    db: Session = Depends(get_db),
):
    """Devuelve intervalos ocupados y huecos libres dentro del rango solicitado."""
    inicio, fin = _sin_zona(inicio), _sin_zona(fin)
    if fin <= inicio:
        raise HTTPException(status_code=422, detail="fin debe ser posterior a inicio")
    solicitados = {usuario.strip() for usuario in usuarios.split(",") if usuario.strip()}
    eventos = (
        db.query(Evento)
        .filter(
            Evento.estado != "cancelado",
            Evento.inicio < fin,
            Evento.fin > inicio,
        )
        .order_by(Evento.inicio)
        .all()
    )
    if not solicitados:
        solicitados = {
            usuario
            for evento in eventos
            for usuario in [evento.creador, *(evento.participantes or [])]
            if usuario
        }

    resultado = {}
    for usuario in sorted(solicitados):
        ocupados = []
        for evento in eventos:
            asistentes = {evento.creador, *(evento.participantes or [])}
            if usuario in asistentes:
                desde = max(inicio, evento.inicio)
                hasta = min(fin, evento.fin)
                ocupados.append(
                    {"inicio": desde, "fin": hasta, "evento_id": evento.id}
                )
        ocupados.sort(key=lambda intervalo: intervalo["inicio"])
        fusionados = []
        for intervalo in ocupados:
            if fusionados and intervalo["inicio"] <= fusionados[-1]["fin"]:
                fusionados[-1]["fin"] = max(fusionados[-1]["fin"], intervalo["fin"])
            else:
                fusionados.append(dict(intervalo))
        libres = []
        cursor = inicio
        for intervalo in fusionados:
            if cursor < intervalo["inicio"]:
                libres.append({"inicio": cursor, "fin": intervalo["inicio"]})
            cursor = max(cursor, intervalo["fin"])
        if cursor < fin:
            libres.append({"inicio": cursor, "fin": fin})
        resultado[usuario] = {"ocupado": fusionados, "disponible": libres}
    return {"inicio": inicio, "fin": fin, "usuarios": resultado}


@router.post("/sync/enviar")
def sincronizar(datos: EnviarSync, response: Response):
    """Envía un lote delta; cada lote contiene eventos y tombstones."""
    try:
        resultado = sync.enviar_cambios(
            datos.destino, datos.cambios, timeout_ms=datos.timeout_ms
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    if resultado.get("status") == "error":
        response.status_code = status.HTTP_504_GATEWAY_TIMEOUT
    return resultado


@router.get("/sync/delta")
def obtener_delta_sync(
    desde: datetime | None = None,
    db: Session = Depends(get_db),
):
    """Prepara el delta desde el checkpoint temporal indicado por el nodo."""
    checkpoint = datetime.now(timezone.utc).replace(tzinfo=None)
    consulta_eventos = db.query(Evento)
    consulta_tombstones = db.query(EventoTombstone)
    if desde is not None:
        marca = _sin_zona(desde)
        consulta_eventos = consulta_eventos.filter(Evento.ultima_modificacion > marca)
        consulta_tombstones = consulta_tombstones.filter(
            EventoTombstone.timestamp > marca
        )
    eventos = []
    for evento in consulta_eventos.order_by(Evento.ultima_modificacion).all():
        datos = evento.to_dict()
        datos["crdt_data"] = evento.crdt_data
        eventos.append(datos)
    tombstones = [
        tombstone.to_dict()
        for tombstone in consulta_tombstones.order_by(EventoTombstone.timestamp).all()
    ]
    return {
        "eventos": eventos,
        "tombstones": tombstones,
        "checkpoint": checkpoint.replace(tzinfo=timezone.utc).isoformat(),
    }


def aplicar_delta_sync(delta: dict) -> dict:
    """Fusiona el delta entrante en la base local y confirma los cambios."""
    db = SessionLocal()
    procesados = 0
    try:
        for remoto in delta["eventos"]:
            datos = dict(remoto)
            evento_id = str(datos.pop("id"))
            registros = datos.pop("crdt_data", None)
            local = db.get(Evento, evento_id)
            if local is None:
                campos = {
                    campo: datos[campo]
                    for campo in (
                        "titulo",
                        "descripcion",
                        "inicio",
                        "fin",
                        "todo_el_dia",
                        "creador",
                        "participantes",
                        "estado",
                        "version",
                        "ultima_modificacion",
                        "calendario_id",
                    )
                    if campo in datos
                }
                if "inicio" not in campos or "fin" not in campos or "titulo" not in campos:
                    raise ValueError(f"El evento sincronizado {evento_id} carece de campos requeridos")
                if campos.get("calendario_id") and db.get(
                    Calendario, campos["calendario_id"]
                ) is None:
                    campos["calendario_id"] = None
                local = Evento(id=evento_id)
                doc = crear_evento_crdt(campos)
                if registros:
                    from pycrdt import Doc, Map

                    doc = Doc()
                    doc.get("evento", type=Map).update(registros)
                _aplicar_campos(local, doc_a_dict(doc))
                local.crdt_data = doc_a_dict(doc)
                db.add(local)
            else:
                doc_local = _crear_doc_evento(local)
                if registros:
                    from pycrdt import Doc, Map

                    doc_remoto = Doc()
                    doc_remoto.get("evento", type=Map).update(registros)
                else:
                    doc_remoto = crear_evento_crdt(datos)
                fusionar_eventos(doc_local, doc_remoto)
                valores = doc_a_dict(doc_local)
                _aplicar_campos(local, valores)
                local.crdt_data = valores
            procesados += 1

        for remoto in delta["tombstones"]:
            evento_id = str(remoto["evento_id"])
            tombstone_id = str(remoto.get("id") or uuid4())
            tombstone = db.get(EventoTombstone, tombstone_id)
            if tombstone is None:
                fecha = remoto.get("timestamp") or datetime.now(timezone.utc).isoformat()
                db.add(
                    EventoTombstone(
                        id=tombstone_id,
                        evento_id=evento_id,
                        eliminado_por=remoto.get("eliminado_por", "remoto"),
                        timestamp=_sin_zona(_parsear_fecha(fecha)),
                    )
                )
            evento = db.get(Evento, evento_id)
            if evento is not None:
                evento.estado = "cancelado"
                evento.version += 1
                evento.ultima_modificacion = datetime.now(timezone.utc).replace(tzinfo=None)
            procesados += 1
        db.commit()
        return {"recibidos": procesados}
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
