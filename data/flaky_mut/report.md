# Flaky runner — relatório

## Custo

- Início: `2026-11-05T21:52:24.846302+00:00`
- Fim: `2026-11-07T18:41:41.259429+00:00`
- Tempo ativo do script: **10h18m08s**
- Janela real dos runs (1º dispatch → última conclusão): **44h48m45s** (inclui fila)
- Minutos de runner somados: **14313.8 min**
- Pico de concorrência medido: **40** jobs (teto do plano Free: 20)

## API / rate limit

- Requisições: 2156 GET, 1037 POST
- Retries: 44
- Rate limit (final): 35/5000 consumidos, reseta em `2026-11-07T19:25:39+00:00`

## Saúde da execução

| Métrica | warm-up | repetições |
|---|---|---|
| Tarefas no plano | 120 | 720 |
| Despachadas | 120 | 720 |
| Com run_id | 120 | 720 |
| Sucesso | 17 | 94 |
| Falha (testes falharam) | 103 | 626 |
| Canceladas | 0 | 0 |
| Em andamento | 0 | 0 |
| Dispatch falhou / run perdido | 0 | 0 |
| SHA do run ≠ SHA do mutante | 0 | 0 |
| Rep sem warm-up concluído | 0 | 0 |

## Por repositório

| repo | runs | success | failure | cancelled | em andamento | makespan | min runner |
|---|---|---|---|---|---|---|---|
| aeon | 84 | 0 | 84 | 0 | 0 | 4h42m37s | 10172.6 |
| apscheduler | 84 | 14 | 70 | 0 | 0 | 1h30m20s | 452.9 |
| dask | 84 | 12 | 72 | 0 | 0 | 2h30m43s | 4246.2 |
| dvc | 84 | 14 | 70 | 0 | 0 | 53m30s | 922.5 |
| ipython | 84 | 8 | 76 | 0 | 0 | 32m32s | 717.4 |
| librosa | 84 | 14 | 70 | 0 | 0 | 1h55m03s | 835.7 |
| networkx | 84 | 14 | 70 | 0 | 0 | 12m22s | 314.5 |
| pytest-django | 84 | 14 | 70 | 0 | 0 | 14m42s | 381.8 |
| pytest-xdist | 84 | 0 | 84 | 0 | 0 | 12m14s | 306.5 |
| pytorch-lightning | 84 | 14 | 70 | 0 | 0 | 3h16m18s | 3583.0 |
| trimesh | 84 | 21 | 63 | 0 | 0 | 9h14m34s | 886.7 |
| ultralytics | 84 | 0 | 84 | 0 | 0 | 1h10m18s | 1981.0 |

## Por workflow

| workflow | runs | min runner |
|---|---|---|
| baseline | 180 | 1328.5 |
| ranking | 240 | 7136.6 |
| regsmart | 240 | 4699.5 |
| regsmart-no-rank | 180 | 1149.2 |

## Testes flaky

Cada teste que falhou é classificado comparando o **baseline** com os workflows de plugin, no mesmo SHA do mutante. Células = falhas/execuções (do job que mais falhou).

| classe | significado |
|---|---|
| ambiente (controle) | também falha no baseline da branch default sem mutante (`run --control`): ambiente ou falha pré-existente, não é efeito do mutante |
| dependente de ordem (controle) | na branch default sem mutante, falha só sob plugin (nunca no baseline): dependência de ordem exposta pelo reordenamento, não é efeito do mutante nem do ambiente |
| flaky | falha em algumas execuções do baseline e passa em outras |
| só no plugin (flaky) | baseline nunca falhou; falha às vezes sob plugin (provável dependência de ordem exposta pelo reordenamento) |
| só no plugin (fixa) | baseline nunca falhou; falha em todas as execuções de algum plugin (investigar o plugin) |
| esperada, diverge | falha sempre no baseline, mas não em todos os workflows (RTS não selecionou ou a ordem mudou o resultado) |
| esperada | falha sempre em todos os workflows: efeito do mutante (ou falha pré-existente); só contada |
| indeterminado / sem baseline | poucas execuções ou baseline ausente |

### Resumo

| repo | mutante | ambiente | dep. ordem (controle) | flaky | só plugin (flaky) | só plugin (fixa) | esperada, diverge | esperada | outros |
|---|---|---|---|---|---|---|---|---|---|
| aeon | aeon-m22318 | 2 | 0 | 0 | 0 | 0 | 0 | 86 | 0 |
| aeon | aeon-m24470 | 2 | 0 | 15 | 2 | 0 | 2 | 44 | 0 |
| aeon | aeon-m30584 | 2 | 0 | 0 | 0 | 0 | 0 | 16 | 0 |
| aeon | aeon-m6601 | 2 | 0 | 0 | 0 | 0 | 0 | 11 | 0 |
| aeon | aeon-m6969 | 2 | 0 | 2 | 0 | 0 | 73 | 891 | 0 |
| aeon | control | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 |
| apscheduler | apscheduler-m0316 | 0 | 0 | 0 | 0 | 0 | 0 | 295 | 0 |
| apscheduler | apscheduler-m0753 | 0 | 0 | 0 | 0 | 0 | 0 | 238 | 0 |
| apscheduler | apscheduler-m1399 | 0 | 0 | 0 | 0 | 0 | 0 | 4 | 0 |
| apscheduler | apscheduler-m2144 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 0 |
| apscheduler | apscheduler-m2213 | 0 | 0 | 0 | 0 | 0 | 0 | 6 | 0 |
| apscheduler | control | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| dask | control | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 |
| dask | dask-m11282 | 0 | 0 | 0 | 0 | 0 | 0 | 16 | 0 |
| dask | dask-m12753 | 0 | 0 | 0 | 0 | 0 | 0 | 9 | 0 |
| dask | dask-m1940 | 0 | 0 | 0 | 0 | 0 | 0 | 24 | 0 |
| dask | dask-m28832 | 0 | 0 | 0 | 0 | 0 | 0 | 15 | 0 |
| dask | dask-m37146 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 |
| dvc | control | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| dvc | dvc-m11576 | 0 | 0 | 0 | 32 | 0 | 0 | 1 | 0 |
| dvc | dvc-m12545 | 0 | 0 | 0 | 0 | 0 | 0 | 177 | 0 |
| dvc | dvc-m16845 | 0 | 0 | 0 | 0 | 0 | 0 | 4 | 0 |
| dvc | dvc-m19066 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| dvc | dvc-m6852 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 0 |
| ipython | control | 0 | 0 | 0 | 42 | 1 | 0 | 0 | 0 |
| ipython | ipython-m1288 | 0 | 42 | 0 | 10 | 0 | 0 | 1 | 0 |
| ipython | ipython-m17283 | 0 | 43 | 0 | 29 | 0 | 2 | 32 | 0 |
| ipython | ipython-m22324 | 0 | 39 | 0 | 6 | 0 | 0 | 1 | 0 |
| ipython | ipython-m22732 | 0 | 41 | 0 | 6 | 0 | 0 | 1 | 0 |
| ipython | ipython-m4267 | 0 | 41 | 0 | 3 | 0 | 0 | 1 | 0 |
| librosa | control | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| librosa | librosa-m0035 | 0 | 0 | 0 | 0 | 0 | 0 | 149 | 0 |
| librosa | librosa-m0265 | 0 | 0 | 0 | 0 | 0 | 0 | 486 | 0 |
| librosa | librosa-m2885 | 0 | 0 | 0 | 0 | 0 | 0 | 566 | 0 |
| librosa | librosa-m4950 | 0 | 0 | 0 | 0 | 0 | 0 | 15 | 0 |
| librosa | librosa-m7678 | 0 | 0 | 0 | 0 | 0 | 0 | 736 | 0 |
| networkx | control | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| networkx | networkx-m1096 | 0 | 0 | 0 | 0 | 0 | 2 | 9 | 0 |
| networkx | networkx-m14277 | 0 | 0 | 0 | 0 | 0 | 1 | 346 | 0 |
| networkx | networkx-m17565 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 |
| networkx | networkx-m25405 | 0 | 0 | 0 | 0 | 0 | 4 | 19 | 0 |
| networkx | networkx-m6449 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 0 |
| pytest-django | control | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| pytest-django | pytest-django-m0049 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 0 |
| pytest-django | pytest-django-m0192 | 0 | 0 | 0 | 0 | 0 | 0 | 4 | 0 |
| pytest-django | pytest-django-m0376 | 0 | 0 | 0 | 0 | 0 | 0 | 5 | 0 |
| pytest-django | pytest-django-m0491 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 |
| pytest-django | pytest-django-m0604 | 0 | 0 | 0 | 0 | 0 | 0 | 6 | 0 |
| pytest-xdist | control | 0 | 0 | 0 | 1 | 8 | 0 | 5 | 0 |
| pytest-xdist | pytest-xdist-m0722 | 5 | 9 | 0 | 1 | 0 | 1 | 1 | 0 |
| pytest-xdist | pytest-xdist-m1049 | 5 | 9 | 0 | 0 | 0 | 2 | 69 | 0 |
| pytest-xdist | pytest-xdist-m1214 | 5 | 9 | 0 | 1 | 0 | 0 | 1 | 0 |
| pytest-xdist | pytest-xdist-m1461 | 5 | 9 | 0 | 1 | 0 | 0 | 8 | 0 |
| pytest-xdist | pytest-xdist-m1537 | 5 | 9 | 0 | 1 | 0 | 0 | 2 | 0 |
| pytorch-lightning | control | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| pytorch-lightning | pytorch-lightning-m0766 | 0 | 0 | 0 | 0 | 0 | 0 | 6 | 0 |
| pytorch-lightning | pytorch-lightning-m14490 | 0 | 0 | 0 | 1 | 0 | 0 | 2 | 0 |
| pytorch-lightning | pytorch-lightning-m15854 | 0 | 0 | 0 | 0 | 0 | 0 | 7 | 0 |
| pytorch-lightning | pytorch-lightning-m20410 | 0 | 0 | 0 | 1 | 0 | 0 | 6 | 0 |
| pytorch-lightning | pytorch-lightning-m9476 | 0 | 0 | 0 | 1 | 0 | 0 | 10 | 0 |
| trimesh | control | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| trimesh | trimesh-extra | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| trimesh | trimesh-m13478 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| trimesh | trimesh-m21160 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 |
| trimesh | trimesh-m25103 | 0 | 0 | 0 | 0 | 0 | 6 | 1 | 0 |
| trimesh | trimesh-m3147 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 |
| ultralytics | control | 0 | 0 | 0 | 0 | 0 | 0 | 4 | 0 |
| ultralytics | ultralytics-m23817 | 4 | 0 | 0 | 0 | 0 | 11 | 38 | 0 |
| ultralytics | ultralytics-m2383 | 4 | 0 | 0 | 0 | 0 | 33 | 129 | 0 |
| ultralytics | ultralytics-m34570 | 4 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| ultralytics | ultralytics-m36889 | 4 | 0 | 0 | 0 | 0 | 0 | 2 | 0 |
| ultralytics | ultralytics-m5380 | 4 | 0 | 0 | 0 | 0 | 2 | 4 | 0 |

### Só no plugin: em quais workflows falhou

Testes que nunca falharam no baseline (flaky + fixa), cada um contado uma vez, na combinação exata de workflows em que falhou. `ranking+regsmart` = falhou nos dois.

| repo | mutante | ranking | regsmart | ranking+regsmart | ranking+regsmart+regsmart-no-rank | total |
|---|---|---|---|---|---|---|
| aeon | aeon-m22318 | 0 | 0 | 0 | 0 | 0 |
| aeon | aeon-m24470 | 2 | 0 | 0 | 0 | 2 |
| aeon | aeon-m30584 | 0 | 0 | 0 | 0 | 0 |
| aeon | aeon-m6601 | 0 | 0 | 0 | 0 | 0 |
| aeon | aeon-m6969 | 0 | 0 | 0 | 0 | 0 |
| aeon | control | 0 | 0 | 0 | 0 | 0 |
| apscheduler | apscheduler-m0316 | 0 | 0 | 0 | 0 | 0 |
| apscheduler | apscheduler-m0753 | 0 | 0 | 0 | 0 | 0 |
| apscheduler | apscheduler-m1399 | 0 | 0 | 0 | 0 | 0 |
| apscheduler | apscheduler-m2144 | 0 | 0 | 0 | 0 | 0 |
| apscheduler | apscheduler-m2213 | 0 | 0 | 0 | 0 | 0 |
| apscheduler | control | 0 | 0 | 0 | 0 | 0 |
| dask | control | 2 | 0 | 0 | 0 | 2 |
| dask | dask-m11282 | 0 | 0 | 0 | 0 | 0 |
| dask | dask-m12753 | 0 | 0 | 0 | 0 | 0 |
| dask | dask-m1940 | 0 | 0 | 0 | 0 | 0 |
| dask | dask-m28832 | 0 | 0 | 0 | 0 | 0 |
| dask | dask-m37146 | 0 | 0 | 0 | 0 | 0 |
| dvc | control | 0 | 0 | 0 | 0 | 0 |
| dvc | dvc-m11576 | 32 | 0 | 0 | 0 | 32 |
| dvc | dvc-m12545 | 0 | 0 | 0 | 0 | 0 |
| dvc | dvc-m16845 | 0 | 0 | 0 | 0 | 0 |
| dvc | dvc-m19066 | 0 | 0 | 0 | 0 | 0 |
| dvc | dvc-m6852 | 0 | 0 | 0 | 0 | 0 |
| ipython | control | 4 | 1 | 38 | 0 | 43 |
| ipython | ipython-m1288 | 6 | 3 | 1 | 0 | 10 |
| ipython | ipython-m17283 | 12 | 5 | 12 | 0 | 29 |
| ipython | ipython-m22324 | 0 | 5 | 1 | 0 | 6 |
| ipython | ipython-m22732 | 4 | 1 | 1 | 0 | 6 |
| ipython | ipython-m4267 | 3 | 0 | 0 | 0 | 3 |
| librosa | control | 0 | 0 | 0 | 0 | 0 |
| librosa | librosa-m0035 | 0 | 0 | 0 | 0 | 0 |
| librosa | librosa-m0265 | 0 | 0 | 0 | 0 | 0 |
| librosa | librosa-m2885 | 0 | 0 | 0 | 0 | 0 |
| librosa | librosa-m4950 | 0 | 0 | 0 | 0 | 0 |
| librosa | librosa-m7678 | 0 | 0 | 0 | 0 | 0 |
| networkx | control | 0 | 0 | 0 | 0 | 0 |
| networkx | networkx-m1096 | 0 | 0 | 0 | 0 | 0 |
| networkx | networkx-m14277 | 0 | 0 | 0 | 0 | 0 |
| networkx | networkx-m17565 | 0 | 0 | 0 | 0 | 0 |
| networkx | networkx-m25405 | 0 | 0 | 0 | 0 | 0 |
| networkx | networkx-m6449 | 0 | 0 | 0 | 0 | 0 |
| pytest-django | control | 0 | 0 | 0 | 0 | 0 |
| pytest-django | pytest-django-m0049 | 0 | 0 | 0 | 0 | 0 |
| pytest-django | pytest-django-m0192 | 0 | 0 | 0 | 0 | 0 |
| pytest-django | pytest-django-m0376 | 0 | 0 | 0 | 0 | 0 |
| pytest-django | pytest-django-m0491 | 0 | 0 | 0 | 0 | 0 |
| pytest-django | pytest-django-m0604 | 0 | 0 | 0 | 0 | 0 |
| pytest-xdist | control | 0 | 1 | 0 | 8 | 9 |
| pytest-xdist | pytest-xdist-m0722 | 1 | 0 | 0 | 0 | 1 |
| pytest-xdist | pytest-xdist-m1049 | 0 | 0 | 0 | 0 | 0 |
| pytest-xdist | pytest-xdist-m1214 | 0 | 0 | 1 | 0 | 1 |
| pytest-xdist | pytest-xdist-m1461 | 0 | 0 | 1 | 0 | 1 |
| pytest-xdist | pytest-xdist-m1537 | 0 | 1 | 0 | 0 | 1 |
| pytorch-lightning | control | 0 | 0 | 0 | 0 | 0 |
| pytorch-lightning | pytorch-lightning-m0766 | 0 | 0 | 0 | 0 | 0 |
| pytorch-lightning | pytorch-lightning-m14490 | 1 | 0 | 0 | 0 | 1 |
| pytorch-lightning | pytorch-lightning-m15854 | 0 | 0 | 0 | 0 | 0 |
| pytorch-lightning | pytorch-lightning-m20410 | 0 | 1 | 0 | 0 | 1 |
| pytorch-lightning | pytorch-lightning-m9476 | 0 | 0 | 1 | 0 | 1 |
| trimesh | control | 0 | 0 | 0 | 0 | 0 |
| trimesh | trimesh-extra | 0 | 0 | 0 | 0 | 0 |
| trimesh | trimesh-m13478 | 0 | 0 | 0 | 0 | 0 |
| trimesh | trimesh-m21160 | 0 | 0 | 0 | 0 | 0 |
| trimesh | trimesh-m25103 | 0 | 0 | 0 | 0 | 0 |
| trimesh | trimesh-m3147 | 0 | 0 | 0 | 0 | 0 |
| ultralytics | control | 0 | 0 | 0 | 0 | 0 |
| ultralytics | ultralytics-m23817 | 0 | 0 | 0 | 0 | 0 |
| ultralytics | ultralytics-m2383 | 0 | 0 | 0 | 0 | 0 |
| ultralytics | ultralytics-m34570 | 0 | 0 | 0 | 0 | 0 |
| ultralytics | ultralytics-m36889 | 0 | 0 | 0 | 0 | 0 |
| ultralytics | ultralytics-m5380 | 0 | 0 | 0 | 0 | 0 |

### aeon

#### aeon-m22318

| teste | baseline | ranking | regsmart | regsmart-no-rank | classe |
|---|---|---|---|---|---|
| `aeon/transformations/collection/feature_based/tests/test_catch22.py::test_catch22_wrapper_on_basic_motions` | 3/3 | 9/9 | 0/9 | 0/3 | ambiente (controle) |
| `aeon/transformations/collection/feature_based/tests/test_catch22_optimisations.py::test_matches_pycatch22_reference_on_scale_invariant_features` | 3/3 | 9/9 | 0/9 | 0/3 | ambiente (controle) |

#### aeon-m24470

| teste | baseline | ranking | regsmart | regsmart-no-rank | classe |
|---|---|---|---|---|---|
| `aeon/transformations/collection/feature_based/tests/test_catch22.py::test_catch22_wrapper_on_basic_motions` | 3/3 | 9/9 | 9/9 | 3/3 | ambiente (controle) |
| `aeon/transformations/collection/feature_based/tests/test_catch22_optimisations.py::test_matches_pycatch22_reference_on_scale_invariant_features` | 3/3 | 9/9 | 9/9 | 3/3 | ambiente (controle) |
| `aeon/classification/distance_based/tests/test_proximity_tree.py::test_get_best_splitter` | 1/3 | 2/9 | 4/9 | 0/3 | flaky |
| `aeon/testing/tests/test_all_estimators.py::test_all_estimators[check_classifier_output(estimator=ProximityForest(max_depth=3,n_splitters=3,n_trees=3),datatype=EqualLengthMultivariate-Classification-np-list)]` | 3/3 | 7/9 | 8/9 | 2/3 | flaky |
| `aeon/testing/tests/test_all_estimators.py::test_all_estimators[check_classifier_output(estimator=ProximityForest(max_depth=3,n_splitters=3,n_trees=3),datatype=EqualLengthUnivariate-Classification-np-list)]` | 2/3 | 8/9 | 7/9 | 3/3 | flaky |
| `aeon/testing/tests/test_all_estimators.py::test_all_estimators[check_classifier_output(estimator=ProximityForest(max_depth=3,n_splitters=3,n_trees=3),datatype=EqualLengthUnivariate-Classification-numpy3D)]` | 2/3 | 5/9 | 7/9 | 3/3 | flaky |
| `aeon/testing/tests/test_all_estimators.py::test_all_estimators[check_classifier_output(estimator=ProximityForest(max_depth=3,n_splitters=3,n_trees=3),datatype=UnequalLengthMultivariate-Classification-np-list)]` | 2/3 | 7/9 | 8/9 | 3/3 | flaky |
| `aeon/testing/tests/test_all_estimators.py::test_all_estimators[check_classifier_output(estimator=ProximityForest(max_depth=3,n_splitters=3,n_trees=3),datatype=UnequalLengthUnivariate-Classification-np-list)]` | 3/3 | 9/9 | 8/9 | 2/3 | flaky |
| `aeon/testing/tests/test_all_estimators.py::test_all_estimators[check_classifier_output(estimator=ProximityTree(n_splitters=3),datatype=EqualLengthMultivariate-Classification-np-list)]` | 1/3 | 7/9 | 5/9 | 3/3 | flaky |
| `aeon/testing/tests/test_all_estimators.py::test_all_estimators[check_classifier_output(estimator=ProximityTree(n_splitters=3),datatype=EqualLengthMultivariate-Classification-numpy3D)]` | 1/3 | 4/9 | 4/9 | 2/3 | flaky |
| `aeon/testing/tests/test_all_estimators.py::test_all_estimators[check_classifier_output(estimator=ProximityTree(n_splitters=3),datatype=EqualLengthUnivariate-Classification-np-list)]` | 1/3 | 3/9 | 5/9 | 3/3 | flaky |
| `aeon/testing/tests/test_all_estimators.py::test_all_estimators[check_classifier_output(estimator=ProximityTree(n_splitters=3),datatype=EqualLengthUnivariate-Classification-numpy3D)]` | 1/3 | 5/9 | 3/9 | 2/3 | flaky |
| `aeon/testing/tests/test_all_estimators.py::test_all_estimators[check_classifier_output(estimator=ProximityTree(n_splitters=3),datatype=UnequalLengthMultivariate-Classification-np-list)]` | 3/3 | 4/9 | 3/9 | 2/3 | flaky |
| `aeon/testing/tests/test_all_estimators.py::test_all_estimators[check_classifier_output(estimator=ProximityTree(n_splitters=3),datatype=UnequalLengthUnivariate-Classification-np-list)]` | 2/3 | 6/9 | 4/9 | 1/3 | flaky |
| `aeon/testing/tests/test_all_estimators.py::test_all_estimators[check_fit_updates_state_and_cloning(estimator=ProximityTree(n_splitters=3),datatype=EqualLengthUnivariate-Classification-np-list)]` | 2/3 | 3/9 | 4/9 | 3/3 | flaky |
| `aeon/testing/tests/test_all_estimators.py::test_all_estimators[check_non_state_changing_method(estimator=ProximityForest(max_depth=3,n_splitters=3,n_trees=3),datatype=EqualLengthUnivariate-Classification-np-list)]` | 2/3 | 6/9 | 9/9 | 3/3 | flaky |
| `aeon/testing/tests/test_all_estimators.py::test_all_estimators[check_non_state_changing_method(estimator=ProximityTree(n_splitters=3),datatype=EqualLengthUnivariate-Classification-np-list)]` | 1/3 | 4/9 | 7/9 | 2/3 | flaky |
| `aeon/datasets/tests/test_data_loaders.py::test_load_classification_from_repo` | 0/3 | 1/9 | 0/9 | 0/3 | só no plugin (flaky) |
| `aeon/datasets/tests/test_data_loaders.py::test_load_regression_from_repo` | 0/3 | 1/9 | 0/9 | 0/3 | só no plugin (flaky) |
| `aeon/testing/tests/test_all_estimators.py::test_all_estimators[check_classifier_output(estimator=ProximityForest(max_depth=3,n_splitters=3,n_trees=3),datatype=EqualLengthMultivariate-Classification-numpy3D)]` | 3/3 | 9/9 | 7/9 | 3/3 | esperada, diverge |
| `aeon/testing/tests/test_all_estimators.py::test_all_estimators[check_fit_updates_state_and_cloning(estimator=ProximityForest(max_depth=3,n_splitters=3,n_trees=3),datatype=EqualLengthUnivariate-Classification-np-list)]` | 3/3 | 6/9 | 7/9 | 2/3 | esperada, diverge |

#### aeon-m30584

| teste | baseline | ranking | regsmart | regsmart-no-rank | classe |
|---|---|---|---|---|---|
| `aeon/transformations/collection/feature_based/tests/test_catch22.py::test_catch22_wrapper_on_basic_motions` | 3/3 | 9/9 | 0/9 | 0/3 | ambiente (controle) |
| `aeon/transformations/collection/feature_based/tests/test_catch22_optimisations.py::test_matches_pycatch22_reference_on_scale_invariant_features` | 3/3 | 9/9 | 0/9 | 0/3 | ambiente (controle) |

#### aeon-m6601

| teste | baseline | ranking | regsmart | regsmart-no-rank | classe |
|---|---|---|---|---|---|
| `aeon/transformations/collection/feature_based/tests/test_catch22.py::test_catch22_wrapper_on_basic_motions` | 3/3 | 9/9 | 9/9 | 3/3 | ambiente (controle) |
| `aeon/transformations/collection/feature_based/tests/test_catch22_optimisations.py::test_matches_pycatch22_reference_on_scale_invariant_features` | 3/3 | 9/9 | 9/9 | 3/3 | ambiente (controle) |

#### aeon-m6969

| teste | baseline | ranking | regsmart | regsmart-no-rank | classe |
|---|---|---|---|---|---|
| `aeon/transformations/collection/feature_based/tests/test_catch22.py::test_catch22_wrapper_on_basic_motions` | 3/3 | 9/9 | 9/9 | 3/3 | ambiente (controle) |
| `aeon/transformations/collection/feature_based/tests/test_catch22_optimisations.py::test_matches_pycatch22_reference_on_scale_invariant_features` | 3/3 | 9/9 | 9/9 | 3/3 | ambiente (controle) |
| `aeon/datasets/tests/test_data_loaders.py::test_load_classification_from_repo` | 1/3 | 1/9 | 0/9 | 0/3 | flaky |
| `aeon/datasets/tests/test_data_loaders.py::test_load_regression_from_repo` | 1/3 | 0/9 | 0/9 | 0/3 | flaky |
| `aeon/classification/deep_learning/tests/test_deep_classifier_base.py::test_dummy_deep_classifier` | 3/3 | 6/9 | 6/9 | 3/3 | esperada, diverge |
| `aeon/classification/deep_learning/tests/test_inception_time.py::test_save_load_inceptiontime` | 3/3 | 6/9 | 6/9 | 3/3 | esperada, diverge |
| `aeon/classification/deep_learning/tests/test_lite_time.py::test_save_load_litetim` | 3/3 | 6/9 | 6/9 | 3/3 | esperada, diverge |
| `aeon/testing/tests/test_all_estimators.py::test_all_estimators[check_classifier_output(estimator=DisjointCNNClassifier(batch_size=4,kernel_size=[2,2],metrics=['accuracy'],n_epochs=3,n_filters=2,n_layers=2,use_bias=False,use_mini_batch_size=True,verbose=True),datatype=EqualLengthMultivariate-Classification-numpy3D)]` | 3/3 | 6/9 | 6/9 | 3/3 | esperada, diverge |
| `aeon/testing/tests/test_all_estimators.py::test_all_estimators[check_classifier_output(estimator=DisjointCNNClassifier(batch_size=4,kernel_size=[2,2],metrics=['accuracy'],n_epochs=3,n_filters=2,n_layers=2,use_bias=False,use_mini_batch_size=True,verbose=True),datatype=EqualLengthUnivariate-Classification-numpy3D)]` | 3/3 | 6/9 | 6/9 | 3/3 | esperada, diverge |
| `aeon/testing/tests/test_all_estimators.py::test_all_estimators[check_classifier_output(estimator=DisjointCNNClassifier(batch_size=4,kernel_size=[2,2],n_epochs=3,n_filters=2,n_layers=2,use_bias=False),datatype=EqualLengthMultivariate-Classification-numpy3D)]` | 3/3 | 6/9 | 6/9 | 3/3 | esperada, diverge |
| `aeon/testing/tests/test_all_estimators.py::test_all_estimators[check_classifier_output(estimator=DisjointCNNClassifier(batch_size=4,kernel_size=[2,2],n_epochs=3,n_filters=2,n_layers=2,use_bias=False),datatype=EqualLengthUnivariate-Classification-numpy3D)]` | 3/3 | 6/9 | 6/9 | 3/3 | esperada, diverge |
| `aeon/testing/tests/test_all_estimators.py::test_all_estimators[check_classifier_output(estimator=EncoderClassifier(batch_size=4,dropout_proba=0,fc_units=8,n_epochs=8,strides=2,use_bias=False),datatype=EqualLengthMultivariate-Classification-numpy3D)]` | 3/3 | 6/9 | 6/9 | 3/3 | esperada, diverge |
| `aeon/testing/tests/test_all_estimators.py::test_all_estimators[check_classifier_output(estimator=EncoderClassifier(batch_size=4,dropout_proba=0,fc_units=8,n_epochs=8,strides=2,use_bias=False),datatype=EqualLengthUnivariate-Classification-numpy3D)]` | 3/3 | 6/9 | 6/9 | 3/3 | esperada, diverge |
| `aeon/testing/tests/test_all_estimators.py::test_all_estimators[check_classifier_output(estimator=FCNClassifier(batch_size=4,kernel_size=3,n_epochs=10,n_filters=4,n_layers=1,padding='valid',strides=2,use_bias=False),datatype=EqualLengthMultivariate-Classification-numpy3D)]` | 3/3 | 6/9 | 6/9 | 3/3 | esperada, diverge |
| `aeon/testing/tests/test_all_estimators.py::test_all_estimators[check_classifier_output(estimator=FCNClassifier(batch_size=4,kernel_size=3,n_epochs=10,n_filters=4,n_layers=1,padding='valid',strides=2,use_bias=False),datatype=EqualLengthUnivariate-Classification-numpy3D)]` | 3/3 | 6/9 | 6/9 | 3/3 | esperada, diverge |
| `aeon/testing/tests/test_all_estimators.py::test_all_estimators[check_classifier_output(estimator=InceptionTimeClassifier(batch_size=4,depth=1,kernel_size=4,n_classifiers=1,n_epochs=10,use_residual=False),datatype=EqualLengthMultivariate-Classification-numpy3D)]` | 3/3 | 6/9 | 6/9 | 3/3 | esperada, diverge |
| `aeon/testing/tests/test_all_estimators.py::test_all_estimators[check_classifier_output(estimator=InceptionTimeClassifier(batch_size=4,depth=1,kernel_size=4,n_classifiers=1,n_epochs=10,use_residual=False),datatype=EqualLengthUnivariate-Classification-numpy3D)]` | 3/3 | 6/9 | 6/9 | 3/3 | esperada, diverge |
| `aeon/testing/tests/test_all_estimators.py::test_all_estimators[check_classifier_output(estimator=IndividualInceptionClassifier(batch_size=4,depth=1,kernel_size=4,n_epochs=10,use_residual=False),datatype=EqualLengthMultivariate-Classification-numpy3D)]` | 3/3 | 6/9 | 6/9 | 3/3 | esperada, diverge |
| `aeon/testing/tests/test_all_estimators.py::test_all_estimators[check_classifier_output(estimator=IndividualInceptionClassifier(batch_size=4,depth=1,kernel_size=4,n_epochs=10,use_residual=False),datatype=EqualLengthUnivariate-Classification-numpy3D)]` | 3/3 | 6/9 | 6/9 | 3/3 | esperada, diverge |
| `aeon/testing/tests/test_all_estimators.py::test_all_estimators[check_classifier_output(estimator=IndividualLITEClassifier(batch_size=4,kernel_size=4,metrics=['accuracy'],n_epochs=2,use_litemv=True,use_mini_batch_size=True,verbose=True),datatype=EqualLengthMultivariate-Classification-numpy3D)]` | 3/3 | 6/9 | 6/9 | 3/3 | esperada, diverge |
| `aeon/testing/tests/test_all_estimators.py::test_all_estimators[check_classifier_output(estimator=IndividualLITEClassifier(batch_size=4,kernel_size=4,metrics=['accuracy'],n_epochs=2,use_litemv=True,use_mini_batch_size=True,verbose=True),datatype=EqualLengthUnivariate-Classification-numpy3D)]` | 3/3 | 6/9 | 6/9 | 3/3 | esperada, diverge |
| `aeon/testing/tests/test_all_estimators.py::test_all_estimators[check_classifier_output(estimator=IndividualLITEClassifier(batch_size=4,kernel_size=4,n_epochs=2),datatype=EqualLengthMultivariate-Classification-numpy3D)]` | 3/3 | 6/9 | 6/9 | 3/3 | esperada, diverge |
| `aeon/testing/tests/test_all_estimators.py::test_all_estimators[check_classifier_output(estimator=IndividualLITEClassifier(batch_size=4,kernel_size=4,n_epochs=2),datatype=EqualLengthUnivariate-Classification-numpy3D)]` | 3/3 | 6/9 | 6/9 | 3/3 | esperada, diverge |
| `aeon/testing/tests/test_all_estimators.py::test_all_estimators[check_classifier_output(estimator=LITETimeClassifier(batch_size=4,kernel_size=4,metrics=['accuracy'],n_classifiers=1,n_epochs=2,use_litemv=True,use_mini_batch_size=True,verbose=True),datatype=EqualLengthMultivariate-Classification-numpy3D)]` | 3/3 | 6/9 | 6/9 | 3/3 | esperada, diverge |
| `aeon/testing/tests/test_all_estimators.py::test_all_estimators[check_classifier_output(estimator=LITETimeClassifier(batch_size=4,kernel_size=4,metrics=['accuracy'],n_classifiers=1,n_epochs=2,use_litemv=True,use_mini_batch_size=True,verbose=True),datatype=EqualLengthUnivariate-Classification-numpy3D)]` | 3/3 | 6/9 | 6/9 | 3/3 | esperada, diverge |
| `aeon/testing/tests/test_all_estimators.py::test_all_estimators[check_classifier_output(estimator=LITETimeClassifier(batch_size=4,kernel_size=4,n_classifiers=1,n_epochs=2),datatype=EqualLengthMultivariate-Classification-numpy3D)]` | 3/3 | 6/9 | 6/9 | 3/3 | esperada, diverge |
| `aeon/testing/tests/test_all_estimators.py::test_all_estimators[check_classifier_output(estimator=LITETimeClassifier(batch_size=4,kernel_size=4,n_classifiers=1,n_epochs=2),datatype=EqualLengthUnivariate-Classification-numpy3D)]` | 3/3 | 6/9 | 6/9 | 3/3 | esperada, diverge |
| `aeon/testing/tests/test_all_estimators.py::test_all_estimators[check_classifier_output(estimator=MLPClassifier(batch_size=4,n_epochs=10,use_bias=False),datatype=EqualLengthMultivariate-Classification-numpy3D)]` | 3/3 | 6/9 | 6/9 | 3/3 | esperada, diverge |
| `aeon/testing/tests/test_all_estimators.py::test_all_estimators[check_classifier_output(estimator=MLPClassifier(batch_size=4,n_epochs=10,use_bias=False),datatype=EqualLengthUnivariate-Classification-numpy3D)]` | 3/3 | 6/9 | 6/9 | 3/3 | esperada, diverge |
| `aeon/testing/tests/test_all_estimators.py::test_all_estimators[check_classifier_output(estimator=ResNetClassifier(batch_size=4,kernel_size=3,n_conv_per_residual_block=1,n_epochs=10,n_filters=5,n_residual_blocks=1),datatype=EqualLengthMultivariate-Classification-numpy3D)]` | 3/3 | 6/9 | 6/9 | 3/3 | esperada, diverge |
| `aeon/testing/tests/test_all_estimators.py::test_all_estimators[check_classifier_output(estimator=ResNetClassifier(batch_size=4,kernel_size=3,n_conv_per_residual_block=1,n_epochs=10,n_filters=5,n_residual_blocks=1),datatype=EqualLengthUnivariate-Classification-numpy3D)]` | 3/3 | 6/9 | 6/9 | 3/3 | esperada, diverge |
| `aeon/testing/tests/test_all_estimators.py::test_all_estimators[check_classifier_output(estimator=TimeCNNClassifier(avg_pool_size=4,batch_size=4,n_epochs=10),datatype=EqualLengthMultivariate-Classification-numpy3D)]` | 3/3 | 6/9 | 6/9 | 3/3 | esperada, diverge |
| `aeon/testing/tests/test_all_estimators.py::test_all_estimators[check_classifier_output(estimator=TimeCNNClassifier(avg_pool_size=4,batch_size=4,n_epochs=10),datatype=EqualLengthUnivariate-Classification-numpy3D)]` | 3/3 | 6/9 | 6/9 | 3/3 | esperada, diverge |
| `aeon/testing/tests/test_all_estimators.py::test_all_estimators[check_classifier_random_state_deep_learning(estimator=DisjointCNNClassifier(batch_size=4,kernel_size=[2,2],metrics=['accuracy'],n_epochs=3,n_filters=2,n_layers=2,use_bias=False,use_mini_batch_size=True,verbose=True),datatype=EqualLengthUnivariate-Classification-numpy3D)]` | 3/3 | 6/9 | 6/9 | 3/3 | esperada, diverge |
| `aeon/testing/tests/test_all_estimators.py::test_all_estimators[check_classifier_random_state_deep_learning(estimator=DisjointCNNClassifier(batch_size=4,kernel_size=[2,2],n_epochs=3,n_filters=2,n_layers=2,use_bias=False),datatype=EqualLengthUnivariate-Classification-numpy3D)]` | 3/3 | 6/9 | 6/9 | 3/3 | esperada, diverge |
| `aeon/testing/tests/test_all_estimators.py::test_all_estimators[check_classifier_random_state_deep_learning(estimator=EncoderClassifier(batch_size=4,dropout_proba=0,fc_units=8,n_epochs=8,strides=2,use_bias=False),datatype=EqualLengthUnivariate-Classification-numpy3D)]` | 3/3 | 6/9 | 6/9 | 3/3 | esperada, diverge |
| `aeon/testing/tests/test_all_estimators.py::test_all_estimators[check_classifier_random_state_deep_learning(estimator=FCNClassifier(batch_size=4,kernel_size=3,n_epochs=10,n_filters=4,n_layers=1,padding='valid',strides=2,use_bias=False),datatype=EqualLengthUnivariate-Classification-numpy3D)]` | 3/3 | 6/9 | 6/9 | 3/3 | esperada, diverge |
| `aeon/testing/tests/test_all_estimators.py::test_all_estimators[check_classifier_random_state_deep_learning(estimator=IndividualInceptionClassifier(batch_size=4,depth=1,kernel_size=4,n_epochs=10,use_residual=False),datatype=EqualLengthUnivariate-Classification-numpy3D)]` | 3/3 | 6/9 | 6/9 | 3/3 | esperada, diverge |
| `aeon/testing/tests/test_all_estimators.py::test_all_estimators[check_classifier_random_state_deep_learning(estimator=IndividualLITEClassifier(batch_size=4,kernel_size=4,metrics=['accuracy'],n_epochs=2,use_litemv=True,use_mini_batch_size=True,verbose=True),datatype=EqualLengthUnivariate-Classification-numpy3D)]` | 3/3 | 6/9 | 6/9 | 3/3 | esperada, diverge |
| `aeon/testing/tests/test_all_estimators.py::test_all_estimators[check_classifier_random_state_deep_learning(estimator=IndividualLITEClassifier(batch_size=4,kernel_size=4,n_epochs=2),datatype=EqualLengthUnivariate-Classification-numpy3D)]` | 3/3 | 6/9 | 6/9 | 3/3 | esperada, diverge |
| _+37 teste(s), ver flaky_tests.json_ | | | | | |


### dask

#### control

| teste | baseline | ranking | regsmart | regsmart-no-rank | classe |
|---|---|---|---|---|---|
| `dask/array/tests/test_array_core.py::test_from_delayed_future` | 0/3 | 2/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `dask/array/tests/test_sparse.py::test_basic[<lambda>28]` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |


### dvc

#### dvc-m11576

| teste | baseline | ranking | regsmart | regsmart-no-rank | classe |
|---|---|---|---|---|---|
| `tests/func/repro/test_repro.py::test_repro_pulls_continue_without_run_cache` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/func/repro/test_repro.py::test_repro_pulls_missing_data_source` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/func/repro/test_repro.py::test_repro_skip_pull_if_no_run_cache_is_passed` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/func/repro/test_repro_pull.py::test_repro_pulls_allow_missing[False]` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/func/repro/test_repro_pull.py::test_repro_pulls_missing_data_source` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/func/repro/test_repro_pull.py::test_repro_pulls_missing_import` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/func/repro/test_repro_pull.py::test_repro_pulls_persisted_output` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/func/repro/test_repro_pull.py::test_repro_skip_pull_if_no_run_cache_is_passed` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/func/test_checkout.py::test_checkout` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/func/test_checkout.py::test_checkout_cli` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/func/test_checkout.py::test_checkout_stats[False-expected_lines1]` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/func/test_checkout.py::test_checkout_stats[True-expected_lines0]` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/func/test_checkout.py::test_checkout_stats_on_failure` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/func/test_checkout.py::test_checkout_with_deps_cli` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/func/test_checkout.py::test_gitignore_when_checkout` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/func/test_checkout.py::test_stats_on_removed_file_from_tracked_dir` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/func/test_checkout.py::test_stats_on_updated_file_from_tracked_dir` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/func/test_data_cloud.py::TestRemote::test_pull_00_prefix` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/func/test_data_cloud.py::TestRemote::test_pull_no_00_prefix` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/func/test_data_cloud.py::test_pull_external_dvc_imports` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/func/test_data_cloud.py::test_pull_external_dvc_imports_mixed` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/func/test_data_cloud.py::test_pull_git_imports[git_dir]` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/func/test_data_cloud.py::test_pull_granular_excluding_import_that_cannot_be_pulled` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/func/test_data_cloud.py::test_pull_partial_import_missing` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/func/test_data_cloud.py::test_push_pull_fetch_pipeline_stages` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/func/test_data_cloud.py::test_target_remote` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/func/test_import.py::test_pull_imported_directory_stage[dir/]` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/func/test_import.py::test_pull_imported_directory_stage[dir]` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/func/test_import.py::test_pull_imported_stage` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/func/test_import.py::test_pull_no_rev_lock` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/func/test_import_url.py::test_import_url_to_remote_status` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/func/test_update.py::test_update_import_url_to_remote_directory_changed_contents` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |


### ipython

#### control

| teste | baseline | ranking | regsmart | regsmart-no-rank | classe |
|---|---|---|---|---|---|
| `IPython/core/magics/config.py::IPython.core.magics.config.ConfigMagics.config` | 0/3 | 3/3 | 3/3 | 0/3 | só no plugin (flaky) |
| `IPython/testing/plugin/dtexample.py::IPython.testing.plugin.dtexample.ipos` | 0/3 | 3/3 | 3/3 | 0/3 | só no plugin (flaky) |
| `tests/test_application.py::test_initialize_stops_at_subapp` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_dict_key_completion_contexts` | 0/3 | 1/3 | 1/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_dict_key_completion_string` | 0/3 | 3/3 | 2/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_dict_key_completion_unicode_py3` | 0/3 | 3/3 | 3/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_dict_key_restrict_to_dicts` | 0/3 | 1/3 | 1/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_func_kw_completions` | 0/3 | 1/3 | 1/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_magic_completion_shadowing` | 0/3 | 1/3 | 1/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_matcher_disabling` | 0/3 | 1/3 | 1/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_mix_terms` | 0/3 | 1/3 | 1/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_quoted_file_completions` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_undefined_variables[t = []\nif condition_1:\n    if condition_2:\n        t = 'nested'\nt.-insert_text30-False-limited]` | 0/3 | 1/3 | 1/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_undefined_variables[t = []\nif condition_1:\n    t = 'string'\nelif condition_2:\n    t = 1\nelif condition_3:\n    t = {}\nt.-insert_text29-False-limited]` | 0/3 | 2/3 | 1/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_undefined_variables[t = []\nif some_condition:\n    t = 'string'\nelse:\n    t = 1\nt.-insert_text27-False-limited]` | 0/3 | 1/3 | 1/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_undefined_variables[t = []\nif some_condition:\n    t = 'string'\nt.-insert_text25-False-limited]` | 0/3 | 1/3 | 1/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_undefined_variables[t = []\nwhile condition_1:\n    while condition_2:\n        t = 'str'\nt.-insert_text33-False-limited]` | 0/3 | 0/3 | 1/3 | 0/3 | só no plugin (flaky) |
| `tests/test_display_2.py::test_matplotlib_positioning` | 0/3 | 3/3 | 3/3 | 0/3 | só no plugin (flaky) |
| `tests/test_displayhook.py::test_underscore_no_overwrite_user` | 0/3 | 3/3 | 3/3 | 0/3 | só no plugin (flaky) |
| `tests/test_editorhooks.py::test_install_editor` | 0/3 | 3/3 | 3/3 | 0/3 | só no plugin (flaky) |
| `tests/test_editorhooks.py::test_line_none_defaults_to_zero` | 0/3 | 3/3 | 3/3 | 0/3 | só no plugin (flaky) |
| `tests/test_historyapp.py::test_history_app_trim_subcommand` | 0/3 | 2/3 | 2/3 | 0/3 | só no plugin (flaky) |
| `tests/test_interactiveshell.py::test_naked_string_cells` | 0/3 | 2/3 | 3/3 | 0/3 | só no plugin (flaky) |
| `tests/test_interactiveshell.py::test_run_cell_asyncio_run` | 0/3 | 3/3 | 3/3 | 0/3 | só no plugin (flaky) |
| `tests/test_interactiveshell.py::test_run_cell_await` | 0/3 | 3/3 | 3/3 | 0/3 | só no plugin (flaky) |
| `tests/test_ipapp.py::test_locate_subcommand` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magic.py::test_cell_magic_class` | 0/3 | 2/3 | 1/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magic.py::test_cell_magic_class2` | 0/3 | 2/3 | 1/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magic.py::test_cell_magic_func_deco` | 0/3 | 2/3 | 1/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magic.py::test_cell_magic_reg` | 0/3 | 2/3 | 1/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magic.py::test_config_available_configs` | 0/3 | 3/3 | 1/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magic.py::test_line_cell_info` | 0/3 | 1/3 | 1/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magic.py::test_multiline_time` | 0/3 | 2/3 | 2/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magic.py::test_notebook_export_json_with_output` | 0/3 | 2/3 | 2/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magic.py::tests.test_magic.doctest_hist_f` | 0/3 | 1/3 | 1/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magic.py::tests.test_magic.doctest_who` | 0/3 | 1/3 | 1/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magic.py::tests.test_magic.test_debug_magic` | 0/3 | 3/3 | 3/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magic.py::tests.test_magic.test_debug_magic_locals` | 0/3 | 3/3 | 3/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magics_pylab.py::test_matplotlib_no_arg_prints_backend` | 0/3 | 2/3 | 3/3 | 0/3 | só no plugin (flaky) |
| `tests/test_profile.py::test_profile_app_list_subcommand` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| _+3 teste(s), ver flaky_tests.json_ | | | | | |

#### ipython-m1288

| teste | baseline | ranking | regsmart | regsmart-no-rank | classe |
|---|---|---|---|---|---|
| `IPython/core/magics/config.py::IPython.core.magics.config.ConfigMagics.config` | 0/3 | 3/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `IPython/testing/plugin/dtexample.py::IPython.testing.plugin.dtexample.ipos` | 0/3 | 3/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_application.py::test_initialize_stops_at_subapp` | 0/3 | 1/3 | 1/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_completer.py::test_dict_key_completion_contexts` | 0/3 | 0/3 | 1/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_completer.py::test_dict_key_completion_string` | 0/3 | 3/3 | 3/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_completer.py::test_dict_key_completion_unicode_py3` | 0/3 | 3/3 | 3/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_completer.py::test_dict_key_restrict_to_dicts` | 0/3 | 0/3 | 2/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_completer.py::test_func_kw_completions` | 0/3 | 1/3 | 1/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_completer.py::test_magic_completion_shadowing` | 0/3 | 1/3 | 1/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_completer.py::test_matcher_disabling` | 0/3 | 1/3 | 1/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_completer.py::test_mix_terms` | 0/3 | 1/3 | 2/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_completer.py::test_undefined_variables[t = []\nif condition_1:\n    if condition_2:\n        t = 'nested'\nt.-insert_text30-False-limited]` | 0/3 | 1/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_completer.py::test_undefined_variables[t = []\nif condition_1:\n    t = 'string'\nelif condition_2:\n    t = 1\nelif condition_3:\n    t = {}\nt.-insert_text29-False-limited]` | 0/3 | 1/3 | 1/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_completer.py::test_undefined_variables[t = []\nif some_condition:\n    t = 'string'\nelse:\n    t = 1\nt.-insert_text27-False-limited]` | 0/3 | 1/3 | 1/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_completer.py::test_undefined_variables[t = []\nif some_condition:\n    t = 'string'\nt.-insert_text25-False-limited]` | 0/3 | 1/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_completer.py::test_undefined_variables[t = []\nwhile condition_1:\n    while condition_2:\n        t = 'str'\nt.-insert_text33-False-limited]` | 0/3 | 1/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_display_2.py::test_matplotlib_positioning` | 0/3 | 3/3 | 3/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_displayhook.py::test_underscore_no_overwrite_user` | 0/3 | 2/3 | 3/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_editorhooks.py::test_install_editor` | 0/3 | 3/3 | 3/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_editorhooks.py::test_line_none_defaults_to_zero` | 0/3 | 3/3 | 3/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_historyapp.py::test_history_app_trim_subcommand` | 0/3 | 2/3 | 2/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_interactiveshell.py::test_naked_string_cells` | 0/3 | 3/3 | 1/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_interactiveshell.py::test_run_cell_asyncio_run` | 0/3 | 3/3 | 3/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_interactiveshell.py::test_run_cell_await` | 0/3 | 3/3 | 3/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_ipapp.py::test_locate_subcommand` | 0/3 | 1/3 | 1/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magic.py::test_cell_magic_class` | 0/3 | 1/3 | 3/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magic.py::test_cell_magic_class2` | 0/3 | 1/3 | 3/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magic.py::test_cell_magic_func_deco` | 0/3 | 1/3 | 3/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magic.py::test_cell_magic_reg` | 0/3 | 1/3 | 3/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magic.py::test_config_available_configs` | 0/3 | 1/3 | 1/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magic.py::test_line_cell_info` | 0/3 | 1/3 | 1/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magic.py::test_multiline_time` | 0/3 | 1/3 | 3/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magic.py::test_notebook_export_json_with_output` | 0/3 | 2/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magic.py::test_reset_in` | 0/3 | 3/3 | 3/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magic.py::tests.test_magic.doctest_hist_f` | 0/3 | 1/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magic.py::tests.test_magic.doctest_who` | 0/3 | 1/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magic.py::tests.test_magic.test_debug_magic` | 0/3 | 3/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magic.py::tests.test_magic.test_debug_magic_locals` | 0/3 | 3/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magics_pylab.py::test_matplotlib_no_arg_prints_backend` | 0/3 | 1/3 | 2/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_profile.py::test_profile_app_list_subcommand` | 0/3 | 1/3 | 1/3 | 0/3 | dependente de ordem (controle) |
| _+12 teste(s), ver flaky_tests.json_ | | | | | |

#### ipython-m17283

| teste | baseline | ranking | regsmart | regsmart-no-rank | classe |
|---|---|---|---|---|---|
| `IPython/core/magics/config.py::IPython.core.magics.config.ConfigMagics.config` | 0/3 | 3/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `IPython/testing/plugin/dtexample.py::IPython.testing.plugin.dtexample.ipos` | 0/3 | 3/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_application.py::test_initialize_stops_at_subapp` | 0/3 | 0/3 | 1/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_completer.py::test_dict_key_completion_contexts` | 0/3 | 1/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_completer.py::test_dict_key_completion_string` | 0/3 | 3/3 | 3/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_completer.py::test_dict_key_completion_unicode_py3` | 0/3 | 3/3 | 2/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_completer.py::test_dict_key_restrict_to_dicts` | 0/3 | 2/3 | 1/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_completer.py::test_func_kw_completions` | 0/3 | 1/3 | 1/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_completer.py::test_magic_completion_shadowing` | 0/3 | 1/3 | 1/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_completer.py::test_matcher_disabling` | 0/3 | 1/3 | 1/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_completer.py::test_mix_terms` | 0/3 | 1/3 | 1/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_completer.py::test_quoted_file_completions` | 0/3 | 1/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_completer.py::test_undefined_variables[t = []\nif condition_1:\n    if condition_2:\n        t = 'nested'\nt.-insert_text30-False-limited]` | 0/3 | 1/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_completer.py::test_undefined_variables[t = []\nif condition_1:\n    t = 'string'\nelif condition_2:\n    t = 1\nelif condition_3:\n    t = {}\nt.-insert_text29-False-limited]` | 0/3 | 2/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_completer.py::test_undefined_variables[t = []\nif some_condition:\n    t = 'string'\nelse:\n    t = 1\nt.-insert_text27-False-limited]` | 0/3 | 2/3 | 1/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_completer.py::test_undefined_variables[t = []\nif some_condition:\n    t = 'string'\nt.-insert_text25-False-limited]` | 0/3 | 1/3 | 1/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_completer.py::test_undefined_variables[t = []\nwhile condition_1:\n    while condition_2:\n        t = 'str'\nt.-insert_text33-False-limited]` | 0/3 | 1/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_display_2.py::test_matplotlib_positioning` | 0/3 | 3/3 | 3/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_displayhook.py::test_underscore_no_overwrite_user` | 0/3 | 3/3 | 3/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_editorhooks.py::test_install_editor` | 0/3 | 3/3 | 3/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_editorhooks.py::test_line_none_defaults_to_zero` | 0/3 | 3/3 | 3/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_historyapp.py::test_history_app_trim_subcommand` | 0/3 | 2/3 | 2/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_interactiveshell.py::test_naked_string_cells` | 0/3 | 1/3 | 1/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_interactiveshell.py::test_run_cell_asyncio_run` | 0/3 | 3/3 | 3/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_interactiveshell.py::test_run_cell_await` | 0/3 | 3/3 | 3/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_ipapp.py::test_locate_subcommand` | 0/3 | 0/3 | 1/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magic.py::test_cell_magic_class` | 0/3 | 2/3 | 2/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magic.py::test_cell_magic_class2` | 0/3 | 2/3 | 2/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magic.py::test_cell_magic_func_deco` | 0/3 | 2/3 | 2/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magic.py::test_cell_magic_reg` | 0/3 | 2/3 | 2/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magic.py::test_config_available_configs` | 0/3 | 1/3 | 3/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magic.py::test_line_cell_info` | 0/3 | 1/3 | 1/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magic.py::test_multiline_time` | 0/3 | 2/3 | 3/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magic.py::test_notebook_export_json_with_output` | 3/3 | 3/3 | 2/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magic.py::test_reset_in` | 0/3 | 3/3 | 3/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magic.py::tests.test_magic.doctest_hist_f` | 0/3 | 1/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magic.py::tests.test_magic.doctest_who` | 0/3 | 1/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magic.py::tests.test_magic.test_debug_magic` | 0/3 | 3/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magic.py::tests.test_magic.test_debug_magic_locals` | 0/3 | 3/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magics_pylab.py::test_matplotlib_no_arg_prints_backend` | 0/3 | 2/3 | 1/3 | 0/3 | dependente de ordem (controle) |
| _+34 teste(s), ver flaky_tests.json_ | | | | | |

#### ipython-m22324

| teste | baseline | ranking | regsmart | regsmart-no-rank | classe |
|---|---|---|---|---|---|
| `IPython/core/magics/config.py::IPython.core.magics.config.ConfigMagics.config` | 0/3 | 3/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `IPython/testing/plugin/dtexample.py::IPython.testing.plugin.dtexample.ipos` | 0/3 | 3/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_completer.py::test_dict_key_completion_contexts` | 0/3 | 1/3 | 1/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_completer.py::test_dict_key_completion_string` | 0/3 | 3/3 | 3/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_completer.py::test_dict_key_completion_unicode_py3` | 0/3 | 3/3 | 3/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_completer.py::test_dict_key_restrict_to_dicts` | 0/3 | 1/3 | 2/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_completer.py::test_func_kw_completions` | 0/3 | 1/3 | 1/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_completer.py::test_magic_completion_shadowing` | 0/3 | 2/3 | 1/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_completer.py::test_matcher_disabling` | 0/3 | 0/3 | 1/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_completer.py::test_mix_terms` | 0/3 | 1/3 | 1/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_completer.py::test_quoted_file_completions` | 0/3 | 1/3 | 1/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_completer.py::test_undefined_variables[t = []\nif condition_1:\n    if condition_2:\n        t = 'nested'\nt.-insert_text30-False-limited]` | 0/3 | 1/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_completer.py::test_undefined_variables[t = []\nif condition_1:\n    t = 'string'\nelif condition_2:\n    t = 1\nelif condition_3:\n    t = {}\nt.-insert_text29-False-limited]` | 0/3 | 1/3 | 1/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_completer.py::test_undefined_variables[t = []\nif some_condition:\n    t = 'string'\nelse:\n    t = 1\nt.-insert_text27-False-limited]` | 0/3 | 1/3 | 1/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_completer.py::test_undefined_variables[t = []\nif some_condition:\n    t = 'string'\nt.-insert_text25-False-limited]` | 0/3 | 1/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_display_2.py::test_matplotlib_positioning` | 0/3 | 3/3 | 3/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_displayhook.py::test_underscore_no_overwrite_user` | 0/3 | 1/3 | 3/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_editorhooks.py::test_install_editor` | 0/3 | 2/3 | 1/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_editorhooks.py::test_line_none_defaults_to_zero` | 0/3 | 2/3 | 1/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_historyapp.py::test_history_app_trim_subcommand` | 0/3 | 2/3 | 2/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_interactiveshell.py::test_naked_string_cells` | 0/3 | 2/3 | 1/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_interactiveshell.py::test_run_cell_asyncio_run` | 0/3 | 3/3 | 3/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_interactiveshell.py::test_run_cell_await` | 0/3 | 3/3 | 3/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magic.py::test_cell_magic_class` | 0/3 | 1/3 | 2/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magic.py::test_cell_magic_class2` | 0/3 | 1/3 | 2/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magic.py::test_cell_magic_func_deco` | 0/3 | 1/3 | 2/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magic.py::test_cell_magic_reg` | 0/3 | 1/3 | 2/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magic.py::test_config_available_configs` | 0/3 | 2/3 | 2/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magic.py::test_line_cell_info` | 0/3 | 1/3 | 1/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magic.py::test_multiline_time` | 0/3 | 1/3 | 3/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magic.py::test_notebook_export_json_with_output` | 0/3 | 2/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magic.py::test_reset_in` | 0/3 | 3/3 | 3/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magic.py::tests.test_magic.doctest_hist_f` | 0/3 | 1/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magic.py::tests.test_magic.doctest_who` | 0/3 | 1/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magic.py::tests.test_magic.test_debug_magic` | 0/3 | 3/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magic.py::tests.test_magic.test_debug_magic_locals` | 0/3 | 3/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magics_pylab.py::test_matplotlib_no_arg_prints_backend` | 0/3 | 1/3 | 3/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_run.py::test_run_tb` | 0/3 | 1/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_storemagic.py::test_store_restore` | 0/3 | 1/3 | 2/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_completer.py::test_file_completions_only_in_path_contexts` | 0/3 | 0/3 | 1/3 | 0/3 | só no plugin (flaky) |
| _+5 teste(s), ver flaky_tests.json_ | | | | | |

#### ipython-m22732

| teste | baseline | ranking | regsmart | regsmart-no-rank | classe |
|---|---|---|---|---|---|
| `IPython/core/magics/config.py::IPython.core.magics.config.ConfigMagics.config` | 0/3 | 3/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `IPython/testing/plugin/dtexample.py::IPython.testing.plugin.dtexample.ipos` | 0/3 | 3/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_application.py::test_initialize_stops_at_subapp` | 0/3 | 1/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_completer.py::test_dict_key_completion_string` | 0/3 | 2/3 | 3/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_completer.py::test_dict_key_completion_unicode_py3` | 0/3 | 3/3 | 2/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_completer.py::test_dict_key_restrict_to_dicts` | 0/3 | 1/3 | 1/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_completer.py::test_func_kw_completions` | 0/3 | 1/3 | 1/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_completer.py::test_magic_completion_shadowing` | 0/3 | 1/3 | 1/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_completer.py::test_matcher_disabling` | 0/3 | 1/3 | 1/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_completer.py::test_mix_terms` | 0/3 | 1/3 | 1/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_completer.py::test_quoted_file_completions` | 0/3 | 1/3 | 1/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_completer.py::test_undefined_variables[t = []\nif condition_1:\n    if condition_2:\n        t = 'nested'\nt.-insert_text30-False-limited]` | 0/3 | 1/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_completer.py::test_undefined_variables[t = []\nif condition_1:\n    t = 'string'\nelif condition_2:\n    t = 1\nelif condition_3:\n    t = {}\nt.-insert_text29-False-limited]` | 0/3 | 1/3 | 1/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_completer.py::test_undefined_variables[t = []\nif some_condition:\n    t = 'string'\nelse:\n    t = 1\nt.-insert_text27-False-limited]` | 0/3 | 1/3 | 1/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_completer.py::test_undefined_variables[t = []\nwhile condition_1:\n    while condition_2:\n        t = 'str'\nt.-insert_text33-False-limited]` | 0/3 | 1/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_display_2.py::test_matplotlib_positioning` | 0/3 | 3/3 | 3/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_displayhook.py::test_underscore_no_overwrite_user` | 0/3 | 2/3 | 3/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_editorhooks.py::test_install_editor` | 0/3 | 3/3 | 3/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_editorhooks.py::test_line_none_defaults_to_zero` | 0/3 | 3/3 | 3/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_historyapp.py::test_history_app_trim_subcommand` | 0/3 | 2/3 | 2/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_interactiveshell.py::test_naked_string_cells` | 0/3 | 1/3 | 1/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_interactiveshell.py::test_run_cell_asyncio_run` | 0/3 | 3/3 | 3/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_interactiveshell.py::test_run_cell_await` | 0/3 | 3/3 | 3/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_ipapp.py::test_locate_subcommand` | 0/3 | 1/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magic.py::test_cell_magic_class` | 0/3 | 2/3 | 3/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magic.py::test_cell_magic_class2` | 0/3 | 2/3 | 3/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magic.py::test_cell_magic_func_deco` | 0/3 | 2/3 | 3/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magic.py::test_cell_magic_reg` | 0/3 | 1/3 | 3/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magic.py::test_config_available_configs` | 0/3 | 1/3 | 2/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magic.py::test_line_cell_info` | 0/3 | 0/3 | 1/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magic.py::test_multiline_time` | 0/3 | 2/3 | 3/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magic.py::test_notebook_export_json_with_output` | 0/3 | 2/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magic.py::test_reset_in` | 0/3 | 3/3 | 3/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magic.py::tests.test_magic.doctest_hist_f` | 0/3 | 1/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magic.py::tests.test_magic.doctest_who` | 0/3 | 1/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magic.py::tests.test_magic.test_debug_magic` | 0/3 | 3/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magic.py::tests.test_magic.test_debug_magic_locals` | 0/3 | 3/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magics_pylab.py::test_matplotlib_no_arg_prints_backend` | 0/3 | 3/3 | 3/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_profile.py::test_profile_app_list_subcommand` | 0/3 | 1/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_run.py::test_run_tb` | 0/3 | 1/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| _+7 teste(s), ver flaky_tests.json_ | | | | | |

#### ipython-m4267

| teste | baseline | ranking | regsmart | regsmart-no-rank | classe |
|---|---|---|---|---|---|
| `IPython/core/magics/config.py::IPython.core.magics.config.ConfigMagics.config` | 0/3 | 3/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `IPython/testing/plugin/dtexample.py::IPython.testing.plugin.dtexample.ipos` | 0/3 | 3/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_application.py::test_initialize_stops_at_subapp` | 0/3 | 0/3 | 1/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_completer.py::test_dict_key_completion_string` | 0/3 | 3/3 | 3/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_completer.py::test_dict_key_completion_unicode_py3` | 0/3 | 3/3 | 3/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_completer.py::test_dict_key_restrict_to_dicts` | 0/3 | 0/3 | 2/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_completer.py::test_func_kw_completions` | 0/3 | 1/3 | 1/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_completer.py::test_magic_completion_shadowing` | 0/3 | 1/3 | 1/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_completer.py::test_matcher_disabling` | 0/3 | 2/3 | 1/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_completer.py::test_mix_terms` | 0/3 | 1/3 | 1/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_completer.py::test_quoted_file_completions` | 0/3 | 1/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_completer.py::test_undefined_variables[t = []\nif condition_1:\n    if condition_2:\n        t = 'nested'\nt.-insert_text30-False-limited]` | 0/3 | 1/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_completer.py::test_undefined_variables[t = []\nif condition_1:\n    t = 'string'\nelif condition_2:\n    t = 1\nelif condition_3:\n    t = {}\nt.-insert_text29-False-limited]` | 0/3 | 1/3 | 1/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_completer.py::test_undefined_variables[t = []\nif some_condition:\n    t = 'string'\nelse:\n    t = 1\nt.-insert_text27-False-limited]` | 0/3 | 1/3 | 1/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_completer.py::test_undefined_variables[t = []\nwhile condition_1:\n    while condition_2:\n        t = 'str'\nt.-insert_text33-False-limited]` | 0/3 | 1/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_display_2.py::test_matplotlib_positioning` | 0/3 | 3/3 | 3/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_displayhook.py::test_underscore_no_overwrite_user` | 0/3 | 3/3 | 3/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_editorhooks.py::test_install_editor` | 0/3 | 3/3 | 3/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_editorhooks.py::test_line_none_defaults_to_zero` | 0/3 | 3/3 | 3/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_historyapp.py::test_history_app_trim_subcommand` | 0/3 | 2/3 | 2/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_interactiveshell.py::test_naked_string_cells` | 0/3 | 3/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_interactiveshell.py::test_run_cell_asyncio_run` | 0/3 | 3/3 | 3/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_interactiveshell.py::test_run_cell_await` | 0/3 | 3/3 | 3/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_ipapp.py::test_locate_subcommand` | 0/3 | 0/3 | 1/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magic.py::test_cell_magic_class` | 0/3 | 2/3 | 2/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magic.py::test_cell_magic_class2` | 0/3 | 2/3 | 2/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magic.py::test_cell_magic_func_deco` | 0/3 | 2/3 | 2/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magic.py::test_cell_magic_reg` | 0/3 | 2/3 | 2/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magic.py::test_config_available_configs` | 0/3 | 1/3 | 2/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magic.py::test_line_cell_info` | 0/3 | 1/3 | 1/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magic.py::test_multiline_time` | 0/3 | 2/3 | 2/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magic.py::test_notebook_export_json_with_output` | 0/3 | 2/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magic.py::test_reset_in` | 0/3 | 3/3 | 3/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magic.py::tests.test_magic.doctest_hist_f` | 0/3 | 1/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magic.py::tests.test_magic.doctest_who` | 0/3 | 1/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magic.py::tests.test_magic.test_debug_magic` | 0/3 | 3/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magic.py::tests.test_magic.test_debug_magic_locals` | 0/3 | 3/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_magics_pylab.py::test_matplotlib_no_arg_prints_backend` | 0/3 | 3/3 | 3/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_profile.py::test_profile_app_list_subcommand` | 0/3 | 0/3 | 1/3 | 0/3 | dependente de ordem (controle) |
| `tests/test_run.py::test_run_tb` | 0/3 | 1/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| _+4 teste(s), ver flaky_tests.json_ | | | | | |


### networkx

#### networkx-m1096

| teste | baseline | ranking | regsmart | regsmart-no-rank | classe |
|---|---|---|---|---|---|
| `networkx/algorithms/dag.py::networkx.algorithms.dag.descendants` | 3/3 | 3/3 | 0/3 | 0/3 | esperada, diverge |
| `networkx/algorithms/dag.py::networkx.algorithms.dag.transitive_closure` | 3/3 | 3/3 | 0/3 | 0/3 | esperada, diverge |

#### networkx-m14277

| teste | baseline | ranking | regsmart | regsmart-no-rank | classe |
|---|---|---|---|---|---|
| `networkx/algorithms/isomorphism/vf2pp.py::networkx.algorithms.isomorphism.vf2pp` | 3/3 | 3/3 | 0/3 | 0/3 | esperada, diverge |

#### networkx-m17565

| teste | baseline | ranking | regsmart | regsmart-no-rank | classe |
|---|---|---|---|---|---|
| `networkx/algorithms/cluster.py::networkx.algorithms.cluster.transitivity` | 3/3 | 3/3 | 0/3 | 0/3 | esperada, diverge |

#### networkx-m25405

| teste | baseline | ranking | regsmart | regsmart-no-rank | classe |
|---|---|---|---|---|---|
| `networkx/algorithms/bipartite/basic.py::networkx.algorithms.bipartite.basic.is_bipartite` | 3/3 | 3/3 | 0/3 | 0/3 | esperada, diverge |
| `networkx/algorithms/bipartite/cluster.py::networkx.algorithms.bipartite.cluster.average_clustering` | 3/3 | 3/3 | 0/3 | 0/3 | esperada, diverge |
| `networkx/algorithms/bipartite/cluster.py::networkx.algorithms.bipartite.cluster.latapy_clustering` | 3/3 | 3/3 | 0/3 | 0/3 | esperada, diverge |
| `networkx/classes/function.py::networkx.classes.function.describe` | 3/3 | 3/3 | 0/3 | 0/3 | esperada, diverge |


### pytest-xdist

#### control

| teste | baseline | ranking | regsmart | regsmart-no-rank | classe |
|---|---|---|---|---|---|
| `testing/acceptance_test.py::TestLoadScope::test_workqueue_ordered_by_size` | 0/3 | 0/3 | 1/3 | 0/3 | só no plugin (flaky) |
| `testing/test_looponfail.py::TestLooponFailing::test_looponfail_from_fail_to_ok` | 0/3 | 3/3 | 3/3 | 3/3 | só no plugin (fixa) |
| `testing/test_looponfail.py::TestLooponFailing::test_looponfail_from_one_to_two_tests` | 0/3 | 3/3 | 3/3 | 3/3 | só no plugin (fixa) |
| `testing/test_looponfail.py::TestLooponFailing::test_looponfail_multiple_errors` | 0/3 | 3/3 | 3/3 | 3/3 | só no plugin (fixa) |
| `testing/test_looponfail.py::TestRemoteControl::test_failure_change` | 0/3 | 3/3 | 3/3 | 3/3 | só no plugin (fixa) |
| `testing/test_looponfail.py::TestRemoteControl::test_failure_subdir_no_init` | 0/3 | 3/3 | 3/3 | 3/3 | só no plugin (fixa) |
| `testing/test_looponfail.py::TestRemoteControl::test_failures_somewhere` | 0/3 | 3/3 | 3/3 | 3/3 | só no plugin (fixa) |
| `testing/test_looponfail.py::TestRemoteControl::test_ignore_sys_path_hook_entry` | 0/3 | 3/3 | 3/3 | 3/3 | só no plugin (fixa) |
| `testing/test_looponfail.py::TestRemoteControl::test_nofailures` | 0/3 | 3/3 | 3/3 | 3/3 | só no plugin (fixa) |

#### pytest-xdist-m0722

| teste | baseline | ranking | regsmart | regsmart-no-rank | classe |
|---|---|---|---|---|---|
| `testing/acceptance_test.py::TestGroupScope::test_by_class` | 3/3 | 3/3 | 3/3 | 3/3 | ambiente (controle) |
| `testing/acceptance_test.py::TestGroupScope::test_by_module` | 3/3 | 3/3 | 3/3 | 3/3 | ambiente (controle) |
| `testing/acceptance_test.py::TestGroupScope::test_module_single_start` | 3/3 | 3/3 | 3/3 | 3/3 | ambiente (controle) |
| `testing/acceptance_test.py::TestGroupScope::test_multiple_group_marks` | 3/3 | 3/3 | 3/3 | 3/3 | ambiente (controle) |
| `testing/acceptance_test.py::TestGroupScope::test_multiple_group_order` | 3/3 | 3/3 | 3/3 | 3/3 | ambiente (controle) |
| `testing/acceptance_test.py::TestLoadScope::test_workqueue_ordered_by_size` | 0/3 | 1/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `testing/test_looponfail.py::TestLooponFailing::test_looponfail_from_fail_to_ok` | 0/3 | 3/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `testing/test_looponfail.py::TestLooponFailing::test_looponfail_from_one_to_two_tests` | 0/3 | 3/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `testing/test_looponfail.py::TestLooponFailing::test_looponfail_multiple_errors` | 0/3 | 3/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `testing/test_looponfail.py::TestRemoteControl::test_failure_change` | 0/3 | 3/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `testing/test_looponfail.py::TestRemoteControl::test_failure_subdir_no_init` | 0/3 | 3/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `testing/test_looponfail.py::TestRemoteControl::test_failures_somewhere` | 0/3 | 3/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `testing/test_looponfail.py::TestRemoteControl::test_ignore_sys_path_hook_entry` | 0/3 | 3/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `testing/test_looponfail.py::TestRemoteControl::test_nofailures` | 0/3 | 3/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `testing/acceptance_test.py::TestLoadScope::test_workqueue_ordered_by_input` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `testing/acceptance_test.py::TestAPI::test_get_xdist_worker_id` | 3/3 | 3/3 | 0/3 | 0/3 | esperada, diverge |

#### pytest-xdist-m1049

| teste | baseline | ranking | regsmart | regsmart-no-rank | classe |
|---|---|---|---|---|---|
| `testing/acceptance_test.py::TestGroupScope::test_by_class` | 3/3 | 3/3 | 3/3 | 3/3 | ambiente (controle) |
| `testing/acceptance_test.py::TestGroupScope::test_by_module` | 3/3 | 3/3 | 3/3 | 3/3 | ambiente (controle) |
| `testing/acceptance_test.py::TestGroupScope::test_module_single_start` | 3/3 | 3/3 | 3/3 | 3/3 | ambiente (controle) |
| `testing/acceptance_test.py::TestGroupScope::test_multiple_group_marks` | 3/3 | 3/3 | 3/3 | 3/3 | ambiente (controle) |
| `testing/acceptance_test.py::TestGroupScope::test_multiple_group_order` | 3/3 | 3/3 | 3/3 | 3/3 | ambiente (controle) |
| `testing/acceptance_test.py::TestLoadScope::test_workqueue_ordered_by_size` | 0/3 | 0/3 | 2/3 | 0/3 | dependente de ordem (controle) |
| `testing/test_looponfail.py::TestLooponFailing::test_looponfail_from_fail_to_ok` | 0/3 | 3/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `testing/test_looponfail.py::TestLooponFailing::test_looponfail_from_one_to_two_tests` | 0/3 | 3/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `testing/test_looponfail.py::TestLooponFailing::test_looponfail_multiple_errors` | 0/3 | 3/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `testing/test_looponfail.py::TestRemoteControl::test_failure_change` | 0/3 | 3/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `testing/test_looponfail.py::TestRemoteControl::test_failure_subdir_no_init` | 0/3 | 3/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `testing/test_looponfail.py::TestRemoteControl::test_failures_somewhere` | 0/3 | 3/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `testing/test_looponfail.py::TestRemoteControl::test_ignore_sys_path_hook_entry` | 0/3 | 3/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `testing/test_looponfail.py::TestRemoteControl::test_nofailures` | 0/3 | 3/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `testing/acceptance_test.py::test_session_testscollected` | 3/3 | 3/3 | 0/3 | 0/3 | esperada, diverge |
| `testing/test_workermanage.py::TestNodeManager::test_proxy_gateway` | 3/3 | 3/3 | 0/3 | 0/3 | esperada, diverge |

#### pytest-xdist-m1214

| teste | baseline | ranking | regsmart | regsmart-no-rank | classe |
|---|---|---|---|---|---|
| `testing/acceptance_test.py::TestGroupScope::test_by_class` | 3/3 | 3/3 | 3/3 | 3/3 | ambiente (controle) |
| `testing/acceptance_test.py::TestGroupScope::test_by_module` | 3/3 | 3/3 | 3/3 | 3/3 | ambiente (controle) |
| `testing/acceptance_test.py::TestGroupScope::test_module_single_start` | 3/3 | 3/3 | 3/3 | 3/3 | ambiente (controle) |
| `testing/acceptance_test.py::TestGroupScope::test_multiple_group_marks` | 3/3 | 3/3 | 3/3 | 3/3 | ambiente (controle) |
| `testing/acceptance_test.py::TestGroupScope::test_multiple_group_order` | 3/3 | 3/3 | 3/3 | 3/3 | ambiente (controle) |
| `testing/acceptance_test.py::TestLoadScope::test_workqueue_ordered_by_size` | 0/3 | 1/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `testing/test_looponfail.py::TestLooponFailing::test_looponfail_from_fail_to_ok` | 0/3 | 3/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `testing/test_looponfail.py::TestLooponFailing::test_looponfail_from_one_to_two_tests` | 0/3 | 3/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `testing/test_looponfail.py::TestLooponFailing::test_looponfail_multiple_errors` | 0/3 | 3/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `testing/test_looponfail.py::TestRemoteControl::test_failure_change` | 0/3 | 3/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `testing/test_looponfail.py::TestRemoteControl::test_failure_subdir_no_init` | 0/3 | 3/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `testing/test_looponfail.py::TestRemoteControl::test_failures_somewhere` | 0/3 | 3/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `testing/test_looponfail.py::TestRemoteControl::test_ignore_sys_path_hook_entry` | 0/3 | 3/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `testing/test_looponfail.py::TestRemoteControl::test_nofailures` | 0/3 | 3/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `testing/acceptance_test.py::TestLoadScope::test_workqueue_ordered_by_input` | 0/3 | 1/3 | 1/3 | 0/3 | só no plugin (flaky) |

#### pytest-xdist-m1461

| teste | baseline | ranking | regsmart | regsmart-no-rank | classe |
|---|---|---|---|---|---|
| `testing/acceptance_test.py::TestGroupScope::test_by_class` | 3/3 | 3/3 | 3/3 | 3/3 | ambiente (controle) |
| `testing/acceptance_test.py::TestGroupScope::test_by_module` | 3/3 | 3/3 | 3/3 | 3/3 | ambiente (controle) |
| `testing/acceptance_test.py::TestGroupScope::test_module_single_start` | 3/3 | 3/3 | 3/3 | 3/3 | ambiente (controle) |
| `testing/acceptance_test.py::TestGroupScope::test_multiple_group_marks` | 3/3 | 3/3 | 3/3 | 3/3 | ambiente (controle) |
| `testing/acceptance_test.py::TestGroupScope::test_multiple_group_order` | 3/3 | 3/3 | 3/3 | 3/3 | ambiente (controle) |
| `testing/acceptance_test.py::TestLoadScope::test_workqueue_ordered_by_size` | 0/3 | 1/3 | 1/3 | 1/3 | dependente de ordem (controle) |
| `testing/test_looponfail.py::TestLooponFailing::test_looponfail_from_fail_to_ok` | 0/3 | 3/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `testing/test_looponfail.py::TestLooponFailing::test_looponfail_from_one_to_two_tests` | 0/3 | 3/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `testing/test_looponfail.py::TestLooponFailing::test_looponfail_multiple_errors` | 0/3 | 3/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `testing/test_looponfail.py::TestRemoteControl::test_failure_change` | 0/3 | 3/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `testing/test_looponfail.py::TestRemoteControl::test_failure_subdir_no_init` | 0/3 | 3/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `testing/test_looponfail.py::TestRemoteControl::test_failures_somewhere` | 0/3 | 3/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `testing/test_looponfail.py::TestRemoteControl::test_ignore_sys_path_hook_entry` | 0/3 | 3/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `testing/test_looponfail.py::TestRemoteControl::test_nofailures` | 0/3 | 3/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `testing/acceptance_test.py::TestLoadScope::test_workqueue_ordered_by_input` | 0/3 | 1/3 | 1/3 | 0/3 | só no plugin (flaky) |

#### pytest-xdist-m1537

| teste | baseline | ranking | regsmart | regsmart-no-rank | classe |
|---|---|---|---|---|---|
| `testing/acceptance_test.py::TestGroupScope::test_by_class` | 3/3 | 3/3 | 3/3 | 3/3 | ambiente (controle) |
| `testing/acceptance_test.py::TestGroupScope::test_by_module` | 3/3 | 3/3 | 3/3 | 3/3 | ambiente (controle) |
| `testing/acceptance_test.py::TestGroupScope::test_module_single_start` | 3/3 | 3/3 | 3/3 | 3/3 | ambiente (controle) |
| `testing/acceptance_test.py::TestGroupScope::test_multiple_group_marks` | 3/3 | 3/3 | 3/3 | 3/3 | ambiente (controle) |
| `testing/acceptance_test.py::TestGroupScope::test_multiple_group_order` | 3/3 | 3/3 | 3/3 | 3/3 | ambiente (controle) |
| `testing/acceptance_test.py::TestLoadScope::test_workqueue_ordered_by_size` | 0/3 | 1/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `testing/test_looponfail.py::TestLooponFailing::test_looponfail_from_fail_to_ok` | 0/3 | 3/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `testing/test_looponfail.py::TestLooponFailing::test_looponfail_from_one_to_two_tests` | 0/3 | 3/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `testing/test_looponfail.py::TestLooponFailing::test_looponfail_multiple_errors` | 0/3 | 3/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `testing/test_looponfail.py::TestRemoteControl::test_failure_change` | 0/3 | 3/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `testing/test_looponfail.py::TestRemoteControl::test_failure_subdir_no_init` | 0/3 | 3/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `testing/test_looponfail.py::TestRemoteControl::test_failures_somewhere` | 0/3 | 3/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `testing/test_looponfail.py::TestRemoteControl::test_ignore_sys_path_hook_entry` | 0/3 | 3/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `testing/test_looponfail.py::TestRemoteControl::test_nofailures` | 0/3 | 3/3 | 0/3 | 0/3 | dependente de ordem (controle) |
| `testing/acceptance_test.py::TestLoadScope::test_workqueue_ordered_by_input` | 0/3 | 0/3 | 1/3 | 0/3 | só no plugin (flaky) |


### pytorch-lightning

#### pytorch-lightning-m14490

| teste | baseline | ranking | regsmart | regsmart-no-rank | classe |
|---|---|---|---|---|---|
| `strategies/test_ddp_integration.py::test_ddp_cpu` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |

#### pytorch-lightning-m20410

| teste | baseline | ranking | regsmart | regsmart-no-rank | classe |
|---|---|---|---|---|---|
| `callbacks/test_stochastic_weight_avg.py::test_swa_callback_ddp_cpu` | 0/3 | 0/3 | 1/3 | 0/3 | só no plugin (flaky) |

#### pytorch-lightning-m9476

| teste | baseline | ranking | regsmart | regsmart-no-rank | classe |
|---|---|---|---|---|---|
| `callbacks/test_stochastic_weight_avg.py::test_swa_callback_ddp_cpu` | 0/3 | 1/3 | 1/3 | 0/2 | só no plugin (flaky) |


### trimesh

#### trimesh-m25103

| teste | baseline | ranking | regsmart | regsmart-no-rank | classe |
|---|---|---|---|---|---|
| `tests/test_dae.py::DAETest::test_invalid_shininess` | 3/3 | 3/3 | 0/3 | 0/3 | esperada, diverge |
| `tests/test_dae.py::DAETest::test_material_round` | 3/3 | 3/3 | 0/3 | 0/3 | esperada, diverge |
| `tests/test_gltf.py::GLTFTest::test_spec_gloss_factors_only` | 3/3 | 3/3 | 0/3 | 0/3 | esperada, diverge |
| `tests/test_gltf.py::GLTFTest::test_specular_glossiness` | 3/3 | 3/3 | 0/3 | 0/3 | esperada, diverge |
| `tests/test_pbr_concatenate.py::PBRConcatenateTest::test_pbr_identical_materials` | 3/3 | 3/3 | 0/3 | 0/3 | esperada, diverge |
| `tests/test_texture.py::TextureTest::test_pbr_nouv_export` | 3/3 | 3/3 | 0/3 | 0/3 | esperada, diverge |

#### trimesh-m3147

| teste | baseline | ranking | regsmart | regsmart-no-rank | classe |
|---|---|---|---|---|---|
| `tests/test_inertia.py::test_points_inertia_sample` | 3/3 | 3/3 | 0/3 | 0/3 | esperada, diverge |


### ultralytics

#### ultralytics-m23817

| teste | baseline | ranking | regsmart | regsmart-no-rank | classe |
|---|---|---|---|---|---|
| `tests/test_cli.py::test_predict[classify-model0-imagenet10]` | 3/3 | 3/3 | 0/3 | 0/3 | ambiente (controle) |
| `tests/test_engine.py::test_task[ClassificationTrainer-ClassificationValidator-ClassificationPredictor-imagenet10-yolo26n-cls.yaml-None]` | 3/3 | 3/3 | 3/3 | 3/3 | ambiente (controle) |
| `tests/test_python.py::test_predict_img[yolo26n-cls.pt]` | 3/3 | 3/3 | 3/3 | 3/3 | ambiente (controle) |
| `tests/test_python.py::test_results[yolo26n-cls.pt]` | 3/3 | 3/3 | 3/3 | 3/3 | ambiente (controle) |
| `tests/test_cli.py::test_distill[detect-coco8.yaml-yolo26n.yaml-teacher0]` | 3/3 | 3/3 | 0/3 | 0/3 | esperada, diverge |
| `tests/test_cli.py::test_distill[obb-dota8.yaml-yolo26n-obb.yaml-teacher3]` | 3/3 | 3/3 | 0/3 | 0/3 | esperada, diverge |
| `tests/test_cli.py::test_distill[pose-coco8-pose.yaml-yolo26n-pose.yaml-teacher2]` | 3/3 | 3/3 | 0/3 | 0/3 | esperada, diverge |
| `tests/test_cli.py::test_distill[segment-coco8-seg.yaml-yolo26n-seg.yaml-teacher1]` | 3/3 | 3/3 | 0/3 | 0/3 | esperada, diverge |
| `tests/test_cli.py::test_train[classify-model0-imagenet10]` | 3/3 | 3/3 | 0/3 | 0/3 | esperada, diverge |
| `tests/test_cli.py::test_train[depth-model1-depth8.yaml]` | 3/3 | 3/3 | 0/3 | 0/3 | esperada, diverge |
| `tests/test_cli.py::test_train[detect-model2-coco8.yaml]` | 3/3 | 3/3 | 0/3 | 0/3 | esperada, diverge |
| `tests/test_cli.py::test_train[obb-model3-dota8.yaml]` | 3/3 | 3/3 | 0/3 | 0/3 | esperada, diverge |
| `tests/test_cli.py::test_train[pose-model4-coco8-pose.yaml]` | 3/3 | 3/3 | 0/3 | 0/3 | esperada, diverge |
| `tests/test_cli.py::test_train[segment-model5-coco8-seg.yaml]` | 3/3 | 3/3 | 0/3 | 0/3 | esperada, diverge |
| `tests/test_cli.py::test_train[semantic-model6-cityscapes8.yaml]` | 3/3 | 3/3 | 0/3 | 0/3 | esperada, diverge |

#### ultralytics-m2383

| teste | baseline | ranking | regsmart | regsmart-no-rank | classe |
|---|---|---|---|---|---|
| `tests/test_cli.py::test_predict[classify-model0-imagenet10]` | 3/3 | 3/3 | 0/3 | 0/3 | ambiente (controle) |
| `tests/test_engine.py::test_task[ClassificationTrainer-ClassificationValidator-ClassificationPredictor-imagenet10-yolo26n-cls.yaml-None]` | 3/3 | 3/3 | 3/3 | 3/3 | ambiente (controle) |
| `tests/test_python.py::test_predict_img[yolo26n-cls.pt]` | 3/3 | 3/3 | 3/3 | 3/3 | ambiente (controle) |
| `tests/test_python.py::test_results[yolo26n-cls.pt]` | 3/3 | 3/3 | 3/3 | 3/3 | ambiente (controle) |
| `tests/test_cli.py::test_distill[detect-coco8.yaml-yolo26n.yaml-teacher0]` | 3/3 | 3/3 | 0/3 | 0/3 | esperada, diverge |
| `tests/test_cli.py::test_distill[obb-dota8.yaml-yolo26n-obb.yaml-teacher3]` | 3/3 | 3/3 | 0/3 | 0/3 | esperada, diverge |
| `tests/test_cli.py::test_distill[pose-coco8-pose.yaml-yolo26n-pose.yaml-teacher2]` | 3/3 | 3/3 | 0/3 | 0/3 | esperada, diverge |
| `tests/test_cli.py::test_distill[segment-coco8-seg.yaml-yolo26n-seg.yaml-teacher1]` | 3/3 | 3/3 | 0/3 | 0/3 | esperada, diverge |
| `tests/test_cli.py::test_predict[depth-model1-depth8.yaml]` | 3/3 | 3/3 | 0/3 | 0/3 | esperada, diverge |
| `tests/test_cli.py::test_predict[detect-model2-coco8.yaml]` | 3/3 | 3/3 | 0/3 | 0/3 | esperada, diverge |
| `tests/test_cli.py::test_predict[obb-model3-dota8.yaml]` | 3/3 | 3/3 | 0/3 | 0/3 | esperada, diverge |
| `tests/test_cli.py::test_predict[pose-model4-coco8-pose.yaml]` | 3/3 | 3/3 | 0/3 | 0/3 | esperada, diverge |
| `tests/test_cli.py::test_predict[segment-model5-coco8-seg.yaml]` | 3/3 | 3/3 | 0/3 | 0/3 | esperada, diverge |
| `tests/test_cli.py::test_predict[semantic-model6-cityscapes8.yaml]` | 3/3 | 3/3 | 0/3 | 0/3 | esperada, diverge |
| `tests/test_cli.py::test_rtdetr` | 3/3 | 3/3 | 0/3 | 0/3 | esperada, diverge |
| `tests/test_cli.py::test_solutions[analytics]` | 3/3 | 3/3 | 0/3 | 0/3 | esperada, diverge |
| `tests/test_cli.py::test_solutions[blur]` | 3/3 | 3/3 | 0/3 | 0/3 | esperada, diverge |
| `tests/test_cli.py::test_solutions[count]` | 3/3 | 3/3 | 0/3 | 0/3 | esperada, diverge |
| `tests/test_cli.py::test_solutions[heatmap]` | 3/3 | 3/3 | 0/3 | 0/3 | esperada, diverge |
| `tests/test_cli.py::test_solutions[isegment]` | 3/3 | 3/3 | 0/3 | 0/3 | esperada, diverge |
| `tests/test_cli.py::test_solutions[queue]` | 3/3 | 3/3 | 0/3 | 0/3 | esperada, diverge |
| `tests/test_cli.py::test_solutions[speed]` | 3/3 | 3/3 | 0/3 | 0/3 | esperada, diverge |
| `tests/test_cli.py::test_solutions[trackzone]` | 3/3 | 3/3 | 0/3 | 0/3 | esperada, diverge |
| `tests/test_cli.py::test_solutions[visioneye]` | 3/3 | 3/3 | 0/3 | 0/3 | esperada, diverge |
| `tests/test_cli.py::test_solutions[workout]` | 3/3 | 3/3 | 0/3 | 0/3 | esperada, diverge |
| `tests/test_cli.py::test_train[depth-model1-depth8.yaml]` | 3/3 | 3/3 | 0/3 | 0/3 | esperada, diverge |
| `tests/test_cli.py::test_train[detect-model2-coco8.yaml]` | 3/3 | 3/3 | 0/3 | 0/3 | esperada, diverge |
| `tests/test_cli.py::test_train[obb-model3-dota8.yaml]` | 3/3 | 3/3 | 0/3 | 0/3 | esperada, diverge |
| `tests/test_cli.py::test_train[pose-model4-coco8-pose.yaml]` | 3/3 | 3/3 | 0/3 | 0/3 | esperada, diverge |
| `tests/test_cli.py::test_train[segment-model5-coco8-seg.yaml]` | 3/3 | 3/3 | 0/3 | 0/3 | esperada, diverge |
| `tests/test_cli.py::test_train[semantic-model6-cityscapes8.yaml]` | 3/3 | 3/3 | 0/3 | 0/3 | esperada, diverge |
| `tests/test_cli.py::test_val[depth-model1-depth8.yaml]` | 3/3 | 3/3 | 0/3 | 0/3 | esperada, diverge |
| `tests/test_cli.py::test_val[detect-model2-coco8.yaml]` | 3/3 | 3/3 | 0/3 | 0/3 | esperada, diverge |
| `tests/test_cli.py::test_val[obb-model3-dota8.yaml]` | 3/3 | 3/3 | 0/3 | 0/3 | esperada, diverge |
| `tests/test_cli.py::test_val[pose-model4-coco8-pose.yaml]` | 3/3 | 3/3 | 0/3 | 0/3 | esperada, diverge |
| `tests/test_cli.py::test_val[segment-model5-coco8-seg.yaml]` | 3/3 | 3/3 | 0/3 | 0/3 | esperada, diverge |
| `tests/test_cli.py::test_val[semantic-model6-cityscapes8.yaml]` | 3/3 | 3/3 | 0/3 | 0/3 | esperada, diverge |

#### ultralytics-m34570

| teste | baseline | ranking | regsmart | regsmart-no-rank | classe |
|---|---|---|---|---|---|
| `tests/test_cli.py::test_predict[classify-model0-imagenet10]` | 3/3 | 3/3 | 0/3 | 0/3 | ambiente (controle) |
| `tests/test_engine.py::test_task[ClassificationTrainer-ClassificationValidator-ClassificationPredictor-imagenet10-yolo26n-cls.yaml-None]` | 3/3 | 3/3 | 3/3 | 3/3 | ambiente (controle) |
| `tests/test_python.py::test_predict_img[yolo26n-cls.pt]` | 3/3 | 3/3 | 3/3 | 3/3 | ambiente (controle) |
| `tests/test_python.py::test_results[yolo26n-cls.pt]` | 3/3 | 3/3 | 3/3 | 3/3 | ambiente (controle) |

#### ultralytics-m36889

| teste | baseline | ranking | regsmart | regsmart-no-rank | classe |
|---|---|---|---|---|---|
| `tests/test_cli.py::test_predict[classify-model0-imagenet10]` | 3/3 | 3/3 | 0/3 | 0/3 | ambiente (controle) |
| `tests/test_engine.py::test_task[ClassificationTrainer-ClassificationValidator-ClassificationPredictor-imagenet10-yolo26n-cls.yaml-None]` | 3/3 | 3/3 | 3/3 | 3/3 | ambiente (controle) |
| `tests/test_python.py::test_predict_img[yolo26n-cls.pt]` | 3/3 | 3/3 | 3/3 | 3/3 | ambiente (controle) |
| `tests/test_python.py::test_results[yolo26n-cls.pt]` | 3/3 | 3/3 | 3/3 | 3/3 | ambiente (controle) |

#### ultralytics-m5380

| teste | baseline | ranking | regsmart | regsmart-no-rank | classe |
|---|---|---|---|---|---|
| `tests/test_cli.py::test_predict[classify-model0-imagenet10]` | 3/3 | 3/3 | 0/3 | 0/3 | ambiente (controle) |
| `tests/test_engine.py::test_task[ClassificationTrainer-ClassificationValidator-ClassificationPredictor-imagenet10-yolo26n-cls.yaml-None]` | 3/3 | 3/3 | 3/3 | 3/3 | ambiente (controle) |
| `tests/test_python.py::test_predict_img[yolo26n-cls.pt]` | 3/3 | 3/3 | 3/3 | 3/3 | ambiente (controle) |
| `tests/test_python.py::test_results[yolo26n-cls.pt]` | 3/3 | 3/3 | 3/3 | 3/3 | ambiente (controle) |
| `tests/test_cli.py::test_train[depth-model1-depth8.yaml]` | 3/3 | 3/3 | 0/3 | 0/3 | esperada, diverge |
| `tests/test_cli.py::test_val[depth-model1-depth8.yaml]` | 3/3 | 3/3 | 0/3 | 0/3 | esperada, diverge |


