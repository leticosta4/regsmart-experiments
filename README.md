# regsmart-experiments

> scripts para coletar métricas de execuções de CI (pytest, pytest-ranking, pytest-regsmart)
>
> projeto avaliado: <https://github.com/leticosta4/pytest-regsmart>

## Métricas (a serem) coletadas

> Nenhuma métrica foi coletada até aqui. O que já existe é a infraestrutura de
> execução (branches de mutante + campanhas no GitHub Actions) e a detecção de
> testes flaky; a coleta em si é a última etapa do [pipeline](#pipeline), ainda
> a fazer.

- TSR time
- RTS time
- RTP time
- Time to first fault
- Número/percentual de falhas/mudanças ocultas (*hidden*)
- Número/percentual de falhas/mudanças detectadas
- APFDc (*average percentage of faults detected*, variante custo-ponderada)
- Tempo de execução do workflow (GitHub Actions) - *talvez*

> TSR, RTS e RTP são as siglas usadas no
> [artigo do pytest-ranking](https://dl.acm.org/doi/pdf/10.1145/3696630.3728587),
> que é a referência de nomenclatura deste estudo.

## Modos de comparação (9)

- pytest puro (baseline)
- estratégias do pytest-ranking (4)
  - QTF: ordena por menor tempo de execução (peso 1–0 no regsmart)
  - RecentFail: ordena por falhas recentes (peso 0–1 no regsmart)
  - SimChgPath: ordena pela similaridade textual entre o ID do teste e os caminhos dos arquivos Python alterados
  - Hybrid: combina as 3 anteriores
- estratégias do pytest-regsmart (4)
  - granularidade da seleção: por função
  - peso do RTP:
    - nenhum (`--no-rank`)
    - QTF
    - RecentFail
    - Hybrid

## Dataset (12 projetos)

Forks dos repos abaixo:

[aeon](https://github.com/aeon-toolkit/aeon) · [apscheduler](https://github.com/agronholm/apscheduler) · [dask](https://github.com/dask/dask) · [dvc](https://github.com/iterative/dvc) · [ipython](https://github.com/ipython/ipython) · [librosa](https://github.com/librosa/librosa) · [networkx](https://github.com/networkx/networkx) · [pytest-django](https://github.com/pytest-dev/pytest-django) · [pytest-xdist](https://github.com/pytest-dev/pytest-xdist) · [pytorch-lightning](https://github.com/Lightning-AI/pytorch-lightning) · [trimesh](https://github.com/mikedh/trimesh) · [ultralytics](https://github.com/ultralytics/ultralytics)

> Fora do escopo (dataset original): `ansible/molecule` e `ansible/ansible-lint`. Eles rodam os testes via tox, reaproveitando outro repositório da mesma organização, então não dá para injetar as flags do pytest-ranking/regsmart no comando. Critérios completos em [criterios-dataset.md](./criterios-dataset.md).

## Pipeline

```
1.  get_info/identify_test_workflows.py    mapeia quais workflows de cada fork rodam a suíte de testes (base para limpeza manual)
2.  pr_inicial_repos.py                    abre um PR inicial em cada fork para validar a limpeza dos workflows
3.  gh_automation/experiments_labels.py    cria/replica as labels de experimento nos 12 forks
4.  mutation_testing/mutation_gen.py       gera os patches dos mutantes (mutmut, sem rodar testes)
5.  mutation_testing/insert_mutations.py   publica uma branch `mut-<repo>-mNNNN` por mutante sobre a base do fork
6.  gh_automation/sync_repo.py             atualiza o `REGSMART_PACKAGE` dos workflows e propaga a base para as branches de mutante
7.  flaky_runner.py                       roda os 4 workflows em cada mutante e detecta testes flaky
8.  mutation_testing/fetch_mut_branches.py realinha o registro com o remoto quando um mutante foi alterado na mão
9.  metrics_collector.py                   coleta métricas do run (TSR/RTS/RTP, APFDc, TTFF, etc.) a partir dos artifacts/logs
```

> A ordem importa: `gh_automation/sync_repo.py` (passo 6) roda **antes** de disparar
> qualquer run, senão os workflows ficam com o SHA antigo do `REGSMART_PACKAGE`.
> `mutation_testing/fetch_mut_branches.py` (passo 8) só é necessário quando um mutante foi
> trocado na mão (branch reescrita, PR com a label `ALT-mutante-modificada`).

## Scripts

| script | função |
|---|---|
| [check_previous_results.py](./check_previous_results.py) | consulta os PRs recentes de cada fork e resume se a avaliação foi positiva, negativa, mista ou sem classificação |
| [metrics_collector.py](./metrics_collector.py) | coleta métricas dos runs de experimentação (tempo, falhas detectadas, ocultas, APFDc, TTFF e demais indicadores) |
| [flaky_runner.py](./flaky_runner.py) | dispara repetições dos workflows em cada mutante, baixa os logs e detecta testes flaky |
| [pr_inicial_repos.py](./pr_inicial_repos.py) | cria uma alteração simples de teste em cada fork e abre um PR inicial para validar o setup de workflows |
| [get_info/identify_test_workflows.py](./get_info/identify_test_workflows.py) | mapeia quais workflows de cada repositório executam a suíte de testes e produzem a base do planejamento |
| [get_info/last_commit.py](./get_info/last_commit.py) | coleta o último commit de atuação do fork em relação ao upstream |
| [gh_automation/check_workflows.py](./gh_automation/check_workflows.py) | verifica, via API do GitHub, se cada workflow já está no formato esperado para o experimento e o coletor |
| [gh_automation/experiments_labels.py](./gh_automation/experiments_labels.py) | remove labels padrão e copia as labels de experimento para os 12 forks |
| [gh_automation/sync_repo.py](./gh_automation/sync_repo.py) | sincroniza o `REGSMART_PACKAGE` do plugin com o HEAD atual e reaplica a base nas branches de mutante |
| [gh_automation/gactions_check.sh](./gh_automation/gactions_check.sh) | lista runs `in_progress`/`queued` nos forks para diagnosticar fila e concorrência do GitHub Actions |
| [mutation_testing/mutation_gen.py](./mutation_testing/mutation_gen.py) | gera os patches de mutação (mutmut) para cada repositório e registra os metadados dos mutantes |
| [mutation_testing/insert_mutations.py](./mutation_testing/insert_mutations.py) | constrói uma branch por mutante aplicando o patch sobre a base do fork e publica o resultado |
| [mutation_testing/fetch_mut_branches.py](./mutation_testing/fetch_mut_branches.py) | reaproveita/realinha o registro das branches de mutante quando elas foram alteradas manualmente |

### Pré-requisitos

- Python 3.10+
- [`gh` CLI](https://cli.github.com/) autenticado (`gh auth login`), ou `GITHUB_TOKEN_REGSMART` (`GH_TOKEN`/`GITHUB_TOKEN`). O token precisa criar branches e disparar workflows nos 12 forks
- `pip install pyyaml` (só o `verify`) e `pip install "mutmut==2.5.1"` (só o `mutation_gen.py`)

## Experimentos

### Passo a passo

Cada script tem instruções completas na docstring; este é o caminho feliz, na ordem correta.

**0. Preparação**

- Siga os [pré-requisitos](#pré-requisitos).
- Clone os 12 forks numa pasta, um clone por repositório, com o `origin` apontando para o fork. **Os scripts não assumem esse caminho**: `insert_mutations.py` aceita `--clones`, enquanto `sync_repo.py` usa o diretório de sincronização configurado em código (`_regsmart_sync/`).

**1. Mapear e limpar os workflows**

```bash
export GITHUB_TOKEN_REGSMART=ghp_xxx
python -m get_info.identify_test_workflows   # gera data/workflows_report.json
python -m get_info.last_commit               # gera data/fork_commits.csv
```

Confirme à mão qual workflow de cada fork roda a suíte de teste, simplifique-o e injete as 4 variantes (`baseline`, `ranking`, `regsmart`, `regsmart-no-rank`), excluindo `mut-*` do gatilho `push` (`branches: ['**', '!mut-*']`).

**2. Labels**

```bash
python3 -m gh_automation.experiments_labels
```

**3. Mutantes**

```bash
python -m mutation_testing.mutation_gen gen --n 5                           # gera os patches (data/mutmut/patches/)
python -m mutation_testing.insert_mutations --dry-run                       # mostra o plano
python -m mutation_testing.insert_mutations --repo pytest-xdist --limit 3 --push  # teste pequeno
python -m mutation_testing.insert_mutations --push --pr                     # publica todas as branches e abre draft PRs
```

**4. Sincronizar os workflows dos mutantes**

```bash
python -m gh_automation.sync_repo --dry-run
python -m gh_automation.sync_repo            # executa a sincronização
```

**5. Rodar e classificar**

```bash
python flaky_runner.py verify               # confere dispatch, push, concurrency, cache
python flaky_runner.py run --dry-run        # mostra o plano
python flaky_runner.py run                  # dispara e espera (lanes sequenciais)
python flaky_runner.py status               # progresso, sem API
python flaky_runner.py flaky                # baixa os logs e acha os testes flaky
python flaky_runner.py report --show-expected
```

**Observações que valem a leitura antes de rodar**

- Os comandos acima são a invocação correta de cada script: `flaky_runner.py` roda como script (`python flaky_runner.py`), os demais como módulo (`python -m <pasta>.<script>`).
- `--reps` define as repetições medidas; `--limit-mutants` restringe aos N primeiros mutantes de cada repo (teste barato).
- `--max-active` limita os runs simultâneos (padrão 30). O plano **Free** tem teto de 20 jobs; acima disso o GitHub enfileira sozinho e a fila contamina a medição de makespan.
- `insert_mutations.py` e `sync_repo.py` só mostram o plano por padrão: nada é publicado sem `--push`. `fetch_mut_branches.py` só grava com `--write`.
- `fetch_mut_branches.py` é o passo 8 do [pipeline](#pipeline): rode-o só se algum mutante foi trocado na mão.
- `sync_repo.py` precisa rodar **antes** de disparar os runs; runs já feitos ficam com o SHA antigo no manifesto.

### Importante: Sobre detecção de flaky (`flaky`)

Dentro de cada workflow, um teste é intermitente se falhou em algumas execuções e passou em outras **no mesmo SHA** (o do mutante), comparando por `(job, nodeid)`. Depois o **baseline é a referência** para classificar cada teste que falhou em algum workflow:

| classe | significado |
|---|---|
| `flaky` | falha em algumas execuções do baseline e passa em outras |
| `só no plugin (flaky)` | baseline nunca falhou; falha às vezes sob plugin (provável dependência de ordem exposta pelo reordenamento) |
| `só no plugin (fixa)` | baseline nunca falhou; falha em todas as execuções de algum plugin (investigar o plugin) |
| `esperada, diverge` | falha sempre no baseline, mas não em todos os workflows (RTS não selecionou ou a ordem mudou o resultado) |
| `esperada` | falha sempre em todos os workflows: efeito do mutante (ou falha pré-existente); só contada no relatório (`report --show-expected` lista) |

O warm-up conta como execução (`--exclude-warmup` desliga). Decisões que valem citar na monografia:

- job sem resumo do pytest no log (infra, lint, runner caiu) é ignorado; "no tests ran" (RTS que não selecionou nada) conta como job válido;
- o log não distingue "passou" de "não foi selecionado": `0/3` num plugin pode ser qualquer um dos dois;
- "baseline nunca falhou" com poucas repetições não prova ausência de flakiness;
- testes que falham por dependência não fixada ou serviço externo aparecem como flaky e podem pedir checagem manual.

## Status do experimento

Preenchida a partir dos arquivos de `data/` — o estado abaixo reflete o commit atual.

| etapa | estado |
|---|---|
| Mapeamento dos workflows | ✅ 12/12 (`data/workflows_report.json`, que também lista os 2 fora de escopo) |
| Limpeza dos workflows | ✅ 12/12 (feita manualmente nos forks) |
| Mutantes gerados | ✅ 12/12 — 5 mutantes por repo (**60** patches, `data/mutmut/mutants.json`) |
| Branches de mutante publicadas | ✅ 60/60 (`data/mutmut/mutant_branches.json`) |
| Branches com SHA divergente do registro | ✅ 60/60 |
| Campanha **flaky** | 🟡 2/12 concluídos — **ipython** e **trimesh** (`data/flaky_mut/runs.json`, relatório em `data/flaky_mut/report.md`) |
| Coleta de métricas | ⬜ não iniciada (TSR/RTS/RTP, APFDc etc.) |

Os 10 repositórios restantes da campanha flaky estão com `enabled: true` no `data/flaky_mut/flaky_plan.json` e prontos para rodar — falta só o tempo de CI.

Para regenerar estes números: branches em `data/mutmut/mutant_branches.json` (campos `published`/`altered`), progresso da campanha com `python flaky_runner.py status` e o detalhamento com `python flaky_runner.py report`.

## Tabelas

- Exemplo de tabela de resultados: [artigo do pytest-ranking](https://dl.acm.org/doi/pdf/10.1145/3696630.3728587)
- [wip] [Tabela de experimentos do regsmart](https://docs.google.com/spreadsheets/d/135Y76Gk5xiq7A5H25R3dVN4CU9mEy-ivjeOr0HiKq0I/edit?usp=sharing)

## Arquivos não versionados

- `work/` — os 12 clones locais dos forks (usados por `insert_mutations.py` via `--clones` e por rotinas locais de validação).
- `_regsmart_sync/` — clones de sincronização usados por `gh_automation/sync_repo.py` para atualizar o `REGSMART_PACKAGE` nos workflows.
- `data/flaky_mut/raw/` — logs brutos baixados da API do Actions (um zip por run); o comando `flaky` os rebaixa quando necessário.
- `data/mutmut/mutcache/` — cache de enumeração do mutmut.

Os três estão no `.gitignore`. Os resultados de experimento (`runs.json`, `flaky_tests.json`, `report.md`, `mutants.json`, `mutant_branches.json`) **são** versionados.
