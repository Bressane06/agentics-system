"""Rastreamento das execuções dos agentes.

Cada execução do orquestrador cria um Tracer; os agentes emitem eventos por meio de
`emitir(...)` sem precisar receber o tracer por parâmetro (ContextVar). Os eventos são
persistidos junto do plano, então qualquer falha pode ser inspecionada e reproduzida.
"""
import json
import logging
import time
from contextlib import contextmanager
from contextvars import ContextVar

log = logging.getLogger("agentes")

class Tracer:
    def __init__(self):
        self.eventos: list[dict] = []

    def registrar(self, agente: str, etapa: str, duracao_ms: float | None = None, **dados) -> dict:
        evento = {"ordem": len(self.eventos) + 1, "agente": agente, "etapa": etapa,
                  "duracao_ms": duracao_ms, "dados": dados}
        self.eventos.append(evento)
        log.info(json.dumps(evento, default=str, ensure_ascii=False))
        return evento

    @contextmanager
    def span(self, agente: str, etapa: str, **entrada):
        """Mede a duração de uma etapa; o corpo pode preencher `saida` para o evento."""
        saida: dict = {}
        inicio = time.perf_counter()
        try:
            yield saida
        except Exception as exc:
            self.registrar(agente, etapa, round((time.perf_counter() - inicio) * 1000, 2),
                           status="erro", erro=str(exc), **entrada)
            raise
        self.registrar(agente, etapa, round((time.perf_counter() - inicio) * 1000, 2),
                       status="ok", **entrada, **saida)

_atual: ContextVar[Tracer | None] = ContextVar("tracer_atual", default=None)

@contextmanager
def ativar(tracer: Tracer):
    token = _atual.set(tracer)
    try:
        yield tracer
    finally:
        _atual.reset(token)

def emitir(agente: str, etapa: str, **dados) -> None:
    """Registra um evento no tracer ativo (no-op fora de uma execução rastreada)."""
    tracer = _atual.get()
    if tracer is not None:
        tracer.registrar(agente, etapa, **dados)

@contextmanager
def etapa(agente: str, nome: str, **entrada):
    """Span no tracer ativo; sem tracer, apenas entrega um dict descartável."""
    tracer = _atual.get()
    if tracer is None:
        yield {}
    else:
        with tracer.span(agente, nome, **entrada) as saida:
            yield saida
