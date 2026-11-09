# regsmart-experiments

Scripts e dados do experimento que avalia o [pytest-regsmart](https://github.com/leticosta4/pytest-regsmart) (seleção + priorização de testes) contra o pytest padrão e o [pytest-ranking](https://github.com/pytest-dev/pytest-ranking) em 12 projetos Python reais, executados no GitHub Actions.

Este README descreve **o que foi de fato executado** e como repetir o experimento do zero.

---

## 1. Desenho do experimento

| item | valor |
|---|---|
| Projetos | 12 forks (seção 2), congelados no estado de **27/09/2026** (`data/fork_commits.csv`) |
| Mutantes | 5 por projeto (60 no total), gerados com `mutmut==2.5.1`, semente `42` (`data/mutmut/mutants.json`) |
| Referências por projeto | 6: as 5 branches `mut-<repo>-mNNNN` + a branch default sem mutação (**controle**) |
| Workflows por referência | 4: baseline, pytest-ranking, pytest-regsmart e pytest-regsmart sem RTP |
| Modos (jobs) | 9 (seção 3) |
| Repetições | 3 por (referência, workflow), em sequência na mesma branch ("lane") |
| Aquecimento | 1 execução antes das repetições, só nos 2 workflows com cache (ranking e regsmart); fica fora das métricas |
| Plugin avaliado | `pytest-regsmart@ec6d08a5986a1c3aeb2e0c21685c70fbf8050d3c` (variável `REGSMART_PACKAGE` dos workflows) |
| Comparação | `pytest-ranking` do PyPI, sem pin (`RANKING_PACKAGE: "pytest-ranking"`); a versão efetiva está no log de cada job |
| Agregação | mediana das 3 repetições → média dos 5 mutantes por projeto → média entre projetos |

Contagens da campanha completa:

| | fórmula | total |
|---|---|---|
| Execuções de workflow medidas | 12 × 6 × 4 × 3 | **864** |
| Execuções de aquecimento | 12 × 6 × 2 | **144** (total no `runs.json`: 1.008) |
| Execuções de modo (jobs) | 12 × 6 × 9 × 3 | 1.944 |
| Execuções de modo dos mutantes (entram nas métricas) | 12 × 5 × 9 × 3 | 1.620 |

> Na execução registrada neste repositório, 8 jobs do pytorch-lightning travaram depois do fim da sessão do pytest e não geraram report-log. Por isso o `runs.csv` tem 1.612 linhas (127 no pytorch-lightning), e nesses pares a mediana usa as repetições disponíveis.

## 2. Dataset (12 projetos)

Forks em `github.com/leticosta4/<repo>` dos projetos abaixo, derivados do dataset de 14 projetos do pytest-ranking (critérios em [criterios-dataset.md](./criterios-dataset.md)):

[aeon](https://github.com/aeon-toolkit/aeon) · [apscheduler](https://github.com/agronholm/apscheduler) · [dask](https://github.com/dask/dask) · [dvc](https://github.com/iterative/dvc) · [ipython](https://github.com/ipython/ipython) · [librosa](https://github.com/librosa/librosa) · [networkx](https://github.com/networkx/networkx) · [pytest-django](https://github.com/pytest-dev/pytest-django) · [pytest-xdist](https://github.com/pytest-dev/pytest-xdist) · [pytorch-lightning](https://github.com/Lightning-AI/pytorch-lightning) · [trimesh](https://github.com/mikedh/trimesh) · [ultralytics](https://github.com/ultralytics/ultralytics)

- `ansible/molecule` e `ansible/ansible-lint` ficaram de fora: rodam os testes via tox reaproveitando outro repositório da organização, então não dá para injetar as flags dos plugins.
- Branch default: `master` em apscheduler, pytest-xdist e pytorch-lightning; `main` nos demais.
- Arquivos de workflow de cada modo, por fork: `data/workflow_plan.json`.
- Particularidades que afetam a replicação:
  - **aeon**: a matriz roda cada modo em Python 3.12, 3.13 e 3.14; a análise usa só o 3.13 (`collect --python aeon=3.13`). O baseline usa o modo reduzido de PR do aeon (`--prtesting true`).
  - **pytest-django** e **pytest-xdist**: rodam a suíte via **tox**. Os workflows de ranking e regsmart precisam de `-o cache_dir="$GITHUB_WORKSPACE/.pytest_cache"` depois do `--`; sem isso o pytest grava o cache em `.tox/<env>/.pytest_cache` e o cache dos plugins nunca é salvo (seção 6).
  - **pytorch-lightning**: usa `pytest-random-order` com semente `$GITHUB_RUN_ID` em todos os workflows, inclusive o baseline.

## 3. Modos de comparação (9)

| modo (label do job) | workflow | ferramenta | peso |
|---|---|---|---|
| `baseline` | baseline | pytest padrão | — |
| `rkn_qtf` | ranking | pytest-ranking QTF | `--rank-weight=1-0-0` |
| `rkn_recentfail` | ranking | pytest-ranking RecentFail | `0-1-0` |
| `rkn_simchgpath` | ranking | pytest-ranking SimChgPath | `0-0-1` |
| `rkn_hybrid` | ranking | pytest-ranking Hybrid | `1-1-1` |
| `rgsm_qtf` | regsmart | RTS + QTF | `--ranking-weight=1-0` |
| `rgsm_recentfail` | regsmart | RTS + RecentFail | `0-1` |
| `rgsm_hybrid` | regsmart | RTS + Hybrid (QTF + RecentFail, sem SimChgPath) | `1-1` |
| `regsmart-nr` | regsmart sem RTP | RTS (seleção por função, sem priorização) | `--no-rank` |

## 4. Métricas

Uma linha de `data/flaky_mut/metrics/runs.csv` = um job de modo ("leg") de um mutante.

| coluna | definição |
|---|---|
| `n_tests` | testes executados (report-log) |
| `suite_s` | tempo da suíte: o "in Xs" do resumo final do pytest (sessão principal) |
| `job_s` | duração do job inteiro (setup + testes + post), pela API de jobs |
| `tsr_s` | duração do step de teste, pela API de jobs |
| `rts_s` / `rtp_s` | tempos de seleção/priorização impressos no resumo do plugin; 0 quando o plugin pula a etapa (`rts_skipped`/`rtp_skipped`) |
| `ttff_s` | tempo até a 1ª falta: RTS + RTP + (fim da 1ª falta detectada − início do 1º teste), pelo report-log |
| `ttff_pos` | posição da 1ª falta na ordem executada |
| `detected` / `hidden` (+ `_pct`) | faltas que o modo detectou / deixou escapar; `hidden_not_selected` = escaparam porque o RTS não selecionou o teste |
| `apfdc` | APFDc (Elbaum et al.), 1 falta = 1 teste; falta oculta contribui 0. Nos modos com RTS o *n* é o conjunto selecionado, então o APFDc de RTS e o de RTP não são diretamente comparáveis |

Definições usadas pelo `metrics_collector.py`:
- **Falta (esperada)**: teste que falha em **todas** as repetições do baseline do mutante.
- **Flaky**: falha em algumas repetições do baseline e passa em outras; sai das faltas.
- **Controle**: todo teste que falhou na branch de controle, em qualquer modo, é tratado como falha de ambiente ou dependente de ordem e sai das faltas de todos os mutantes do repo. As linhas do controle não entram no `runs.csv`.

## 5. Como replicar

### 5.0 Pré-requisitos

- Python 3.10+, `pip install pyyaml`; `pip install "mutmut==2.5.1"` só para gerar mutantes.
- [`gh` CLI](https://cli.github.com/) autenticado (`gh auth login`) e `GITHUB_TOKEN_REGSMART` (ou `GH_TOKEN`/`GITHUB_TOKEN`) com permissão para criar branches e disparar workflows nos forks. O `collect` baixa logs e artifacts pelo `gh`.
- Forks próprios dos 12 projetos. O dono dos forks está fixo em `OWNER = "leticosta4"` no `flaky_runner.py`; para replicar em outra conta, altere essa constante.
- Uma pasta com um clone de cada fork (`origin` = fork), passada com `--clones` ao `insert_mutations.py` (o padrão no código é um caminho local da autora).
- Os scripts rodam a partir da raiz deste repositório. `flaky_runner.py` e `metrics_collector.py` rodam como script; os demais, como módulo (`python3 -m <pasta>.<script>`).
- **Use uma única cópia deste repositório** para disparar e coletar: o `runs.json` é o registro de tudo que foi despachado, e duas cópias divergentes perdem runs ao serem juntadas.

### 5.1 Preparar os workflows dos forks

Em cada fork, a partir do workflow que roda a suíte de testes (`python3 -m get_info.identify_test_workflows` ajuda a mapear; resultado em `data/workflows_report.json`), crie os 4 workflows listados em `data/workflow_plan.json`. Requisitos de cada um:

- gatilho `workflow_dispatch`; o gatilho `push` deve excluir `mut-*`;
- um job por modo, com o label do modo no nome do job, `fail-fast: false`;
- `pytest-reportlog` instalado, `--report-log=reportlog.jsonl` e upload do artifact `reportlog-<label>` com `if: ${{ !cancelled() }}`;
- ranking e regsmart: restore do cache com `restore-keys` por prefixo e save com `if: always()` (ou `if: ${{ !cancelled() }}`) do diretório do plugin (`.pytest_cache/v/pytest_ranking_data` e `.pytest_cache/v/pytest_ranked_selection_data`);
- regsmart: `actions/checkout` com `fetch-depth: 0`;
- `concurrency` que não cancele runs de workflows diferentes na mesma branch.

Confira com:
```bash
python3 -m gh_automation.check_workflows                 # só leitura; sai com 1 se houver ERRO
python3 -m gh_automation.sync_repo --sha ec6d08a5986a1c3aeb2e0c21685c70fbf8050d3c --dry-run
python3 -m gh_automation.sync_repo --sha ec6d08a5986a1c3aeb2e0c21685c70fbf8050d3c   # fixa o REGSMART_PACKAGE
```

> Todo commit em workflow de fork deve levar `[skip ci]` na mensagem. Os workflows também rodam em `push` na default e em `pull_request` dos PRs das `mut-*`, e esses runs gravariam cache dos plugins antes do aquecimento. O `[skip ci]` não afeta o `workflow_dispatch`.

### 5.2 Gerar e publicar os mutantes

```bash
python3 -m mutation_testing.mutation_gen gen --n 5                 # patches em data/mutmut/patches/ (usa data/mutmut/mutation_plan.json)
python3 -m mutation_testing.insert_mutations --clones <pasta-dos-clones> --dry-run
python3 -m mutation_testing.insert_mutations --clones <pasta-dos-clones> --push --pr
python3 -m mutation_testing.fetch_mut_branches --write             # registra os SHAs em data/mutmut/mutant_branches.json
```

Cada `mut-*` é a branch default do fork + 1 commit com o patch. Quando a default muda (workflow, pin do plugin), faça `git merge <default>` em cada `mut-*` (o `sync_repo.py` já faz isso) e rode `fetch_mut_branches --write` de novo. O `flaky_runner.py run` aborta com "branches mudaram" se o SHA de uma branch não bater com o registro.

### 5.3 Executar a campanha (um repo por vez)

```bash
python3 flaky_runner.py verify --repo <repo>                                    # esperar "0 bloqueio(s)"
python3 flaky_runner.py run --repo <repo> --control --warmup --dry-run          # 84 runs por repo
python3 flaky_runner.py run --repo <repo> --control --warmup --max-active 15    # aeon: --max-active 5
python3 flaky_runner.py status --repo <repo>                                    # acompanhar (outro terminal, sem API)
python3 flaky_runner.py run --repo <repo> --control --warmup --redo             # só para runs cancelados/perdidos
```

- `--control` inclui a branch default como mutante `control`; `--warmup` liga o aquecimento nos workflows com `warmup: true` no `workflow_plan.json`.
- As repetições de uma lane rodam em sequência, para que o cache passe de uma para a outra.
- O plano Free do GitHub tem teto de 20 jobs simultâneos; `--max-active` evita que a fila entre na medição.
- Não faça push nas `mut-*` durante a campanha: os runs seguintes rodariam em outro commit.
- Antes de seguir, `python3 flaky_runner.py status` deve mostrar nenhuma run ativa e "Dispatch falhou / run perdido" = 0.

**Refazer tarefas já concluídas** (ex.: depois de corrigir um workflow): o `--redo` só redispara runs cancelados. Para as concluídas, zere as linhas no `runs.json` com `flaky_runner.reset_row(r)` (guarda o run antigo em `history`) e `r.pop("sha")` se a branch ganhou commit novo; depois rode `run` com os mesmos filtros (`--repo`, `--workflow`), começando por `--dry-run`. Baseline e regsmart sem RTP não usam cache e não precisam ser refeitos junto com ranking/regsmart.

### 5.4 Testes flaky, relatório e métricas (todos os repos de uma vez)

Nesta ordem:
```bash
python3 flaky_runner.py flaky --exclude-warmup        # atualiza conclusões no runs.json e gera flaky_tests.json
python3 flaky_runner.py report                        # report.md (lê runs.json e flaky_tests.json)
python3 metrics_collector.py probe --campaign flaky --repo <repo> --workflow regsmart   # 1x por repo novo: confere os regex de RTS/RTP
python3 metrics_collector.py collect --campaign flaky --python aeon=3.13              # runs.csv e faults.json
python3 metrics_collector.py aggregate --campaign flaky                               # tables/
```

- O `flaky` vem antes do `collect` porque atualiza no `runs.json` a conclusão de runs que terminaram sem o `run` ter visto; o `collect` só usa runs `success`/`failure`.
- **Nunca rode o `collect` com `--repo`**: ele reescreve o `runs.csv` e o `faults.json` só com aquele repo.
- Logs e artifacts ficam em cache local (`data/flaky_mut/raw/`, `data/flaky_mut/metrics/cache/`); repetir os comandos só baixa o que falta.
- `aggregate` aceita `--rep-stat {median,mean}` (entre repetições, padrão mediana) e `--mut-stat {mean,median}` (entre mutantes, padrão média).

Checagem do resultado:
```bash
python3 -c "import json,collections;print(collections.Counter(r['repo'] for r in json.load(open('data/flaky_mut/runs.json'))['runs']))"  # 84 por repo
python3 -c "import pandas as pd;print(pd.read_csv('data/flaky_mut/metrics/runs.csv').groupby('repo').size())"                          # 135 por repo
```
O `collect` deve informar 864 runs concluídos. Em ranking/regsmart, `ttff_pos` deve variar entre QTF, RecentFail e Hybrid; se for idêntico ao baseline, o cache do plugin não está sendo gravado.

## 6. Problemas encontrados e como foram tratados

| problema | efeito | tratamento |
|---|---|---|
| tox muda o `cache_dir` (pytest-django, pytest-xdist) | cache dos plugins nunca salvo; priorização sem efeito | `-o cache_dir="$GITHUB_WORKSPACE/.pytest_cache"`; ranking e regsmart desses 2 repos refeitos (96 runs) |
| Jobs do pytorch-lightning travam após o fim do pytest (processo DDP órfão) | 8 jobs sem report-log | mantidos de fora; mediana das reps disponíveis. Não refaça só o job: a semente do random-order é o run id e a ordem se repete |
| Matriz de Python do aeon (nomes de job repetidos) | o coletor antigo perdia legs | coletor baixa o log por id do job (PR #26); `--python aeon=3.13` |
| Dispatch duplicado depois de erro 5xx | run a mais na mesma lane | detectado e sinalizado pelo `flaky_runner` (PR #19) |
| Falhas dependentes de ordem no controle (ex.: ipython) | testes falham só sob reordenação | saem das faltas pela regra do controle (PR #18) |

## 7. Dados versionados

| arquivo | conteúdo |
|---|---|
| `data/fork_commits.csv` | commit e data de congelamento de cada fork |
| `data/mutmut/mutants.json`, `patches/` | metadados e patch de cada mutante |
| `data/mutmut/mutant_branches.json` | branch e SHA publicados de cada mutante |
| `data/workflow_plan.json` | arquivo de workflow de cada modo, por fork |
| `data/flaky_mut/runs.json` | registro de todas as execuções despachadas (run ids, SHAs, conclusões, histórico de refações) |
| `data/flaky_mut/flaky_tests.json`, `report.md` | classificação de testes flaky e relatório da campanha |
| `data/flaky_mut/metrics/runs.csv`, `faults.json` | métricas por leg e faltas/flaky por mutante |
| `data/flaky_mut/metrics/tables/` | tabelas por métrica (`<métrica>.csv`, `_sd.csv`, `.tex`), linhas = repos, colunas = modos |

Não versionados (`.gitignore`): clones locais (`work/`, `_regsmart_sync/`), logs brutos (`data/flaky_mut/raw/`), cache do coletor (`data/flaky_mut/metrics/cache/`) e cache do mutmut (`data/mutmut/mutcache/`).

## 8. Scripts

Usados no experimento:

| script | função |
|---|---|
| [flaky_runner.py](./flaky_runner.py) | `verify`, `run`, `status`, `flaky`, `report`: dispara os workflows por lane, registra tudo no `runs.json` e classifica testes flaky |
| [metrics_collector.py](./metrics_collector.py) | `probe`, `collect`, `aggregate`: calcula as métricas por leg e gera as tabelas |
| [mutation_testing/mutation_gen.py](./mutation_testing/mutation_gen.py) | gera os patches de mutação (mutmut, sem rodar testes) |
| [mutation_testing/insert_mutations.py](./mutation_testing/insert_mutations.py) | publica uma branch `mut-*` por mutante (e draft PR com `--pr`) |
| [mutation_testing/fetch_mut_branches.py](./mutation_testing/fetch_mut_branches.py) | realinha `mutant_branches.json` com os forks |
| [gh_automation/sync_repo.py](./gh_automation/sync_repo.py) | fixa o `REGSMART_PACKAGE` nos workflows e faz merge da default nas `mut-*` |
| [gh_automation/check_workflows.py](./gh_automation/check_workflows.py) | confere (só leitura) se os 4 workflows de cada fork atendem aos requisitos |
| [get_info/identify_test_workflows.py](./get_info/identify_test_workflows.py), [get_info/last_commit.py](./get_info/last_commit.py) | mapeamento inicial dos workflows e do commit de congelamento |

Auxiliares da fase de validação (avaliação manual por PR com labels), não necessários para replicar as métricas: [check_previous_results.py](./check_previous_results.py), [pr_inicial_repos.py](./pr_inicial_repos.py), [gh_automation/experiments_labels.py](./gh_automation/experiments_labels.py), [gh_automation/gactions_check.sh](./gh_automation/gactions_check.sh).

> O `flaky_runner.py` também define uma campanha `experiment` (`data/experiment/`); ela não foi usada. Todas as métricas vêm da campanha `flaky` com `--control --warmup`.
