from fastapi import APIRouter, Depends, Response
from dependencies import get_disciplina_service
from services.disciplina_service import DisciplinaService
from views.disciplina_view import DisciplinaCreate, DisciplinaUpdate, DisciplinaOut

router = APIRouter(prefix="/disciplinas", tags=["Disciplinas"])

@router.post("", response_model=DisciplinaOut, status_code=201)
def criar(dados: DisciplinaCreate, service: DisciplinaService = Depends(get_disciplina_service)):
    return service.criar(dados)

@router.get("", response_model=list[DisciplinaOut])
def listar(service: DisciplinaService = Depends(get_disciplina_service)):
    return service.listar()

@router.get("/{id}", response_model=DisciplinaOut)
def obter(id: int, service: DisciplinaService = Depends(get_disciplina_service)):
    return service.obter(id)

@router.patch("/{id}", response_model=DisciplinaOut)
def atualizar(id: int, dados: DisciplinaUpdate,
              service: DisciplinaService = Depends(get_disciplina_service)):
    return service.atualizar(id, dados)

@router.delete("/{id}", status_code=204)
def remover(id: int, service: DisciplinaService = Depends(get_disciplina_service)):
    service.remover(id)
    return Response(status_code=204)