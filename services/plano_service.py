import json
from dataclasses import asdict
from datetime import date, datetime, time

from models import Plano, Sessao, Traco
from repositories.disponibilidade_repository import DisponibilidadeRepository
from repositories.historico_repository import HistoricoRepository
from repositories.plano_repository import PlanoRepository
from repositories.tarefa_repository import TarefaRepository
from services import observability
from services.domain import Bloco, ResultadoPlanejamento, TarefaInfo
from services.orchestrator import Orquestrador
from exceptions import ConflitoError, NaoEncontradoError, RegraDeNegocioError

def _hora(minutos: int) -> time:
    return time(minutos // 60, minutos % 60)

def serializar_resumo(r: ResultadoPlanejamento) -> dict:
    return {
        "ordem": [{"posicao": i.posicao, "tarefa_id": i.tarefa.id,
                   "pontuacao": round(i.pontuacao, 4), "justificativa": i.justificativa}
                  for i in r.ordem],
        "problemas": [asdict(p) for p in r.problemas],
        "inviaveis": r.inviaveis,
        "revisoes": [asdict(v) for v in r.revisoes],
        "parametros": asdict(r.parametros),
        "convergiu": r.convergiu,
        "motivo_parada": r.motivo_parada,
    }

class PlanoService:
    """Fronteira de autonomia: os agentes só *propõem* um plano. Nada vira definitivo sem
    aprovação humana, e os agentes nunca alteram tarefas ou disponibilidade."""

    def __init__(self, tarefas: TarefaRepository, disponibilidades: DisponibilidadeRepository,
                 planos: PlanoRepository, historico: HistoricoRepository,
                 orquestrador: Orquestrador, usa_llm: bool = False):
        self.tarefas = tarefas
        self.disponibilidades = disponibilidades
        self.planos = planos
        self.historico = historico
        self.orquestrador = orquestrador
        self.usa_llm = usa_llm

    def gerar(self, hoje: date | None = None, agora: datetime | None = None) -> Plano:
        agora = agora or datetime.now()
        hoje = hoje or agora.date()
        pendentes = self.tarefas.listar_filtrado(status="pendente")
        if not pendentes:
            raise RegraDeNegocioError("Não há tarefas pendentes para planejar.")
        blocos = [Bloco.from_model(d) for d in self.disponibilidades.listar_ordenado()]
        if not blocos:
            raise RegraDeNegocioError("Cadastre ao menos um bloco de disponibilidade.")

        infos = [TarefaInfo.from_model(t) for t in pendentes]
        tracer = observability.Tracer()
        agora_min = agora.hour * 60 + agora.minute if agora.date() == hoje else None
        with observability.ativar(tracer):
            resultado = self.orquestrador.executar(infos, blocos, hoje, agora_min)

        plano = Plano(referencia=hoje, usou_llm=self.usa_llm,
                      resumo=json.dumps(serializar_resumo(resultado), default=str))
        sessoes = [Sessao(tarefa_id=s.tarefa_id, data=s.data, hora_inicio=_hora(s.inicio),
                          hora_fim=_hora(s.fim), status="proposta") for s in resultado.sessoes]
        tracos = [Traco(ordem=e["ordem"], agente=e["agente"], etapa=e["etapa"],
                        dados=json.dumps(e["dados"], default=str, ensure_ascii=False),
                        duracao_ms=e["duracao_ms"]) for e in tracer.eventos]
        plano = self.planos.salvar_completo(plano, sessoes, tracos)
        self.historico.registrar(
            "plano_gerado",
            f"{plano.id}: {len(sessoes)} sessões, {len(resultado.problemas)} problema(s), "
            f"convergiu={resultado.convergiu}")
        return plano

    def obter(self, id: int) -> Plano:
        plano = self.planos.get(id)
        if plano is None:
            raise NaoEncontradoError(f"Plano {id} não encontrado.")
        return plano

    def listar(self) -> list[Plano]:
        return self.planos.listar_recentes()

    def aprovar(self, id: int, confirmar_riscos: bool = False) -> Plano:
        plano = self.obter(id)
        if plano.status != "proposta":
            raise ConflitoError(f"Só planos 'proposta' podem ser aprovados (atual: {plano.status}).")
        problemas = json.loads(plano.resumo).get("problemas", [])
        if problemas and not confirmar_riscos:
            raise RegraDeNegocioError(
                f"O plano tem {len(problemas)} problema(s) (ex.: tarefas inviáveis). "
                "Revise-os e reenvie com confirmar_riscos=true para aprovar mesmo assim.")
        anterior = self.planos.aprovado_atual()
        if anterior is not None:
            self.planos.definir_status(anterior, "substituida")
        plano = self.planos.definir_status(plano, "aprovada")
        self.historico.registrar("plano_aprovado", f"{id} (riscos confirmados={bool(problemas)})")
        return plano

    def rejeitar(self, id: int, motivo: str = "") -> Plano:
        plano = self.obter(id)
        if plano.status != "proposta":
            raise ConflitoError(f"Só planos 'proposta' podem ser rejeitados (atual: {plano.status}).")
        plano = self.planos.definir_status(plano, "rejeitada", motivo)
        self.historico.registrar("plano_rejeitado", f"{id}: {motivo}")
        return plano
