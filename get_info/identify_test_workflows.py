"""
identify_test_workflows.py

Primeiro script da pipeline do regsmart-metrics: varre os workflows de CI
de cada fork e sinaliza, por heurística, qual arquivo provavelmente roda a
suíte de testes de verdade (pra você confirmar manualmente antes de simplificar).

USO:
    export GITHUB_TOKEN_REGSMART=ghp_xxx   # token pessoal, escopo "repo" (ou "public_repo") já basta
    python identify_test_workflows.py

Sem GITHUB_TOKEN_REGSMART, o script ainda funciona, mas usa a API não-autenticada do
GitHub (60 requisições/hora) -- com 14 repositórios e vários arquivos cada,
é fácil estourar esse limite no meio da execução (foi o que aconteceu comigo
ao mapear a lista a primeira vez). Com token, o limite sobe pra 5.000/hora.

Gerar um token: https://github.com/settings/tokens (classic, escopo "repo"
ou, se os forks forem públicos, só "public_repo" já é suficiente pra leitura).

SAÍDA:
    workflows_report.json -- lista de workflows por repo + candidato(s) a
    workflow de teste, com sinalização de matrix (OS/Python) quando detectada.
"""

import json
import os
import re
import sys
import time
import urllib.request
import urllib.error

OWNER = "leticosta4"

REPOS = [
    "aeon", "ansible-lint", "apscheduler", "dask", "dvc", "ipython",
    "librosa", "molecule", "networkx", "pytest-django", "pytest-xdist",
    "pytorch-lightning", "trimesh", "ultralytics",
]

# Palavras-chave que indicam que o workflow NÃO é o que roda a suíte de
# testes (lint, docs, publicação, release, manutenção do repo, etc.)
# -- ajuste essa lista se notar falso positivo/negativo em algum projeto.
NOT_TEST_KEYWORDS = (
    "publish", "release", "deploy", "docs", "lint", "mypy", "ruff",
    "stale", "cla", "mirror", "format", "fuzz", "links", "merge",
    "conda-check", "codeql", "benchmark", "labeler", "probot", "cleanup",
    "ack", "finalize", "push.yml", "redirects", "issue_", "monthly_",
    "weekly_", "update_contributors", "fast_release", "pr_label_edited",
    "pr_opened", "pr_examples", "pr_typecheck", "pr_precommit",
    "pr_core_dep_import", "nightly-wheel", "zizmor", "zulip",
    "python-package", "docker", "readme",
)

TOKEN = os.environ.get("GITHUB_TOKEN_REGSMART")


def api_headers():
    h = {"Accept": "application/vnd.github+json", "User-Agent": "regsmart-metrics"}
    if TOKEN:
        h["Authorization"] = f"Bearer {TOKEN}"
    return h


def list_workflow_files(repo):
    url = f"https://api.github.com/repos/{OWNER}/{repo}/contents/.github/workflows"
    req = urllib.request.Request(url, headers=api_headers())
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode())
    return [item["name"] for item in data if item["type"] == "file"]


def fetch_raw(repo, filename, branch_hints=("main", "master")):
    for branch in branch_hints:
        url = f"https://raw.githubusercontent.com/{OWNER}/{repo}/{branch}/.github/workflows/{filename}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "regsmart-metrics"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                return resp.read().decode(errors="replace"), branch
        except urllib.error.HTTPError:
            continue
    return None, None


def guess_test_candidates(files):
    """Retorna os arquivos que sobram depois de excluir os claramente não-teste."""
    return [f for f in files if not any(k in f.lower() for k in NOT_TEST_KEYWORDS)]


def analyze_workflow(content):
    has_pytest = bool(re.search(r"\bpytest\b", content))
    has_matrix = "matrix:" in content
    py_versions = re.findall(r"python-version:\s*\[([^\]]+)\]", content)
    os_list = re.findall(r"\bos:\s*\[([^\]]+)\]", content)
    return {
        "has_pytest_literal": has_pytest,
        "has_matrix": has_matrix,
        "python_versions_found": py_versions[:1],
        "os_found": os_list[:1],
    }


def main():
    if not TOKEN:
        print("AVISO: sem GITHUB_TOKEN definido -- rodando sem autenticação "
              "(limite de 60 req/h, pode falhar no meio do caminho).",
              file=sys.stderr)

    report = {}
    for repo in REPOS:
        print(f"Mapeando {repo}...", file=sys.stderr)
        try:
            files = list_workflow_files(repo)
        except urllib.error.HTTPError as e:
            report[repo] = {"error": f"http_{e.code}", "files": []}
            continue

        candidates = guess_test_candidates(files)
        candidate_details = []
        for fname in candidates:
            content, branch = fetch_raw(repo, fname)
            if content is None:
                candidate_details.append({"file": fname, "error": "conteudo_nao_encontrado"})
                continue
            info = analyze_workflow(content)
            info["file"] = fname
            info["branch"] = branch
            candidate_details.append(info)
            time.sleep(0.5)  # gentileza com a API, evita rate-limit por rajada

        report[repo] = {
            "all_workflow_files": files,
            "test_candidates": candidate_details,
        }
        time.sleep(0.5)

    with open("data/workflows_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("\nResumo:")
    for repo, info in report.items():
        if "error" in info:
            print(f"  {repo}: ERRO ({info['error']})")
            continue
        candidatos = [c["file"] for c in info["test_candidates"] if c.get("has_pytest_literal") or c.get("has_matrix")]
        print(f"  {repo}: candidatos fortes = {candidatos or '(nenhum claro -- checar manualmente)'}")

    print("\nRelatório completo salvo em data/workflows_report.json")


if __name__ == "__main__":
    main()
