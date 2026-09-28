## Fase 1: Triagem Automatizada (Metadados e Repositório)

* **Universo Inicial:** Selecione os 2.500 projetos mais baixados do PyPI em um período recente.
* **Filtro de Compatibilidade:** Exclua projetos que não possuam nos metadados do PyPI: uma URL do GitHub válida, a versão de Python e a versão de Pytest requeridas.
* **Filtro de Atividade de CI:** Mantenha apenas os projetos que executam integração contínua (CI) em seus commits recentes.
* **Filtro de Tamanho:** Exclua repositórios cujo comando `git clone` demore mais de 1 minuto para ser concluído.
* **Filtro de Popularidade:** Mantenha somente os projetos com mais de 1.000 estrelas no GitHub.
* **Filtro de Falhas:** Garanta que o projeto tenha pelo menos uma execução de testes (TSR) com falha registrada no branch padrão.

---

## Fase 2: Validação Prática em Fork (Top 40 Candidatos)

Inspecione os 40 projetos restantes mais baixados. Crie um fork de cada um, execute o último build bem-sucedido e valide se atende rigorosamente a estes três critérios:

* Os testes são executados via GitHub Actions.
* A execução passa sem erros em ambiente `ubuntu-latest` e Python 3.
* A suíte de testes (TSR) demora mais de 45 segundos para rodar. *(Este processo resultou em 12 projetos no estudo original).*

---

## Fase 3: Busca Complementar (Projetos com Ordem Aleatória)

Para adicionar projetos que já usavam execução de testes de forma aleatória (mitigando dependências de ordem de teste):

* Amplie a busca para os 50.000 projetos mais baixados do PyPI.
* Identifique projetos que utilizem plugins de ordenação aleatória (como `pytest-random-order` ou `pytest-randomly`).
* Aplique os mesmos filtros de metadados, estrelas, tempo de clone e faça a mesma inspeção prática da Fase 2. *(Este processo adicionou mais 2 projetos, totalizando os 14 do dataset).*
