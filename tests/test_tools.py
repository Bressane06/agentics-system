from datetime import date

from services.domain import Bloco, Parametros, SessaoPlanejada, TarefaInfo
from services.tools import scheduling, validation

HOJE = date(2026, 11, 16)  # segunda
NOITE = [Bloco(d, 19 * 60, 21 * 60) for d in range(7)]

def t(id, dias, horas, feitas=0.0):
    return TarefaInfo(id, f"T{id}", date.fromordinal(HOJE.toordinal() + dias), 3, 3, horas, feitas)

def test_expandir_slots_respeita_dia_da_semana_e_intervalo():
    slots = scheduling.expandir_slots([Bloco(0, 600, 720)], HOJE, date(2026, 11, 30))
    assert [s.data for s in slots] == [date(2026, 11, 16), date(2026, 11, 23), date(2026, 11, 30)]

def test_expandir_slots_descarta_trecho_ja_passado_de_hoje():
    slots = scheduling.expandir_slots([Bloco(0, 600, 720)], HOJE, HOJE, agora_min=660)
    assert (slots[0].inicio, slots[0].fim) == (660, 720)
    assert scheduling.expandir_slots([Bloco(0, 600, 720)], HOJE, HOJE, agora_min=720) == []

def test_alocar_nao_ultrapassa_prazo_nem_teto_diario():
    slots = scheduling.expandir_slots(NOITE, HOJE, date(2026, 11, 20))
    sessoes = scheduling.alocar([t(1, 4, 6.0)], slots, Parametros(max_bloco_min=60))
    assert all(s.data <= date(2026, 11, 20) for s in sessoes)
    assert all(s.minutos <= 60 for s in sessoes)
    assert sum(s.minutos for s in sessoes) == 300  # 5 dias x 60 min: o restante não cabe

def test_alocar_cobre_tarefa_quando_ha_capacidade():
    slots = scheduling.expandir_slots(NOITE, HOJE, date(2026, 11, 22))
    sessoes = scheduling.alocar([t(1, 6, 5.0)], slots, Parametros())
    assert sum(s.minutos for s in sessoes) == 300

def test_alocar_desconta_horas_concluidas():
    slots = scheduling.expandir_slots(NOITE, HOJE, date(2026, 11, 22))
    sessoes = scheduling.alocar([t(1, 6, 5.0, feitas=3.0)], slots, Parametros())
    assert sum(s.minutos for s in sessoes) == 120

def test_estrategia_prazo_ignora_ordem_do_ranking():
    slots = scheduling.expandir_slots(NOITE, HOJE, date(2026, 11, 22))
    grande, curta = t(1, 6, 10.0), t(2, 1, 2.0)
    por_ranking = scheduling.alocar([grande, curta], slots, Parametros("prioridade"))
    por_prazo = scheduling.alocar([grande, curta], slots, Parametros("prazo"))
    assert sum(s.minutos for s in por_ranking if s.tarefa_id == 2) < 120
    assert sum(s.minutos for s in por_prazo if s.tarefa_id == 2) == 120

def test_alocacao_nunca_sobrepoe_sessoes():
    slots = scheduling.expandir_slots(NOITE, HOJE, date(2026, 11, 25))
    sessoes = scheduling.alocar([t(1, 9, 6.0), t(2, 5, 4.0), t(3, 3, 3.0)], slots, Parametros("prazo"))
    assert not [p for p in validation.validar(sessoes, [t(1, 9, 6.0), t(2, 5, 4.0), t(3, 3, 3.0)], slots, HOJE)
                if p.tipo == validation.SOBREPOSICAO]

# ---- verificador: precisa detectar planos inválidos que o planejador não produziria ----

def _slots():
    return scheduling.expandir_slots(NOITE, HOJE, date(2026, 11, 20))

def test_validar_detecta_sobreposicao():
    sessoes = [SessaoPlanejada(1, HOJE, 1140, 1200), SessaoPlanejada(2, HOJE, 1170, 1230)]
    tipos = {p.tipo for p in validation.validar(sessoes, [t(1, 4, 1.0), t(2, 4, 1.0)], _slots(), HOJE)}
    assert validation.SOBREPOSICAO in tipos

def test_validar_detecta_sessao_fora_da_disponibilidade_apos_prazo_e_no_passado():
    fora = SessaoPlanejada(1, HOJE, 600, 660)
    depois = SessaoPlanejada(1, date(2026, 11, 20), 1140, 1200)
    tipos = {p.tipo for p in validation.validar([fora, depois], [t(1, 1, 2.0)], _slots(), HOJE)}
    assert {validation.FORA_DA_DISPONIBILIDADE, validation.APOS_PRAZO} <= tipos
    passado = SessaoPlanejada(1, date(2026, 11, 15), 1140, 1200)
    assert validation.NO_PASSADO in {p.tipo for p in validation.validar([passado], [t(1, 4, 1.0)], _slots(), HOJE)}

def test_validar_detecta_horas_excedentes():
    sessoes = [SessaoPlanejada(1, HOJE, 1140, 1260)]
    tipos = {p.tipo for p in validation.validar(sessoes, [t(1, 4, 1.0)], _slots(), HOJE)}
    assert validation.HORAS_EXCEDENTES in tipos

def test_validar_classifica_inviavel_sobrecarga_e_cobertura():
    slots = _slots()
    inviavel = validation.validar([], [t(1, 0, 5.0)], slots, HOJE)[0]
    assert (inviavel.tipo, inviavel.corrigivel) == (validation.INVIAVEL, False)
    sobrecarga = validation.validar([], [t(1, 1, 3.0), t(2, 1, 3.0)], slots, HOJE)
    assert {p.tipo for p in sobrecarga} == {validation.SOBRECARGA}
    cobertura = validation.validar([], [t(1, 4, 2.0)], slots, HOJE)[0]
    assert (cobertura.tipo, cobertura.corrigivel) == (validation.COBERTURA_INCOMPLETA, True)
