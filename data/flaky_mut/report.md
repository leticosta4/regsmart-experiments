# Flaky runner — relatório

## Custo

- Início: `2026-10-08T19:07:56.558771+00:00`
- Fim: `2026-10-08T23:03:06.418363+00:00`
- Tempo ativo do script: **58m24s**
- Janela real dos runs (1º dispatch → última conclusão): **3h54m38s** (inclui fila)
- Minutos de runner somados: **1021.6 min**
- Pico de concorrência medido: **20** jobs (teto do plano Free: 20)

## API / rate limit

- Requisições: 241 GET, 120 POST
- Retries: 0
- Rate limit (final): 47/5000 consumidos, reseta em `2026-10-08T23:51:24+00:00`

## Saúde da execução

| Métrica | warm-up | repetições |
|---|---|---|
| Tarefas no plano | 0 | 120 |
| Despachadas | 0 | 120 |
| Com run_id | 0 | 120 |
| Sucesso | 0 | 12 |
| Falha (testes falharam) | 0 | 108 |
| Canceladas | 0 | 0 |
| Em andamento | 0 | 0 |
| Dispatch falhou / run perdido | 0 | 0 |

## Por repositório

| repo | runs | success | failure | cancelled | em andamento | makespan | min runner |
|---|---|---|---|---|---|---|---|
| ipython | 60 | 0 | 60 | 0 | 0 | 20m55s | 375.6 |
| trimesh | 60 | 12 | 48 | 0 | 0 | 36m25s | 646.0 |

## Por workflow

| workflow | runs | min runner |
|---|---|---|
| baseline | 30 | 129.7 |
| ranking | 30 | 528.5 |
| regsmart | 30 | 273.4 |
| regsmart-no-rank | 30 | 90.1 |

## Testes flaky

Cada teste que falhou é classificado comparando o **baseline** com os workflows de plugin, no mesmo SHA do mutante. Células = falhas/execuções (do job que mais falhou).

| classe | significado |
|---|---|
| flaky | falha em algumas execuções do baseline e passa em outras |
| só no plugin (flaky) | baseline nunca falhou; falha às vezes sob plugin (provável dependência de ordem exposta pelo reordenamento) |
| só no plugin (fixa) | baseline nunca falhou; falha em todas as execuções de algum plugin (investigar o plugin) |
| esperada, diverge | falha sempre no baseline, mas não em todos os workflows (RTS não selecionou ou a ordem mudou o resultado) |
| esperada | falha sempre em todos os workflows: efeito do mutante (ou falha pré-existente); só contada |
| indeterminado / sem baseline | poucas execuções ou baseline ausente |

### Resumo

| repo | mutante | flaky | só plugin (flaky) | só plugin (fixa) | esperada, diverge | esperada | outros |
|---|---|---|---|---|---|---|---|
| ipython | ipython-m1288 | 0 | 38 | 9 | 0 | 1 | 0 |
| ipython | ipython-m17283 | 0 | 60 | 6 | 30 | 5 | 0 |
| ipython | ipython-m22324 | 0 | 57 | 8 | 0 | 1 | 0 |
| ipython | ipython-m22732 | 0 | 39 | 8 | 0 | 1 | 0 |
| ipython | ipython-m4267 | 0 | 45 | 9 | 0 | 1 | 0 |
| trimesh | trimesh-m13478 | 0 | 0 | 0 | 0 | 1 | 0 |
| trimesh | trimesh-m1825 | 0 | 0 | 0 | 0 | 1 | 0 |
| trimesh | trimesh-m21160 | 0 | 0 | 0 | 0 | 2 | 0 |
| trimesh | trimesh-m25103 | 0 | 0 | 0 | 0 | 7 | 0 |
| trimesh | trimesh-m3147 | 0 | 0 | 0 | 0 | 0 | 0 |

### Só no plugin: em quais workflows falhou

Testes que nunca falharam no baseline (flaky + fixa), cada um contado uma vez, na combinação exata de workflows em que falhou. `ranking+regsmart` = falhou nos dois.

| repo | mutante | ranking | regsmart | ranking+regsmart | regsmart+regsmart-no-rank | total |
|---|---|---|---|---|---|---|
| ipython | ipython-m1288 | 39 | 1 | 7 | 0 | 47 |
| ipython | ipython-m17283 | 59 | 0 | 7 | 0 | 66 |
| ipython | ipython-m22324 | 58 | 0 | 7 | 0 | 65 |
| ipython | ipython-m22732 | 14 | 3 | 29 | 1 | 47 |
| ipython | ipython-m4267 | 47 | 0 | 7 | 0 | 54 |
| trimesh | trimesh-m13478 | 0 | 0 | 0 | 0 | 0 |
| trimesh | trimesh-m1825 | 0 | 0 | 0 | 0 | 0 |
| trimesh | trimesh-m21160 | 0 | 0 | 0 | 0 | 0 |
| trimesh | trimesh-m25103 | 0 | 0 | 0 | 0 | 0 |
| trimesh | trimesh-m3147 | 0 | 0 | 0 | 0 | 0 |

### ipython

#### ipython-m1288

| teste | baseline | ranking | regsmart | regsmart-no-rank | classe |
|---|---|---|---|---|---|
| `   ProfileLocate:history.py:793 Failed to create history session in /tmp/pytest-of-runner/pytest-0/test_histmanager_memory_fallba0/history.sqlite. History will not be saved.` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_application.py::test_initialize_stops_at_subapp` | 0/3 | 2/3 | 1/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_dataframe_key_completion` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_dict_key_completion_bytes` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_dict_key_completion_string` | 0/3 | 3/3 | 2/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_dict_key_restrict_to_dicts` | 0/3 | 0/3 | 2/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_func_kw_completions` | 0/3 | 1/3 | 1/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_magic_completion_order` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_magic_completion_shadowing` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_misc_no_jedi_completions[a="str"; b=1-(a, b).-expected1-not_expected1]` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_mix_terms` | 0/3 | 2/3 | 1/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_undefined_variables[a = []\nwhile condition:\n    a.-append-False-limited]` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_undefined_variables[t = []\nif condition_1:\n    t = 'string'\nelif condition_2:\n    t = 1\nelif condition_3:\n    t = {}\nt.-insert_text29-False-limited]` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_undefined_variables[t = []\nif some_condition:\n    t.-append-False-limited]` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_undefined_variables_without_jedi[t: int \| str\nt.-insert_text3]` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_displayhook.py::test_underscore_no_overwrite_builtins` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_displayhook.py::test_underscore_no_overwrite_user` | 0/3 | 3/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_history.py::test_histmanager_memory_fallback_reopens_db` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_historyapp.py::test_history_app_trim_subcommand` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_interactiveshell.py::test_naked_string_cells` | 0/3 | 2/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_interactiveshell.py::test_run_cell_asyncio_run` | 0/3 | 3/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_interactiveshell.py::test_run_cell_await` | 0/3 | 3/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_ipapp.py::test_locate_subcommand` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magic.py::test_cell_magic_class` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magic.py::test_cell_magic_class2` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magic.py::test_cell_magic_func_deco` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magic.py::test_cell_magic_reg` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magic.py::test_config_available_configs` | 0/3 | 2/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magic.py::test_dirops` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magic.py::test_multiline_time` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magic.py::test_time_raise_on_interrupt` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magic.py::test_timeit_raise_on_interrupt` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magic.py::tests.test_magic.doctest_hist_op` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magics_pylab.py::test_matplotlib_no_arg_prints_backend` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_profile.py::test_profile_app_list_subcommand` | 0/3 | 2/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_run.py::test_builtins_id` | 0/3 | 2/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_run.py::test_run_tb` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_storemagic.py::test_store_restore` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `IPython/core/magics/config.py::IPython.core.magics.config.ConfigMagics.config` | 0/3 | 3/3 | 0/3 | 0/3 | só no plugin (fixa) |
| `IPython/testing/plugin/dtexample.py::IPython.testing.plugin.dtexample.ipos` | 0/3 | 3/3 | 0/3 | 0/3 | só no plugin (fixa) |
| _+7 teste(s), ver flaky_tests.json_ | | | | | |

#### ipython-m17283

| teste | baseline | ranking | regsmart | regsmart-no-rank | classe |
|---|---|---|---|---|---|
| `   ProfileLocate:history.py:793 Failed to create history session in /tmp/pytest-of-runner/pytest-0/test_histmanager_memory_fallba0/history.sqlite. History will not be saved.` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `IPython/core/magics/config.py::IPython.core.magics.config.ConfigMagics.config` | 0/3 | 3/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_application.py::test_initialize_stops_at_subapp` | 0/3 | 2/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_backgroundjobs.py::test_dead_job_attributes` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_backgroundjobs.py::test_traceback` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_dict_key_completion_string` | 0/3 | 3/3 | 1/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_dict_key_restrict_to_dicts` | 0/3 | 2/3 | 1/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_func_kw_completions` | 0/3 | 1/3 | 1/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_magic_completion_order` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_magic_completion_shadowing` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_mix_terms` | 0/3 | 2/3 | 1/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_quoted_file_completions` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_undefined_variables[a = []\nwhile condition:\n    a.-append-False-limited]` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_undefined_variables[t = []\nif condition_1:\n    t = 'string'\nelif condition_2:\n    t = 1\nelif condition_3:\n    t = {}\nt.-insert_text29-False-limited]` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_undefined_variables[t = []\nif some_condition:\n    t = 'string'\nelse:\n    t = 1\nt.-insert_text27-False-limited]` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_displayhook.py::test_underscore_no_overwrite_builtins` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_displayhook.py::test_underscore_no_overwrite_user` | 0/3 | 3/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_formatters.py::test_bad_repr_traceback` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_formatters.py::test_error_method` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_formatters.py::test_error_pretty_method` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_formatters.py::test_warn_error_for_type` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_history.py::test_histmanager_memory_fallback_reopens_db` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_historyapp.py::test_history_app_trim_subcommand` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_interactiveshell.py::test_input_rejection` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_interactiveshell.py::test_multiline_string_cells` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_interactiveshell.py::test_naked_string_cells` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_interactiveshell.py::test_run_cell_asyncio_run` | 0/3 | 3/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_interactiveshell.py::test_run_cell_await` | 0/3 | 3/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_ipapp.py::test_locate_subcommand` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magic.py::test_cd_force_quiet` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magic.py::test_cell_magic_class` | 0/3 | 2/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magic.py::test_cell_magic_class2` | 0/3 | 2/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magic.py::test_cell_magic_func_deco` | 0/3 | 2/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magic.py::test_cell_magic_reg` | 0/3 | 2/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magic.py::test_config_available_configs` | 0/3 | 3/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magic.py::test_dirops` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magic.py::test_line_cell_info` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magic.py::test_multiline_time` | 0/3 | 2/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magic.py::test_script_do_not_raise_on_interrupt` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magic.py::test_script_raise_on_interrupt` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| _+56 teste(s), ver flaky_tests.json_ | | | | | |

#### ipython-m22324

| teste | baseline | ranking | regsmart | regsmart-no-rank | classe |
|---|---|---|---|---|---|
| `   LocateIPythonApp:history.py:793 Failed to create history session in /tmp/pytest-of-runner/pytest-0/test_histmanager_memory_fallba0/history.sqlite. History will not be saved.` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `IPython/core/magics/config.py::IPython.core.magics.config.ConfigMagics.config` | 0/3 | 3/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_application.py::test_initialize_stops_at_subapp` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_dict_key_completion_string` | 0/3 | 3/3 | 1/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_dict_key_restrict_to_dicts` | 0/3 | 2/3 | 1/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_func_kw_completions` | 0/3 | 1/3 | 1/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_magic_completion_shadowing` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_mix_terms` | 0/3 | 1/3 | 2/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_quoted_file_completions` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_undefined_variables[a = []\nwhile condition:\n    a.-append-False-limited]` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_debug_magic.py::test_debug_magic_passes_through_generators` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_debugger.py::test_where_erase_value` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_debugger.py::test_xmode_skip` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_displayhook.py::test_underscore_no_overwrite_builtins` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_displayhook.py::test_underscore_no_overwrite_user` | 0/3 | 3/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_embed.py::test_nest_embed` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_help.py::test_locate_help` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_help.py::test_locate_profile_help` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_help.py::test_profile_create_help` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_help.py::test_profile_help` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_help.py::test_profile_list_help` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_help.py::test_trust_help` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_history.py::test_histmanager_memory_fallback_reopens_db` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_history.py::test_history_trim_cli[subcommand0-2]` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_history.py::test_history_trim_cli[subcommand1-0]` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_historyapp.py::test_history_app_trim_subcommand` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_interactiveshell.py::test_extraneous_loads` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_interactiveshell.py::test_naked_string_cells` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_interactiveshell.py::test_run_cell_asyncio_run` | 0/3 | 3/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_interactiveshell.py::test_run_cell_await` | 0/3 | 3/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magic.py::test_cd_force_quiet` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magic.py::test_cell_magic_class` | 0/3 | 2/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magic.py::test_cell_magic_class2` | 0/3 | 2/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magic.py::test_cell_magic_func_deco` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magic.py::test_cell_magic_reg` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magic.py::test_config_available_configs` | 0/3 | 3/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magic.py::test_dirops` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magic.py::test_line_cell_info` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magic.py::test_multiline_time` | 0/3 | 2/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magic.py::test_time_raise_on_interrupt` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| _+25 teste(s), ver flaky_tests.json_ | | | | | |

#### ipython-m22732

| teste | baseline | ranking | regsmart | regsmart-no-rank | classe |
|---|---|---|---|---|---|
| `   ProfileLocate:history.py:793 Failed to create history session in /tmp/pytest-of-runner/pytest-0/test_histmanager_memory_fallba0/history.sqlite. History will not be saved.` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_application.py::test_initialize_stops_at_subapp` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_dataframe_key_completion` | 0/3 | 0/3 | 1/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_dict_key_completion_string` | 0/3 | 3/3 | 3/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_dict_key_completion_unicode_py3` | 0/3 | 3/3 | 2/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_dict_key_restrict_to_dicts` | 0/3 | 2/3 | 2/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_func_kw_completions` | 0/3 | 1/3 | 1/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_magic_completion_shadowing` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_mix_terms` | 0/3 | 1/3 | 1/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_omit__names` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_struct_array_key_completion` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_undefined_variables[a = []\nwhile condition:\n    a.-append-False-limited]` | 0/3 | 1/3 | 1/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_undefined_variables[t = []\nif condition_1:\n    t = 'string'\nelif condition_2:\n    t = 1\nelif condition_3:\n    t = {}\nt.-insert_text29-False-limited]` | 0/3 | 1/3 | 1/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_undefined_variables[t = []\nif some_condition:\n    t = 'string'\nt.-insert_text25-False-limited]` | 0/3 | 0/3 | 1/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_undefined_variables_without_jedi[t: int \| str\nt.-insert_text3]` | 0/3 | 1/3 | 1/3 | 0/3 | só no plugin (flaky) |
| `tests/test_displayhook.py::test_underscore_no_overwrite_builtins` | 0/3 | 1/3 | 1/3 | 0/3 | só no plugin (flaky) |
| `tests/test_displayhook.py::test_underscore_no_overwrite_user` | 0/3 | 3/3 | 3/3 | 0/3 | só no plugin (flaky) |
| `tests/test_history.py::test_histmanager_memory_fallback_reopens_db` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_historyapp.py::test_history_app_trim_subcommand` | 0/3 | 1/3 | 1/3 | 0/3 | só no plugin (flaky) |
| `tests/test_interactiveshell.py::test_naked_string_cells` | 0/3 | 2/3 | 1/3 | 0/3 | só no plugin (flaky) |
| `tests/test_interactiveshell.py::test_run_cell_asyncio_run` | 0/3 | 3/3 | 3/3 | 0/3 | só no plugin (flaky) |
| `tests/test_interactiveshell.py::test_run_cell_await` | 0/3 | 3/3 | 3/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magic.py::test_cell_magic_class` | 0/3 | 1/3 | 3/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magic.py::test_cell_magic_class2` | 0/3 | 1/3 | 3/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magic.py::test_cell_magic_func_deco` | 0/3 | 1/3 | 3/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magic.py::test_cell_magic_reg` | 0/3 | 1/3 | 3/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magic.py::test_dirops` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magic.py::test_line_cell_info` | 0/3 | 0/3 | 1/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magic.py::test_multiline_time` | 0/3 | 1/3 | 3/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magic.py::test_reset_in` | 0/3 | 3/3 | 3/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magic.py::test_reset_out` | 0/3 | 0/3 | 1/3 | 3/3 | só no plugin (flaky) |
| `tests/test_magic.py::test_time_raise_on_interrupt` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magic.py::test_timeit_raise_on_interrupt` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magic.py::tests.test_magic.doctest_hist_op` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magics_pylab.py::test_matplotlib_no_arg_prints_backend` | 0/3 | 1/3 | 1/3 | 0/3 | só no plugin (flaky) |
| `tests/test_profile.py::test_profile_app_list_subcommand` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_run.py::test_builtins_id` | 0/3 | 2/3 | 2/3 | 0/3 | só no plugin (flaky) |
| `tests/test_run.py::test_run_tb` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_storemagic.py::test_store_restore` | 0/3 | 1/3 | 2/3 | 0/3 | só no plugin (flaky) |
| `IPython/core/magics/config.py::IPython.core.magics.config.ConfigMagics.config` | 0/3 | 3/3 | 0/3 | 0/3 | só no plugin (fixa) |
| _+7 teste(s), ver flaky_tests.json_ | | | | | |

#### ipython-m4267

| teste | baseline | ranking | regsmart | regsmart-no-rank | classe |
|---|---|---|---|---|---|
| `   ProfileLocate:history.py:793 Failed to create history session in /tmp/pytest-of-runner/pytest-0/test_histmanager_memory_fallba0/history.sqlite. History will not be saved.` | 0/3 | 2/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `IPython/core/magics/config.py::IPython.core.magics.config.ConfigMagics.config` | 0/3 | 3/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_application.py::test_initialize_stops_at_subapp` | 0/3 | 2/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_dict_key_completion_contexts` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_dict_key_completion_string` | 0/3 | 3/3 | 1/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_dict_key_restrict_to_dicts` | 0/3 | 2/3 | 1/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_func_kw_completions` | 0/3 | 1/3 | 1/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_magic_completion_shadowing` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_mix_terms` | 0/3 | 2/3 | 1/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_struct_array_key_completion` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_undefined_variables[a = []\nwhile condition:\n    a.-append-False-limited]` | 0/3 | 2/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_undefined_variables[t = []\nif condition_1:\n    if condition_2:\n        t = 'nested'\nt.-insert_text30-False-limited]` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_undefined_variables[t = []\nif condition_1:\n    t = 'string'\nelif condition_2:\n    t = 1\nelif condition_3:\n    t = {}\nt.-insert_text29-False-limited]` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_undefined_variables[t = []\nif condition_1:\n    t = 'string'\nelif condition_2:\n    t = 1\nelif condition_3:\n    t.-append-False-limited]` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_undefined_variables[t = []\nif some_condition:\n    t = 'string'\nelse:\n    t = 1\nt.-insert_text27-False-limited]` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_undefined_variables[t = []\nif some_condition:\n    t = 'string'\nelse:\n    t.-append-False-limited]` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_undefined_variables[t = []\nif some_condition:\n    t = 'string'\nt.-insert_text25-False-limited]` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_undefined_variables[t = []\nif some_condition:\n    t.-append-False-limited]` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_undefined_variables[t = []\nwhile condition:\n    t = 'str'\nt.-insert_text32-False-limited]` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_undefined_variables[t = []\nwhile condition_1:\n    while condition_2:\n        t = 'str'\nt.-insert_text33-False-limited]` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_undefined_variables_without_jedi[t: int \| dict = {'a': []}\nt.-insert_text1]` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_completer.py::test_undefined_variables_without_jedi[t: int \| str\nt.-insert_text3]` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_displayhook.py::test_underscore_no_overwrite_builtins` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_displayhook.py::test_underscore_no_overwrite_user` | 0/3 | 3/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_history.py::test_histmanager_memory_fallback_reopens_db` | 0/3 | 2/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_historyapp.py::test_history_app_trim_subcommand` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_interactiveshell.py::test_naked_string_cells` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_interactiveshell.py::test_run_cell_asyncio_run` | 0/3 | 3/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_interactiveshell.py::test_run_cell_await` | 0/3 | 3/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_ipapp.py::test_locate_subcommand` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magic.py::test_cd_force_quiet` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magic.py::test_cell_magic_class` | 0/3 | 3/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magic.py::test_cell_magic_class2` | 0/3 | 3/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magic.py::test_cell_magic_func_deco` | 0/3 | 2/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magic.py::test_cell_magic_reg` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magic.py::test_dirops` | 0/3 | 2/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magic.py::test_line_cell_info` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magic.py::test_multiline_time` | 0/3 | 3/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magic.py::test_time_raise_on_interrupt` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| `tests/test_magic.py::test_timeit_raise_on_interrupt` | 0/3 | 1/3 | 0/3 | 0/3 | só no plugin (flaky) |
| _+14 teste(s), ver flaky_tests.json_ | | | | | |


