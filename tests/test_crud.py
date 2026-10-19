from datetime import date, timedelta

def _disciplina(client, nome="Cálculo I"):
    return client.post("/disciplinas", json={"nome": nome, "dificuldade": 4})

def _tarefa(client, disciplina_id, **extra):
    corpo = {
        "disciplina_id": disciplina_id,
        "titulo": "Lista 1",
        "prazo": str(date.today() + timedelta(days=7)),
        "horas_estimadas": 4,
        **extra,
    }
    return client.post("/tarefas", json=corpo)

def test_criar_disciplina(client):
    r = _disciplina(client)
    assert r.status_code == 201
    assert r.json()["nome"] == "Cálculo I"

def test_disciplina_duplicada_retorna_409(client):
    _disciplina(client)
    assert _disciplina(client).status_code == 409

def test_tarefa_com_disciplina_inexistente_retorna_404(client):
    assert _tarefa(client, disciplina_id=999).status_code == 404

def test_tarefa_com_prazo_passado_retorna_422(client):
    d = _disciplina(client).json()
    r = _tarefa(client, d["id"], prazo=str(date.today() - timedelta(days=1)))
    assert r.status_code == 422

def test_tarefa_concluida_automaticamente(client):
    d = _disciplina(client).json()
    t = _tarefa(client, d["id"]).json()
    r = client.patch(f"/tarefas/{t['id']}", json={"horas_concluidas": 4})
    assert r.json()["status"] == "concluida"

def test_filtrar_tarefas_por_status(client):
    d = _disciplina(client).json()
    _tarefa(client, d["id"])
    assert len(client.get("/tarefas?status=pendente").json()) == 1
    assert client.get("/tarefas?status=concluida").json() == []

def test_remover_tarefa(client):
    d = _disciplina(client).json()
    t = _tarefa(client, d["id"]).json()
    assert client.delete(f"/tarefas/{t['id']}").status_code == 204
    assert client.get(f"/tarefas/{t['id']}").status_code == 404