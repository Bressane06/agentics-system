from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.database import Base

class Disciplina(Base):
    __tablename__ = "disciplinas"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(100), unique=True)
    dificuldade: Mapped[int] = mapped_column(default=3)  # 1 a 5

    tarefas = relationship("Tarefa", back_populates="disciplina", cascade="all, delete-orphan")