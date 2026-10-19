from sqlalchemy import select
from sqlalchemy.orm import Session
from models import Disciplina
from repositories.base import BaseRepository

class DisciplinaRepository(BaseRepository[Disciplina]):
    def __init__(self, db: Session):
        super().__init__(db, Disciplina)

    def get_by_nome(self, nome: str) -> Disciplina | None:
        return self.db.scalar(
            select(Disciplina).where(
                Disciplina.nome == nome)
                )