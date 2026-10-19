from sqlalchemy import select
from sqlalchemy.orm import Session
from models import Tarefa
from repositories.base import BaseRepository

class TarefaRepository(BaseRepository[Tarefa]):
    def __init__(self, db: Session):
        super().__init__(db, Tarefa)

    def listar_filtrado(self, status: str | None = None,
                        disciplina_id: int | None = None) -> list[Tarefa]:
        stmt = select(Tarefa).order_by(Tarefa.prazo)
        if status:
            stmt = stmt.where(Tarefa.status == status)
        if disciplina_id:
            stmt = stmt.where(Tarefa.disciplina_id == disciplina_id)
        return list(self.db.scalars(stmt).all())