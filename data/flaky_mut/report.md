# Flaky runner — relatório

## Custo

- Início: `2026-11-05T21:52:24.846302+00:00`
- Fim: `2026-11-06T00:02:53.421274+00:00`
- Tempo ativo do script: **1h19m41s**
- Janela real dos runs (1º dispatch → última conclusão): **2h10m03s** (inclui fila)
- Minutos de runner somados: **1288.6 min**
- Pico de concorrência medido: **40** jobs (teto do plano Free: 20)

## API / rate limit

- Requisições: 405 GET, 246 POST
- Retries: 20
- Rate limit (final): 10/5000 consumidos, reseta em `2026-11-06T02:57:12+00:00`

## Saúde da execução

| Métrica | warm-up | repetições |
|---|---|---|
| Tarefas no plano | 24 | 144 |
| Despachadas | 24 | 144 |
| Com run_id | 24 | 144 |
| Sucesso | 4 | 24 |
| Falha (testes falharam) | 20 | 120 |
| Canceladas | 0 | 0 |
| Em andamento | 0 | 0 |
| Dispatch falhou / run perdido | 0 | 0 |
| SHA do run ≠ SHA do mutante | 0 | 0 |
| Rep sem warm-up concluído | 0 | 0 |

## Por repositório

| repo | runs | success | failure | cancelled | em andamento | makespan | min runner |
|---|---|---|---|---|---|---|---|
| apscheduler | 84 | 14 | 70 | 0 | 0 | 1h30m20s | 452.9 |
| librosa | 84 | 14 | 70 | 0 | 0 | 1h55m03s | 835.7 |

## Por workflow

| workflow | runs | min runner |
|---|---|---|
| baseline | 36 | 135.9 |
| ranking | 48 | 718.7 |
| regsmart | 48 | 345.1 |
| regsmart-no-rank | 36 | 89.0 |

## Testes flaky

Cada teste que falhou é classificado comparando o **baseline** com os workflows de plugin, no mesmo SHA do mutante. Células = falhas/execuções (do job que mais falhou).

| classe | significado |
|---|---|
| ambiente (controle) | também falha na branch default sem mutante (`run --control`): ambiente ou falha pré-existente, não é efeito do mutante |
| flaky | falha em algumas execuções do baseline e passa em outras |
| só no plugin (flaky) | baseline nunca falhou; falha às vezes sob plugin (provável dependência de ordem exposta pelo reordenamento) |
| só no plugin (fixa) | baseline nunca falhou; falha em todas as execuções de algum plugin (investigar o plugin) |
| esperada, diverge | falha sempre no baseline, mas não em todos os workflows (RTS não selecionou ou a ordem mudou o resultado) |
| esperada | falha sempre em todos os workflows: efeito do mutante (ou falha pré-existente); só contada |
| indeterminado / sem baseline | poucas execuções ou baseline ausente |

### Resumo

| repo | mutante | ambiente | flaky | só plugin (flaky) | só plugin (fixa) | esperada, diverge | esperada | outros |
|---|---|---|---|---|---|---|---|---|
| apscheduler | apscheduler-m0316 | 0 | 0 | 0 | 0 | 0 | 295 | 0 |
| apscheduler | apscheduler-m0753 | 0 | 0 | 0 | 0 | 0 | 238 | 0 |
| apscheduler | apscheduler-m1399 | 0 | 0 | 0 | 0 | 0 | 4 | 0 |
| apscheduler | apscheduler-m2144 | 0 | 0 | 0 | 0 | 0 | 3 | 0 |
| apscheduler | apscheduler-m2213 | 0 | 0 | 0 | 0 | 0 | 6 | 0 |
| apscheduler | control | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| librosa | control | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| librosa | librosa-m0035 | 0 | 0 | 0 | 0 | 0 | 149 | 0 |
| librosa | librosa-m0265 | 0 | 0 | 0 | 0 | 0 | 486 | 0 |
| librosa | librosa-m2885 | 0 | 0 | 0 | 0 | 0 | 566 | 0 |
| librosa | librosa-m4950 | 0 | 0 | 0 | 0 | 0 | 15 | 0 |
| librosa | librosa-m7678 | 0 | 0 | 0 | 0 | 0 | 736 | 0 |

