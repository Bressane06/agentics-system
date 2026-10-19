from dataclasses import dataclass
from datetime import date

@dataclass(frozen=True)
class TarefaInfo:
    """Visão da tarefa usada pelos agentes (independente do banco)."""
    id: int
    titulo: str
    prazo: date
    dificuldade: int
    importancia: int
    horas_estimadas: float
    horas_concluidas: float = 0.0

    @classmethod
    def from_model(cls, t) -> "TarefaInfo":
        return cls(
            id=t.id, titulo=t.titulo, prazo=t.prazo,
            dificuldade=t.dificuldade, importancia=t.importancia,
            horas_estimadas=t.horas_estimadas, horas_concluidas=t.horas_concluidas,
        )

@dataclass(frozen=True)
class Componentes:
    """Fatores normalizados (0 a 1) que entram na pontuação."""
    urgencia: float
    importancia: float
    dificuldade: float
    progresso: float

@dataclass(frozen=True)
class ItemPriorizado:
    posicao: int
    tarefa: TarefaInfo
    pontuacao: float
    componentes: Componentes
    justificativa: str