from sqlalchemy import select
from sqlalchemy.orm import Session
from models import Disponibilidade
from repositories.base import BaseRepository

class DisponibilidadeRepository(BaseRepository[Disponibilidade]):
    def __init__(self, db: Session):
        super().__init__(db, Disponibilidade)

    def listar_ordenado(self, dia_semana: int | None = None) -> list[Disponibilidade]:
        stmt = select(Disponibilidade).order_by(
            Disponibilidade.dia_semana, Disponibilidade.hora_inicio
        )
        if dia_semana is not None:
            stmt = stmt.where(Disponibilidade.dia_semana == dia_semana)
        return list(self.db.scalars(stmt).all())