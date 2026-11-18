from fastapi import APIRouter, Depends
from dependencies import get_prioridade_service
from services.prioridade_service import PrioridadeService
from views.prioridade_view import PrioridadeOut

router = APIRouter(prefix="/prioridades", tags=["Prioridades"])

@router.get("", response_model=list[PrioridadeOut])
def ranking(service: PrioridadeService = Depends(get_prioridade_service)):
    return [PrioridadeOut.from_item(i) for i in service.ranking()]