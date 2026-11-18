from data.seed import popular, DISCIPLINAS, TAREFAS, DISPONIBILIDADE
from models import Disciplina, Tarefa, Disponibilidade, Historico

def test_seed_popula_o_banco(db):
    assert popular(db) is True
    assert db.query(Disciplina).count() == len(DISCIPLINAS)
    assert db.query(Tarefa).count() == len(TAREFAS)
    assert db.query(Disponibilidade).count() == len(DISPONIBILIDADE)

def test_seed_e_idempotente(db):
    popular(db)
    assert popular(db) is False
    assert db.query(Disciplina).count() == len(DISCIPLINAS)

def test_seed_registra_historico(db):
    popular(db)
    assert db.query(Historico).count() > 0