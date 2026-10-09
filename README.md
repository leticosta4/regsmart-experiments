# regsmart-experiments

> scripts para coletar métricas de execuções de CI (pytest, pytest-ranking, pytest-regsmart)
>
> projeto avaliado: <https://github.com/leticosta4/pytest-regsmart>

## Métricas (a serem) coletadas

- TSR time
- RTS time
- RTP time
- Time to first fault
- Número/percentual de falhas/mudanças ocultas (*hidden*)
- Número/percentual de falhas/mudanças detectadas
- APFDc
- Tempo de execução do workflow (GitHub Actions) - *talvez*

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
1. mutation_gen.py       gera os patches dos mutantes (mutmut, sem rodar testes)
2. insert_mutations.py   cria a branch base `insert-mutations` e uma branch `mut-<repo>-mNNNN` por mutante
3. flaky_runner.py       roda os 4 workflows em cada mutante e detecta testes flaky
4. (a fazer) coleta de métricas a partir de data/experiment/runs.json
```

## Scripts

| script | função |
|---|---|
| [identify_test_workflows.py](./identify_test_workflows.py) | mapeia os workflows de teste de cada repositório |
| [last_commit.py](./last_commit.py) | pega o último commit de atuação do fork em relação ao upstream |
| [pr_inicial_repos.py](./pr_inicial_repos.py) | sobe uma mudança simples de comentário em um arquivo Python e abre um PR; serviu de base para a limpeza dos workflows |
| [experiments_labels.py](./experiments_labels.py) | cria labels nos 12 repositórios e apaga as labels default |
| [mutation_gen.py](./mutation_gen.py) | gera N mutantes por repositório e salva um *patch* por mutante |
| [insert_mutations.py](./insert_mutations.py) | cria a branch base e as branches de mutante, publicando o patch |
| [flaky_runner.py](./flaky_runner.py) | dispara repetições dos workflows nos mutantes e detecta testes flaky |
| [sync_mut_branches.md](./sync_mut_branches.md) | sincroniza as branches de mutação com a `insert_mutations` |
| [fetch_mut_branches.md](./fetch_mut_branches.md) | verifica alterações nas branches de mutação como preparo para o _flay_runner.py` |

### Pré-requisitos

- Python 3.10+
- [`gh` CLI](https://cli.github.com/) autenticado (`gh auth login`), ou `GITHUB_TOKEN_REGSMART` (`GH_TOKEN`/`GITHUB_TOKEN`). O token precisa criar branches e disparar workflows nos 12 forks
- `pip install pyyaml` (só o `verify`) e `pip install "mutmut==2.5.1"` (só o `mutation_gen.py`)

## Experimentos

Os principais workflows do pipeline possuem instruções de uso em docstrings logo no início de cada arquivo, estão linkados na Seção de [scripts](./README.md) . 

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

## Tabelas

- Exemplo de tabela de resultados: [artigo do pytest-ranking](https://dl.acm.org/doi/pdf/10.1145/3696630.3728587)
- [wip] [Tabela de experimentos do regsmart](https://docs.google.com/spreadsheets/d/135Y76Gk5xiq7A5H25R3dVN4CU9mEy-ivjeOr0HiKq0I/edit?usp=sharing)
