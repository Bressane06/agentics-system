from sqlalchemy import select
from sqlalchemy.orm import Session
from models import Plano, Sessao, Traco
from repositories.base import BaseRepository

class PlanoRepository(BaseRepository[Plano]):
    def __init__(self, db: Session):
        super().__init__(db, Plano)

    def listar_recentes(self, limite: int = 20) -> list[Plano]:
        stmt = select(Plano).order_by(Plano.id.desc()).limit(limite)
        return list(self.db.scalars(stmt).all())

    def aprovado_atual(self) -> Plano | None:
        return self.db.scalar(select(Plano).where(Plano.status == "aprovada"))

    def salvar_completo(self, plano: Plano, sessoes: list[Sessao],
                        tracos: list[Traco]) -> Plano:
        """Persiste plano, sessões e traços numa única transação."""
        plano.sessoes = sessoes
        plano.tracos = tracos
        return self.add(plano)

    def definir_status(self, plano: Plano, status: str, motivo: str = "") -> Plano:
        for sessao in plano.sessoes:
            sessao.status = status
        plano.status = status
        if motivo:
            plano.motivo_rejeicao = motivo
        self.db.commit()
        self.db.refresh(plano)
        return plano
