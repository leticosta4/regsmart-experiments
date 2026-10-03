# Flaky runner — relatório

## Custo

- Início: `2026-10-03T01:40:31.692547+00:00`
- Fim: `2026-10-03T03:34:20.549792+00:00`
- Tempo ativo do script: **1h32m25s**
- Janela real dos runs (1º dispatch → última conclusão): **1h53m05s** (inclui fila)
- Minutos de runner somados: **705.6 min**
- Pico de concorrência medido: **15** jobs (teto do plano Free: 20)

## API / rate limit

- Requisições: 568 GET, 28 POST/PATCH
- Retries: 0
- Rate limit (final): 518/5000 consumidos, reseta em `2026-10-03T04:08:09+00:00`

## Saúde da execução

| Métrica | Valor |
|---|---|
| Repetições pedidas | 120 |
| Repetições despachadas | 34 |
| Com run_id localizado | 34 |
| Sem run_id localizado | 0 |
| Concluídas com sucesso | 30 |
| Concluídas com falha | 2 |
| Canceladas | 2 |
| Ainda em andamento | 0 |
| Jobs executados (com timestamps) | 53 |

## Por repositório

| repo | reps | success | failure | cancelled | em andamento | makespan | min runner |
|---|---|---|---|---|---|---|---|
| aeon | 10 | 4 | 1 | 0 | 0 | 48m34s | 279.2 |
| apscheduler | 10 | 4 | 1 | 0 | 0 | 3m17s | 14.1 |
| dask | 10 | 5 | 0 | 0 | 0 | 27m06s | 109.0 |
| ipython | 10 | 4 | 0 | 0 | 0 | 4m19s | 28.0 |
| librosa | 10 | 5 | 0 | 0 | 0 | 6m08s | 28.6 |
| pytorch-lightning | 10 | 3 | 0 | 2 | 0 | 56m54s | 219.0 |
| trimesh | 10 | 5 | 0 | 0 | 0 | 6m32s | 27.6 |

## Testes flaky

| repo | testes | flaky | taxa |
|---|---|---|---|
| aeon | 34924 | 1 | 0.0% |
| apscheduler | 885 | 1 | 0.1% |
| dask | 17237 | 0 | 0.0% |
| ipython | 5568 | 0 | 0.0% |
| librosa | 10877 | 0 | 0.0% |
| pytorch-lightning | 6634 | 0 | 0.0% |
| trimesh | 754 | 0 | 0.0% |

### aeon

| teste | reps | falhou | passou |
|---|---|---|---|
| `aeon/testing/tests/test_all_estimators.py::test_all_estimators[check_non_state_changing_method(estimator=HIVECOTEV2(arsenal_params={'n_estimators':1,'n_kernels':5},drcif_params={'att_subsample_size':2,'n_estimators':1,'n_intervals':2},stc_params={'batch_size':5,'estimator':RandomForestClassifier(n_estimators=1),'max_shapelets':5,'n_shapelet_samples':5},tde_params={'max_ensemble_size':1,'n_parameter_samples':1,'randomly_selected_params':1}),datatype=EqualLengthUnivariate-Classification-numpy3D)] [pytest (ubuntu-24.04, 3.12)]` | 5 | 1 | 4 |

### apscheduler

| teste | reps | falhou | passou |
|---|---|---|---|
| `   apscheduler._schedulers.async_:async_.py:914 Scheduler crashed [test-linux (3.12)]` | 5 | 1 | 4 |

## Canceladas (investigar)

| repo | rep | ref | run_id |
|---|---|---|---|
| pytorch-lightning | r01 | `flaky-r01` | 37090412619 |
| pytorch-lightning | r05 | `flaky-r05` | 37090421900 |

