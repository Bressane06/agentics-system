from datetime import time
from pydantic import BaseModel, ConfigDict, Field, model_validator

class DisponibilidadeCreate(BaseModel):
    dia_semana: int = Field(ge=0, le=6, description="0 = segunda ... 6 = domingo")
    hora_inicio: time
    hora_fim: time

    @model_validator(mode="after")
    def validar_intervalo(self):
        if self.hora_fim <= self.hora_inicio:
            raise ValueError("hora_fim deve ser maior que hora_inicio")
        return self

class DisponibilidadeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    dia_semana: int
    hora_inicio: time
    hora_fim: time