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
z- networkx/networkx - https://github.com/networkx/networkx
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

## Detectando flaky tests: `flaky_runner.py`

Dispara N repetições do workflow de testes de cada fork sobre o **mesmo SHA** da
branch `track-flaky` e usa o resultado pra medir flakiness, respeitando o teto de
jobs simultâneos da conta (Free = 20).

O isolamento por repetição é feito com **uma branch por repetição**
(`flaky-r01`..`flaky-r10`), todas apontando pro mesmo commit. Isso dá um
`github.ref` distinto por repetição, então os runs não se cancelam pelo
`concurrency` dos próprios workflows — sem editar nenhum workflow.

Branches e não tags porque `dask` e `pytest-django` declaram `push.tags: ["*"]`:
criar uma tag dispara um workflow extra via `push`, poluindo a contagem. Nenhum
dos 12 workflows dispara `push` para `flaky-r01`.

As branches são criadas pela API (`POST /git/refs`), sem clone local: apontar
uma ref num commit que já existe não precisa montar blob/tree/commit. Mover uma
branch existente é `DELETE` + `POST`, e por isso exige `--repoint` — criar branch
nova não toca em nada e segue sem a flag.

```bash
# pré-flight: confere que cada workflow aceita workflow_dispatch
python3 flaky_runner.py verify

# roda (sem --no-wait ele espera tudo terminar)
python3 flaky_runner.py run --repo dask --reps 10

# depois, a qualquer momento:
python3 flaky_runner.py status   # relê status/conclusão de cada run
python3 flaky_runner.py report   # gera data/flaky/flaky_report.md
```

Opções do `run`:
- `--budget N` teto de jobs simultâneos (default 20)
- `--no-wait` despacha e sai; o `status`/`report` reconciliam depois
- `--repoint` move branches que apontam para outro SHA
- `--restart` redespacha tudo do zero
- `--dry-run` mostra o plano sem criar branch nem disparar nada

Arquivos em `data/flaky/`:
- `flaky_plan.json` — repos, workflow, branch, número de repetições
- `flaky_runs.json` — manifesto de execução (uma linha por repetição)
- `flaky_report.md` — relatório de custo e saúde da execução

**Custo é medido, não estimado.** Sai dos `started_at`/`completed_at` reais de
cada job: minutos de runner somados, makespan por repo e pico de concorrência
medido. A trava de orçamento aprende o tamanho de cada repo na primeira
repetição em vez de estimar pelo YAML.

> **Pendente:** a seção "Testes flaky" do relatório ainda sai vazia. Falta a
> análise de logs (`nodeid` → outcome por repetição), que é a parte que responde
> *quais* testes são flaky. Também falta `-rA` em 7 dos 12 workflows — só
> `dask`, `pytorch-lightning` e `apscheduler` emitem resultado por teste hoje.

## Tables

- Result table example: https://dl.acm.org/doi/pdf/10.1145/3696630.3728587 (pytest-ranking paper)
- [wip] Regsmart experiments table: https://docs.google.com/spreadsheets/d/135Y76Gk5xiq7A5H25R3dVN4CU9mEy-ivjeOr0HiKq0I/edit?usp=sharing
