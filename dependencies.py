from fastapi import Depends
from sqlalchemy.orm import Session
from models import get_db
from repositories.disciplina_repository import DisciplinaRepository
from repositories.tarefa_repository import TarefaRepository
from repositories.historico_repository import HistoricoRepository
from services.agents.base import Priorizador
from services.agents.prioritizer import PriorizadorDeterministico
from services.disciplina_service import DisciplinaService
from services.prioridade_service import PrioridadeService
from services.tarefa_service import TarefaService

def get_disciplina_service(db: Session = Depends(get_db)) -> DisciplinaService:
    return DisciplinaService(DisciplinaRepository(db), HistoricoRepository(db))

def get_tarefa_service(db: Session = Depends(get_db)) -> TarefaService:
    return TarefaService(TarefaRepository(db), DisciplinaRepository(db), HistoricoRepository(db))

def get_priorizador() -> Priorizador:
    return PriorizadorDeterministico()

def get_prioridade_service(
    db: Session = Depends(get_db),
    priorizador: Priorizador = Depends(get_priorizador),
) -> PrioridadeService:
    return PrioridadeService(TarefaRepository(db), priorizador)