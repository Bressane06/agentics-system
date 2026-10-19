from datetime import date
from typing import Protocol, Sequence
from services.domain import TarefaInfo, ItemPriorizado

class Priorizador(Protocol):
    def priorizar(self, tarefas: Sequence[TarefaInfo],
                  hoje: date | None = None) -> list[ItemPriorizado]: ...