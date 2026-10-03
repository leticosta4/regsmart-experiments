# regsmart-metrics 

> script to collect metrics from CI workflows runs (pytest, ranking, regsmart)
> 
> project being evaluated: https://github.com/leticosta4/pytest-regsmart
> 

## metrics to be collected

- TSR time
- RTS time
- RTP time
- Time to first fault
- Number/percentage of hidden faults/changes
- Number/percentage of detected faults/changes
- APFDc
- Workflow run time (Github Actions) - _maybe_


## comparison modes (9)

- pytest only (baseline)
- pytest-ranking strategies (4)
    - QTF: orders tests by shorter runtime (weighted 1–0 in regsmart)
    - RecentFail: orders tests by recent failures (weighted 0–1 in regsmart)
    - SimChgPath: orders tests by how textually similar their IDs are to the paths of changed Python files
    - Hybrid: unify/balance all 3 above
- pytest-regsmart strategies (4)
    - selection granularity: per function
    - RTP weight:
      - none (--no-rank)
      - QTF
      - RecentFail
      - Hybrid


## dataset: list of projects (12)

the dataset is composed of 12 forks from the GitHub repositories below:

- aeon-toolkit/aeon - https://github.com/aeon-toolkit/aeon
- agronholm/apscheduler - https://github.com/agronholm/apscheduler
- dask/dask - https://github.com/dask/dask
- iterative/dvc - https://github.com/iterative/dvc
- ipython/ipython - https://github.com/ipython/ipython
- librosa/librosa - https://github.com/librosa/librosa
- networkx/networkx - https://github.com/networkx/networkx
- pytest-dev/pytest-django - https://github.com/pytest-dev/pytest-django
- pytest-dev/pytest-xdist - https://github.com/pytest-dev/pytest-xdist
- Lightning-AI/pytorch-lightning - https://github.com/Lightning-AI/pytorch-lightning
- mikedh/trimesh - https://github.com/mikedh/trimesh
- ultralytics/ultralytics - https://github.com/ultralytics/ultralytics

> Removed from scope (og dataset): `ansible/molecule` and `ansible/ansible-lint` because of their test workflow structure. They run tests via tox, reusing another repo from the same org - so i can't simply inject pytest-ranking/regsmart testing flags in the command.
>


## Scripts on this repo
- [identify_test_workflows.py](./identify_test_workflows.py) - mapeia os workflows de teste dos repositórios
- [last_commit.py](./last_commit.py) - pega o último commit de atuação do fork em relação ao repositório upstream
- [track_flaky_attempt.py](./track_flaky_attempt.py) - sobe uma mudança simples de comentário em algum arquivo python e abre um PR para melhor visibilidade; usei como base para fazer a limpeza dos workflows
- [flaky_runner.py](./flaky_runner.py) - dispara N repetições do workflow de cada fork e detecta os testes flaky (detalhes abaixo)

### Detectando flaky tests: `flaky_runner.py`

Dispara N repetições do workflow de testes de cada fork sobre o **mesmo SHA** da
branch `track-flaky`, mede o custo da execução e descobre **quais testes são
flaky** a partir dos logs dos runs.

### Pré-requisitos

- Python 3.10+
- [`gh` CLI](https://cli.github.com/) instalado e autenticado (`gh auth login`). O
  script usa o token dele; alternativamente, defina `GITHUB_TOKEN_REGSMART`
  (ou `GH_TOKEN`/`GITHUB_TOKEN`). O token precisa criar branches e disparar
  workflows nos 12 forks
- `pip install pyyaml` (só o `verify` usa)

### Fluxo

```bash
# 1x: confere workflow_dispatch e mostra o concurrency de cada workflow
python3 flaky_runner.py verify

# teste pequeno antes da rodada completa
python3 flaky_runner.py run --repo dask --reps 2 --dry-run   # só mostra o plano
python3 flaky_runner.py run --repo dask --reps 2

# rodada completa (sem --no-wait ele espera todos os runs terminarem)
python3 flaky_runner.py run

# acha os testes flaky (pode rodar com runs ainda em andamento: análise parcial)
python3 flaky_runner.py flaky

# gera data/flaky/flaky_report.md (offline, não chama a API)
python3 flaky_runner.py report
```

Todos os subcomandos aceitam `--repo` (repetível) e `--reps`.

| comando | o que faz | usa a API | gasta runner |
|---|---|---|---|
| `verify` | confere `workflow_dispatch` e mostra o `concurrency` de cada workflow | sim (leitura) | não |
| `run` | cria as branches, dispara, localiza os `run_id` e espera terminar | sim | **sim** |
| `flaky` | atualiza o status dos runs, baixa os logs e acha os testes flaky | sim | não |
| `report` | monta o relatório a partir dos arquivos em `data/flaky/` | não | não |

Opções do `run`:
- `--no-wait` despacha e sai; o `flaky` reconcilia o status depois
- `--repoint` move branches `flaky-rNN` que apontam para outro SHA
- `--dry-run` resolve o SHA de cada repo e mostra o plano, sem criar branch nem disparar nada
- `--poll-interval N` segundos entre as checagens enquanto espera (default 60)

Rodar o `run` de novo **pula** as repetições já despachadas (útil se o processo
cair no meio). Para recomeçar do zero, apague `data/flaky/flaky_runs.json`.

### Como o isolamento por repetição funciona

Cada repetição roda numa **branch própria** (`flaky-r01`..`flaky-r10`), todas
criadas a partir do SHA atual da `track-flaky`. Isso dá um `github.ref` distinto
por repetição, então os runs não se cancelam pelo `concurrency` dos próprios
workflows, sem editar nenhum deles.

Branches e não tags porque `dask` e `pytest-django` declaram `push.tags: ["*"]`:
criar uma tag dispararia um workflow extra via `push`, poluindo a contagem.
Nenhum dos 12 workflows dispara `push` para `flaky-r01`.

As branches são criadas pela API (`POST /git/refs`), sem clone local. Mover uma
branch existente é um `PATCH` com `force` e por isso exige `--repoint`; criar
branch nova não toca em nada e segue sem a flag.

> O `verify` imprime o `concurrency` de cada workflow. Se nenhum agrupar por
> `github.ref`, as branches por repetição passam a ser dispensáveis.

### Concorrência e limite de jobs

O script **não controla orçamento de jobs**: acima do teto de 20 jobs
simultâneos do plano Free, o próprio GitHub enfileira o que sobra. Duas
consequências para a análise de custo:

- o **makespan** inclui o tempo de fila;
- o **pico de concorrência** medido tende a saturar em 20, o que é um dado
  legítimo (a execução ficou no teto do plano) e não um erro.

Os dispatches saem com 1 s de intervalo para não esbarrar no limite secundário
de requisições da API.

### Como os testes flaky são detectados

O `flaky` baixa o log de cada run concluído (`gh api .../actions/runs/{id}/logs`,
com cache em `data/flaky/raw/`) e usa só o que o pytest imprime por padrão:

- as linhas `FAILED <nodeid>` / `ERROR <nodeid>` do resumo final;
- a linha de contagem (`3 failed, 1200 passed in 90s`), para o total de testes.

Não é preciso `-rA` nem editar os workflows.

Critério: um teste é **flaky** se falhou em pelo menos uma repetição e passou
em outra, **no mesmo SHA**. A comparação é feita por `(job, nodeid)`: o nome do
job inclui a perna da matriz (SO/versão do Python), então um teste que falha só
em uma versão não é contado como flaky.

Decisões que valem citar na monografia (ameaças à validade):

- teste que falha em **todas** as repetições é determinístico, não flaky, e fica
  de fora da tabela;
- job **sem resumo do pytest** no log (falha de infra, lint, runner caiu) é
  ignorado, para não virar "passou" por engano;
- o total de testes por repo (`total_seen`, usado na taxa de flakiness) é
  aproximado: soma, por job, do maior total visto (passed + failed + errors,
  sem skipped);
- testes que falham por dependência não fixada ou serviço externo aparecem como
  flaky e podem exigir checagem manual.

### Arquivos em `data/flaky/`

| arquivo | quem cria | conteúdo |
|---|---|---|
| `flaky_plan.json` | você (entrada) | repos, workflow, branch, número de repetições, `enabled` |
| `flaky_runs.json` | `run` (atualizado por `flaky`) | manifesto: uma linha por repetição (branch, `run_id`, status, jobs com timestamps), contadores de API e rate limit |
| `raw/<repo>/<run_id>.zip` | `flaky` | cache dos logs baixados (vale pôr no `.gitignore`) |
| `flaky_tests.json` | `flaky` | por repo: `total_seen` e os testes flaky com `reps`/`failed`/`passed` |
| `flaky_report.md` | `report` | relatório: custo, API/rate limit, saúde da execução, por repo e testes flaky |

### Métricas de custo

**Custo é medido, não estimado.** Sai dos `started_at`/`completed_at` reais de
cada job: minutos de runner somados, makespan por repo e pico de concorrência
(sweep line). Também são registrados o consumo de rate limit (inicial e final)
e os contadores de requisições (GET, POST/PATCH, retries), acumulados entre
execuções.

Para economizar rate limit, os jobs de cada run são buscados **uma única vez**,
quando o run termina; enquanto espera, cada checagem custa 1 GET por repo.

## Tables

- Result table example: https://dl.acm.org/doi/pdf/10.1145/3696630.3728587 (pytest-ranking paper)
- [wip] Regsmart experiments table: https://docs.google.com/spreadsheets/d/135Y76Gk5xiq7A5H25R3dVN4CU9mEy-ivjeOr0HiKq0I/edit?usp=sharing
