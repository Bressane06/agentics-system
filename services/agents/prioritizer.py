from datetime import date
from typing import Sequence
from services.domain import TarefaInfo, ItemPriorizado
from services.tools import priority
from services.tools.priority import Pesos

class PriorizadorDeterministico:
    """Prioriza só com a fórmula. Também serve de fallback quando o LLM falha."""

    def __init__(self, pesos: Pesos | None = None):
        self.pesos = pesos or Pesos()

    def priorizar(self, tarefas: Sequence[TarefaInfo],
                  hoje: date | None = None) -> list[ItemPriorizado]:
        return priority.priorizar(tarefas, hoje, self.pesos)