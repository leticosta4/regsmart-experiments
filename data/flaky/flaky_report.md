# Flaky runner — relatório

## Custo

- Início: `2026-10-01T00:45:46.995498+00:00`
- Fim: `2026-10-01T00:45:47.428240+00:00`
- Wall-clock do processo: **0m00s**
- Janela real dos runs (1º dispatch → última conclusão): **20m25s**
- Minutos de runner somados: **37.9 min**
- Pico de concorrência medido: **2** jobs
- Teto configurado: 20 slots

## API / rate limit

- Requisições: 5 GET, 0 POST
- Retries: 0
- Rate limit (final): 247/5000 consumidos, reseta em `2026-10-01T01:22:33+00:00`

## Saúde da execução

| Métrica | Valor |
|---|---|
| Repetições pedidas | 120 |
| Repetições despachadas | 2 |
| Com run_id localizado | 2 |
| Sem run_id localizado | 0 |
| Concluídas com sucesso | 2 |
| Concluídas com falha | 0 |
| Canceladas | 0 |
| Ainda em andamento | 0 |
| Jobs executados (com timestamps) | 2 |

## Por repositório

| repo | reps | success | failure | cancelled | em andamento | makespan | min runner |
|---|---|---|---|---|---|---|---|
| dask | 10 | 2 | 0 | 0 | 0 | 20m25s | 37.9 |

## Testes flaky

_Análise de logs ainda não rodada. Use `flaky_runner.py flaky`._
