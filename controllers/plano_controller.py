from fastapi import APIRouter, Depends
from dependencies import get_plano_service
from services.plano_service import PlanoService
from views.plano_view import (PlanoOut, PlanoResumoOut, TracoOut, AprovarIn, RejeitarIn)

router = APIRouter(prefix="/planos", tags=["Planos"])

@router.post("", response_model=PlanoOut, status_code=201)
def gerar(service: PlanoService = Depends(get_plano_service)):
    """Os agentes geram uma *proposta* de plano. Ela só vale após aprovação humana."""
    return PlanoOut.from_model(service.gerar())

@router.get("", response_model=list[PlanoResumoOut])
def listar(service: PlanoService = Depends(get_plano_service)):
    return [PlanoResumoOut.from_model(p) for p in service.listar()]

@router.get("/{id}", response_model=PlanoOut)
def obter(id: int, service: PlanoService = Depends(get_plano_service)):
    return PlanoOut.from_model(service.obter(id))

@router.get("/{id}/trace", response_model=list[TracoOut])
def trace(id: int, service: PlanoService = Depends(get_plano_service)):
    return [TracoOut.from_model(t) for t in service.obter(id).tracos]

@router.post("/{id}/aprovar", response_model=PlanoOut)
def aprovar(id: int, corpo: AprovarIn | None = None,
            service: PlanoService = Depends(get_plano_service)):
    return PlanoOut.from_model(service.aprovar(id, (corpo or AprovarIn()).confirmar_riscos))

@router.post("/{id}/rejeitar", response_model=PlanoOut)
def rejeitar(id: int, corpo: RejeitarIn | None = None,
             service: PlanoService = Depends(get_plano_service)):
    return PlanoOut.from_model(service.rejeitar(id, (corpo or RejeitarIn()).motivo))
