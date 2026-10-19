from datetime import date
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.database import Base

class Tarefa(Base):
    __tablename__ = "tarefas"

    id: Mapped[int] = mapped_column(primary_key=True)
    disciplina_id: Mapped[int] = mapped_column(ForeignKey("disciplinas.id"))
    titulo: Mapped[str] = mapped_column(String(150))
    prazo: Mapped[date]
    dificuldade: Mapped[int] = mapped_column(default=3)   
    importancia: Mapped[int] = mapped_column(default=3)    
    horas_estimadas: Mapped[float]
    horas_concluidas: Mapped[float] = mapped_column(default=0.0)
    status: Mapped[str] = mapped_column(String(20), default="pendente") 

    disciplina = relationship("Disciplina", back_populates="tarefas")
    sessoes = relationship("Sessao", back_populates="tarefa", cascade="all, delete-orphan")