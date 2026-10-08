# Flaky runner — relatório

## Custo

- Início: `2026-10-08T19:07:56.558771+00:00`
- Fim: `2026-10-08T19:29:25.172847+00:00`
- Tempo ativo do script: **21m28s**
- Janela real dos runs (1º dispatch → última conclusão): **20m55s** (inclui fila)
- Minutos de runner somados: **375.6 min**
- Pico de concorrência medido: **20** jobs (teto do plano Free: 20)

## API / rate limit

- Requisições: 106 GET, 60 POST
- Retries: 0
- Rate limit (final): 0/5000 consumidos, reseta em `2026-10-08T21:32:15+00:00`

## Saúde da execução

| Métrica | warm-up | repetições |
|---|---|---|
| Tarefas no plano | 0 | 60 |
| Despachadas | 0 | 60 |
| Com run_id | 0 | 60 |
| Sucesso | 0 | 0 |
| Falha (testes falharam) | 0 | 60 |
| Canceladas | 0 | 0 |
| Em andamento | 0 | 0 |
| Dispatch falhou / run perdido | 0 | 0 |

## Por repositório

| repo | runs | success | failure | cancelled | em andamento | makespan | min runner |
|---|---|---|---|---|---|---|---|
| ipython | 60 | 0 | 60 | 0 | 0 | 20m55s | 375.6 |

## Por workflow

| workflow | runs | min runner |
|---|---|---|
| baseline | 15 | 50.8 |
| ranking | 15 | 205.0 |
| regsmart | 15 | 89.8 |
| regsmart-no-rank | 15 | 30.1 |

## Testes flaky

| repo | mutantes | workflow | flaky (distintos) | falham em todas as reps |
|---|---|---|---|---|
| ipython | 5 | baseline | 0 | 39 |
| ipython | 5 | ranking | 148 | 163 |
| ipython | 5 | regsmart | 28 | 42 |
| ipython | 5 | regsmart-no-rank | 0 | 10 |

`falham em todas as reps` inclui falhas pré-existentes (que já falham sem o mutante). Teste que falha em todos os mutantes do repo é candidato a isso.

### ipython

| workflow | teste | mutantes afetados (falhou/reps) |
|---|---|---|
| ranking | `   LocateIPythonApp:history.py:793 Failed to create history session in /tmp/pytest-of-runner/pytest-0/test_histmanager_memory_fallba0/history.sqlite. History will not be saved. [ranking (rkn_hybrid)]` | ipython-m22324 (1/3) |
| ranking | `   LocateIPythonApp:history.py:793 Failed to create history session in /tmp/pytest-of-runner/pytest-0/test_histmanager_memory_fallba0/history.sqlite. History will not be saved. [ranking (rkn_qtf)]` | ipython-m22324 (1/3) |
| ranking | `   ProfileLocate:history.py:793 Failed to create history session in /tmp/pytest-of-runner/pytest-0/test_histmanager_memory_fallba0/history.sqlite. History will not be saved. [ranking (rkn_hybrid)]` | ipython-m1288 (1/3), ipython-m22732 (1/3) |
| ranking | `   ProfileLocate:history.py:793 Failed to create history session in /tmp/pytest-of-runner/pytest-0/test_histmanager_memory_fallba0/history.sqlite. History will not be saved. [ranking (rkn_qtf)]` | ipython-m17283 (1/3), ipython-m4267 (2/3) |
| ranking | `IPython/core/magics/config.py::IPython.core.magics.config.ConfigMagics.config [ranking (rkn_hybrid)]` | ipython-m17283 (2/3), ipython-m22324 (1/3), ipython-m4267 (1/3) |
| ranking | `tests/test_application.py::test_initialize_stops_at_subapp [ranking (rkn_hybrid)]` | ipython-m22324 (1/3) |
| ranking | `tests/test_application.py::test_initialize_stops_at_subapp [ranking (rkn_qtf)]` | ipython-m1288 (2/3), ipython-m17283 (2/3), ipython-m22324 (1/3), ipython-m22732 (1/3) +1 |
| ranking | `tests/test_application.py::test_initialize_stops_at_subapp [ranking (rkn_simchgpath)]` | ipython-m22324 (1/3) |
| ranking | `tests/test_backgroundjobs.py::test_dead_job_attributes [ranking (rkn_recentfail)]` | ipython-m17283 (1/3) |
| ranking | `tests/test_backgroundjobs.py::test_traceback [ranking (rkn_recentfail)]` | ipython-m17283 (1/3) |
| ranking | `tests/test_completer.py::test_dataframe_key_completion [ranking (rkn_qtf)]` | ipython-m1288 (1/3) |
| ranking | `tests/test_completer.py::test_dict_key_completion_bytes [ranking (rkn_qtf)]` | ipython-m1288 (1/3) |
| ranking | `tests/test_completer.py::test_dict_key_completion_contexts [ranking (rkn_qtf)]` | ipython-m4267 (1/3) |
| ranking | `tests/test_completer.py::test_dict_key_completion_string [ranking (rkn_hybrid)]` | ipython-m17283 (2/3), ipython-m22324 (1/3), ipython-m22732 (2/3) |
| ranking | `tests/test_completer.py::test_dict_key_completion_string [ranking (rkn_simchgpath)]` | ipython-m22324 (1/3), ipython-m22732 (1/3), ipython-m4267 (1/3) |
| ranking | `tests/test_completer.py::test_dict_key_restrict_to_dicts [ranking (rkn_qtf)]` | ipython-m17283 (2/3), ipython-m22324 (2/3), ipython-m22732 (2/3), ipython-m4267 (2/3) |
| ranking | `tests/test_completer.py::test_func_kw_completions [ranking (rkn_qtf)]` | ipython-m1288 (1/3), ipython-m17283 (1/3), ipython-m22324 (1/3), ipython-m22732 (1/3) +1 |
| ranking | `tests/test_completer.py::test_magic_completion_order [ranking (rkn_qtf)]` | ipython-m1288 (1/3), ipython-m17283 (1/3) |
| ranking | `tests/test_completer.py::test_magic_completion_shadowing [ranking (rkn_qtf)]` | ipython-m1288 (1/3), ipython-m17283 (1/3), ipython-m22324 (1/3), ipython-m22732 (1/3) +1 |
| ranking | `tests/test_completer.py::test_misc_no_jedi_completions[a="str"; b=1-(a, b).-expected1-not_expected1] [ranking (rkn_hybrid)]` | ipython-m1288 (1/3) |
| ranking | `tests/test_completer.py::test_mix_terms [ranking (rkn_qtf)]` | ipython-m1288 (2/3), ipython-m17283 (2/3), ipython-m22324 (1/3), ipython-m22732 (1/3) +1 |
| ranking | `tests/test_completer.py::test_omit__names [ranking (rkn_qtf)]` | ipython-m22732 (1/3) |
| ranking | `tests/test_completer.py::test_quoted_file_completions [ranking (rkn_qtf)]` | ipython-m17283 (1/3), ipython-m22324 (1/3) |
| ranking | `tests/test_completer.py::test_struct_array_key_completion [ranking (rkn_qtf)]` | ipython-m22732 (1/3), ipython-m4267 (1/3) |
| ranking | `tests/test_completer.py::test_undefined_variables[a = []\nwhile condition:\n    a.-append-False-limited] [ranking (rkn_hybrid)]` | ipython-m1288 (1/3), ipython-m22324 (1/3), ipython-m22732 (1/3), ipython-m4267 (2/3) |
| ranking | `tests/test_completer.py::test_undefined_variables[a = []\nwhile condition:\n    a.-append-False-limited] [ranking (rkn_qtf)]` | ipython-m17283 (1/3) |
| ranking | `tests/test_completer.py::test_undefined_variables[t = []\nif condition_1:\n    if condition_2:\n        t = 'nested'\nt.-insert_text30-False-limited] [ranking (rkn_qtf)]` | ipython-m4267 (1/3) |
| ranking | `tests/test_completer.py::test_undefined_variables[t = []\nif condition_1:\n    t = 'string'\nelif condition_2:\n    t = 1\nelif condition_3:\n    t = {}\nt.-insert_text29-False-limited] [ranking (rkn_qtf)]` | ipython-m1288 (1/3), ipython-m17283 (1/3), ipython-m22732 (1/3), ipython-m4267 (1/3) |
| ranking | `tests/test_completer.py::test_undefined_variables[t = []\nif condition_1:\n    t = 'string'\nelif condition_2:\n    t = 1\nelif condition_3:\n    t.-append-False-limited] [ranking (rkn_qtf)]` | ipython-m4267 (1/3) |
| ranking | `tests/test_completer.py::test_undefined_variables[t = []\nif some_condition:\n    t = 'string'\nelse:\n    t = 1\nt.-insert_text27-False-limited] [ranking (rkn_qtf)]` | ipython-m17283 (1/3), ipython-m4267 (1/3) |
| ranking | `tests/test_completer.py::test_undefined_variables[t = []\nif some_condition:\n    t = 'string'\nelse:\n    t.-append-False-limited] [ranking (rkn_qtf)]` | ipython-m4267 (1/3) |
| ranking | `tests/test_completer.py::test_undefined_variables[t = []\nif some_condition:\n    t = 'string'\nt.-insert_text25-False-limited] [ranking (rkn_qtf)]` | ipython-m4267 (1/3) |
| ranking | `tests/test_completer.py::test_undefined_variables[t = []\nif some_condition:\n    t.-append-False-limited] [ranking (rkn_hybrid)]` | ipython-m1288 (1/3) |
| ranking | `tests/test_completer.py::test_undefined_variables[t = []\nif some_condition:\n    t.-append-False-limited] [ranking (rkn_qtf)]` | ipython-m4267 (1/3) |
| ranking | `tests/test_completer.py::test_undefined_variables[t = []\nwhile condition:\n    t = 'str'\nt.-insert_text32-False-limited] [ranking (rkn_qtf)]` | ipython-m4267 (1/3) |
| ranking | `tests/test_completer.py::test_undefined_variables[t = []\nwhile condition_1:\n    while condition_2:\n        t = 'str'\nt.-insert_text33-False-limited] [ranking (rkn_qtf)]` | ipython-m4267 (1/3) |
| ranking | `tests/test_completer.py::test_undefined_variables_without_jedi[t: int | dict = {'a': []}\nt.-insert_text1] [ranking (rkn_qtf)]` | ipython-m4267 (1/3) |
| ranking | `tests/test_completer.py::test_undefined_variables_without_jedi[t: int | str\nt.-insert_text3] [ranking (rkn_qtf)]` | ipython-m1288 (1/3), ipython-m22732 (1/3), ipython-m4267 (1/3) |
| ranking | `tests/test_debug_magic.py::test_debug_magic_passes_through_generators [ranking (rkn_hybrid)]` | ipython-m22324 (1/3) |
| ranking | `tests/test_debugger.py::test_where_erase_value [ranking (rkn_hybrid)]` | ipython-m22324 (1/3) |
| ranking | `tests/test_debugger.py::test_xmode_skip [ranking (rkn_hybrid)]` | ipython-m22324 (1/3) |
| ranking | `tests/test_displayhook.py::test_underscore_no_overwrite_builtins [ranking (rkn_hybrid)]` | ipython-m1288 (1/3), ipython-m22324 (1/3), ipython-m22732 (1/3), ipython-m4267 (1/3) |
| ranking | `tests/test_displayhook.py::test_underscore_no_overwrite_builtins [ranking (rkn_recentfail)]` | ipython-m17283 (1/3), ipython-m22732 (1/3) |
| ranking | `tests/test_displayhook.py::test_underscore_no_overwrite_user [ranking (rkn_hybrid)]` | ipython-m1288 (2/3), ipython-m22324 (2/3), ipython-m22732 (1/3), ipython-m4267 (1/3) |
| ranking | `tests/test_displayhook.py::test_underscore_no_overwrite_user [ranking (rkn_recentfail)]` | ipython-m17283 (1/3), ipython-m22732 (1/3) |
| ranking | `tests/test_displayhook.py::test_underscore_no_overwrite_user [ranking (rkn_simchgpath)]` | ipython-m22324 (1/3), ipython-m22732 (1/3) |
| ranking | `tests/test_embed.py::test_nest_embed [ranking (rkn_hybrid)]` | ipython-m22324 (1/3) |
| ranking | `tests/test_formatters.py::test_bad_repr_traceback [ranking (rkn_recentfail)]` | ipython-m17283 (1/3) |
| ranking | `tests/test_formatters.py::test_error_method [ranking (rkn_recentfail)]` | ipython-m17283 (1/3) |
| ranking | `tests/test_formatters.py::test_error_pretty_method [ranking (rkn_recentfail)]` | ipython-m17283 (1/3) |
| ranking | `tests/test_formatters.py::test_warn_error_for_type [ranking (rkn_qtf)]` | ipython-m17283 (1/3) |
| ranking | `tests/test_formatters.py::test_warn_error_for_type [ranking (rkn_recentfail)]` | ipython-m17283 (1/3) |
| ranking | `tests/test_help.py::test_locate_help [ranking (rkn_hybrid)]` | ipython-m22324 (1/3) |
| ranking | `tests/test_help.py::test_locate_profile_help [ranking (rkn_hybrid)]` | ipython-m22324 (1/3) |
| ranking | `tests/test_help.py::test_profile_create_help [ranking (rkn_hybrid)]` | ipython-m22324 (1/3) |
| ranking | `tests/test_help.py::test_profile_help [ranking (rkn_hybrid)]` | ipython-m22324 (1/3) |
| ranking | `tests/test_help.py::test_profile_list_help [ranking (rkn_hybrid)]` | ipython-m22324 (1/3) |
| ranking | `tests/test_help.py::test_trust_help [ranking (rkn_hybrid)]` | ipython-m22324 (1/3) |
| ranking | `tests/test_history.py::test_histmanager_memory_fallback_reopens_db [ranking (rkn_hybrid)]` | ipython-m1288 (1/3), ipython-m22324 (1/3), ipython-m22732 (1/3) |
| ranking | `tests/test_history.py::test_histmanager_memory_fallback_reopens_db [ranking (rkn_qtf)]` | ipython-m17283 (1/3), ipython-m22324 (1/3), ipython-m4267 (2/3) |
| ranking | `tests/test_history.py::test_history_trim_cli[subcommand0-2] [ranking (rkn_hybrid)]` | ipython-m22324 (1/3) |
| ranking | `tests/test_history.py::test_history_trim_cli[subcommand1-0] [ranking (rkn_hybrid)]` | ipython-m22324 (1/3) |
| ranking | `tests/test_historyapp.py::test_history_app_trim_subcommand [ranking (rkn_hybrid)]` | ipython-m22324 (1/3) |
| ranking | `tests/test_historyapp.py::test_history_app_trim_subcommand [ranking (rkn_qtf)]` | ipython-m1288 (1/3), ipython-m17283 (1/3), ipython-m22324 (1/3), ipython-m22732 (1/3) +1 |
| ranking | `tests/test_historyapp.py::test_history_app_trim_subcommand [ranking (rkn_simchgpath)]` | ipython-m22324 (1/3) |
| ranking | `tests/test_interactiveshell.py::test_extraneous_loads [ranking (rkn_hybrid)]` | ipython-m22324 (1/3) |
| ranking | `tests/test_interactiveshell.py::test_input_rejection [ranking (rkn_qtf)]` | ipython-m17283 (1/3) |
| ranking | `tests/test_interactiveshell.py::test_input_rejection [ranking (rkn_recentfail)]` | ipython-m17283 (1/3) |
| ranking | `tests/test_interactiveshell.py::test_multiline_string_cells [ranking (rkn_qtf)]` | ipython-m17283 (1/3) |
| ranking | `tests/test_interactiveshell.py::test_naked_string_cells [ranking (rkn_hybrid)]` | ipython-m1288 (1/3), ipython-m22324 (1/3), ipython-m22732 (1/3), ipython-m4267 (1/3) |
| ranking | `tests/test_interactiveshell.py::test_naked_string_cells [ranking (rkn_qtf)]` | ipython-m1288 (2/3), ipython-m17283 (1/3), ipython-m22324 (1/3), ipython-m22732 (2/3) |
| ranking | `tests/test_interactiveshell.py::test_naked_string_cells [ranking (rkn_recentfail)]` | ipython-m17283 (1/3), ipython-m22732 (1/3) |
| ranking | `tests/test_interactiveshell.py::test_naked_string_cells [ranking (rkn_simchgpath)]` | ipython-m4267 (1/3) |
| ranking | `tests/test_interactiveshell.py::test_run_cell_asyncio_run [ranking (rkn_hybrid)]` | ipython-m1288 (1/3), ipython-m22324 (1/3), ipython-m22732 (1/3), ipython-m4267 (2/3) |
| ranking | `tests/test_interactiveshell.py::test_run_cell_asyncio_run [ranking (rkn_recentfail)]` | ipython-m17283 (1/3), ipython-m22732 (1/3) |
| ranking | `tests/test_interactiveshell.py::test_run_cell_asyncio_run [ranking (rkn_simchgpath)]` | ipython-m4267 (1/3) |
| ranking | `tests/test_interactiveshell.py::test_run_cell_await [ranking (rkn_hybrid)]` | ipython-m1288 (1/3), ipython-m22324 (1/3), ipython-m22732 (1/3), ipython-m4267 (2/3) |
| ranking | `tests/test_interactiveshell.py::test_run_cell_await [ranking (rkn_recentfail)]` | ipython-m17283 (1/3), ipython-m22732 (1/3) |
| ranking | `tests/test_interactiveshell.py::test_run_cell_await [ranking (rkn_simchgpath)]` | ipython-m4267 (1/3) |
| ranking | `tests/test_interactivshell.py::test_repl_not_plain_text [ranking (rkn_hybrid)]` | ipython-m17283 (2/3) |
| ranking | `tests/test_ipapp.py::test_locate_subcommand [ranking (rkn_hybrid)]` | ipython-m17283 (1/3) |
| ranking | `tests/test_ipapp.py::test_locate_subcommand [ranking (rkn_qtf)]` | ipython-m1288 (1/3), ipython-m17283 (1/3), ipython-m4267 (1/3) |
| ranking | `tests/test_magic.py::test_cd_force_quiet [ranking (rkn_hybrid)]` | ipython-m17283 (1/3), ipython-m22324 (1/3) |
| ranking | `tests/test_magic.py::test_cd_force_quiet [ranking (rkn_qtf)]` | ipython-m4267 (1/3) |
| ranking | `tests/test_magic.py::test_cell_magic_class [ranking (rkn_hybrid)]` | ipython-m1288 (1/3), ipython-m17283 (2/3), ipython-m22324 (1/3), ipython-m22732 (1/3) +1 |
| ranking | `tests/test_magic.py::test_cell_magic_class [ranking (rkn_qtf)]` | ipython-m1288 (1/3), ipython-m17283 (2/3), ipython-m22324 (2/3), ipython-m22732 (1/3) |
| ranking | `tests/test_magic.py::test_cell_magic_class2 [ranking (rkn_hybrid)]` | ipython-m1288 (1/3), ipython-m17283 (2/3), ipython-m22324 (1/3), ipython-m22732 (1/3) +1 |
| ranking | `tests/test_magic.py::test_cell_magic_class2 [ranking (rkn_qtf)]` | ipython-m1288 (1/3), ipython-m17283 (2/3), ipython-m22324 (2/3), ipython-m22732 (1/3) |
| ranking | `tests/test_magic.py::test_cell_magic_func_deco [ranking (rkn_hybrid)]` | ipython-m1288 (1/3), ipython-m22324 (1/3), ipython-m22732 (1/3), ipython-m4267 (1/3) |
| ranking | `tests/test_magic.py::test_cell_magic_func_deco [ranking (rkn_qtf)]` | ipython-m1288 (1/3), ipython-m17283 (2/3), ipython-m22324 (1/3), ipython-m22732 (1/3) +1 |
| ranking | `tests/test_magic.py::test_cell_magic_reg [ranking (rkn_hybrid)]` | ipython-m1288 (1/3), ipython-m17283 (2/3), ipython-m22324 (1/3), ipython-m22732 (1/3) +1 |
| ranking | `tests/test_magic.py::test_cell_magic_reg [ranking (rkn_qtf)]` | ipython-m1288 (1/3), ipython-m17283 (2/3), ipython-m22324 (1/3), ipython-m22732 (1/3) +1 |
| ranking | `tests/test_magic.py::test_config_available_configs [ranking (rkn_hybrid)]` | ipython-m17283 (1/3), ipython-m22324 (1/3) |
| ranking | `tests/test_magic.py::test_config_available_configs [ranking (rkn_qtf)]` | ipython-m1288 (2/3) |
| ranking | `tests/test_magic.py::test_dirops [ranking (rkn_hybrid)]` | ipython-m1288 (1/3), ipython-m17283 (1/3), ipython-m22324 (1/3), ipython-m22732 (1/3) +1 |
| ranking | `tests/test_magic.py::test_dirops [ranking (rkn_qtf)]` | ipython-m17283 (1/3), ipython-m22324 (1/3), ipython-m4267 (2/3) |
| ranking | `tests/test_magic.py::test_line_cell_info [ranking (rkn_hybrid)]` | ipython-m17283 (1/3), ipython-m22324 (1/3), ipython-m4267 (1/3) |
| ranking | `tests/test_magic.py::test_multiline_time [ranking (rkn_hybrid)]` | ipython-m1288 (1/3), ipython-m22324 (2/3), ipython-m22732 (1/3), ipython-m4267 (1/3) |
| ranking | `tests/test_magic.py::test_multiline_time [ranking (rkn_qtf)]` | ipython-m1288 (1/3), ipython-m17283 (2/3), ipython-m22324 (2/3), ipython-m22732 (1/3) |
| ranking | `tests/test_magic.py::test_notebook_export_json_with_output [ranking (rkn_hybrid)]` | ipython-m17283 (1/3) |
| ranking | `tests/test_magic.py::test_notebook_export_json_with_output [ranking (rkn_qtf)]` | ipython-m17283 (1/3) |
| ranking | `tests/test_magic.py::test_script_do_not_raise_on_interrupt [ranking (rkn_hybrid)]` | ipython-m17283 (1/3) |
| ranking | `tests/test_magic.py::test_script_raise_on_interrupt [ranking (rkn_hybrid)]` | ipython-m17283 (1/3) |
| ranking | `tests/test_magic.py::test_time_raise_on_interrupt [ranking (rkn_hybrid)]` | ipython-m1288 (1/3), ipython-m17283 (1/3), ipython-m22324 (1/3), ipython-m22732 (1/3) +1 |
| ranking | `tests/test_magic.py::test_timeit_raise_on_interrupt [ranking (rkn_hybrid)]` | ipython-m1288 (1/3), ipython-m17283 (1/3), ipython-m22324 (1/3), ipython-m22732 (1/3) +1 |
| ranking | `tests/test_magic.py::tests.test_magic.doctest_hist_f [ranking (rkn_hybrid)]` | ipython-m17283 (1/3) |
| ranking | `tests/test_magic.py::tests.test_magic.doctest_hist_op [ranking (rkn_hybrid)]` | ipython-m1288 (1/3), ipython-m22732 (1/3), ipython-m4267 (1/3) |
| ranking | `tests/test_magic.py::tests.test_magic.test_debug_magic [ranking (rkn_hybrid)]` | ipython-m17283 (1/3) |
| ranking | `tests/test_magic.py::tests.test_magic.test_debug_magic_locals [ranking (rkn_hybrid)]` | ipython-m17283 (1/3) |
| ranking | `tests/test_magic_table.py::test_startup_does_not_import_the_magics_modules [ranking (rkn_hybrid)]` | ipython-m22324 (1/3) |
| ranking | `tests/test_magic_terminal.py::test_cpaste [ranking (rkn_qtf)]` | ipython-m17283 (2/3) |
| ranking | `tests/test_magics_pylab.py::test_matplotlib_no_arg_prints_backend [ranking (rkn_qtf)]` | ipython-m1288 (1/3), ipython-m17283 (1/3), ipython-m22732 (1/3), ipython-m4267 (1/3) |
| ranking | `tests/test_profile.py::test_profile_app_list_subcommand [ranking (rkn_hybrid)]` | ipython-m22324 (1/3) |
| ranking | `tests/test_profile.py::test_profile_app_list_subcommand [ranking (rkn_qtf)]` | ipython-m1288 (2/3), ipython-m17283 (2/3), ipython-m22324 (1/3), ipython-m22732 (1/3) +1 |
| ranking | `tests/test_profile.py::test_profile_app_list_subcommand [ranking (rkn_simchgpath)]` | ipython-m22324 (1/3) |
| ranking | `tests/test_profile.py::test_startup_ipy [ranking (rkn_hybrid)]` | ipython-m22324 (1/3) |
| ranking | `tests/test_profile.py::test_startup_py [ranking (rkn_hybrid)]` | ipython-m22324 (1/3) |
| ranking | `tests/test_run.py::test_builtins_id [ranking (rkn_qtf)]` | ipython-m1288 (2/3), ipython-m17283 (1/3), ipython-m22732 (2/3) |
| ranking | `tests/test_run.py::test_debug_run_submodule[absolute] [ranking (rkn_hybrid)]` | ipython-m17283 (2/3) |
| ranking | `tests/test_run.py::test_debug_run_submodule[absolute] [ranking (rkn_qtf)]` | ipython-m17283 (1/3) |
| ranking | `tests/test_run.py::test_debug_run_submodule[relative] [ranking (rkn_hybrid)]` | ipython-m17283 (2/3) |
| ranking | `tests/test_run.py::test_multiprocessing_run [ranking (rkn_qtf)]` | ipython-m17283 (1/3) |
| ranking | `tests/test_run.py::test_obj_del [ranking (rkn_hybrid)]` | ipython-m22324 (1/3) |
| ranking | `tests/test_run.py::test_run_tb [ranking (rkn_hybrid)]` | ipython-m17283 (2/3) |
| ranking | `tests/test_run.py::test_run_tb [ranking (rkn_qtf)]` | ipython-m1288 (1/3), ipython-m17283 (2/3), ipython-m22324 (2/3), ipython-m22732 (1/3) +1 |
| ranking | `tests/test_run.py::test_script_tb [ranking (rkn_hybrid)]` | ipython-m22324 (1/3) |
| ranking | `tests/test_run.py::test_tclass [ranking (rkn_hybrid)]` | ipython-m22324 (1/3) |
| ranking | `tests/test_shellapp.py::test_ipy_script_file_attribute [ranking (rkn_hybrid)]` | ipython-m22324 (1/3) |
| ranking | `tests/test_shellapp.py::test_py_script_file_attribute [ranking (rkn_hybrid)]` | ipython-m22324 (1/3) |
| ranking | `tests/test_shellapp.py::test_py_script_file_attribute_interactively [ranking (rkn_hybrid)]` | ipython-m22324 (1/3) |
| ranking | `tests/test_storemagic.py::test_store_restore [ranking (rkn_hybrid)]` | ipython-m17283 (1/3), ipython-m4267 (1/3) |
| ranking | `tests/test_storemagic.py::test_store_restore [ranking (rkn_qtf)]` | ipython-m1288 (1/3), ipython-m17283 (1/3), ipython-m22324 (1/3), ipython-m22732 (1/3) +1 |
| ranking | `tests/test_tools.py::test_ipexec_validate_exception_path [ranking (rkn_hybrid)]` | ipython-m22324 (1/3) |
| ranking | `tests/test_tools.py::test_ipexec_validate_exception_path2 [ranking (rkn_hybrid)]` | ipython-m22324 (1/3) |
| ranking | `tests/test_tools.py::test_ipexec_validate_main_path [ranking (rkn_hybrid)]` | ipython-m22324 (1/3) |
| ranking | `tests/test_tools.py::test_ipexec_validate_main_path2 [ranking (rkn_hybrid)]` | ipython-m22324 (1/3) |
| ranking | `tests/test_ultratb.py::test_changing_py_file [ranking (rkn_qtf)]` | ipython-m17283 (1/3) |
| ranking | `tests/test_ultratb.py::test_direct_cause_error [ranking (rkn_qtf)]` | ipython-m17283 (1/3) |
| ranking | `tests/test_ultratb.py::test_dynamic_code [ranking (rkn_qtf)]` | ipython-m17283 (1/3) |
| ranking | `tests/test_ultratb.py::test_exception_during_handling_error [ranking (rkn_qtf)]` | ipython-m17283 (1/3) |
| ranking | `tests/test_ultratb.py::test_iso8859_5 [ranking (rkn_qtf)]` | ipython-m17283 (1/3) |
| ranking | `tests/test_ultratb.py::test_nonascii_path [ranking (rkn_qtf)]` | ipython-m17283 (1/3) |
| ranking | `tests/test_ultratb.py::test_recursion_one_frame [ranking (rkn_qtf)]` | ipython-m17283 (1/3) |
| ranking | `tests/test_ultratb.py::test_recursion_three_frames [ranking (rkn_qtf)]` | ipython-m17283 (1/3) |
| ranking | `tests/test_ultratb.py::test_suppress_exception_chaining [ranking (rkn_qtf)]` | ipython-m17283 (2/3) |
| ranking | `tests/test_ultratb.py::test_syntaxerror_no_stacktrace_at_compile_time [ranking (rkn_hybrid)]` | ipython-m17283 (2/3) |
| ranking | `tests/test_ultratb.py::test_syntaxerror_no_stacktrace_at_compile_time [ranking (rkn_qtf)]` | ipython-m17283 (1/3) |
| ranking | `tests/test_ultratb.py::test_verbose_reports_notes [ranking (rkn_qtf)]` | ipython-m17283 (1/3) |
| regsmart | `tests/test_application.py::test_initialize_stops_at_subapp [regsmart (rgsm_hybrid)]` | ipython-m1288 (1/3) |
| regsmart | `tests/test_completer.py::test_dataframe_key_completion [regsmart (rgsm_hybrid)]` | ipython-m22732 (1/3) |
| regsmart | `tests/test_completer.py::test_dict_key_completion_string [regsmart (rgsm_hybrid)]` | ipython-m22732 (1/3) |
| regsmart | `tests/test_completer.py::test_dict_key_completion_string [regsmart (rgsm_qtf)]` | ipython-m1288 (2/3), ipython-m17283 (1/3), ipython-m22324 (1/3), ipython-m4267 (1/3) |
| regsmart | `tests/test_completer.py::test_dict_key_completion_unicode_py3 [regsmart (rgsm_qtf)]` | ipython-m22732 (2/3) |
| regsmart | `tests/test_completer.py::test_dict_key_restrict_to_dicts [regsmart (rgsm_qtf)]` | ipython-m1288 (2/3), ipython-m17283 (1/3), ipython-m22324 (1/3), ipython-m22732 (2/3) +1 |
| regsmart | `tests/test_completer.py::test_func_kw_completions [regsmart (rgsm_qtf)]` | ipython-m1288 (1/3), ipython-m17283 (1/3), ipython-m22324 (1/3), ipython-m22732 (1/3) +1 |
| regsmart | `tests/test_completer.py::test_mix_terms [regsmart (rgsm_qtf)]` | ipython-m1288 (1/3), ipython-m17283 (1/3), ipython-m22324 (2/3), ipython-m22732 (1/3) +1 |
| regsmart | `tests/test_completer.py::test_undefined_variables[a = []\nwhile condition:\n    a.-append-False-limited] [regsmart (rgsm_hybrid)]` | ipython-m22732 (1/3) |
| regsmart | `tests/test_completer.py::test_undefined_variables[t = []\nif condition_1:\n    t = 'string'\nelif condition_2:\n    t = 1\nelif condition_3:\n    t = {}\nt.-insert_text29-False-limited] [regsmart (rgsm_qtf)]` | ipython-m22732 (1/3) |
| regsmart | `tests/test_completer.py::test_undefined_variables[t = []\nif some_condition:\n    t = 'string'\nt.-insert_text25-False-limited] [regsmart (rgsm_qtf)]` | ipython-m22732 (1/3) |
| regsmart | `tests/test_completer.py::test_undefined_variables_without_jedi[t: int | str\nt.-insert_text3] [regsmart (rgsm_qtf)]` | ipython-m22732 (1/3) |
| regsmart | `tests/test_displayhook.py::test_underscore_no_overwrite_builtins [regsmart (rgsm_recentfail)]` | ipython-m22732 (1/3) |
| regsmart | `tests/test_displayhook.py::test_underscore_no_overwrite_user [regsmart (rgsm_hybrid)]` | ipython-m22732 (1/3) |
| regsmart | `tests/test_displayhook.py::test_underscore_no_overwrite_user [regsmart (rgsm_recentfail)]` | ipython-m22732 (1/3) |
| regsmart | `tests/test_historyapp.py::test_history_app_trim_subcommand [regsmart (rgsm_qtf)]` | ipython-m22732 (1/3) |
| regsmart | `tests/test_interactiveshell.py::test_naked_string_cells [regsmart (rgsm_recentfail)]` | ipython-m22732 (1/3) |
| regsmart | `tests/test_interactiveshell.py::test_run_cell_asyncio_run [regsmart (rgsm_hybrid)]` | ipython-m22732 (1/3) |
| regsmart | `tests/test_interactiveshell.py::test_run_cell_asyncio_run [regsmart (rgsm_recentfail)]` | ipython-m22732 (1/3) |
| regsmart | `tests/test_interactiveshell.py::test_run_cell_await [regsmart (rgsm_hybrid)]` | ipython-m22732 (1/3) |
| regsmart | `tests/test_interactiveshell.py::test_run_cell_await [regsmart (rgsm_recentfail)]` | ipython-m22732 (1/3) |
| regsmart | `tests/test_interactivshell.py::test_repl_not_plain_text [regsmart (rgsm_hybrid)]` | ipython-m17283 (2/3) |
| regsmart | `tests/test_magic.py::test_line_cell_info [regsmart (rgsm_qtf)]` | ipython-m22732 (1/3) |
| regsmart | `tests/test_magic.py::test_reset_in [regsmart (rgsm_recentfail)]` | ipython-m22732 (2/3) |
| regsmart | `tests/test_magic.py::test_reset_out [regsmart (rgsm_recentfail)]` | ipython-m22732 (1/3) |
| regsmart | `tests/test_magics_pylab.py::test_matplotlib_no_arg_prints_backend [regsmart (rgsm_qtf)]` | ipython-m22732 (1/3) |
| regsmart | `tests/test_run.py::test_builtins_id [regsmart (rgsm_qtf)]` | ipython-m22732 (2/3) |
| regsmart | `tests/test_storemagic.py::test_store_restore [regsmart (rgsm_qtf)]` | ipython-m22732 (2/3) |

