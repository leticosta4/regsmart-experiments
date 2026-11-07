0. Preparação (uma vez por sessão de terminal)
```
git checkout main && git pull
pip install pyyaml
export GITHUB_TOKEN_REGSMART=<token>
gh auth status          # o collector usa o gh para baixar logs/artifacts
```

Se você mexeu em branches mut-* ou PRs desde a última vez, sincronize o registro e faça o commit:

```
python3 -m mutation_testing.fetch_mut_branches --write
git add data/mutmut/mutant_branches.json && git commit -m "data: sync mutant branches" && git push
```

1. Execução, um repo por vez

```
python3 flaky_runner.py verify --repo <repo>                                   # esperar "0 bloqueio(s)"
python3 flaky_runner.py run --repo <repo> --control --warmup --dry-run         # 84 runs por repo
python3 flaky_runner.py run --repo <repo> --control --warmup --max-active 15   # aeon: --max-active 5
python3 flaky_runner.py status --repo <repo>                                   # acompanhar (outro terminal)
python3 flaky_runner.py run --repo <repo> --control --warmup --redo            # só se algo cancelar/falhar
```

No librosa e no apscheduler, a refação é o mesmo run com --workflow ranking --workflow regsmart (48 runs por repo).

2. Confirmar que terminou

```
python3 flaky_runner.py status
```

Antes de seguir, confira duas coisas: nenhuma run "ativa" e a linha "Dispatch falhou / run perdido" em 0.

3. Flaky e relatório (todos os repos de uma vez)

```
python3 flaky_runner.py flaky --exclude-warmup
python3 flaky_runner.py report
```

O resultado sai em `data/flaky_mut/flaky_tests.json e data/flaky_mut/report.md`.

4. Métricas

```
# checagem do formato dos tempos (1x por repo novo)
python3 metrics_collector.py probe --campaign flaky --repo <repo> --workflow regsmart

# coleta + tabelas: UMA vez, sem --repo (processa tudo que está no runs.json)
python3 metrics_collector.py collect   --campaign flaky --python aeon=3.13
python3 metrics_collector.py aggregate --campaign flaky
```

O resultado sai em `data/flaky_mut/metrics/runs.csv`, `faults.json` e `tables/*.csv|_sd.csv|.tex`.

Lembretes
Não rode o collect com --repo de um repo só. Ele reescreve o runs.csv inteiro e apaga os outros repos.
Repetir os passos 3 e 4 não tem problema. Quando mais repos terminarem, basta rodar de novo, e o que já foi baixado sai do cache.
Não dê push nas branches mut-* durante a campanha. O run passaria a usar outro commit.
Se o PR #12 for mergeado no meio, dê Ctrl+C, faça git pull e rode o mesmo comando de novo. O script continua de onde parou.
Para a 1ª passada (librosa + apscheduler), siga os passos 2 a 4. Depois me mande o report.md e o runs.csv para eu revisar antes dos outros 10 repos.