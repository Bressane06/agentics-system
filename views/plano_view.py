import json
from datetime import date, datetime, time
from pydantic import BaseModel, ConfigDict
from models import Plano, Traco

class ItemOrdemOut(BaseModel):
    posicao: int
    tarefa_id: int
    pontuacao: float
    justificativa: str

class ProblemaOut(BaseModel):
    tipo: str
    tarefa_id: int | None
    detalhe: str
    corrigivel: bool

class RevisaoOut(BaseModel):
    numero: int
    acao: str
    justificativa: str
    origem: str          # regra | llm | fallback
    problemas: int

class ParametrosOut(BaseModel):
    estrategia: str
    max_bloco_min: int

class ResumoOut(BaseModel):
    ordem: list[ItemOrdemOut]
    problemas: list[ProblemaOut]
    inviaveis: list[int]
    revisoes: list[RevisaoOut]
    parametros: ParametrosOut
    convergiu: bool
    motivo_parada: str

class SessaoOut(BaseModel):
    id: int
    tarefa_id: int
    titulo: str
    data: date
    hora_inicio: time
    hora_fim: time
    status: str

class PlanoOut(BaseModel):
    id: int
    criado_em: datetime
    referencia: date
    status: str
    usou_llm: bool
    motivo_rejeicao: str
    resumo: ResumoOut
    sessoes: list[SessaoOut]

    @classmethod
    def from_model(cls, p: Plano) -> "PlanoOut":
        return cls(
            id=p.id, criado_em=p.criado_em, referencia=p.referencia, status=p.status,
            usou_llm=p.usou_llm, motivo_rejeicao=p.motivo_rejeicao,
            resumo=ResumoOut(**json.loads(p.resumo)),
            sessoes=[SessaoOut(id=s.id, tarefa_id=s.tarefa_id, titulo=s.tarefa.titulo,
                               data=s.data, hora_inicio=s.hora_inicio, hora_fim=s.hora_fim,
                               status=s.status) for s in p.sessoes],
        )

class PlanoResumoOut(BaseModel):
    id: int
    criado_em: datetime
    status: str
    usou_llm: bool
    sessoes: int
    problemas: int

    @classmethod
    def from_model(cls, p: Plano) -> "PlanoResumoOut":
        return cls(id=p.id, criado_em=p.criado_em, status=p.status, usou_llm=p.usou_llm,
                   sessoes=len(p.sessoes), problemas=len(json.loads(p.resumo).get("problemas", [])))

class TracoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    ordem: int
    agente: str
    etapa: str
    duracao_ms: float | None
    dados: dict

    @classmethod
    def from_model(cls, t: Traco) -> "TracoOut":
        return cls(ordem=t.ordem, agente=t.agente, etapa=t.etapa,
                   duracao_ms=t.duracao_ms, dados=json.loads(t.dados))

class AprovarIn(BaseModel):
    confirmar_riscos: bool = False

class RejeitarIn(BaseModel):
    motivo: str = ""
