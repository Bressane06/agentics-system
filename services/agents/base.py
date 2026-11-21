from datetime import date
from typing import Protocol, Sequence
from services.domain import (TarefaInfo, ItemPriorizado, Slot, SessaoPlanejada,
                             Parametros, Problema, Decisao)

class Priorizador(Protocol):
    def priorizar(self, tarefas: Sequence[TarefaInfo],
                  hoje: date | None = None) -> list[ItemPriorizado]: ...

class Planejador(Protocol):
    def planejar(self, ordem: Sequence[TarefaInfo], slots: Sequence[Slot],
                 params: Parametros) -> list[SessaoPlanejada]: ...

class Avaliador(Protocol):
    def decidir(self, problemas: Sequence[Problema], params: Parametros,
                tentadas: frozenset[str]) -> Decisao: ...
