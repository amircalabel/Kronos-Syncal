from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database import Base


class Calendario(Base):
    __tablename__ = "calendarios"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    nombre = Column(String, nullable=False)
    propietario = Column(String, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nombre": self.nombre,
            "propietario": self.propietario,
        }


class Evento(Base):
    __tablename__ = "eventos"
    __table_args__ = (
        CheckConstraint(
            "estado IN ('propuesta', 'confirmado', 'cancelado')",
            name="ck_eventos_estado",
        ),
        CheckConstraint("fin > inicio", name="ck_eventos_intervalo"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()), index=True)
    titulo = Column(String, nullable=False)
    descripcion = Column(Text, nullable=False, default="")
    inicio = Column(DateTime, nullable=False)
    fin = Column(DateTime, nullable=False)
    todo_el_dia = Column(Boolean, nullable=False, default=False)
    creador = Column(String, nullable=False, default="anon")
    participantes = Column(JSON, nullable=False, default=list)
    estado = Column(String, nullable=False, default="propuesta")
    version = Column(Integer, nullable=False, default=1)
    ultima_modificacion = Column(DateTime, nullable=False, default=datetime.utcnow)
    calendario_id = Column(
        String(36), ForeignKey("calendarios.id", ondelete="SET NULL"), nullable=True
    )
    crdt_data = Column(JSON, nullable=False, default=dict)
    invitaciones = relationship(
        "Invitacion",
        back_populates="evento",
        cascade="all, delete-orphan",
        order_by="Invitacion.usuario",
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "titulo": self.titulo,
            "descripcion": self.descripcion,
            "inicio": self.inicio,
            "fin": self.fin,
            "todo_el_dia": self.todo_el_dia,
            "creador": self.creador,
            "participantes": self.participantes or [],
            "estado": self.estado,
            "version": self.version,
            "ultima_modificacion": self.ultima_modificacion,
            "calendario_id": self.calendario_id,
        }


class Invitacion(Base):
    __tablename__ = "invitaciones"
    __table_args__ = (
        UniqueConstraint("evento_id", "usuario", name="uq_invitaciones_evento_usuario"),
        CheckConstraint(
            "respuesta IN ('pendiente', 'aceptado', 'rechazado')",
            name="ck_invitaciones_respuesta",
        ),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    evento_id = Column(
        String(36), ForeignKey("eventos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    usuario = Column(String, nullable=False)
    respuesta = Column(String, nullable=False, default="pendiente")
    respondido_en = Column(DateTime, nullable=True)
    evento = relationship("Evento", back_populates="invitaciones")


class EventoTombstone(Base):
    __tablename__ = "eventos_tombstones"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    evento_id = Column(String(36), nullable=False, index=True)
    eliminado_por = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "evento_id": self.evento_id,
            "eliminado_por": self.eliminado_por,
            "timestamp": self.timestamp,
        }
