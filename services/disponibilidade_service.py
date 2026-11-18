from models import Disponibilidade
from repositories.disponibilidade_repository import DisponibilidadeRepository
from repositories.historico_repository import HistoricoRepository
from views.disponibilidade_view import DisponibilidadeCreate
from exceptions import NaoEncontradoError, ConflitoError

class DisponibilidadeService:
    def __init__(self, disponibilidades: DisponibilidadeRepository,
                 historico: HistoricoRepository):
        self.disponibilidades = disponibilidades
        self.historico = historico

    def criar(self, dados: DisponibilidadeCreate) -> Disponibilidade:
        # regra: dois blocos do mesmo dia não podem se sobrepor
        for existente in self.disponibilidades.listar_ordenado(dados.dia_semana):
            if dados.hora_inicio < existente.hora_fim and dados.hora_fim > existente.hora_inicio:
                raise ConflitoError(
                    f"Sobrepõe o bloco {existente.hora_inicio:%H:%M}-{existente.hora_fim:%H:%M}."
                )
        bloco = self.disponibilidades.add(Disponibilidade(**dados.model_dump()))
        self.historico.registrar(
            "disponibilidade_criada",
            f"dia {bloco.dia_semana}: {bloco.hora_inicio:%H:%M}-{bloco.hora_fim:%H:%M}",
        )
        return bloco

    def listar(self, dia_semana: int | None = None) -> list[Disponibilidade]:
        return self.disponibilidades.listar_ordenado(dia_semana)

    def remover(self, id: int) -> None:
        bloco = self.disponibilidades.get(id)
        if bloco is None:
            raise NaoEncontradoError(f"Bloco {id} não encontrado.")
        self.disponibilidades.delete(bloco)
        self.historico.registrar("disponibilidade_removida", str(id))