from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, Integer, JSON, String, Text

from app.database import Base


class Evento(Base):
    __tablename__ = "eventos"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid4()))
    titulo = Column(String, nullable=False)
    descripcion = Column(Text, nullable=True)
    inicio = Column(DateTime, nullable=False)
    fin = Column(DateTime, nullable=False)
    todo_el_dia = Column(Boolean, default=False)
    creador = Column(String, nullable=False, default="anon")
    participantes = Column(JSON, default=list)
    estado = Column(String, default="propuesta")
    version = Column(Integer, default=1)
    ultima_modificacion = Column(DateTime, default=datetime.utcnow)


class Calendario(Base):
    __tablename__ = "calendarios"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid4()))
    nombre = Column(String, nullable=False)
    propietario = Column(String, nullable=False)
