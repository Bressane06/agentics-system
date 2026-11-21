from datetime import date

import pytest

from evals.fakes import LLMIndisponivel, LLMRoteirizado
from services import observability
from services.agents.evaluator import AvaliadorDeterministico, AvaliadorLLM
from services.agents.prioritizer import PriorizadorDeterministico, PriorizadorLLM
from services.domain import Parametros, Problema, TarefaInfo
from services.llm import LLMError, OllamaClient

HOJE = date(2026, 11, 16)

def tarefas(n=4):
    return [TarefaInfo(i, f"T{i}", date.fromordinal(HOJE.toordinal() + 3 + i), 3, 3, 2.0)
            for i in range(1, n + 1)]

def ids(ranking):
    return [i.tarefa.id for i in ranking]

# ---------------- Priorizador LLM ----------------

def test_priorizador_aceita_permutacao_valida_e_renumera_posicoes():
    base = ids(PriorizadorDeterministico().priorizar(tarefas(), HOJE))
    nova = [base[1], base[0], base[2], base[3]]
    ranking = PriorizadorLLM(LLMRoteirizado({"ordem": nova, "justificativa": "teste"})).priorizar(tarefas(), HOJE)
    assert ids(ranking) == nova
    assert [i.posicao for i in ranking] == [1, 2, 3, 4]

def test_priorizador_registra_quando_llm_apenas_confirma_a_ordem():
    base = ids(PriorizadorDeterministico().priorizar(tarefas(), HOJE))
    llm = LLMRoteirizado({"ordem": base, "justificativa": "Mudança para evitar tarefas difíceis"})
    tracer = observability.Tracer()
    with observability.ativar(tracer):
        ranking = PriorizadorLLM(llm).priorizar(tarefas(), HOJE)
    assert ids(ranking) == base
    assert not any("Ajuste do LLM" in i.justificativa for i in ranking)
    assert [e["etapa"] for e in tracer.eventos] == ["llm_confirmou_ordem"]

@pytest.mark.parametrize("resposta", [
    {"ordem": [1, 2, 3]},                     # faltam ids
    {"ordem": [1, 2, 3, 4, 4]},               # repetido
    {"ordem": [1, 2, 3, 99]},                 # id desconhecido
    {"ordem": "1,2,3,4"},                     # tipo errado
    {"ordem": [True, 2, 3, 4]},               # bool não é id
    {"justificativa": "sem ordem"},           # campo ausente
])
def test_priorizador_rejeita_respostas_invalidas(resposta):
    base = ids(PriorizadorDeterministico().priorizar(tarefas(), HOJE))
    assert ids(PriorizadorLLM(LLMRoteirizado(resposta)).priorizar(tarefas(), HOJE)) == base

def test_priorizador_cai_no_fallback_quando_llm_falha():
    base = ids(PriorizadorDeterministico().priorizar(tarefas(), HOJE))
    assert ids(PriorizadorLLM(LLMIndisponivel()).priorizar(tarefas(), HOJE)) == base

def test_priorizador_respeita_deslocamento_maximo():
    base = ids(PriorizadorDeterministico().priorizar(tarefas(6), HOJE))
    invertida = list(reversed(base))
    assert ids(PriorizadorLLM(LLMRoteirizado({"ordem": invertida}), max_deslocamento=2)
               .priorizar(tarefas(6), HOJE)) == base
    assert ids(PriorizadorLLM(LLMRoteirizado({"ordem": invertida}), max_deslocamento=5)
               .priorizar(tarefas(6), HOJE)) == invertida

def test_priorizador_nao_chama_llm_com_menos_de_duas_tarefas():
    llm = LLMRoteirizado({"ordem": [1]})
    PriorizadorLLM(llm).priorizar(tarefas(1), HOJE)
    assert llm.prompts == []

def test_priorizador_emite_evento_de_fallback_no_trace():
    tracer = observability.Tracer()
    with observability.ativar(tracer):
        PriorizadorLLM(LLMIndisponivel()).priorizar(tarefas(), HOJE)
    assert [e["etapa"] for e in tracer.eventos] == ["fallback"]
    assert "Ollama fora do ar" in tracer.eventos[0]["dados"]["motivo"]

# ---------------- Avaliador ----------------

CORRIGIVEL = [Problema("cobertura_incompleta", 1, "faltam 60 min", True)]
INVIAVEL = [Problema("inviavel", 1, "não cabe", False)]

def test_avaliador_deterministico_percorre_ajustes_e_depois_aceita():
    av, p = AvaliadorDeterministico(), Parametros()
    assert av.decidir(CORRIGIVEL, p, frozenset()).acao == "usar_prazo"
    assert av.decidir(CORRIGIVEL, p, frozenset({"usar_prazo"})).acao == "ampliar_bloco"
    assert av.decidir(CORRIGIVEL, p, frozenset({"usar_prazo", "ampliar_bloco"})).acao == "aceitar"

def test_avaliador_aceita_quando_so_ha_problemas_nao_corrigiveis():
    assert AvaliadorDeterministico().decidir(INVIAVEL, Parametros(), frozenset()).acao == "aceitar"

def test_avaliador_llm_nao_gasta_chamada_sem_problema_corrigivel():
    llm = LLMRoteirizado({"acao": "usar_prazo"})
    decisao = AvaliadorLLM(llm).decidir(INVIAVEL, Parametros(), frozenset())
    assert decisao.acao == "aceitar" and llm.prompts == []

def test_avaliador_llm_aceita_acao_valida():
    d = AvaliadorLLM(LLMRoteirizado({"acao": "ampliar_bloco", "justificativa": "blocos curtos"})) \
        .decidir(CORRIGIVEL, Parametros(), frozenset())
    assert (d.acao, d.origem) == ("ampliar_bloco", "llm")

@pytest.mark.parametrize("resposta", [
    {"acao": "apagar_tudo"}, {"acao": None}, {}, {"acao": "usar_prazo"},
])
def test_avaliador_llm_rejeita_acao_invalida_ou_ja_tentada(resposta):
    d = AvaliadorLLM(LLMRoteirizado(resposta)).decidir(CORRIGIVEL, Parametros(), frozenset({"usar_prazo"}))
    assert d.origem == "fallback" and d.acao == "ampliar_bloco"

# ---------------- Cliente Ollama ----------------

class _Resp:
    def __init__(self, corpo, status=200):
        self._corpo, self.status_code = corpo, status
    def raise_for_status(self):
        import httpx
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("erro", request=None, response=None)
    def json(self):
        return self._corpo

class _Http:
    def __init__(self, resp):
        self.resp, self.chamadas = resp, []
    def post(self, url, json):
        self.chamadas.append((url, json))
        return self.resp

def test_ollama_client_envia_formato_json_e_parseia_resposta():
    http = _Http(_Resp({"response": '{"acao": "aceitar"}'}))
    assert OllamaClient("http://x:1/", "m", http=http).gerar_json("oi") == {"acao": "aceitar"}
    url, corpo = http.chamadas[0]
    assert url == "http://x:1/api/generate" and corpo["format"] == "json" and corpo["stream"] is False

@pytest.mark.parametrize("resp", [
    _Resp({"response": "isto não é json"}), _Resp({"sem_response": 1}),
    _Resp({"response": "[1, 2]"}), _Resp({}, status=500),
])
def test_ollama_client_converte_falhas_em_llmerror(resp):
    with pytest.raises(LLMError):
        OllamaClient("http://x", "m", http=_Http(resp)).gerar_json("oi")
