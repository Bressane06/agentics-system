from datetime import date, time
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.database import Base

class Sessao(Base):
    __tablename__ = "sessoes"

    id: Mapped[int] = mapped_column(primary_key=True)
    tarefa_id: Mapped[int] = mapped_column(ForeignKey("tarefas.id"))
    data: Mapped[date]
    hora_inicio: Mapped[time]
    hora_fim: Mapped[time]
    versao: Mapped[int] = mapped_column(ForeignKey("planos.id"))   # id do Plano
    status: Mapped[str] = mapped_column(String(20), default="proposta")

    tarefa = relationship("Tarefa", back_populates="sessoes")
    plano = relationship("Plano", back_populates="sessoes")
