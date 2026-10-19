from sqlalchemy.orm import Session
from models import Historico
from repositories.base import BaseRepository

class HistoricoRepository(BaseRepository[Historico]):
    def __init__(self, db: Session):
        super().__init__(db, Historico)

    def registrar(self, acao: str, detalhes: str = "") -> Historico:
        return self.add(Historico(acao=acao, detalhes=detalhes))