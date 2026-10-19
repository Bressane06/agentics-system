from datetime import date
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

StatusTarefa = Literal["pendente", "concluida"]

class TarefaCreate(BaseModel):
    disciplina_id: int
    titulo: str = Field(min_length=2, max_length=150)
    prazo: date
    dificuldade: int = Field(default=3, ge=1, le=5)
    importancia: int = Field(default=3, ge=1, le=5)
    horas_estimadas: float = Field(gt=0)

class TarefaUpdate(BaseModel):
    disciplina_id: int | None = None
    titulo: str | None = Field(default=None, min_length=2, max_length=150)
    prazo: date | None = None
    dificuldade: int | None = Field(default=None, ge=1, le=5)
    importancia: int | None = Field(default=None, ge=1, le=5)
    horas_estimadas: float | None = Field(default=None, gt=0)
    horas_concluidas: float | None = Field(default=None, ge=0)
    status: StatusTarefa | None = None

class TarefaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    disciplina_id: int
    titulo: str
    prazo: date
    dificuldade: int
    importancia: int
    horas_estimadas: float
    horas_concluidas: float
    status: StatusTarefa