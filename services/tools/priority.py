from dataclasses import dataclass, replace
from datetime import date
from typing import Sequence

import config
from services.domain import TarefaInfo, Componentes, ItemPriorizado

URGENCIA_MIN_DIAS = 0.5

ROTULOS = {
    "urgencia": "urgência",
    "importancia": "importância",
    "dificuldade": "dificuldade",
    "progresso": "trabalho restante",
}

@dataclass(frozen=True)
class Pesos:
    urgencia: float = config.PESO_URGENCIA
    importancia: float = config.PESO_IMPORTANCIA
    dificuldade: float = config.PESO_DIFICULDADE
    progresso: float = config.PESO_PROGRESSO

    def __post_init__(self):
        valores = (self.urgencia, self.importancia, self.dificuldade, self.progresso)
        if any(v < 0 for v in valores):
            raise ValueError("Os pesos não podem ser negativos.")
        if abs(sum(valores) - 1.0) > 1e-6:
            raise ValueError(f"Os pesos devem somar 1.0 (soma atual: {sum(valores):.2f}).")

def dias_ate_prazo(prazo: date, hoje: date) -> int:
    return (prazo - hoje).days

def calcular_urgencia(dias: float) -> float:
    return URGENCIA_MIN_DIAS / max(dias, URGENCIA_MIN_DIAS)

def calcular_componentes(t: TarefaInfo, hoje: date) -> Componentes:
    restantes = max(t.horas_estimadas - t.horas_concluidas, 0.0)
    progresso = restantes / t.horas_estimadas if t.horas_estimadas > 0 else 0.0
    return Componentes(
        urgencia=calcular_urgencia(dias_ate_prazo(t.prazo, hoje)),
        importancia=t.importancia / 5,
        dificuldade=t.dificuldade / 5,
        progresso=progresso,
    )

def pontuar(c: Componentes, pesos: Pesos) -> float:
    return (
        pesos.urgencia * c.urgencia
        + pesos.importancia * c.importancia
        + pesos.dificuldade * c.dificuldade
        + pesos.progresso * c.progresso
    )

def gerar_justificativa(c: Componentes, pesos: Pesos, dias: int) -> str:
    contribuicoes = {nome: getattr(pesos, nome) * getattr(c, nome) for nome in ROTULOS}
    principais = sorted(contribuicoes, key=contribuicoes.get, reverse=True)[:2]
    fatores = " e ".join(ROTULOS[n] for n in principais)
    if dias < 0:
        prazo = f"prazo vencido há {-dias} dia(s)"
    elif dias == 0:
        prazo = "o prazo é hoje"
    else:
        prazo = f"prazo em {dias} dia(s)"
    return f"Pesaram mais: {fatores}; {prazo}."

def priorizar(tarefas: Sequence[TarefaInfo], hoje: date | None = None,
              pesos: Pesos | None = None) -> list[ItemPriorizado]:
    hoje = hoje or date.today()
    pesos = pesos or Pesos()

    itens = []
    for t in tarefas:
        c = calcular_componentes(t, hoje)
        itens.append(ItemPriorizado(
            posicao=0,
            tarefa=t,
            pontuacao=pontuar(c, pesos),
            componentes=c,
            justificativa=gerar_justificativa(c, pesos, dias_ate_prazo(t.prazo, hoje)),
        ))

    # desempate determinístico: maior pontuação, prazo mais próximo, menor id
    itens.sort(key=lambda i: (-i.pontuacao, i.tarefa.prazo, i.tarefa.id))
    return [replace(item, posicao=n) for n, item in enumerate(itens, start=1)]