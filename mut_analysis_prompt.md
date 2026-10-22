# Tarefa: analisar PRs de mutação e classificá-los com labels

## Contexto
Estou avaliando o plugin pytest-regsmart (seleção/priorização de testes) para o meu TCC.
Owner de todos os repositórios: `leticosta4`. Repositórios (12):
`librosa, apscheduler, pytest-django, trimesh, networkx, pytest-xdist, pytorch-lightning, aeon, dvc, dask, ultralytics, ipython`

Cada repo tem exatamente 5 PRs de mutação, com branch de origem no padrão `mut-<nome-do-repo>-m<dígitos>` (ex.: `mut-librosa-m123`, `mut-pytest-django-m45`).

Em cada PR são comparados 5 modos:
- **baseline**: suíte completa
- **rts-only**: só seleção (workflow `regsmart-no-rank`)
- **3 modos ranqueados**: seleção + priorização, que ficam DENTRO do workflow `regsmart`, como uma matrix interna que itera pelos 3 modos (entre eles `recentfail` e `QTF`; o terceiro não tem label própria)

**IMPORTANTE: ignore completamente o pytest-ranking** (workflow `ranking` no mapeamento abaixo, ou qualquer run com "ranking" no nome). Não liste runs, não baixe logs, não use em nenhuma métrica.

Use o `gh` CLI (já autenticado). Não use scraping.

## Passo 0: Descoberta dos PRs e mapeamento dos workflows

Mapeamento exato dos arquivos de workflow por repo:

```json
{
  "apscheduler":       {"baseline": "test.yml",             "ranking": "test-ranking.yml",       "regsmart": "test-regsmart.yml",       "regsmart-no-rank": "test-regsmart-nr.yml"},
  "ipython":           {"baseline": "test.yml",             "ranking": "test-ranking.yml",       "regsmart": "test-regsmart.yml",       "regsmart-no-rank": "test-regsmart-nr.yml"},
  "dvc":               {"baseline": "tests.yaml",           "ranking": "tests-ranking.yaml",     "regsmart": "tests-regsmart.yaml",     "regsmart-no-rank": "tests-regsmart-nr.yaml"},
  "librosa":           {"baseline": "ci.yml",               "ranking": "ci-ranking.yml",         "regsmart": "ci-regsmart.yml",         "regsmart-no-rank": "ci-regsmart-nr.yml"},
  "pytorch-lightning": {"baseline": "ci-tests-pytorch.yml", "ranking": "ci-tests-ranking.yml",   "regsmart": "ci-tests-regsmart.yml",   "regsmart-no-rank": "ci-tests-regsmart-nr.yml"},
  "trimesh":           {"baseline": "test.yml",             "ranking": "test-ranking.yml",       "regsmart": "test-regsmart.yml",       "regsmart-no-rank": "test-regsmart-nr.yml"},
  "aeon":              {"baseline": "pr_pytest.yml",        "ranking": "pr_ranking.yml",         "regsmart": "pr_regsmart.yml",         "regsmart-no-rank": "pr_regsmart-nr.yml"},
  "ultralytics":       {"baseline": "ci-pytorch.yml",       "ranking": "ci-ranking.yml",         "regsmart": "ci-regsmart.yml",         "regsmart-no-rank": "ci-regsmart-nr.yml"},
  "dask":              {"baseline": "tests.yml",            "ranking": "tests-ranking.yml",      "regsmart": "tests-regsmart.yml",      "regsmart-no-rank": "tests-regsmart-nr.yml"},
  "networkx":          {"baseline": "test.yml",             "ranking": "test-ranking.yml",       "regsmart": "test-regsmart.yml",       "regsmart-no-rank": "test-regsmart-nr.yml"},
  "pytest-xdist":      {"baseline": "test.yml",             "ranking": "test-ranking.yml",       "regsmart": "test-regsmart.yml",       "regsmart-no-rank": "test-regsmart-nr.yml"},
  "pytest-django":     {"baseline": "main.yml",             "ranking": "main-ranking.yml",       "regsmart": "main-regsmart.yml",       "regsmart-no-rank": "main-regsmart-nr.yml"}
}
```

Etapas:
1. Para cada repo, liste os PRs em qualquer estado: `gh pr list --repo leticosta4/<repo> --state all --limit 200 --json number,headRefName,headRefOid,state`. Filtre pela regex `^mut-<repo>-m\d+$` (escape o nome do repo; atenção a `pytest-django` e `pytest-xdist`). O esperado são 5 PRs por repo; se for diferente, registre a divergência e siga.
2. Para cada PR, pegue o run mais recente no head SHA de cada um dos 3 arquivos relevantes (`baseline`, `regsmart-no-rank`, `regsmart`) com `gh run list --repo leticosta4/<repo> --workflow <arquivo> --commit <sha> --json databaseId,conclusion,createdAt,updatedAt,attempt`. Se faltar algum, registre "não identificado" e siga, sem adivinhar.
3. **Seleção dos jobs (para não analisar a matrix inteira):** cada workflow pode ter matrix de versão do Python (e talvez de SO). NÃO analise todas as combinações. Use `gh run view <id> --json jobs` e escolha **um único job por modo**:
   - **Python 3.13**. Se o repo não tiver 3.13 na matrix, use a maior versão disponível que exista tanto no baseline quanto no regsmart, e registre qual foi usada.
   - Se também houver matrix de SO, use `ubuntu`. Se ainda restar mais de um job candidato, escolha o primeiro em ordem alfabética do nome do job e registre.
   - No workflow `regsmart`, a matrix interna dos 3 modos ranqueados NÃO é filtrada: pegue 1 job por modo (3 jobs), todos na mesma versão do Python (e SO) escolhida acima. Descubra qual chave da matrix representa o modo (nome do job, valor da matrix ou flag do pytest) lendo o YAML do workflow na branch do PR e os nomes dos jobs, e identifique `recentfail`, `QTF` e o terceiro (`outro-ranqueado`).
   - Resultado esperado: **5 jobs por PR** (baseline, rts-only, recentfail, QTF, outro-ranqueado). Baixe logs só desses jobs (`gh run view <run_id> --job <job_id> --log`), nunca o run inteiro.
4. **Validação pelo log:** o bloco do regsmart que tem a linha `Time to run the regression test prioritization` é de modo ranqueado; no rts-only ela não deve existir. Se nome e log discordarem, o log vence e o conflito vai para o relatório.

## Passo 1: Coleta (somente leitura)
Para cada um dos 5 jobs selecionados, colete:
- **duração do job** (`startedAt` → `completedAt` do job, não `createdAt` do run, para não contar fila). Esse é o "tempo do workflow" na comparação, já que só um job por modo é analisado.
- **duração do step de testes** (o step que roda pytest)
- lista de testes que falharam (linhas `FAILED path::test` do pytest)
- total de testes executados (linha final do pytest, ex.: "N passed, M failed")
- nos jobs do regsmart, o bloco de resumo do plugin (formato abaixo)

Se o run tiver múltiplas tentativas (re-runs), use a mais recente e registre que houve re-run.

## Formato do resumo do pytest-regsmart (parse do log)
O bloco começa com uma linha `=== pytest-regsmart summary info ===` e contém, conforme o caso:

```
Default branch used for comparison: origin/main
WARNING: Function-level selection found no affected tests; falling back to file-level selection (109 test file(s)).
Time to run the regression test selection (s): 14511.07 ms (14.51107120513916 s)
Time to run the file-level regression test selection (s): 938.34 ms (0.9383382797241211 s)
Time to run the regression test prioritization (s): 8.69 ms (0.008693933486938477 s)
Time to collect test features (s): 10.15 ms (0.01015329360961914 s)
Tests executed: 2783
```

Regras de extração:
- `Tests executed: N` → testes que o regsmart executou. Compare com o total do baseline do mesmo PR (`proporção = N / total_baseline`).
- `WARNING: ... falling back to file-level selection (K test file(s))` → **fallback de nível de arquivo** (registre K).
- Qualquer outro `WARNING` com "falling back" que indique execução da suíte toda → **fallback de suíte inteira**. Se o texto não for reconhecível mas houver `WARNING` e `Tests executed` for igual (ou praticamente igual) ao total do baseline, registre como "provável fallback de suíte inteira" e sinalize. Inclua no relatório o texto literal de todo `WARNING` inédito, para eu conhecer as mensagens.
- `Time to run the regression test selection` → overhead de seleção (use o valor em segundos entre parênteses). `Time to run the file-level regression test selection` só existe com fallback de arquivo; some os dois para o overhead total de seleção e registre os dois valores.
- `Time to run the regression test prioritization` só aparece nos modos ranqueados; sua ausência no rts-only é esperada, não é erro.
- Se o bloco não existir no log, registre "resumo ausente" (possível falha antes do pytest) e trate o job como suspeito.
- Registre o overhead (seleção + priorização + coleta de features) separado do tempo do step de testes, para eu saber se o ganho vem dos testes ou se é consumido pelo overhead.

## Passo 2: Análise por PR
Compare cada um dos 4 modos do regsmart com o baseline:

**Falhas**
- `mesmas_falhas`: o conjunto de testes que falharam no regsmart é igual ao do baseline?
- `falhas_perdidas`: falharam no baseline mas NÃO falharam (ou não rodaram) no regsmart.
- `falhas_extras`: falharam no regsmart mas NÃO falharam no baseline.

**Tempo** (job inteiro e step de testes, separados)
- regsmart menor / igual (diferença ≤ 5%) / maior que o baseline.

**Fallback** (pelo resumo do plugin): nível de arquivo / suíte inteira / nenhum.

**Flakiness**
- Nos modos ranqueados, `falhas_extras` indicam provável flakiness por ordem (order-dependent).
- Se possível, registre se o mesmo teste extra falha em mais de um modo ranqueado ou só em um.

## Passo 3: Regras de labels (use APENAS labels já existentes no repo; não crie nem altere cores)
- `BOM-menor-tempo-geral`: algum modo regsmart teve tempo total do job menor que o baseline, com mesmas falhas.
- `BOM-regsmart-rts-only`: o modo rts-only teve mesmas falhas do baseline e foi mais rápido (step de testes ou total).
- `BOM-regsmart-recentfail`: o modo recentfail teve mesmas falhas e foi mais rápido.
- `BOM-regsmart-QTF`: o modo QTF teve mesmas falhas e foi mais rápido.
- `MAL-baseline-melhor`: baseline foi mais rápido que todos os modos regsmart, ou os regsmart perderam falhas que o baseline pegou.
- `MAL-demorou-mais`: algum modo regsmart demorou mais que o baseline (total ou step de testes).
- `MAL-selecao-bugada`: houve `falhas_perdidas` sem fallback e sem explicação óbvia no resumo do plugin.
- `SAD-limitacao-callgraph`: houve `falhas_perdidas` e há evidência clara no log de dependência não resolvida pelo call graph (ex.: import dinâmico, reflection, fixtures/conftest). Sem evidência clara, NÃO aplique e liste como "suspeita".
- `PROB-od-flakiness`: `falhas_extras` em modo ranqueado, conforme descrito acima.
- `fallback-nivel-arquivo`: pelo menos um modo caiu em fallback de nível de arquivo.
- `fallback-suite-inteira`: pelo menos um modo caiu em fallback de suíte inteira (apenas casos confirmados; os "prováveis" vão só para o relatório).
- `tempo-igual`: diferença de tempo dentro de 5% em todos os modos.
- `ALT-mutante-bugada` / `ALT-mutante-modificada`: NÃO aplicar automaticamente. Se o baseline passou inteiro (mutante não detectado) ou algo indicar mutante inválido, apenas sinalize no relatório.

Várias labels podem ser aplicadas ao mesmo PR. Antes de adicionar, remova do PR as labels desta lista que já estiverem nele e não se aplicam mais (análise idempotente), sem mexer em labels fora da lista. Se uma label da lista não existir no repo, não crie: registre no relatório.

## Passo 4: Execução em duas fases
1. **Dry-run (padrão):** não altere nada no GitHub. Gere `relatorio.md` e `relatorio.csv` com, por PR: repo, nº do PR, branch, run ids e job ids dos 5 modos, versão do Python (e SO) usada, tempos (job e step de testes) de cada modo, overhead do regsmart, testes executados vs total do baseline, falhas perdidas/extras, tipo de fallback, labels propostas e justificativa curta por label. Termine com resumo agregado (contagem por label e por repo) e lista de casos ambíguos ou não identificados.
2. **Aplicação:** só depois que eu revisar o relatório e disser "aplicar", rode `gh pr edit <n> --repo leticosta4/<repo> --add-label ... --remove-label ...` usando o CSV e gere o log do que foi feito.

## Regras
- Job falho por motivo de infraestrutura (timeout, erro de setup, cancelado) e não por teste → marque "run inválido" e não use na comparação.
- Não infira nada que não esteja no log; se faltar dado, registre "sem dados".
- Paralelismo moderado, respeitando rate limit do `gh`; salve logs em `./logs/<repo>/<pr>/` para não baixar duas vezes.
- **Piloto primeiro:** rode o fluxo completo (Passos 0 a 2 e proposta de labels, sem aplicar) em **1 PR do `librosa`** e pare. Mostre: o mapeamento arquivo → papel, qual versão do Python foi escolhida, como os 3 modos ranqueados foram identificados dentro da matrix, os 5 jobs selecionados e o resultado da análise. Só varra os 60 PRs depois que eu confirmar.