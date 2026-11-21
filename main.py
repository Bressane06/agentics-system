import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from models import Base, engine
from controllers import (disciplina_controller, disponibilidade_controller,
                         plano_controller, prioridade_controller, tarefa_controller)
from exceptions import NaoEncontradoError, ConflitoError, RegraDeNegocioError

logging.basicConfig(level=logging.INFO)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Agente de Planejamento Acadêmico")

app.include_router(disciplina_controller.router)
app.include_router(tarefa_controller.router)
app.include_router(disponibilidade_controller.router)
app.include_router(prioridade_controller.router)
app.include_router(plano_controller.router)

# Tradução de erros de domínio para HTTP
@app.exception_handler(NaoEncontradoError)
def handle_nao_encontrado(request: Request, exc: NaoEncontradoError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})

@app.exception_handler(ConflitoError)
def handle_conflito(request: Request, exc: ConflitoError):
    return JSONResponse(status_code=409, content={"detail": str(exc)})

@app.exception_handler(RegraDeNegocioError)
def handle_regra(request: Request, exc: RegraDeNegocioError):
    return JSONResponse(status_code=422, content={"detail": str(exc)})

@app.get("/health")
def health():
    return {"status": "ok"}
