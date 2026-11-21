from datetime import date, timedelta

import pytest

from data.seed import popular
from dependencies import get_llm
from evals.fakes import LLMIndisponivel, LLMRoteirizado
from main import app

@pytest.fixture
def cenario_seed(db):
    popular(db)

def _disciplina_e_disponibilidade(client):
    d = client.post("/disciplinas", json={"nome": "Cálculo I", "dificuldade": 4}).json()
    for dia in range(7):
        client.post("/disponibilidade", json={"dia_semana": dia, "hora_inicio": "19:00", "hora_fim": "21:00"})
    return d

def _tarefa(client, disc, titulo, dias, horas, **extra):
    return client.post("/tarefas", json={"disciplina_id": disc["id"], "titulo": titulo,
                                         "prazo": str(date.today() + timedelta(days=dias)),
                                         "horas_estimadas": horas, **extra}).json()

def test_gerar_plano_sem_tarefas_retorna_422(client):
    _disciplina_e_disponibilidade(client)
    assert client.post("/planos").status_code == 422

def test_gerar_plano_sem_disponibilidade_retorna_422(client):
    d = client.post("/disciplinas", json={"nome": "X1", "dificuldade": 3}).json()
    _tarefa(client, d, "Lista", 5, 2)
    assert client.post("/planos").status_code == 422

def test_plano_simples_e_proposta_e_sem_problemas(client):
    d = _disciplina_e_disponibilidade(client)
    _tarefa(client, d, "Lista", 5, 4)
    r = client.post("/planos")
    assert r.status_code == 201
    plano = r.json()
    assert plano["status"] == "proposta" and plano["usou_llm"] is False
    assert plano["resumo"]["problemas"] == [] and plano["resumo"]["convergiu"] is True
    assert all(s["status"] == "proposta" and s["titulo"] == "Lista" for s in plano["sessoes"])
    assert sum(1 for _ in plano["sessoes"]) >= 2

def test_agentes_nao_alteram_tarefas_nem_disponibilidade(client):
    d = _disciplina_e_disponibilidade(client)
    _tarefa(client, d, "Lista", 5, 4)
    antes = (client.get("/tarefas").json(), client.get("/disponibilidade").json())
    client.post("/planos")
    assert (client.get("/tarefas").json(), client.get("/disponibilidade").json()) == antes

def test_plano_com_riscos_exige_confirmacao_explicita(client):
    d = _disciplina_e_disponibilidade(client)
    _tarefa(client, d, "Seminário surpresa", 1, 12, dificuldade=5)
    plano = client.post("/planos").json()
    assert plano["resumo"]["inviaveis"] == [plano["sessoes"][0]["tarefa_id"]]
    negado = client.post(f"/planos/{plano['id']}/aprovar")
    assert negado.status_code == 422 and "confirmar_riscos" in negado.json()["detail"]
    assert client.get(f"/planos/{plano['id']}").json()["status"] == "proposta"
    ok = client.post(f"/planos/{plano['id']}/aprovar", json={"confirmar_riscos": True})
    assert ok.status_code == 200 and ok.json()["status"] == "aprovada"
    assert {s["status"] for s in ok.json()["sessoes"]} == {"aprovada"}

def test_aprovar_novo_plano_substitui_o_anterior(client):
    d = _disciplina_e_disponibilidade(client)
    _tarefa(client, d, "Lista", 5, 4)
    p1 = client.post("/planos").json()
    client.post(f"/planos/{p1['id']}/aprovar")
    p2 = client.post("/planos").json()
    client.post(f"/planos/{p2['id']}/aprovar")
    assert client.get(f"/planos/{p1['id']}").json()["status"] == "substituida"
    assert client.get(f"/planos/{p2['id']}").json()["status"] == "aprovada"

def test_rejeitar_plano_registra_motivo_e_impede_nova_decisao(client):
    d = _disciplina_e_disponibilidade(client)
    _tarefa(client, d, "Lista", 5, 4)
    p = client.post("/planos").json()
    r = client.post(f"/planos/{p['id']}/rejeitar", json={"motivo": "horários ruins"})
    assert r.json()["status"] == "rejeitada" and r.json()["motivo_rejeicao"] == "horários ruins"
    assert client.post(f"/planos/{p['id']}/aprovar").status_code == 409
    assert client.post(f"/planos/{p['id']}/rejeitar").status_code == 409

def test_plano_inexistente_retorna_404(client):
    assert client.get("/planos/999").status_code == 404
    assert client.post("/planos/999/aprovar").status_code == 404

def test_trace_registra_cada_agente_em_ordem(client):
    d = _disciplina_e_disponibilidade(client)
    _tarefa(client, d, "Lista", 5, 4)
    p = client.post("/planos").json()
    trace = client.get(f"/planos/{p['id']}/trace").json()
    assert [e["ordem"] for e in trace] == list(range(1, len(trace) + 1))
    agentes = [e["agente"] for e in trace]
    assert agentes[0] == "priorizador" and agentes[-1] == "orquestrador"
    assert {"planejador", "verificador", "avaliador"} <= set(agentes)
    assert all(e["duracao_ms"] is not None for e in trace if e["etapa"] in {"priorizar", "validar"})

def test_listar_planos(client):
    d = _disciplina_e_disponibilidade(client)
    _tarefa(client, d, "Lista", 5, 4)
    client.post("/planos"); client.post("/planos")
    lista = client.get("/planos").json()
    assert [p["id"] for p in lista] == [2, 1]

def test_plano_com_seed_converge_e_sinaliza_tarefas_inviaveis(client, cenario_seed):
    plano = client.post("/planos").json()
    r = plano["resumo"]
    assert r["convergiu"] is True and len(r["inviaveis"]) == 1
    assert r["revisoes"][0]["acao"] == "usar_prazo"
    assert plano["sessoes"]

def test_modo_llm_usa_agentes_com_llm_e_marca_o_plano(client):
    d = _disciplina_e_disponibilidade(client)
    _tarefa(client, d, "Grande", 6, 10, dificuldade=5, importancia=5)
    _tarefa(client, d, "Curta", 1, 2, dificuldade=2, importancia=2)
    llm = LLMRoteirizado({"ordem": [1, 2]}, {"acao": "usar_prazo", "justificativa": "prazo"},
                         {"acao": "aceitar", "justificativa": "ok"})
    app.dependency_overrides[get_llm] = lambda: llm
    plano = client.post("/planos").json()
    assert plano["usou_llm"] is True
    assert plano["resumo"]["revisoes"][0]["origem"] == "llm"
    assert plano["resumo"]["problemas"] == []

def test_llm_fora_do_ar_nao_impede_geracao_do_plano(client):
    d = _disciplina_e_disponibilidade(client)
    _tarefa(client, d, "Lista", 5, 4)
    _tarefa(client, d, "Outra", 6, 3)
    app.dependency_overrides[get_llm] = lambda: LLMIndisponivel()
    r = client.post("/planos")
    assert r.status_code == 201 and r.json()["sessoes"]
    trace = client.get(f"/planos/{r.json()['id']}/trace").json()
    assert any(e["etapa"] == "fallback" for e in trace)
