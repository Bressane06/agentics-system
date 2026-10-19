from datetime import date
from repositories.tarefa_repository import TarefaRepository
from services.agents.base import Priorizador
from services.domain import TarefaInfo, ItemPriorizado

class PrioridadeService:
    def __init__(self, tarefas: TarefaRepository, priorizador: Priorizador):
        self.tarefas = tarefas
        self.priorizador = priorizador

    def ranking(self, hoje: date | None = None) -> list[ItemPriorizado]:
        pendentes = self.tarefas.listar_filtrado(status="pendente")
        infos = [TarefaInfo.from_model(t) for t in pendentes]
        return self.priorizador.priorizar(infos, hoje)