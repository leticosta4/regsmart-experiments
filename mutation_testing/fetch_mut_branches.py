"""
realinha data/mutmut/mutant_branches.json com o que
existe de fato nos forks.

Quando você troca um mutante na mão (branch mut-* reescrita, PR com a label
ALT-mutante-alterada), o registro gerado pelo insert_mutations.py fica velho:
o `head_sha` não bate mais e o flaky_runner/experiment_runner se recusam a rodar.
Este script lê o remoto e corrige o registro. O remoto é a fonte da verdade.

Pra cada repo:
  - branch do registro existe com outro SHA -> atualiza head_sha, guarda o
    original em `original_head_sha` e marca `altered: true`;
  - branch do registro não existe mais -> `published: false`;
  - branch mut-<repo>-m* no remoto que não está no registro -> entra como
    `altered: true` (chave = nome sem o prefixo `mut-`);
  - PR (head = a branch) com a label ALT-mutante-alterada -> `altered: true`
    e guarda a url em `pr`;
  - confere (compare API) quantos commits o mutante está à frente/atrás da
    `insert-mutations` atual: atrás > 0 significa que workflows novos da base
    NÃO estão nessa branch (o dispatch usa o workflow da branch do mutante).

Uso:
  python -m mutation_testing.fetch_mut_branches                # só mostra o que mudaria
  python -m mutation_testing.fetch_mut_branches --write        # grava (backup em .json.bak)
  python -m mutation_testing.fetch_mut_branches --repo ipython --write

ATENÇÃO: não rode `insert_mutations.py --mutants --reset` nos mutantes
alterados: ele reconstrói a branch a partir do patch original e apaga a sua troca.
"""
import argparse
import json
import shutil
import sys
import urllib.parse

from flaky_runner import BRANCHES_PATH, OWNER, TOKEN, Api, save_json

PREFIX = "mut-"
LABEL = "ALT-mutante-alterada"


def paged(api: Api, path: str) -> list:
    sep = "&" if "?" in path else "?"
    out, page = [], 1
    while True:
        chunk = api.get(f"{path}{sep}per_page=100&page={page}")
        out += chunk
        if len(chunk) < 100:
            return out
        page += 1


def remote_mutants(api: Api, repo: str) -> dict[str, str]:
    refs = paged(api, f"/repos/{OWNER}/{repo}/git/matching-refs/heads/{PREFIX}{repo}-m")
    return {x["ref"].removeprefix("refs/heads/"): x["object"]["sha"] for x in refs}


def labeled_prs(api: Api, repo: str, label: str) -> dict[str, str]:
    """{branch head: url} dos PRs (qualquer estado) que têm a label."""
    out = {}
    for pr in paged(api, f"/repos/{OWNER}/{repo}/pulls?state=all"):
        if any(l["name"] == label for l in pr.get("labels", [])):
            out[pr["head"]["ref"]] = pr["html_url"]
    return out


def sync_repo(api: Api, repo: str, meta: dict, label: str) -> list[str]:
    base = meta.get("base_branch", "insert-mutations")
    mutants = meta.setdefault("mutants", {})
    remote = remote_mutants(api, repo)
    prs = labeled_prs(api, repo, label)
    by_branch = {m["branch"]: k for k, m in mutants.items()}
    notes = []

    for key, m in sorted(mutants.items()):
        sha = remote.get(m["branch"])
        if sha is None:
            if m.get("published"):
                notes.append(f"{key}: branch sumiu do remoto -> published=false")
            m["published"] = False
            continue
        if m.get("head_sha") != sha:
            m.setdefault("original_head_sha", m.get("head_sha"))
            notes.append(f"{key}: head_sha {str(m.get('head_sha'))[:8]} -> {sha[:8]} (alterado)")
            m["head_sha"] = sha
            m["altered"] = True
        elif not m.get("published"):
            notes.append(f"{key}: branch existe e bate com o registro -> published=true")
        m["published"] = True
        if m["branch"] in prs:
            if not m.get("altered"):
                notes.append(f"{key}: PR com label {label} -> altered=true")
            m["altered"] = True
            m["pr"] = prs[m["branch"]]

    for branch, sha in sorted(remote.items()):
        if branch in by_branch:
            continue
        key = branch.removeprefix(PREFIX)
        notes.append(f"{key}: branch só no remoto -> adicionado (altered)")
        mutants[key] = {"branch": branch, "head_sha": sha, "published": True,
                        "altered": True, "source": "remote"}
        if branch in prs:
            mutants[key]["pr"] = prs[branch]

    for key, m in sorted(mutants.items()):  # defasagem em relação à base atual
        if not m.get("published"):
            continue
        cmp_ = api.get(f"/repos/{OWNER}/{repo}/compare/"
                       f"{urllib.parse.quote(base, safe='')}...{m['head_sha']}")
        m["ahead_base"], m["behind_base"] = cmp_["ahead_by"], cmp_["behind_by"]
        if cmp_["behind_by"]:
            notes.append(f"{key}: {cmp_['behind_by']} commit(s) ATRÁS de {base}: workflows "
                         f"novos da base não estão nessa branch")
        if cmp_["ahead_by"] != 1:
            notes.append(f"{key}: {cmp_['ahead_by']} commit(s) à frente de {base} (esperado 1)")
    return notes


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--repo", action="append", help="restringe a um repo (repetível)")
    p.add_argument("--label", default=LABEL, help=f"label de PR de mutante alterado (padrão {LABEL})")
    p.add_argument("--write", action="store_true", help="grava o registro (senão só mostra)")
    args = p.parse_args()
    if not TOKEN:
        sys.exit("token obrigatório: defina GITHUB_TOKEN_REGSMART ou rode `gh auth login`")
    if not BRANCHES_PATH.exists():
        sys.exit(f"{BRANCHES_PATH} não existe")
    registry = json.loads(BRANCHES_PATH.read_text(encoding="utf-8"))
    repos = args.repo or sorted(registry)
    unknown = set(repos) - set(registry)
    if unknown:
        sys.exit(f"repo(s) fora do registro: {', '.join(sorted(unknown))}")

    api = Api(TOKEN)
    changed = 0
    for repo in repos:
        notes = sync_repo(api, repo, registry[repo], args.label)
        n_pub = sum(1 for m in registry[repo]["mutants"].values() if m.get("published"))
        print(f"\n{repo}: {n_pub} publicados")
        for n in notes:
            print(f"  - {n}")
        changed += len(notes)
    if not args.write:
        print(f"\n{changed} diferença(s). Nada gravado: use --write.")
        return
    shutil.copy(BRANCHES_PATH, BRANCHES_PATH.with_suffix(".json.bak"))
    save_json(BRANCHES_PATH, registry)
    print(f"\nGravado em {BRANCHES_PATH} (backup .json.bak).")


if __name__ == "__main__":
    main()
