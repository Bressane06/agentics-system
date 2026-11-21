from typing import Sequence

from services import observability
from services.domain import Decisao, Parametros, Problema
from services.llm import LLMClient, LLMError

ACAO_ACEITAR = "aceitar"
ACAO_USAR_PRAZO = "usar_prazo"        # troca a estratégia de alocação para "prazo mais próximo primeiro"
ACAO_AMPLIAR_BLOCO = "ampliar_bloco"  # permite sessões diárias mais longas por tarefa
ACOES_DE_AJUSTE = (ACAO_USAR_PRAZO, ACAO_AMPLIAR_BLOCO)   # ordem de preferência das regras

class AvaliadorDeterministico:
    """Decide o próximo passo do loop de revisão por regras simples."""

    def decidir(self, problemas: Sequence[Problema], params: Parametros,
                tentadas: frozenset[str]) -> Decisao:
        if not any(p.corrigivel for p in problemas):
            return Decisao(ACAO_ACEITAR, "Nenhum problema corrigível restante.", "regra")
        for acao in ACOES_DE_AJUSTE:
            if acao not in tentadas:
                return Decisao(acao, "Há problemas corrigíveis; tentando o próximo ajuste.", "regra")
        return Decisao(ACAO_ACEITAR, "Todos os ajustes disponíveis já foram tentados.", "regra")

class AvaliadorLLM:
    """Agente avaliador: dado o diagnóstico (calculado por ferramenta determinística),
    o LLM escolhe qual ajuste tentar a seguir.

    Delegado ao LLM: a *escolha* entre ações de um conjunto fechado, com justificativa.
    Guardrails: a ação deve estar entre as ainda não tentadas (ou "aceitar"); o prompt só leva
    texto gerado pelo sistema; erro ou ação inválida cai nas regras (fallback).
    Ele nunca edita tarefas, disponibilidade ou sessões — só devolve uma Decisao.
    """

    def __init__(self, llm: LLMClient, base: AvaliadorDeterministico | None = None):
        self.llm = llm
        self.base = base or AvaliadorDeterministico()

    def decidir(self, problemas: Sequence[Problema], params: Parametros,
                tentadas: frozenset[str]) -> Decisao:
        regra = self.base.decidir(problemas, params, tentadas)
        if regra.acao == ACAO_ACEITAR and not any(p.corrigivel for p in problemas):
            return regra  # nada a decidir: não gasta chamada de LLM
        opcoes = [a for a in ACOES_DE_AJUSTE if a not in tentadas] + [ACAO_ACEITAR]
        try:
            resposta = self.llm.gerar_json(self._prompt(problemas, params, opcoes))
            acao = resposta.get("acao")
            if acao not in opcoes:
                raise ValueError(f"ação inválida: {acao!r}")
        except (LLMError, ValueError) as exc:
            observability.emitir("avaliador", "fallback", motivo=str(exc))
            return Decisao(regra.acao, regra.justificativa, "fallback")
        return Decisao(acao, str(resposta.get("justificativa", "")).strip()[:200], "llm")

    def _prompt(self, problemas: Sequence[Problema], params: Parametros, opcoes: list[str]) -> str:
        lista = [{"tipo": p.tipo, "tarefa_id": p.tarefa_id, "detalhe": p.detalhe,
                  "corrigivel": p.corrigivel} for p in problemas]
        return (
            "Você revisa um plano de estudos. Problemas encontrados pelo verificador: "
            f"{lista}. Parâmetros atuais: estrategia={params.estrategia}, "
            f"max_bloco_min={params.max_bloco_min}. Ações possíveis: "
            "usar_prazo (aloca primeiro as tarefas com prazo mais próximo), "
            "ampliar_bloco (permite sessões diárias maiores por tarefa), "
            "aceitar (encerra a revisão). "
            f"Escolha UMA entre {opcoes}. Responda SOMENTE JSON: "
            '{"acao": "...", "justificativa": "uma frase"}.'
        )
