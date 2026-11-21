"""Ferramentas determinísticas de agendamento: expandem a disponibilidade em janelas
concretas e alocam sessões de estudo. Nenhuma decisão do LLM passa por aqui."""
from collections import defaultdict
from datetime import date, timedelta
from typing import Sequence

import config
from services.domain import Bloco, Slot, SessaoPlanejada, TarefaInfo, Parametros

def minutos_restantes(t: TarefaInfo) -> int:
    return round(max(t.horas_estimadas - t.horas_concluidas, 0.0) * 60)

def expandir_slots(blocos: Sequence[Bloco], hoje: date, ate: date,
                   agora_min: int | None = None) -> list[Slot]:
    """Transforma a grade semanal em janelas por data, de `hoje` até `ate` (inclusive).
    Se `agora_min` for informado, descarta o trecho de hoje que já passou."""
    slots: list[Slot] = []
    dia = hoje
    while dia <= ate:
        for b in blocos:
            if b.dia_semana != dia.weekday():
                continue
            inicio = b.inicio
            if dia == hoje and agora_min is not None:
                inicio = max(inicio, agora_min)
            if b.fim > inicio:
                slots.append(Slot(dia, inicio, b.fim))
        dia += timedelta(days=1)
    return sorted(slots, key=lambda s: (s.data, s.inicio))

def capacidade_ate(slots: Sequence[Slot], prazo: date) -> int:
    """Minutos disponíveis até o prazo (inclusive)."""
    return sum(s.fim - s.inicio for s in slots if s.data <= prazo)

def alocar(ordem: Sequence[TarefaInfo], slots: Sequence[Slot], params: Parametros,
           min_bloco_min: int = config.SESSAO_MIN_BLOCO_MIN) -> list[SessaoPlanejada]:
    """Aloca sessões de forma gulosa.

    estrategia "prioridade": processa as tarefas na ordem recebida (ranking).
    estrategia "prazo": processa por prazo mais próximo (EDF), ignorando o ranking.
    Cada tarefa recebe no máximo `max_bloco_min` minutos por dia e nenhuma sessão passa do prazo.
    """
    processamento = (list(ordem) if params.estrategia == "prioridade"
                     else sorted(ordem, key=lambda t: (t.prazo, t.id)))
    cursor = [s.inicio for s in slots]
    usado_no_dia: dict[tuple[int, date], int] = defaultdict(int)
    sessoes: list[SessaoPlanejada] = []

    for t in processamento:
        falta = minutos_restantes(t)
        for i, slot in enumerate(slots):
            if falta <= 0 or slot.data > t.prazo:
                break
            while falta > 0:
                livre = slot.fim - cursor[i]
                teto_dia = params.max_bloco_min - usado_no_dia[(t.id, slot.data)]
                dur = min(livre, teto_dia, falta)
                if dur <= 0 or (dur < min_bloco_min and dur < falta):
                    break  # evita fragmentos pequenos, exceto para fechar a tarefa
                sessoes.append(SessaoPlanejada(t.id, slot.data, cursor[i], cursor[i] + dur))
                cursor[i] += dur
                usado_no_dia[(t.id, slot.data)] += dur
                falta -= dur
    return sorted(sessoes, key=lambda s: (s.data, s.inicio, s.tarefa_id))
