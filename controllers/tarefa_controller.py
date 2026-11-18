from fastapi import APIRouter, Depends, Response
from dependencies import get_tarefa_service
from services.tarefa_service import TarefaService
from views.tarefa_view import TarefaCreate, TarefaUpdate, TarefaOut, StatusTarefa

router = APIRouter(prefix="/tarefas", tags=["Tarefas"])

@router.post("", response_model=TarefaOut, status_code=201)
def criar(dados: TarefaCreate, service: TarefaService = Depends(get_tarefa_service)):
    return service.criar(dados)

@router.get("", response_model=list[TarefaOut])
def listar(status: StatusTarefa | None = None, disciplina_id: int | None = None,
           service: TarefaService = Depends(get_tarefa_service)):
    return service.listar(status, disciplina_id)

@router.get("/{id}", response_model=TarefaOut)
def obter(id: int, service: TarefaService = Depends(get_tarefa_service)):
    return service.obter(id)

@router.patch("/{id}", response_model=TarefaOut)
def atualizar(id: int, dados: TarefaUpdate, service: TarefaService = Depends(get_tarefa_service)):
    return service.atualizar(id, dados)

@router.delete("/{id}", status_code=204)
def remover(id: int, service: TarefaService = Depends(get_tarefa_service)):
    service.remover(id)
    return Response(status_code=204)