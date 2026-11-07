# Flaky runner — relatório

## Custo

- Início: `2026-11-05T21:52:24.846302+00:00`
- Fim: `2026-11-07T00:23:37.788996+00:00`
- Tempo ativo do script: **5h45m37s**
- Janela real dos runs (1º dispatch → última conclusão): **26h30m53s** (inclui fila)
- Minutos de runner somados: **8061.5 min**
- Pico de concorrência medido: **40** jobs (teto do plano Free: 20)

## API / rate limit

- Requisições: 1279 GET, 587 POST
- Retries: 44
- Rate limit (final): 49/5000 consumidos, reseta em `2026-11-07T00:31:12+00:00`

## Saúde da execução

| Métrica | warm-up | repetições |
|---|---|---|
| Tarefas no plano | 72 | 432 |
| Despachadas | 72 | 432 |
| Com run_id | 72 | 432 |
| Sucesso | 13 | 70 |
| Falha (testes falharam) | 59 | 362 |
| Canceladas | 0 | 0 |
| Em andamento | 0 | 0 |
| Dispatch falhou / run perdido | 0 | 0 |
| SHA do run ≠ SHA do mutante | 0 | 0 |
| Rep sem warm-up concluído | 0 | 0 |

## Por repositório

| repo | runs | success | failure | cancelled | em andamento | makespan | min runner |
|---|---|---|---|---|---|---|---|
| apscheduler | 84 | 14 | 70 | 0 | 0 | 1h30m20s | 452.9 |
| dask | 84 | 12 | 72 | 0 | 0 | 2h30m43s | 4246.2 |
| dvc | 84 | 14 | 70 | 0 | 0 | 53m30s | 922.5 |
| ipython | 84 | 8 | 76 | 0 | 0 | 32m32s | 717.4 |
| librosa | 84 | 14 | 70 | 0 | 0 | 1h55m03s | 835.7 |
| trimesh | 84 | 21 | 63 | 0 | 0 | 9h14m34s | 886.7 |

## Por workflow

| workflow | runs | min runner |
|---|---|---|
| baseline | 108 | 781.8 |
| ranking | 144 | 4218.7 |
| regsmart | 144 | 2428.4 |
| regsmart-no-rank | 108 | 632.6 |

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
| dask | control | 0 | 0 | 2 | 0 | 0 | 0 | 0 |
| dask | dask-m11282 | 0 | 0 | 0 | 0 | 0 | 16 | 0 |
| dask | dask-m12753 | 0 | 0 | 0 | 0 | 0 | 9 | 0 |
| dask | dask-m1940 | 0 | 0 | 0 | 0 | 0 | 24 | 0 |
| dask | dask-m28832 | 0 | 0 | 0 | 0 | 0 | 15 | 0 |
| dask | dask-m37146 | 0 | 0 | 0 | 0 | 0 | 2 | 0 |
| dvc | control | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| dvc | dvc-m11576 | 0 | 0 | 32 | 0 | 0 | 1 | 0 |
| dvc | dvc-m12545 | 0 | 0 | 0 | 0 | 0 | 177 | 0 |
| dvc | dvc-m16845 | 0 | 0 | 0 | 0 | 0 | 4 | 0 |
| dvc | dvc-m19066 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| dvc | dvc-m6852 | 0 | 0 | 0 | 0 | 0 | 3 | 0 |
| ipython | control | 0 | 0 | 42 | 1 | 0 | 0 | 0 |
| ipython | ipython-m1288 | 42 | 0 | 10 | 0 | 0 | 1 | 0 |
| ipython | ipython-m17283 | 43 | 0 | 29 | 0 | 2 | 32 | 0 |
| ipython | ipython-m22324 | 39 | 0 | 6 | 0 | 0 | 1 | 0 |
| ipython | ipython-m22732 | 41 | 0 | 6 | 0 | 0 | 1 | 0 |
| ipython | ipython-m4267 | 41 | 0 | 3 | 0 | 0 | 1 | 0 |
| librosa | control | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| librosa | librosa-m0035 | 0 | 0 | 0 | 0 | 0 | 149 | 0 |
| librosa | librosa-m0265 | 0 | 0 | 0 | 0 | 0 | 486 | 0 |
| librosa | librosa-m2885 | 0 | 0 | 0 | 0 | 0 | 566 | 0 |
| librosa | librosa-m4950 | 0 | 0 | 0 | 0 | 0 | 15 | 0 |
| librosa | librosa-m7678 | 0 | 0 | 0 | 0 | 0 | 736 | 0 |
| trimesh | control | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| trimesh | trimesh-extra | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| trimesh | trimesh-m13478 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| trimesh | trimesh-m21160 | 0 | 0 | 0 | 0 | 0 | 2 | 0 |
| trimesh | trimesh-m25103 | 0 | 0 | 0 | 0 | 6 | 1 | 0 |
| trimesh | trimesh-m3147 | 0 | 0 | 0 | 0 | 1 | 0 | 0 |

### Só no plugin: em quais workflows falhou

Testes que nunca falharam no baseline (flaky + fixa), cada um contado uma vez, na combinação exata de workflows em que falhou. `ranking+regsmart` = falhou nos dois.

| repo | mutante | ranking | regsmart | ranking+regsmart | total |
|---|---|---|---|---|---|
| apscheduler | apscheduler-m0316 | 0 | 0 | 0 | 0 |
| apscheduler | apscheduler-m0753 | 0 | 0 | 0 | 0 |
| apscheduler | apscheduler-m1399 | 0 | 0 | 0 | 0 |
| apscheduler | apscheduler-m2144 | 0 | 0 | 0 | 0 |
| apscheduler | apscheduler-m2213 | 0 | 0 | 0 | 0 |
| apscheduler | control | 0 | 0 | 0 | 0 |
| dask | control | 2 | 0 | 0 | 2 |
| dask | dask-m11282 | 0 | 0 | 0 | 0 |
| dask | dask-m12753 | 0 | 0 | 0 | 0 |
| dask | dask-m1940 | 0 | 0 | 0 | 0 |
| dask | dask-m28832 | 0 | 0 | 0 | 0 |
| dask | dask-m37146 | 0 | 0 | 0 | 0 |
| dvc | control | 0 | 0 | 0 | 0 |
| dvc | dvc-m11576 | 32 | 0 | 0 | 32 |
| dvc | dvc-m12545 | 0 | 0 | 0 | 0 |
| dvc | dvc-m16845 | 0 | 0 | 0 | 0 |
| dvc | dvc-m19066 | 0 | 0 | 0 | 0 |
| dvc | dvc-m6852 | 0 | 0 | 0 | 0 |
| ipython | control | 4 | 1 | 38 | 43 |
| ipython | ipython-m1288 | 6 | 3 | 1 | 10 |
| ipython | ipython-m17283 | 12 | 5 | 12 | 29 |
| ipython | ipython-m22324 | 0 | 5 | 1 | 6 |
| ipython | ipython-m22732 | 4 | 1 | 1 | 6 |
| ipython | ipython-m4267 | 3 | 0 | 0 | 3 |
| librosa | control | 0 | 0 | 0 | 0 |
| librosa | librosa-m0035 | 0 | 0 | 0 | 0 |
| librosa | librosa-m0265 | 0 | 0 | 0 | 0 |
| librosa | librosa-m2885 | 0 | 0 | 0 | 0 |
| librosa | librosa-m4950 | 0 | 0 | 0 | 0 |
| librosa | librosa-m7678 | 0 | 0 | 0 | 0 |
| trimesh | control | 0 | 0 | 0 | 0 |
| trimesh | trimesh-extra | 0 | 0 | 0 | 0 |
| trimesh | trimesh-m13478 | 0 | 0 | 0 | 0 |
| trimesh | trimesh-m21160 | 0 | 0 | 0 | 0 |
| trimesh | trimesh-m25103 | 0 | 0 | 0 | 0 |
| trimesh | trimesh-m3147 | 0 | 0 | 0 | 0 |

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
| `IPython/core/magics/config.py::IPython.core.magics.config.ConfigMagics.config` | 0/3 | 3/3 | 0/3 | 0/3 | ambiente (controle) |
| `IPython/testing/plugin/dtexample.py::IPython.testing.plugin.dtexample.ipos` | 0/3 | 3/3 | 0/3 | 0/3 | ambiente (controle) |
| `tests/test_application.py::test_initialize_stops_at_subapp` | 0/3 | 1/3 | 1/3 | 0/3 | ambiente (controle) |
| `tests/test_completer.py::test_dict_key_completion_contexts` | 0/3 | 0/3 | 1/3 | 0/3 | ambiente (controle) |
| `tests/test_completer.py::test_dict_key_completion_string` | 0/3 | 3/3 | 3/3 | 0/3 | ambiente (controle) |
| `tests/test_completer.py::test_dict_key_completion_unicode_py3` | 0/3 | 3/3 | 3/3 | 0/3 | ambiente (controle) |
| `tests/test_completer.py::test_dict_key_restrict_to_dicts` | 0/3 | 0/3 | 2/3 | 0/3 | ambiente (controle) |
| `tests/test_completer.py::test_func_kw_completions` | 0/3 | 1/3 | 1/3 | 0/3 | ambiente (controle) |
| `tests/test_completer.py::test_magic_completion_shadowing` | 0/3 | 1/3 | 1/3 | 0/3 | ambiente (controle) |
| `tests/test_completer.py::test_matcher_disabling` | 0/3 | 1/3 | 1/3 | 0/3 | ambiente (controle) |
| `tests/test_completer.py::test_mix_terms` | 0/3 | 1/3 | 2/3 | 0/3 | ambiente (controle) |
| `tests/test_completer.py::test_undefined_variables[t = []\nif condition_1:\n    if condition_2:\n        t = 'nested'\nt.-insert_text30-False-limited]` | 0/3 | 1/3 | 0/3 | 0/3 | ambiente (controle) |
| `tests/test_completer.py::test_undefined_variables[t = []\nif condition_1:\n    t = 'string'\nelif condition_2:\n    t = 1\nelif condition_3:\n    t = {}\nt.-insert_text29-False-limited]` | 0/3 | 1/3 | 1/3 | 0/3 | ambiente (controle) |
| `tests/test_completer.py::test_undefined_variables[t = []\nif some_condition:\n    t = 'string'\nelse:\n    t = 1\nt.-insert_text27-False-limited]` | 0/3 | 1/3 | 1/3 | 0/3 | ambiente (controle) |
| `tests/test_completer.py::test_undefined_variables[t = []\nif some_condition:\n    t = 'string'\nt.-insert_text25-False-limited]` | 0/3 | 1/3 | 0/3 | 0/3 | ambiente (controle) |
| `tests/test_completer.py::test_undefined_variables[t = []\nwhile condition_1:\n    while condition_2:\n        t = 'str'\nt.-insert_text33-False-limited]` | 0/3 | 1/3 | 0/3 | 0/3 | ambiente (controle) |
| `tests/test_display_2.py::test_matplotlib_positioning` | 0/3 | 3/3 | 3/3 | 0/3 | ambiente (controle) |
| `tests/test_displayhook.py::test_underscore_no_overwrite_user` | 0/3 | 2/3 | 3/3 | 0/3 | ambiente (controle) |
| `tests/test_editorhooks.py::test_install_editor` | 0/3 | 3/3 | 3/3 | 0/3 | ambiente (controle) |
| `tests/test_editorhooks.py::test_line_none_defaults_to_zero` | 0/3 | 3/3 | 3/3 | 0/3 | ambiente (controle) |
| `tests/test_historyapp.py::test_history_app_trim_subcommand` | 0/3 | 2/3 | 2/3 | 0/3 | ambiente (controle) |
| `tests/test_interactiveshell.py::test_naked_string_cells` | 0/3 | 3/3 | 1/3 | 0/3 | ambiente (controle) |
| `tests/test_interactiveshell.py::test_run_cell_asyncio_run` | 0/3 | 3/3 | 3/3 | 0/3 | ambiente (controle) |
| `tests/test_interactiveshell.py::test_run_cell_await` | 0/3 | 3/3 | 3/3 | 0/3 | ambiente (controle) |
| `tests/test_ipapp.py::test_locate_subcommand` | 0/3 | 1/3 | 1/3 | 0/3 | ambiente (controle) |
| `tests/test_magic.py::test_cell_magic_class` | 0/3 | 1/3 | 3/3 | 0/3 | ambiente (controle) |
| `tests/test_magic.py::test_cell_magic_class2` | 0/3 | 1/3 | 3/3 | 0/3 | ambiente (controle) |
| `tests/test_magic.py::test_cell_magic_func_deco` | 0/3 | 1/3 | 3/3 | 0/3 | ambiente (controle) |
| `tests/test_magic.py::test_cell_magic_reg` | 0/3 | 1/3 | 3/3 | 0/3 | ambiente (controle) |
| `tests/test_magic.py::test_config_available_configs` | 0/3 | 1/3 | 1/3 | 0/3 | ambiente (controle) |
| `tests/test_magic.py::test_line_cell_info` | 0/3 | 1/3 | 1/3 | 0/3 | ambiente (controle) |
| `tests/test_magic.py::test_multiline_time` | 0/3 | 1/3 | 3/3 | 0/3 | ambiente (controle) |
| `tests/test_magic.py::test_notebook_export_json_with_output` | 0/3 | 2/3 | 0/3 | 0/3 | ambiente (controle) |
| `tests/test_magic.py::test_reset_in` | 0/3 | 3/3 | 3/3 | 0/3 | ambiente (controle) |
| `tests/test_magic.py::tests.test_magic.doctest_hist_f` | 0/3 | 1/3 | 0/3 | 0/3 | ambiente (controle) |
| `tests/test_magic.py::tests.test_magic.doctest_who` | 0/3 | 1/3 | 0/3 | 0/3 | ambiente (controle) |
| `tests/test_magic.py::tests.test_magic.test_debug_magic` | 0/3 | 3/3 | 0/3 | 0/3 | ambiente (controle) |
| `tests/test_magic.py::tests.test_magic.test_debug_magic_locals` | 0/3 | 3/3 | 0/3 | 0/3 | ambiente (controle) |
| `tests/test_magics_pylab.py::test_matplotlib_no_arg_prints_backend` | 0/3 | 1/3 | 2/3 | 0/3 | ambiente (controle) |
| `tests/test_profile.py::test_profile_app_list_subcommand` | 0/3 | 1/3 | 1/3 | 0/3 | ambiente (controle) |
| _+12 teste(s), ver flaky_tests.json_ | | | | | |

#### ipython-m17283

| teste | baseline | ranking | regsmart | regsmart-no-rank | classe |
|---|---|---|---|---|---|
| `IPython/core/magics/config.py::IPython.core.magics.config.ConfigMagics.config` | 0/3 | 3/3 | 0/3 | 0/3 | ambiente (controle) |
| `IPython/testing/plugin/dtexample.py::IPython.testing.plugin.dtexample.ipos` | 0/3 | 3/3 | 0/3 | 0/3 | ambiente (controle) |
| `tests/test_application.py::test_initialize_stops_at_subapp` | 0/3 | 0/3 | 1/3 | 0/3 | ambiente (controle) |
| `tests/test_completer.py::test_dict_key_completion_contexts` | 0/3 | 1/3 | 0/3 | 0/3 | ambiente (controle) |
| `tests/test_completer.py::test_dict_key_completion_string` | 0/3 | 3/3 | 3/3 | 0/3 | ambiente (controle) |
| `tests/test_completer.py::test_dict_key_completion_unicode_py3` | 0/3 | 3/3 | 2/3 | 0/3 | ambiente (controle) |
| `tests/test_completer.py::test_dict_key_restrict_to_dicts` | 0/3 | 2/3 | 1/3 | 0/3 | ambiente (controle) |
| `tests/test_completer.py::test_func_kw_completions` | 0/3 | 1/3 | 1/3 | 0/3 | ambiente (controle) |
| `tests/test_completer.py::test_magic_completion_shadowing` | 0/3 | 1/3 | 1/3 | 0/3 | ambiente (controle) |
| `tests/test_completer.py::test_matcher_disabling` | 0/3 | 1/3 | 1/3 | 0/3 | ambiente (controle) |
| `tests/test_completer.py::test_mix_terms` | 0/3 | 1/3 | 1/3 | 0/3 | ambiente (controle) |
| `tests/test_completer.py::test_quoted_file_completions` | 0/3 | 1/3 | 0/3 | 0/3 | ambiente (controle) |
| `tests/test_completer.py::test_undefined_variables[t = []\nif condition_1:\n    if condition_2:\n        t = 'nested'\nt.-insert_text30-False-limited]` | 0/3 | 1/3 | 0/3 | 0/3 | ambiente (controle) |
| `tests/test_completer.py::test_undefined_variables[t = []\nif condition_1:\n    t = 'string'\nelif condition_2:\n    t = 1\nelif condition_3:\n    t = {}\nt.-insert_text29-False-limited]` | 0/3 | 2/3 | 0/3 | 0/3 | ambiente (controle) |
| `tests/test_completer.py::test_undefined_variables[t = []\nif some_condition:\n    t = 'string'\nelse:\n    t = 1\nt.-insert_text27-False-limited]` | 0/3 | 2/3 | 1/3 | 0/3 | ambiente (controle) |
| `tests/test_completer.py::test_undefined_variables[t = []\nif some_condition:\n    t = 'string'\nt.-insert_text25-False-limited]` | 0/3 | 1/3 | 1/3 | 0/3 | ambiente (controle) |
| `tests/test_completer.py::test_undefined_variables[t = []\nwhile condition_1:\n    while condition_2:\n        t = 'str'\nt.-insert_text33-False-limited]` | 0/3 | 1/3 | 0/3 | 0/3 | ambiente (controle) |
| `tests/test_display_2.py::test_matplotlib_positioning` | 0/3 | 3/3 | 3/3 | 0/3 | ambiente (controle) |
| `tests/test_displayhook.py::test_underscore_no_overwrite_user` | 0/3 | 3/3 | 3/3 | 0/3 | ambiente (controle) |
| `tests/test_editorhooks.py::test_install_editor` | 0/3 | 3/3 | 3/3 | 0/3 | ambiente (controle) |
| `tests/test_editorhooks.py::test_line_none_defaults_to_zero` | 0/3 | 3/3 | 3/3 | 0/3 | ambiente (controle) |
| `tests/test_historyapp.py::test_history_app_trim_subcommand` | 0/3 | 2/3 | 2/3 | 0/3 | ambiente (controle) |
| `tests/test_interactiveshell.py::test_naked_string_cells` | 0/3 | 1/3 | 1/3 | 0/3 | ambiente (controle) |
| `tests/test_interactiveshell.py::test_run_cell_asyncio_run` | 0/3 | 3/3 | 3/3 | 0/3 | ambiente (controle) |
| `tests/test_interactiveshell.py::test_run_cell_await` | 0/3 | 3/3 | 3/3 | 0/3 | ambiente (controle) |
| `tests/test_ipapp.py::test_locate_subcommand` | 0/3 | 0/3 | 1/3 | 0/3 | ambiente (controle) |
| `tests/test_magic.py::test_cell_magic_class` | 0/3 | 2/3 | 2/3 | 0/3 | ambiente (controle) |
| `tests/test_magic.py::test_cell_magic_class2` | 0/3 | 2/3 | 2/3 | 0/3 | ambiente (controle) |
| `tests/test_magic.py::test_cell_magic_func_deco` | 0/3 | 2/3 | 2/3 | 0/3 | ambiente (controle) |
| `tests/test_magic.py::test_cell_magic_reg` | 0/3 | 2/3 | 2/3 | 0/3 | ambiente (controle) |
| `tests/test_magic.py::test_config_available_configs` | 0/3 | 1/3 | 3/3 | 0/3 | ambiente (controle) |
| `tests/test_magic.py::test_line_cell_info` | 0/3 | 1/3 | 1/3 | 0/3 | ambiente (controle) |
| `tests/test_magic.py::test_multiline_time` | 0/3 | 2/3 | 3/3 | 0/3 | ambiente (controle) |
| `tests/test_magic.py::test_notebook_export_json_with_output` | 3/3 | 3/3 | 2/3 | 0/3 | ambiente (controle) |
| `tests/test_magic.py::test_reset_in` | 0/3 | 3/3 | 3/3 | 0/3 | ambiente (controle) |
| `tests/test_magic.py::tests.test_magic.doctest_hist_f` | 0/3 | 1/3 | 0/3 | 0/3 | ambiente (controle) |
| `tests/test_magic.py::tests.test_magic.doctest_who` | 0/3 | 1/3 | 0/3 | 0/3 | ambiente (controle) |
| `tests/test_magic.py::tests.test_magic.test_debug_magic` | 0/3 | 3/3 | 0/3 | 0/3 | ambiente (controle) |
| `tests/test_magic.py::tests.test_magic.test_debug_magic_locals` | 0/3 | 3/3 | 0/3 | 0/3 | ambiente (controle) |
| `tests/test_magics_pylab.py::test_matplotlib_no_arg_prints_backend` | 0/3 | 2/3 | 1/3 | 0/3 | ambiente (controle) |
| _+34 teste(s), ver flaky_tests.json_ | | | | | |

#### ipython-m22324

| teste | baseline | ranking | regsmart | regsmart-no-rank | classe |
|---|---|---|---|---|---|
| `IPython/core/magics/config.py::IPython.core.magics.config.ConfigMagics.config` | 0/3 | 3/3 | 0/3 | 0/3 | ambiente (controle) |
| `IPython/testing/plugin/dtexample.py::IPython.testing.plugin.dtexample.ipos` | 0/3 | 3/3 | 0/3 | 0/3 | ambiente (controle) |
| `tests/test_completer.py::test_dict_key_completion_contexts` | 0/3 | 1/3 | 1/3 | 0/3 | ambiente (controle) |
| `tests/test_completer.py::test_dict_key_completion_string` | 0/3 | 3/3 | 3/3 | 0/3 | ambiente (controle) |
| `tests/test_completer.py::test_dict_key_completion_unicode_py3` | 0/3 | 3/3 | 3/3 | 0/3 | ambiente (controle) |
| `tests/test_completer.py::test_dict_key_restrict_to_dicts` | 0/3 | 1/3 | 2/3 | 0/3 | ambiente (controle) |
| `tests/test_completer.py::test_func_kw_completions` | 0/3 | 1/3 | 1/3 | 0/3 | ambiente (controle) |
| `tests/test_completer.py::test_magic_completion_shadowing` | 0/3 | 2/3 | 1/3 | 0/3 | ambiente (controle) |
| `tests/test_completer.py::test_matcher_disabling` | 0/3 | 0/3 | 1/3 | 0/3 | ambiente (controle) |
| `tests/test_completer.py::test_mix_terms` | 0/3 | 1/3 | 1/3 | 0/3 | ambiente (controle) |
| `tests/test_completer.py::test_quoted_file_completions` | 0/3 | 1/3 | 1/3 | 0/3 | ambiente (controle) |
| `tests/test_completer.py::test_undefined_variables[t = []\nif condition_1:\n    if condition_2:\n        t = 'nested'\nt.-insert_text30-False-limited]` | 0/3 | 1/3 | 0/3 | 0/3 | ambiente (controle) |
| `tests/test_completer.py::test_undefined_variables[t = []\nif condition_1:\n    t = 'string'\nelif condition_2:\n    t = 1\nelif condition_3:\n    t = {}\nt.-insert_text29-False-limited]` | 0/3 | 1/3 | 1/3 | 0/3 | ambiente (controle) |
| `tests/test_completer.py::test_undefined_variables[t = []\nif some_condition:\n    t = 'string'\nelse:\n    t = 1\nt.-insert_text27-False-limited]` | 0/3 | 1/3 | 1/3 | 0/3 | ambiente (controle) |
| `tests/test_completer.py::test_undefined_variables[t = []\nif some_condition:\n    t = 'string'\nt.-insert_text25-False-limited]` | 0/3 | 1/3 | 0/3 | 0/3 | ambiente (controle) |
| `tests/test_display_2.py::test_matplotlib_positioning` | 0/3 | 3/3 | 3/3 | 0/3 | ambiente (controle) |
| `tests/test_displayhook.py::test_underscore_no_overwrite_user` | 0/3 | 1/3 | 3/3 | 0/3 | ambiente (controle) |
| `tests/test_editorhooks.py::test_install_editor` | 0/3 | 2/3 | 1/3 | 0/3 | ambiente (controle) |
| `tests/test_editorhooks.py::test_line_none_defaults_to_zero` | 0/3 | 2/3 | 1/3 | 0/3 | ambiente (controle) |
| `tests/test_historyapp.py::test_history_app_trim_subcommand` | 0/3 | 2/3 | 2/3 | 0/3 | ambiente (controle) |
| `tests/test_interactiveshell.py::test_naked_string_cells` | 0/3 | 2/3 | 1/3 | 0/3 | ambiente (controle) |
| `tests/test_interactiveshell.py::test_run_cell_asyncio_run` | 0/3 | 3/3 | 3/3 | 0/3 | ambiente (controle) |
| `tests/test_interactiveshell.py::test_run_cell_await` | 0/3 | 3/3 | 3/3 | 0/3 | ambiente (controle) |
| `tests/test_magic.py::test_cell_magic_class` | 0/3 | 1/3 | 2/3 | 0/3 | ambiente (controle) |
| `tests/test_magic.py::test_cell_magic_class2` | 0/3 | 1/3 | 2/3 | 0/3 | ambiente (controle) |
| `tests/test_magic.py::test_cell_magic_func_deco` | 0/3 | 1/3 | 2/3 | 0/3 | ambiente (controle) |
| `tests/test_magic.py::test_cell_magic_reg` | 0/3 | 1/3 | 2/3 | 0/3 | ambiente (controle) |
| `tests/test_magic.py::test_config_available_configs` | 0/3 | 2/3 | 2/3 | 0/3 | ambiente (controle) |
| `tests/test_magic.py::test_line_cell_info` | 0/3 | 1/3 | 1/3 | 0/3 | ambiente (controle) |
| `tests/test_magic.py::test_multiline_time` | 0/3 | 1/3 | 3/3 | 0/3 | ambiente (controle) |
| `tests/test_magic.py::test_notebook_export_json_with_output` | 0/3 | 2/3 | 0/3 | 0/3 | ambiente (controle) |
| `tests/test_magic.py::test_reset_in` | 0/3 | 3/3 | 3/3 | 0/3 | ambiente (controle) |
| `tests/test_magic.py::tests.test_magic.doctest_hist_f` | 0/3 | 1/3 | 0/3 | 0/3 | ambiente (controle) |
| `tests/test_magic.py::tests.test_magic.doctest_who` | 0/3 | 1/3 | 0/3 | 0/3 | ambiente (controle) |
| `tests/test_magic.py::tests.test_magic.test_debug_magic` | 0/3 | 3/3 | 0/3 | 0/3 | ambiente (controle) |
| `tests/test_magic.py::tests.test_magic.test_debug_magic_locals` | 0/3 | 3/3 | 0/3 | 0/3 | ambiente (controle) |
| `tests/test_magics_pylab.py::test_matplotlib_no_arg_prints_backend` | 0/3 | 1/3 | 3/3 | 0/3 | ambiente (controle) |
| `tests/test_run.py::test_run_tb` | 0/3 | 1/3 | 0/3 | 0/3 | ambiente (controle) |
| `tests/test_storemagic.py::test_store_restore` | 0/3 | 1/3 | 2/3 | 0/3 | ambiente (controle) |
| `tests/test_completer.py::test_file_completions_only_in_path_contexts` | 0/3 | 0/3 | 1/3 | 0/3 | só no plugin (flaky) |
| _+5 teste(s), ver flaky_tests.json_ | | | | | |

#### ipython-m22732

| teste | baseline | ranking | regsmart | regsmart-no-rank | classe |
|---|---|---|---|---|---|
| `IPython/core/magics/config.py::IPython.core.magics.config.ConfigMagics.config` | 0/3 | 3/3 | 0/3 | 0/3 | ambiente (controle) |
| `IPython/testing/plugin/dtexample.py::IPython.testing.plugin.dtexample.ipos` | 0/3 | 3/3 | 0/3 | 0/3 | ambiente (controle) |
| `tests/test_application.py::test_initialize_stops_at_subapp` | 0/3 | 1/3 | 0/3 | 0/3 | ambiente (controle) |
| `tests/test_completer.py::test_dict_key_completion_string` | 0/3 | 2/3 | 3/3 | 0/3 | ambiente (controle) |
| `tests/test_completer.py::test_dict_key_completion_unicode_py3` | 0/3 | 3/3 | 2/3 | 0/3 | ambiente (controle) |
| `tests/test_completer.py::test_dict_key_restrict_to_dicts` | 0/3 | 1/3 | 1/3 | 0/3 | ambiente (controle) |
| `tests/test_completer.py::test_func_kw_completions` | 0/3 | 1/3 | 1/3 | 0/3 | ambiente (controle) |
| `tests/test_completer.py::test_magic_completion_shadowing` | 0/3 | 1/3 | 1/3 | 0/3 | ambiente (controle) |
| `tests/test_completer.py::test_matcher_disabling` | 0/3 | 1/3 | 1/3 | 0/3 | ambiente (controle) |
| `tests/test_completer.py::test_mix_terms` | 0/3 | 1/3 | 1/3 | 0/3 | ambiente (controle) |
| `tests/test_completer.py::test_quoted_file_completions` | 0/3 | 1/3 | 1/3 | 0/3 | ambiente (controle) |
| `tests/test_completer.py::test_undefined_variables[t = []\nif condition_1:\n    if condition_2:\n        t = 'nested'\nt.-insert_text30-False-limited]` | 0/3 | 1/3 | 0/3 | 0/3 | ambiente (controle) |
| `tests/test_completer.py::test_undefined_variables[t = []\nif condition_1:\n    t = 'string'\nelif condition_2:\n    t = 1\nelif condition_3:\n    t = {}\nt.-insert_text29-False-limited]` | 0/3 | 1/3 | 1/3 | 0/3 | ambiente (controle) |
| `tests/test_completer.py::test_undefined_variables[t = []\nif some_condition:\n    t = 'string'\nelse:\n    t = 1\nt.-insert_text27-False-limited]` | 0/3 | 1/3 | 1/3 | 0/3 | ambiente (controle) |
| `tests/test_completer.py::test_undefined_variables[t = []\nwhile condition_1:\n    while condition_2:\n        t = 'str'\nt.-insert_text33-False-limited]` | 0/3 | 1/3 | 0/3 | 0/3 | ambiente (controle) |
| `tests/test_display_2.py::test_matplotlib_positioning` | 0/3 | 3/3 | 3/3 | 0/3 | ambiente (controle) |
| `tests/test_displayhook.py::test_underscore_no_overwrite_user` | 0/3 | 2/3 | 3/3 | 0/3 | ambiente (controle) |
| `tests/test_editorhooks.py::test_install_editor` | 0/3 | 3/3 | 3/3 | 0/3 | ambiente (controle) |
| `tests/test_editorhooks.py::test_line_none_defaults_to_zero` | 0/3 | 3/3 | 3/3 | 0/3 | ambiente (controle) |
| `tests/test_historyapp.py::test_history_app_trim_subcommand` | 0/3 | 2/3 | 2/3 | 0/3 | ambiente (controle) |
| `tests/test_interactiveshell.py::test_naked_string_cells` | 0/3 | 1/3 | 1/3 | 0/3 | ambiente (controle) |
| `tests/test_interactiveshell.py::test_run_cell_asyncio_run` | 0/3 | 3/3 | 3/3 | 0/3 | ambiente (controle) |
| `tests/test_interactiveshell.py::test_run_cell_await` | 0/3 | 3/3 | 3/3 | 0/3 | ambiente (controle) |
| `tests/test_ipapp.py::test_locate_subcommand` | 0/3 | 1/3 | 0/3 | 0/3 | ambiente (controle) |
| `tests/test_magic.py::test_cell_magic_class` | 0/3 | 2/3 | 3/3 | 0/3 | ambiente (controle) |
| `tests/test_magic.py::test_cell_magic_class2` | 0/3 | 2/3 | 3/3 | 0/3 | ambiente (controle) |
| `tests/test_magic.py::test_cell_magic_func_deco` | 0/3 | 2/3 | 3/3 | 0/3 | ambiente (controle) |
| `tests/test_magic.py::test_cell_magic_reg` | 0/3 | 1/3 | 3/3 | 0/3 | ambiente (controle) |
| `tests/test_magic.py::test_config_available_configs` | 0/3 | 1/3 | 2/3 | 0/3 | ambiente (controle) |
| `tests/test_magic.py::test_line_cell_info` | 0/3 | 0/3 | 1/3 | 0/3 | ambiente (controle) |
| `tests/test_magic.py::test_multiline_time` | 0/3 | 2/3 | 3/3 | 0/3 | ambiente (controle) |
| `tests/test_magic.py::test_notebook_export_json_with_output` | 0/3 | 2/3 | 0/3 | 0/3 | ambiente (controle) |
| `tests/test_magic.py::test_reset_in` | 0/3 | 3/3 | 3/3 | 0/3 | ambiente (controle) |
| `tests/test_magic.py::tests.test_magic.doctest_hist_f` | 0/3 | 1/3 | 0/3 | 0/3 | ambiente (controle) |
| `tests/test_magic.py::tests.test_magic.doctest_who` | 0/3 | 1/3 | 0/3 | 0/3 | ambiente (controle) |
| `tests/test_magic.py::tests.test_magic.test_debug_magic` | 0/3 | 3/3 | 0/3 | 0/3 | ambiente (controle) |
| `tests/test_magic.py::tests.test_magic.test_debug_magic_locals` | 0/3 | 3/3 | 0/3 | 0/3 | ambiente (controle) |
| `tests/test_magics_pylab.py::test_matplotlib_no_arg_prints_backend` | 0/3 | 3/3 | 3/3 | 0/3 | ambiente (controle) |
| `tests/test_profile.py::test_profile_app_list_subcommand` | 0/3 | 1/3 | 0/3 | 0/3 | ambiente (controle) |
| `tests/test_run.py::test_run_tb` | 0/3 | 1/3 | 0/3 | 0/3 | ambiente (controle) |
| _+7 teste(s), ver flaky_tests.json_ | | | | | |

#### ipython-m4267

| teste | baseline | ranking | regsmart | regsmart-no-rank | classe |
|---|---|---|---|---|---|
| `IPython/core/magics/config.py::IPython.core.magics.config.ConfigMagics.config` | 0/3 | 3/3 | 0/3 | 0/3 | ambiente (controle) |
| `IPython/testing/plugin/dtexample.py::IPython.testing.plugin.dtexample.ipos` | 0/3 | 3/3 | 0/3 | 0/3 | ambiente (controle) |
| `tests/test_application.py::test_initialize_stops_at_subapp` | 0/3 | 0/3 | 1/3 | 0/3 | ambiente (controle) |
| `tests/test_completer.py::test_dict_key_completion_string` | 0/3 | 3/3 | 3/3 | 0/3 | ambiente (controle) |
| `tests/test_completer.py::test_dict_key_completion_unicode_py3` | 0/3 | 3/3 | 3/3 | 0/3 | ambiente (controle) |
| `tests/test_completer.py::test_dict_key_restrict_to_dicts` | 0/3 | 0/3 | 2/3 | 0/3 | ambiente (controle) |
| `tests/test_completer.py::test_func_kw_completions` | 0/3 | 1/3 | 1/3 | 0/3 | ambiente (controle) |
| `tests/test_completer.py::test_magic_completion_shadowing` | 0/3 | 1/3 | 1/3 | 0/3 | ambiente (controle) |
| `tests/test_completer.py::test_matcher_disabling` | 0/3 | 2/3 | 1/3 | 0/3 | ambiente (controle) |
| `tests/test_completer.py::test_mix_terms` | 0/3 | 1/3 | 1/3 | 0/3 | ambiente (controle) |
| `tests/test_completer.py::test_quoted_file_completions` | 0/3 | 1/3 | 0/3 | 0/3 | ambiente (controle) |
| `tests/test_completer.py::test_undefined_variables[t = []\nif condition_1:\n    if condition_2:\n        t = 'nested'\nt.-insert_text30-False-limited]` | 0/3 | 1/3 | 0/3 | 0/3 | ambiente (controle) |
| `tests/test_completer.py::test_undefined_variables[t = []\nif condition_1:\n    t = 'string'\nelif condition_2:\n    t = 1\nelif condition_3:\n    t = {}\nt.-insert_text29-False-limited]` | 0/3 | 1/3 | 1/3 | 0/3 | ambiente (controle) |
| `tests/test_completer.py::test_undefined_variables[t = []\nif some_condition:\n    t = 'string'\nelse:\n    t = 1\nt.-insert_text27-False-limited]` | 0/3 | 1/3 | 1/3 | 0/3 | ambiente (controle) |
| `tests/test_completer.py::test_undefined_variables[t = []\nwhile condition_1:\n    while condition_2:\n        t = 'str'\nt.-insert_text33-False-limited]` | 0/3 | 1/3 | 0/3 | 0/3 | ambiente (controle) |
| `tests/test_display_2.py::test_matplotlib_positioning` | 0/3 | 3/3 | 3/3 | 0/3 | ambiente (controle) |
| `tests/test_displayhook.py::test_underscore_no_overwrite_user` | 0/3 | 3/3 | 3/3 | 0/3 | ambiente (controle) |
| `tests/test_editorhooks.py::test_install_editor` | 0/3 | 3/3 | 3/3 | 0/3 | ambiente (controle) |
| `tests/test_editorhooks.py::test_line_none_defaults_to_zero` | 0/3 | 3/3 | 3/3 | 0/3 | ambiente (controle) |
| `tests/test_historyapp.py::test_history_app_trim_subcommand` | 0/3 | 2/3 | 2/3 | 0/3 | ambiente (controle) |
| `tests/test_interactiveshell.py::test_naked_string_cells` | 0/3 | 3/3 | 0/3 | 0/3 | ambiente (controle) |
| `tests/test_interactiveshell.py::test_run_cell_asyncio_run` | 0/3 | 3/3 | 3/3 | 0/3 | ambiente (controle) |
| `tests/test_interactiveshell.py::test_run_cell_await` | 0/3 | 3/3 | 3/3 | 0/3 | ambiente (controle) |
| `tests/test_ipapp.py::test_locate_subcommand` | 0/3 | 0/3 | 1/3 | 0/3 | ambiente (controle) |
| `tests/test_magic.py::test_cell_magic_class` | 0/3 | 2/3 | 2/3 | 0/3 | ambiente (controle) |
| `tests/test_magic.py::test_cell_magic_class2` | 0/3 | 2/3 | 2/3 | 0/3 | ambiente (controle) |
| `tests/test_magic.py::test_cell_magic_func_deco` | 0/3 | 2/3 | 2/3 | 0/3 | ambiente (controle) |
| `tests/test_magic.py::test_cell_magic_reg` | 0/3 | 2/3 | 2/3 | 0/3 | ambiente (controle) |
| `tests/test_magic.py::test_config_available_configs` | 0/3 | 1/3 | 2/3 | 0/3 | ambiente (controle) |
| `tests/test_magic.py::test_line_cell_info` | 0/3 | 1/3 | 1/3 | 0/3 | ambiente (controle) |
| `tests/test_magic.py::test_multiline_time` | 0/3 | 2/3 | 2/3 | 0/3 | ambiente (controle) |
| `tests/test_magic.py::test_notebook_export_json_with_output` | 0/3 | 2/3 | 0/3 | 0/3 | ambiente (controle) |
| `tests/test_magic.py::test_reset_in` | 0/3 | 3/3 | 3/3 | 0/3 | ambiente (controle) |
| `tests/test_magic.py::tests.test_magic.doctest_hist_f` | 0/3 | 1/3 | 0/3 | 0/3 | ambiente (controle) |
| `tests/test_magic.py::tests.test_magic.doctest_who` | 0/3 | 1/3 | 0/3 | 0/3 | ambiente (controle) |
| `tests/test_magic.py::tests.test_magic.test_debug_magic` | 0/3 | 3/3 | 0/3 | 0/3 | ambiente (controle) |
| `tests/test_magic.py::tests.test_magic.test_debug_magic_locals` | 0/3 | 3/3 | 0/3 | 0/3 | ambiente (controle) |
| `tests/test_magics_pylab.py::test_matplotlib_no_arg_prints_backend` | 0/3 | 3/3 | 3/3 | 0/3 | ambiente (controle) |
| `tests/test_profile.py::test_profile_app_list_subcommand` | 0/3 | 0/3 | 1/3 | 0/3 | ambiente (controle) |
| `tests/test_run.py::test_run_tb` | 0/3 | 1/3 | 0/3 | 0/3 | ambiente (controle) |
| _+4 teste(s), ver flaky_tests.json_ | | | | | |


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


