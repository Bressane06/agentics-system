"""Orquestrador: controla o loop Priorizador -> Planejador -> Verificador -> Avaliador.

É ele (código, não o LLM) quem decide quando o loop termina: plano sem problemas corrigíveis,
Avaliador aceitou, ajustes esgotados ou MAX_REVISOES atingido. Guarda o melhor plano visto,
então uma revisão que piora o resultado nunca substitui uma versão melhor.
"""
from dataclasses import replace
from datetime import date, timedelta
from typing import Sequence

import config
from services import observability
from services.agents.base import Avaliador, Planejador, Priorizador
from services.agents.evaluator import ACAO_ACEITAR, ACAO_AMPLIAR_BLOCO, ACAO_USAR_PRAZO
from services.domain import (Bloco, Parametros, ResultadoPlanejamento, Revisao, TarefaInfo)
from services.tools import scheduling, validation

TETO_BLOCO_MIN = 240

def aplicar_acao(params: Parametros, acao: str) -> Parametros:
    if acao == ACAO_USAR_PRAZO:
        return replace(params, estrategia="prazo")
    if acao == ACAO_AMPLIAR_BLOCO:
        return replace(params, max_bloco_min=min(params.max_bloco_min + 60, TETO_BLOCO_MIN))
    raise ValueError(f"Ação desconhecida: {acao}")

class Orquestrador:
    def __init__(self, priorizador: Priorizador, planejador: Planejador, avaliador: Avaliador,
                 max_revisoes: int = config.MAX_REVISOES):
        self.priorizador = priorizador
        self.planejador = planejador
        self.avaliador = avaliador
        self.max_revisoes = max_revisoes

    def executar(self, tarefas: Sequence[TarefaInfo], blocos: Sequence[Bloco],
                 hoje: date, agora_min: int | None = None) -> ResultadoPlanejamento:
        params = Parametros(max_bloco_min=config.SESSAO_MAX_BLOCO_MIN)
        if not tarefas:
            return ResultadoPlanejamento([], [], [], [], [], params, True, "sem_tarefas")

        with observability.etapa("priorizador", "priorizar", tarefas=len(tarefas)) as saida:
            ranking = self.priorizador.priorizar(tarefas, hoje)
            saida["ordem"] = [i.tarefa.id for i in ranking]
        ordem = [i.tarefa for i in ranking]

        limite = min(max(t.prazo for t in tarefas), hoje + timedelta(days=config.HORIZONTE_MAX_DIAS))
        slots = scheduling.expandir_slots(blocos, hoje, limite, agora_min)

        melhor = None
        revisoes: list[Revisao] = []
        tentadas: set[str] = set()
        motivo = "limite_de_revisoes"

        for n in range(self.max_revisoes + 1):
            sessoes = self.planejador.planejar(ordem, slots, params)
            with observability.etapa("verificador", "validar", tentativa=n) as saida:
                problemas = validation.validar(sessoes, ordem, slots, hoje)
                saida["problemas"] = [f"{p.tipo}:{p.tarefa_id}" for p in problemas]
            nao_alocado = validation.minutos_nao_alocados(sessoes, ordem)
            nota = (len(problemas), nao_alocado)
            if melhor is None or nota < melhor[0]:
                melhor = (nota, sessoes, problemas, params)

            if n == self.max_revisoes:
                break
            decisao = self.avaliador.decidir(problemas, params, frozenset(tentadas))
            observability.emitir("avaliador", "decisao", acao=decisao.acao,
                                 origem=decisao.origem, justificativa=decisao.justificativa)
            revisoes.append(Revisao(n + 1, decisao.acao, decisao.justificativa,
                                    decisao.origem, len(problemas)))
            if decisao.acao == ACAO_ACEITAR:
                motivo = "aceito_pelo_avaliador"
                break
            tentadas.add(decisao.acao)
            params = aplicar_acao(params, decisao.acao)

        _, sessoes, problemas, params_final = melhor
        convergiu = not any(p.corrigivel for p in problemas)
        resultado = ResultadoPlanejamento(
            ordem=ranking, sessoes=sessoes, problemas=problemas,
            inviaveis=sorted({p.tarefa_id for p in problemas if p.tipo == validation.INVIAVEL}),
            revisoes=revisoes, parametros=params_final, convergiu=convergiu,
            motivo_parada=motivo,
        )
        observability.emitir("orquestrador", "fim", convergiu=convergiu, motivo=motivo,
                             revisoes=len(revisoes), problemas=len(problemas),
                             sessoes=len(sessoes))
        return resultado
