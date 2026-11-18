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

# ---------- Tipos do planejamento (agentes de planejamento e avaliação) ----------

@dataclass(frozen=True)
class Bloco:
    """Janela semanal de disponibilidade, em minutos desde 00:00."""
    dia_semana: int      # 0 = segunda ... 6 = domingo
    inicio: int
    fim: int

    @classmethod
    def from_model(cls, d) -> "Bloco":
        return cls(d.dia_semana, d.hora_inicio.hour * 60 + d.hora_inicio.minute,
                   d.hora_fim.hour * 60 + d.hora_fim.minute)

@dataclass(frozen=True)
class Slot:
    """Janela concreta de estudo em uma data."""
    data: date
    inicio: int
    fim: int

@dataclass(frozen=True)
class SessaoPlanejada:
    tarefa_id: int
    data: date
    inicio: int
    fim: int

    @property
    def minutos(self) -> int:
        return self.fim - self.inicio

@dataclass(frozen=True)
class Parametros:
    """Parâmetros que o loop de revisão pode ajustar (e só estes)."""
    estrategia: str = "prioridade"   # "prioridade" | "prazo"
    max_bloco_min: int = 120         # máximo de minutos por tarefa por dia

@dataclass(frozen=True)
class Problema:
    tipo: str          # ver services/tools/validation.py
    tarefa_id: int | None
    detalhe: str
    corrigivel: bool   # False = não há ajuste de plano que resolva (ex.: tarefa inviável)

@dataclass(frozen=True)
class Decisao:
    acao: str          # "aceitar" | "usar_prazo" | "ampliar_bloco"
    justificativa: str
    origem: str        # "regra" | "llm" | "fallback"

@dataclass(frozen=True)
class Revisao:
    numero: int
    acao: str
    justificativa: str
    origem: str
    problemas: int

@dataclass(frozen=True)
class ResultadoPlanejamento:
    ordem: list
    sessoes: list
    problemas: list
    inviaveis: list
    revisoes: list
    parametros: Parametros
    convergiu: bool
    motivo_parada: str
