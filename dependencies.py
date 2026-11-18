from fastapi import Depends
from sqlalchemy.orm import Session
import config
from models import get_db
from repositories.disciplina_repository import DisciplinaRepository
from repositories.disponibilidade_repository import DisponibilidadeRepository
from repositories.tarefa_repository import TarefaRepository
from repositories.historico_repository import HistoricoRepository
from repositories.plano_repository import PlanoRepository
from services.agents.base import Priorizador
from services.agents.evaluator import AvaliadorDeterministico, AvaliadorLLM
from services.agents.planner import PlanejadorDeterministico
from services.agents.prioritizer import PriorizadorDeterministico, PriorizadorLLM
from services.disciplina_service import DisciplinaService
from services.disponibilidade_service import DisponibilidadeService
from services.llm import LLMClient, OllamaClient
from services.orchestrator import Orquestrador
from services.plano_service import PlanoService
from services.prioridade_service import PrioridadeService
from services.tarefa_service import TarefaService

def get_disciplina_service(db: Session = Depends(get_db)) -> DisciplinaService:
    return DisciplinaService(DisciplinaRepository(db), HistoricoRepository(db))

def get_disponibilidade_service(db: Session = Depends(get_db)) -> DisponibilidadeService:
    return DisponibilidadeService(DisponibilidadeRepository(db), HistoricoRepository(db))

def get_tarefa_service(db: Session = Depends(get_db)) -> TarefaService:
    return TarefaService(TarefaRepository(db), DisciplinaRepository(db), HistoricoRepository(db))

def get_llm() -> LLMClient | None:
    """None => agentes rodam só com regras. Sobrescrito nos testes por um dublê."""
    return OllamaClient() if config.LLM_HABILITADO else None

def get_priorizador() -> Priorizador:
    return PriorizadorDeterministico()

def get_prioridade_service(
    db: Session = Depends(get_db),
    priorizador: Priorizador = Depends(get_priorizador),
) -> PrioridadeService:
    return PrioridadeService(TarefaRepository(db), priorizador)

def get_plano_service(db: Session = Depends(get_db),
                      llm: LLMClient | None = Depends(get_llm)) -> PlanoService:
    if llm is not None:
        priorizador, avaliador = PriorizadorLLM(llm), AvaliadorLLM(llm)
    else:
        priorizador, avaliador = PriorizadorDeterministico(), AvaliadorDeterministico()
    orquestrador = Orquestrador(priorizador, PlanejadorDeterministico(), avaliador)
    return PlanoService(TarefaRepository(db), DisponibilidadeRepository(db),
                        PlanoRepository(db), HistoricoRepository(db),
                        orquestrador, usa_llm=llm is not None)
