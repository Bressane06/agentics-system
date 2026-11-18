from fastapi import APIRouter, Depends, Query, Response
from dependencies import get_disponibilidade_service
from services.disponibilidade_service import DisponibilidadeService
from views.disponibilidade_view import DisponibilidadeCreate, DisponibilidadeOut

router = APIRouter(prefix="/disponibilidade", tags=["Disponibilidade"])

@router.post("", response_model=DisponibilidadeOut, status_code=201)
def criar(dados: DisponibilidadeCreate,
          service: DisponibilidadeService = Depends(get_disponibilidade_service)):
    return service.criar(dados)

@router.get("", response_model=list[DisponibilidadeOut])
def listar(dia_semana: int | None = Query(default=None, ge=0, le=6),
           service: DisponibilidadeService = Depends(get_disponibilidade_service)):
    return service.listar(dia_semana)

@router.delete("/{id}", status_code=204)
def remover(id: int, service: DisponibilidadeService = Depends(get_disponibilidade_service)):
    service.remover(id)
    return Response(status_code=204)