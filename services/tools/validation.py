"""Verificações independentes de um plano. Não confia no planejador: reconfere tudo."""
from collections import defaultdict
from datetime import date
from typing import Sequence

from services.domain import Problema, SessaoPlanejada, Slot, TarefaInfo
from services.tools.scheduling import capacidade_ate, minutos_restantes

# Tipos de problema
SOBREPOSICAO = "sobreposicao"
FORA_DA_DISPONIBILIDADE = "fora_da_disponibilidade"
APOS_PRAZO = "apos_prazo"
NO_PASSADO = "no_passado"
HORAS_EXCEDENTES = "horas_excedentes"
COBERTURA_INCOMPLETA = "cobertura_incompleta"   # falta alocar, mas cabe em tese
INVIAVEL = "inviavel"                           # não cabe nem sozinha até o prazo
SOBRECARGA = "sobrecarga"                       # cabe sozinha, mas a carga acumulada até o prazo não cabe

def _fmt(minutos: int) -> str:
    return f"{minutos // 60:02d}:{minutos % 60:02d}"

def _inevitaveis(tarefas: Sequence[TarefaInfo], slots: Sequence[Slot]) -> dict[int, tuple[str, str]]:
    """Tarefas que ficariam sem cobertura mesmo na melhor ordenação (prazo mais próximo primeiro).

    Percorre por prazo acumulando a demanda; quando ela passa da capacidade até o prazo, essa
    tarefa é inevitavelmente prejudicada e a capacidade é considerada esgotada. Já uma tarefa
    curta no plano atual que *não* está aqui é problema de ordenação, não de falta de tempo.
    """
    resultado: dict[int, tuple[str, str]] = {}
    acumulado = 0
    for t in sorted(tarefas, key=lambda x: (x.prazo, x.id)):
        necessario = minutos_restantes(t)
        cap = capacidade_ate(slots, t.prazo)
        if acumulado + necessario > cap:
            if necessario > cap:
                resultado[t.id] = (INVIAVEL, f"Precisa de {necessario} min até {t.prazo}, "
                                             f"mas só há {cap} min disponíveis")
            else:
                resultado[t.id] = (SOBRECARGA, f"Carga acumulada até {t.prazo} é "
                                               f"{acumulado + necessario} min, mas só há {cap} min disponíveis")
            acumulado = cap
        else:
            acumulado += necessario
    return resultado

def validar(sessoes: Sequence[SessaoPlanejada], tarefas: Sequence[TarefaInfo],
            slots: Sequence[Slot], hoje: date) -> list[Problema]:
    por_id = {t.id: t for t in tarefas}
    problemas: list[Problema] = []

    for s in sessoes:
        t = por_id.get(s.tarefa_id)
        if t is None:
            problemas.append(Problema(FORA_DA_DISPONIBILIDADE, s.tarefa_id,
                                      "Sessão referencia tarefa desconhecida.", True))
            continue
        quando = f"{s.data} {_fmt(s.inicio)}-{_fmt(s.fim)}"
        if s.data < hoje:
            problemas.append(Problema(NO_PASSADO, t.id, f"Sessão no passado ({quando}).", True))
        if s.data > t.prazo:
            problemas.append(Problema(APOS_PRAZO, t.id,
                                      f"Sessão após o prazo {t.prazo} ({quando}).", True))
        if not any(sl.data == s.data and sl.inicio <= s.inicio and s.fim <= sl.fim for sl in slots):
            problemas.append(Problema(FORA_DA_DISPONIBILIDADE, t.id,
                                      f"Sessão fora da disponibilidade ({quando}).", True))

    por_dia = defaultdict(list)
    for s in sessoes:
        por_dia[s.data].append(s)
    for data, doDia in por_dia.items():
        doDia.sort(key=lambda x: x.inicio)
        for a, b in zip(doDia, doDia[1:]):
            if b.inicio < a.fim:
                problemas.append(Problema(
                    SOBREPOSICAO, b.tarefa_id,
                    f"Sessões sobrepostas em {data}: {_fmt(a.inicio)}-{_fmt(a.fim)} "
                    f"e {_fmt(b.inicio)}-{_fmt(b.fim)}.", True))

    inevitaveis = _inevitaveis(tarefas, slots)
    for t in tarefas:
        necessario = minutos_restantes(t)
        alocado = sum(s.minutos for s in sessoes if s.tarefa_id == t.id)
        if alocado > necessario:
            problemas.append(Problema(HORAS_EXCEDENTES, t.id,
                                      f"Alocados {alocado} min para {necessario} min necessários.", True))
        elif alocado < necessario:
            falta = necessario - alocado
            if t.id in inevitaveis:
                tipo, detalhe = inevitaveis[t.id]
                problemas.append(Problema(tipo, t.id, f"{detalhe} (faltam {falta} min no plano).", False))
            else:
                # a melhor ordenação cumpriria esta tarefa: é falha do plano, logo corrigível
                problemas.append(Problema(
                    COBERTURA_INCOMPLETA, t.id,
                    f"Faltam {falta} min de {necessario} min antes de {t.prazo}.", True))
    return problemas

def minutos_nao_alocados(sessoes: Sequence[SessaoPlanejada], tarefas: Sequence[TarefaInfo]) -> int:
    return sum(max(minutos_restantes(t) - sum(s.minutos for s in sessoes if s.tarefa_id == t.id), 0)
               for t in tarefas)
