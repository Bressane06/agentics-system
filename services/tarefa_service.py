from datetime import date
from models import Tarefa
from repositories.tarefa_repository import TarefaRepository
from repositories.disciplina_repository import DisciplinaRepository
from repositories.historico_repository import HistoricoRepository
from views.tarefa_view import TarefaCreate, TarefaUpdate
from exceptions import NaoEncontradoError, RegraDeNegocioError

class TarefaService:
    def __init__(self, tarefas: TarefaRepository,
                 disciplinas: DisciplinaRepository,
                 historico: HistoricoRepository):
        self.tarefas = tarefas
        self.disciplinas = disciplinas
        self.historico = historico

    def _garantir_disciplina(self, disciplina_id: int) -> None:
        if self.disciplinas.get(disciplina_id) is None:
            raise NaoEncontradoError(f"Disciplina {disciplina_id} não encontrada.")

    def criar(self, dados: TarefaCreate) -> Tarefa:
        self._garantir_disciplina(dados.disciplina_id)
        if dados.prazo < date.today():
            raise RegraDeNegocioError("O prazo não pode estar no passado.")
        tarefa = self.tarefas.add(Tarefa(**dados.model_dump()))
        self.historico.registrar("tarefa_criada", f"{tarefa.id}: {tarefa.titulo}")
        return tarefa

    def obter(self, id: int) -> Tarefa:
        tarefa = self.tarefas.get(id)
        if tarefa is None:
            raise NaoEncontradoError(f"Tarefa {id} não encontrada.")
        return tarefa

    def listar(self, status: str | None = None,
               disciplina_id: int | None = None) -> list[Tarefa]:
        return self.tarefas.listar_filtrado(status, disciplina_id)

    def atualizar(self, id: int, dados: TarefaUpdate) -> Tarefa:
        tarefa = self.obter(id)
        campos = dados.model_dump(exclude_none=True)

        if "disciplina_id" in campos:
            self._garantir_disciplina(campos["disciplina_id"])

        estimadas = campos.get("horas_estimadas", tarefa.horas_estimadas)
        concluidas = campos.get("horas_concluidas", tarefa.horas_concluidas)
        if concluidas > estimadas:
            raise RegraDeNegocioError("Horas concluídas não podem exceder as estimadas.")

        # regra: tarefa com todas as horas feitas é marcada como concluída
        if concluidas >= estimadas and "status" not in campos:
            campos["status"] = "concluida"

        tarefa = self.tarefas.update(tarefa, campos)
        self.historico.registrar("tarefa_atualizada", f"{id}: {campos}")
        return tarefa

    def remover(self, id: int) -> None:
        tarefa = self.obter(id)
        titulo = tarefa.titulo
        self.tarefas.delete(tarefa)
        self.historico.registrar("tarefa_removida", f"{id}: {titulo}")