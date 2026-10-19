def _bloco(client, dia=0, inicio="19:00", fim="21:00"):
    return client.post("/disponibilidade",
                       json={"dia_semana": dia, "hora_inicio": inicio, "hora_fim": fim})

def test_criar_bloco(client):
    r = _bloco(client)
    assert r.status_code == 201
    assert r.json()["dia_semana"] == 0

def test_hora_fim_antes_do_inicio_retorna_422(client):
    assert _bloco(client, inicio="21:00", fim="19:00").status_code == 422

def test_dia_invalido_retorna_422(client):
    assert _bloco(client, dia=7).status_code == 422

def test_sobreposicao_retorna_409(client):
    _bloco(client, inicio="19:00", fim="21:00")
    assert _bloco(client, inicio="20:00", fim="22:00").status_code == 409

def test_blocos_adjacentes_sao_permitidos(client):
    _bloco(client, inicio="19:00", fim="20:00")
    assert _bloco(client, inicio="20:00", fim="21:00").status_code == 201

def test_filtrar_por_dia(client):
    _bloco(client, dia=0)
    _bloco(client, dia=2)
    assert len(client.get("/disponibilidade?dia_semana=2").json()) == 1

def test_remover_bloco(client):
    bloco = _bloco(client).json()
    assert client.delete(f"/disponibilidade/{bloco['id']}").status_code == 204
    assert client.delete(f"/disponibilidade/{bloco['id']}").status_code == 404