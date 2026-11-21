from typing import Sequence

from services import observability
from services.domain import TarefaInfo, Slot, SessaoPlanejada, Parametros
from services.tools import scheduling

class PlanejadorDeterministico:
    """Transforma uma ordem de tarefas + janelas livres em sessões de estudo.

    Propositalmente sem LLM: alocar horários é um problema com regras exatas (sem sobreposição,
    dentro da disponibilidade, antes do prazo) e um erro aqui produziria um plano inválido.
    O Avaliador controla *como* ele roda (estratégia, tamanho de bloco) via Parametros.
    """

    def planejar(self, ordem: Sequence[TarefaInfo], slots: Sequence[Slot],
                 params: Parametros) -> list[SessaoPlanejada]:
        sessoes = scheduling.alocar(ordem, slots, params)
        observability.emitir("planejador", "plano_gerado", estrategia=params.estrategia,
                             max_bloco_min=params.max_bloco_min, sessoes=len(sessoes),
                             minutos=sum(s.minutos for s in sessoes))
        return sessoes
