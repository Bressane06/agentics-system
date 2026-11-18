from dataclasses import replace
from datetime import date
from typing import Sequence

import config
from services import observability
from services.domain import TarefaInfo, ItemPriorizado
from services.llm import LLMClient, LLMError
from services.tools import priority
from services.tools.priority import Pesos

class PriorizadorDeterministico:
    """Prioriza só com a fórmula. Também serve de fallback quando o LLM falha."""

    def __init__(self, pesos: Pesos | None = None):
        self.pesos = pesos or Pesos()

    def priorizar(self, tarefas: Sequence[TarefaInfo],
                  hoje: date | None = None) -> list[ItemPriorizado]:
        return priority.priorizar(tarefas, hoje, self.pesos)

class PriorizadorLLM:
    """Agente priorizador: parte do ranking da fórmula e o LLM pode ajustar a ordem
    com base em fatores contextuais (ex.: carga de trabalho, dependências entre tarefas).

    O que é delegado ao LLM: apenas a *ordem final*. O que é protegido por guardrails:
      - a resposta deve ser uma permutação exata dos ids recebidos;
      - nenhuma tarefa pode se mover mais que MAX_DESLOCAMENTO_LLM posições;
      - títulos e textos livres do usuário NUNCA entram no prompt (anti prompt-injection);
      - qualquer erro ou violação cai no ranking determinístico (fallback).
    """

    def __init__(self, llm: LLMClient, base: PriorizadorDeterministico | None = None,
                 max_deslocamento: int = config.MAX_DESLOCAMENTO_LLM):
        self.llm = llm
        self.base = base or PriorizadorDeterministico()
        self.max_deslocamento = max_deslocamento

    def priorizar(self, tarefas: Sequence[TarefaInfo],
                  hoje: date | None = None) -> list[ItemPriorizado]:
        hoje = hoje or date.today()
        ranking = self.base.priorizar(tarefas, hoje)
        if len(ranking) < 2:
            return ranking

        try:
            resposta = self.llm.gerar_json(self._prompt(ranking, hoje))
            nova_ordem = self._validar(resposta, ranking)
        except (LLMError, ValueError) as exc:
            observability.emitir("priorizador", "fallback", motivo=str(exc))
            return ranking

        justificativa = str(resposta.get("justificativa", "")).strip()[:200]
        por_id = {i.tarefa.id: i for i in ranking}
        resultado = []
        for posicao, tid in enumerate(nova_ordem, start=1):
            item = por_id[tid]
            if posicao != item.posicao:
                nota = f" Ajuste do LLM: {justificativa}" if justificativa else " Ajuste do LLM."
                item = replace(item, justificativa=item.justificativa + nota)
            resultado.append(replace(item, posicao=posicao))
        observability.emitir("priorizador", "ajuste_llm",
                             ordem_formula=[i.tarefa.id for i in ranking],
                             ordem_final=nova_ordem, justificativa=justificativa)
        return resultado

    def _prompt(self, ranking: list[ItemPriorizado], hoje: date) -> str:
        linhas = [
            {"id": i.tarefa.id, "posicao": i.posicao, "pontuacao": round(i.pontuacao, 3),
             "dias_ate_prazo": (i.tarefa.prazo - hoje).days, "dificuldade": i.tarefa.dificuldade,
             "importancia": i.tarefa.importancia,
             "horas_restantes": round(max(i.tarefa.horas_estimadas - i.tarefa.horas_concluidas, 0), 2)}
            for i in ranking
        ]
        return (
            "Você ajusta a ordem de estudo de tarefas acadêmicas. A ordem abaixo já foi calculada "
            "por uma fórmula (urgência, importância, dificuldade, trabalho restante). "
            "Só altere se houver motivo claro (ex.: várias tarefas difíceis seguidas, ou muito "
            "trabalho restante com prazo curto). Responda SOMENTE JSON no formato "
            '{"ordem": [ids...], "justificativa": "uma frase"}. '
            f"A lista deve conter exatamente os mesmos ids, sem repetir. Tarefas: {linhas}"
        )

    def _validar(self, resposta: dict, ranking: list[ItemPriorizado]) -> list[int]:
        ordem = resposta.get("ordem")
        ids = [i.tarefa.id for i in ranking]
        if not isinstance(ordem, list) or any(isinstance(x, bool) or not isinstance(x, int) for x in ordem):
            raise ValueError("'ordem' ausente ou inválida")
        if sorted(ordem) != sorted(ids):
            raise ValueError("'ordem' não é uma permutação dos ids recebidos")
        original = {tid: n for n, tid in enumerate(ids)}
        for n, tid in enumerate(ordem):
            if abs(n - original[tid]) > self.max_deslocamento:
                raise ValueError(
                    f"tarefa {tid} movida mais de {self.max_deslocamento} posições")
        return ordem
