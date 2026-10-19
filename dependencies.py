from fastapi import Depends
from sqlalchemy.orm import Session
from models import get_db
from repositories.disciplina_repository import DisciplinaRepository
from repositories.disponibilidade_repository import DisponibilidadeRepository
from repositories.tarefa_repository import TarefaRepository
from repositories.historico_repository import HistoricoRepository
from services.disciplina_service import DisciplinaService
from services.disponibilidade_service import DisponibilidadeService
from services.tarefa_service import TarefaService

def get_disciplina_service(db: Session = Depends(get_db)) -> DisciplinaService:
    return DisciplinaService(DisciplinaRepository(db), HistoricoRepository(db))

def get_tarefa_service(db: Session = Depends(get_db)) -> TarefaService:
    return TarefaService(TarefaRepository(db), DisciplinaRepository(db), HistoricoRepository(db))

def get_disponibilidade_service(db: Session = Depends(get_db)) -> DisponibilidadeService:
    return DisponibilidadeService(DisponibilidadeRepository(db), HistoricoRepository(db))