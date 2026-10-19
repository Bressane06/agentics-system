from pydantic import BaseModel, ConfigDict, Field

class DisciplinaCreate(BaseModel):
    nome: str = Field(min_length=2, max_length=100)
    dificuldade: int = Field(default=3, ge=1, le=5)

class DisciplinaUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=2, max_length=100)
    dificuldade: int | None = Field(default=None, ge=1, le=5)

class DisciplinaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nome: str
    dificuldade: int