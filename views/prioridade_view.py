from dataclasses import asdict
from datetime import date
from pydantic import BaseModel
from services.domain import ItemPriorizado

class ComponentesOut(BaseModel):
    urgencia: float
    importancia: float
    dificuldade: float
    progresso: float

class PrioridadeOut(BaseModel):
    posicao: int
    tarefa_id: int
    titulo: str
    prazo: date
    pontuacao: float
    componentes: ComponentesOut
    justificativa: str

    @classmethod
    def from_item(cls, item: ItemPriorizado) -> "PrioridadeOut":
        c = {k: round(v, 4) for k, v in asdict(item.componentes).items()}
        return cls(
            posicao=item.posicao,
            tarefa_id=item.tarefa.id,
            titulo=item.tarefa.titulo,
            prazo=item.tarefa.prazo,
            pontuacao=round(item.pontuacao, 4),
            componentes=ComponentesOut(**c),
            justificativa=item.justificativa,
        )