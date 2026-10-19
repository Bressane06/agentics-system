"""Popula o banco com dados fictícios.

Uso:
    python -m data.seed            # popula se o banco estiver vazio
    python -m data.seed --reset    # apaga tudo e popula de novo
"""
import argparse
from datetime import date, time, timedelta
from sqlalchemy.orm import Session

from models import Base, engine, SessionLocal
from repositories.disciplina_repository import DisciplinaRepository
from repositories.tarefa_repository import TarefaRepository
from repositories.disponibilidade_repository import DisponibilidadeRepository
from repositories.historico_repository import HistoricoRepository
from services.disciplina_service import DisciplinaService
from services.tarefa_service import TarefaService
from services.disponibilidade_service import DisponibilidadeService
from views.disciplina_view import DisciplinaCreate
from views.tarefa_view import TarefaCreate
from views.disponibilidade_view import DisponibilidadeCreate

DISCIPLINAS = [
    ("Cálculo I", 5),
    ("Programação Orientada a Objetos", 3),
    ("Banco de Dados", 3),
    ("Inglês Técnico", 2),
]

# (disciplina, título, dias até o prazo, dificuldade, importância, horas)
TAREFAS = [
    ("Cálculo I", "Lista de limites", 5, 4, 3, 4.0),
    ("Cálculo I", "Prova P1", 12, 5, 5, 14.0),
    ("Programação Orientada a Objetos", "Trabalho: padrões de projeto", 14, 4, 5, 10.0),
    ("Programação Orientada a Objetos", "Exercícios de herança", 4, 2, 2, 3.0),
    ("Banco de Dados", "Modelagem ER", 8, 3, 4, 6.0),
    ("Banco de Dados", "Lista de SQL", 3, 2, 3, 3.0),
    ("Inglês Técnico", "Resumo de artigo", 10, 2, 2, 2.5),
    # tarefa propositalmente inviável: o avaliador deve apontá-la nas próximas etapas
    ("Cálculo I", "Seminário surpresa", 1, 5, 4, 12.0),
]

# 0 = segunda ... 6 = domingo
DISPONIBILIDADE = (
    [(d, time(19, 0), time(22, 0)) for d in range(0, 5)]      # seg a sex à noite
    + [(5, time(9, 0), time(12, 0)), (5, time(14, 0), time(17, 0))]  # sábado
)

def popular(db: Session) -> bool:
    """Popula o banco usando os services. Retorna False se já havia dados."""
    historico = HistoricoRepository(db)
    disciplinas_repo = DisciplinaRepository(db)
    disciplinas = DisciplinaService(disciplinas_repo, historico)
    tarefas = TarefaService(TarefaRepository(db), disciplinas_repo, historico)
    disponibilidade = DisponibilidadeService(DisponibilidadeRepository(db), historico)

    if disciplinas.listar():
        return False

    ids = {}
    for nome, dificuldade in DISCIPLINAS:
        ids[nome] = disciplinas.criar(DisciplinaCreate(nome=nome, dificuldade=dificuldade)).id

    hoje = date.today()
    for disc, titulo, dias, dif, imp, horas in TAREFAS:
        tarefas.criar(TarefaCreate(
            disciplina_id=ids[disc], titulo=titulo,
            prazo=hoje + timedelta(days=dias),
            dificuldade=dif, importancia=imp, horas_estimadas=horas,
        ))

    for dia, inicio, fim in DISPONIBILIDADE:
        disponibilidade.criar(DisponibilidadeCreate(
            dia_semana=dia, hora_inicio=inicio, hora_fim=fim
        ))
    return True

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="apaga tudo antes de popular")
    args = parser.parse_args()

    if args.reset:
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        if popular(db):
            print("Banco populado com dados fictícios.")
        else:
            print("O banco já tem dados. Use --reset para recriar.")

if __name__ == "__main__":
    main()