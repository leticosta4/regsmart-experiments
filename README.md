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
- [track_flaky_attempt.py](./track_flaky_attempt.py) - tentativa de rastrear testes flaky no CI subindo uma mudança simples de comentário em algum arquivo python e abrindo um PR para melhor visibilidade

## Tables

- Result table example: https://dl.acm.org/doi/pdf/10.1145/3696630.3728587 (pytest-ranking paper)
- [wip] Regsmart experiments table: https://docs.google.com/spreadsheets/d/135Y76Gk5xiq7A5H25R3dVN4CU9mEy-ivjeOr0HiKq0I/edit?usp=sharing
