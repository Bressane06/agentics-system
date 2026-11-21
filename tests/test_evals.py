import pytest
from evals.cenarios import CENARIOS

@pytest.mark.parametrize("nome", list(CENARIOS))
def test_cenario_de_avaliacao(nome):
    falhas = [f"{v.nome}: {v.detalhe}" for v in CENARIOS[nome]() if not v.ok]
    assert not falhas, falhas
