# FLUXO — Endpoints principais e como testar

Guia rápido para usar e validar o sistema. A arquitetura completa está no [README](README.md).

## Visão geral do fluxo

```
cadastrar dados ──► POST /planos ──► GET /planos/{id}/trace ──► aprovar ou rejeitar
(disciplina,         agentes geram     o que cada agente       decisão humana
 disponibilidade,    uma PROPOSTA      decidiu
 tarefas)
```

Os agentes só **propõem**. Nada vira definitivo sem aprovação humana, e eles nunca alteram
tarefas nem disponibilidade.

## Endpoints principais

Documentação interativa: **http://localhost:8000/docs**

### Planos (o núcleo do sistema)

| Método | Rota | O que faz |
|---|---|---|
| `POST` | `/planos` | Executa os agentes e salva uma **proposta** de plano |
| `GET` | `/planos` | Lista os planos (mais recentes primeiro) |
| `GET` | `/planos/{id}` | Detalha: ordem de prioridade, problemas, revisões e sessões |
| `GET` | `/planos/{id}/trace` | Eventos de cada agente, em ordem, com duração |
| `POST` | `/planos/{id}/aprovar` | Aprova a proposta. Corpo opcional: `{"confirmar_riscos": true}` |
| `POST` | `/planos/{id}/rejeitar` | Rejeita a proposta. Corpo opcional: `{"motivo": "..."}` |

**Status do plano:** `proposta` → `aprovada` ou `rejeitada`. Um plano `aprovada` vira
`substituida` quando outro é aprovado.

### Dados de entrada

| Método | Rota | O que faz |
|---|---|---|
| `POST` | `/disciplinas` | Cria disciplina (`nome`, `dificuldade` 1–5) |
| `GET` | `/disciplinas` | Lista |
| `PATCH` · `DELETE` | `/disciplinas/{id}` | Edita / remove |
| `POST` | `/tarefas` | Cria tarefa (`disciplina_id`, `titulo`, `prazo`, `horas_estimadas`, `dificuldade`, `importancia`) |
| `GET` | `/tarefas?status=pendente&disciplina_id=1` | Lista, com filtros opcionais |
| `PATCH` · `DELETE` | `/tarefas/{id}` | Edita (inclui `horas_concluidas` e `status`) / remove |
| `POST` | `/disponibilidade` | Cria janela semanal (`dia_semana` 0=seg … 6=dom, `hora_inicio`, `hora_fim`) |
| `GET` · `DELETE` | `/disponibilidade`, `/disponibilidade/{id}` | Lista / remove |
| `GET` | `/prioridades` | Ranking só pela fórmula, sem agentes |
| `GET` | `/health` | Verificação de saúde |

## Como testar

### Opção A — Teste rápido com dados prontos

```bash
python -m data.seed --reset
uvicorn main:app --reload
```

Abra `/docs` e execute, nesta ordem:

1. `POST /planos` → gera a proposta.
2. `GET /planos/1/trace` → veja o que cada agente fez.
3. `POST /planos/1/aprovar` → deve retornar **422**: o seed tem uma tarefa propositalmente
   inviável, então é preciso confirmar o risco.
4. `POST /planos/1/aprovar` com `{"confirmar_riscos": true}` → **200**, status `aprovada`.

### Opção B — Cenário do zero (passo a passo)

Troque as datas de `prazo` por datas futuras. Exemplos em PowerShell:

```powershell
$api = "http://localhost:8000"
$json = @{ "Content-Type" = "application/json" }

# 1. disciplina
Invoke-RestMethod -Method Post "$api/disciplinas" -Headers $json `
  -Body '{"nome":"Calculo I","dificuldade":4}'

# 2. disponibilidade: segunda a domingo, 19h às 21h
0..6 | ForEach-Object {
  Invoke-RestMethod -Method Post "$api/disponibilidade" -Headers $json `
    -Body (@{dia_semana=$_; hora_inicio="19:00"; hora_fim="21:00"} | ConvertTo-Json)
}

# 3. tarefas
Invoke-RestMethod -Method Post "$api/tarefas" -Headers $json `
  -Body '{"disciplina_id":1,"titulo":"Lista de limites","prazo":"2026-11-25","horas_estimadas":4}'

# 4. gerar o plano, ver o trace e aprovar
Invoke-RestMethod -Method Post "$api/planos"
Invoke-RestMethod "$api/planos/1/trace"
Invoke-RestMethod -Method Post "$api/planos/1/aprovar"
```

Em bash/curl:

```bash
curl -X POST localhost:8000/disciplinas -H "Content-Type: application/json" \
     -d '{"nome":"Calculo I","dificuldade":4}'
curl -X POST localhost:8000/disponibilidade -H "Content-Type: application/json" \
     -d '{"dia_semana":0,"hora_inicio":"19:00","hora_fim":"21:00"}'
curl -X POST localhost:8000/tarefas -H "Content-Type: application/json" \
     -d '{"disciplina_id":1,"titulo":"Lista de limites","prazo":"2026-11-25","horas_estimadas":4}'
curl -X POST localhost:8000/planos
curl localhost:8000/planos/1/trace
curl -X POST localhost:8000/planos/1/aprovar
```

### Cenários que vale exercitar

| Cenário | Como provocar | Resultado esperado |
|---|---|---|
| Plano sem problemas | Poucas tarefas, prazos folgados | `problemas: []`, `convergiu: true`; aprova direto |
| Tarefa inviável | Tarefa de 12 h com prazo amanhã | `inviaveis: [id]`; aprovar sem confirmação retorna **422** |
| Revisão que conserta | Tarefa grande e importante + tarefa curta com prazo próximo | `revisoes[0].acao = "usar_prazo"`; problemas caem a 0 |
| Sem tarefas pendentes | Banco sem tarefas | `POST /planos` retorna **422** |
| Sem disponibilidade | Nenhum bloco cadastrado | `POST /planos` retorna **422** |
| Aprovar duas vezes | Aprovar o mesmo plano de novo | **409** |
| Plano inexistente | `GET /planos/999` | **404** |

### Como ler a resposta de `POST /planos`

| Campo | Significado |
|---|---|
| `resumo.ordem` | Ranking final de prioridade, com justificativa |
| `resumo.problemas` | Diagnóstico: `inviavel`, `sobrecarga`, `cobertura_incompleta`… |
| `resumo.inviaveis` | Ids das tarefas que não cabem no tempo disponível |
| `resumo.revisoes` | Ajustes tentados. `origem`: `regra`, `llm` ou `fallback` |
| `resumo.convergiu` | `true` se não restou nenhum problema corrigível |
| `resumo.motivo_parada` | `aceito_pelo_avaliador` ou `limite_de_revisoes` |
| `usou_llm` | O LLM estava habilitado nessa geração |
| `sessoes` | Blocos de estudo propostos (data, hora, tarefa) |

### Como ler o trace

Cada evento tem `agente`, `etapa`, `duracao_ms` e `dados`:

| Etapa | Significado |
|---|---|
| `priorizar` | Ordem final entregue pelo priorizador |
| `ajuste_llm` | O LLM reordenou e a resposta passou nas guardrails (a ordem mudou de fato) |
| `llm_confirmou_ordem` | O LLM respondeu corretamente, mas devolveu a mesma ordem da fórmula |
| `fallback` | Resposta do LLM rejeitada ou erro; `dados.motivo` explica |
| `plano_gerado` | O planejador alocou sessões (estratégia e minutos) |
| `validar` | O verificador listou os problemas |
| `decisao` | O avaliador escolheu uma ação e informou a `origem` |
| `fim` | Resultado final do orquestrador |

## Testes automatizados

```bash
pytest -q                      # unitários, API, guardrails e integração dos evals
python -m evals.run            # cenários de avaliação, imprime PASSOU/FALHOU
python -m evals.run --salvar   # também grava evals/relatorio.md
```

## Testando com o LLM (Ollama)

1. Instale o Ollama (https://ollama.com/download) e reabra o terminal.
2. `ollama pull qwen2.5:3b`
3. No `.env`: `LLM_HABILITADO=true` e reinicie o `uvicorn`.
4. `POST /planos` e confira o trace: `ajuste_llm`, `llm_confirmou_ordem` e `decisao` com `origem: "llm"` mostram que o
   modelo foi usado; `fallback` mostra que a resposta foi rejeitada, com o motivo.

Se o Ollama estiver fora do ar, o plano continua sendo gerado com as regras e o trace registra
`fallback`.

## Solução de problemas

| Sintoma | Causa provável |
|---|---|
| `no such table: planos` | Banco antigo. Rode `python -m data.seed --reset` |
| `ollama` não reconhecido | Ollama não instalado, ou terminal não reaberto após instalar |
| Plano com `usou_llm: true` mas só `fallback` no trace | O modelo responde fora do formato esperado. Ajustar os prompts |
| `curl` no PowerShell dá erro de parâmetro | Use `curl.exe` ou `Invoke-RestMethod` |
