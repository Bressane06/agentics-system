from models import Disciplina
from repositories.disciplina_repository import DisciplinaRepository
from repositories.historico_repository import HistoricoRepository
from views.disciplina_view import DisciplinaCreate, DisciplinaUpdate
from exceptions import NaoEncontradoError, ConflitoError

class DisciplinaService:
    def __init__(self, disciplinas: DisciplinaRepository, historico: HistoricoRepository):
        self.disciplinas = disciplinas
        self.historico = historico

    def criar(self, dados: DisciplinaCreate) -> Disciplina:
        if self.disciplinas.get_by_nome(dados.nome):
            raise ConflitoError(f"Já existe a disciplina '{dados.nome}'.")
        disciplina = self.disciplinas.add(Disciplina(**dados.model_dump()))
        self.historico.registrar("disciplina_criada", f"{disciplina.id}: {disciplina.nome}")
        return disciplina

    def obter(self, id: int) -> Disciplina:
        disciplina = self.disciplinas.get(id)
        if disciplina is None:
            raise NaoEncontradoError(f"Disciplina {id} não encontrada.")
        return disciplina

    def listar(self) -> list[Disciplina]:
        return self.disciplinas.list()

    def atualizar(self, id: int, dados: DisciplinaUpdate) -> Disciplina:
        disciplina = self.obter(id)
        campos = dados.model_dump(exclude_none=True)
        novo_nome = campos.get("nome")
        if novo_nome and novo_nome != disciplina.nome and self.disciplinas.get_by_nome(novo_nome):
            raise ConflitoError(f"Já existe a disciplina '{novo_nome}'.")
        disciplina = self.disciplinas.update(disciplina, campos)
        self.historico.registrar("disciplina_atualizada", f"{id}: {campos}")
        return disciplina

    def remover(self, id: int) -> None:
        disciplina = self.obter(id)
        nome = disciplina.nome
        self.disciplinas.delete(disciplina)
        self.historico.registrar("disciplina_removida", f"{id}: {nome}")