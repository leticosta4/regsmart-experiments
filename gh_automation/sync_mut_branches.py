"""
Atualiza o REGSMART_PACKAGE dos workflows do regsmart na `insert-mutations` e
propaga a mudança para as branches de mutante.

Por repo (de data/flaky/flaky_plan.json, com mutantes `published` no
data/mutmut/mutant_branches.json):
  1. nos workflows `regsmart` e `regsmart-no-rank` (nomes em data/workflow_plan.json),
     troca o valor de REGSMART_PACKAGE por
       git+https://github.com/leticosta4/pytest-regsmart@<sha mais recente da main>
     (edição textual: comentários, aspas e indentação ficam como estão);
  2. commita e sobe na `insert-mutations` (nada é commitado se já estiver no sha);
  3. `git switch insert-mutations` + `git pull`;
  4. em cada branch de mutante: `git merge insert-mutations` e push. Sem force:
     o histórico do mutante é preservado e ganha um commit de merge.

Os merges rodam em HEAD destacado a partir de `origin/<mut-*>` (não cria branch
local). No fim o clone volta para a branch em que estava. Clone com alterações
locais em arquivos versionados é pulado. Conflito de merge = `git merge --abort`
e o mutante é listado; nada é alterado nele.

Sem --push só mostra o plano (nada é escrito, commitado ou publicado). O registro
(mutant_branches.json, backup em .json.bak) só é gravado quando publica. Rode ANTES
de disparar os runs: runs já feitos ficam com o SHA antigo no manifesto.

Uso:
  python -m gh_automation.sync_mut_branches --repo ipython              # dry-run (padrão)
  python -m gh_automation.sync_mut_branches --repo ipython --push
  python -m gh_automation.sync_mut_branches --push --mutant ipython-m4267
  python -m gh_automation.sync_mut_branches --push --regsmart-sha <sha>  # fixa um commit específico

Não confundir com fetch_mut_branches.py, que só realinha o registro com o
remoto. Rode fetch_mut_branches.py --write` antes se você trocou mutantes na
mão.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from flaky_runner import (BRANCHES_PATH, OWNER, TOKEN, Api, load_repo_plan,
                          load_workflow_cfg, workflows_for)

CLONES = Path("/home/Letícia/Projetos/tcc-experiments/effective-validation")
BASE = "insert-mutations"
PKG_REPO = "pytest-regsmart"
MESSAGE = "ci: update REGSMART_PACKAGE to the latest commit"
DEFAULT_WORKFLOWS = ["regsmart", "regsmart-no-rank"]


def git(args: list[str], cwd: Path, check: bool = True):
    proc = subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True)
    if check and proc.returncode:
        raise RuntimeError((proc.stderr or proc.stdout).strip().splitlines()[-1][:200])
    return proc


def git_out(args: list[str], cwd: Path, **kw) -> str:
    return git(args, cwd, **kw).stdout.strip()


def is_ancestor(cwd: Path, a: str, b: str) -> bool:
    return git(["merge-base", "--is-ancestor", a, b], cwd, check=False).returncode == 0


def set_package(text: str, new: str) -> tuple[str, list[str]]:
    """Troca o valor de toda linha `REGSMART_PACKAGE: ...`, preservando aspas,
    indentação e comentário no fim da linha. Devolve (texto novo, valores antigos)."""
    out, olds = [], []
    for line in text.splitlines(keepends=True):
        m = re.match(r"^(\s*REGSMART_PACKAGE:[ \t]*)(.*?)(\r?\n?)$", line)
        if not m:
            out.append(line)
            continue
        pre, rest, nl = m.groups()
        if rest and rest[0] in "\"'":
            end = rest.find(rest[0], 1)
            if end == -1:
                out.append(line)
                continue
            old, tail, val = rest[1:end], rest[end + 1:], f"{rest[0]}{new}{rest[0]}"
        else:
            old, tail = re.match(r"(\S*)(.*)", rest).groups()
            val = new
        olds.append(old)
        out.append(f"{pre}{val}{tail}{nl}")
    return "".join(out), olds


def short(v: str) -> str:
    return v.split("@")[-1][:8] if "@" in v else v[:60]


def save_registry(registry: dict) -> None:
    shutil.copy(BRANCHES_PATH, BRANCHES_PATH.with_suffix(".json.bak"))
    tmp = BRANCHES_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(BRANCHES_PATH)


def process_repo(repo: str, cwd: Path, meta: dict, wf_files: dict[str, str], pkg: str,
                 args) -> tuple[int, bool]:
    """Devolve (falhas, registro alterado)."""
    failed, changed = 0, False
    if git_out(["status", "--porcelain", "-uno"], cwd):
        print(f"!! {repo}: alterações locais em arquivos versionados -- pulando "
              f"(commit/stash antes)", file=sys.stderr)
        return 1, False
    git(["fetch", "--prune", "origin"], cwd)
    try:
        base_sha = git_out(["rev-parse", "--verify", f"origin/{args.base}"], cwd)
    except RuntimeError:
        print(f"!! {repo}: origin/{args.base} não existe", file=sys.stderr)
        return 1, False
    print(f"\n{repo}: {args.base} @ {base_sha[:8]}")

    # 1) edição dos workflows (lida do remoto: o mesmo que o pull traria)
    edits: dict[str, str] = {}
    for wf, fname in wf_files.items():
        path = f".github/workflows/{fname}"
        blob = git(["show", f"origin/{args.base}:{path}"], cwd, check=False)
        if blob.returncode:
            print(f"  ! {wf}: {path} não existe em {args.base}")
            failed += 1
            continue
        new_text, olds = set_package(blob.stdout, pkg)
        if not olds:
            print(f"  ! {wf}: {path} não tem REGSMART_PACKAGE")
            failed += 1
        elif new_text == blob.stdout:
            print(f"  = {wf}: REGSMART_PACKAGE já em {short(pkg)}")
        else:
            edits[path] = new_text
            print(f"  ~ {wf}: REGSMART_PACKAGE {', '.join(dict.fromkeys(short(o) for o in olds))}"
                  f" -> {short(pkg)}  ({path})")

    mutants = [(k, m) for k, m in sorted((meta.get("mutants") or {}).items())
               if m.get("published") and not (args.mutant and k not in args.mutant)]

    if not args.push:
        for key, m in mutants:
            if is_ancestor(cwd, base_sha, m["head_sha"]) and not edits:
                print(f"  = {key}: já contém {args.base}")
                continue
            mb = git_out(["merge-base", f"origin/{args.base}", m["head_sha"]], cwd, check=False)
            touched = set(git_out(["diff", "--name-only", mb, m["head_sha"]], cwd, check=False).splitlines()) if mb else set()
            clash = sorted(touched & set(edits))
            print(f"  + {key}: merge de {args.base}"
                  + (f"  (CONFLITO provável: o mutante altera {', '.join(clash)})" if clash else ""))
        return failed, False

    original = git_out(["rev-parse", "--abbrev-ref", "HEAD"], cwd)
    if original == "HEAD":
        original = git_out(["rev-parse", "HEAD"], cwd)
    try:
        # 2) + 3) commit na base, push, switch + pull
        has_local = git(["rev-parse", "--verify", "--quiet", f"refs/heads/{args.base}"], cwd, check=False).returncode == 0
        git(["switch", args.base] if has_local else ["switch", "-c", args.base, "--track", f"origin/{args.base}"], cwd)
        git(["pull", "--ff-only", "origin", args.base], cwd)
        if edits:
            for path, text in edits.items():
                (cwd / path).write_text(text, encoding="utf-8", newline="")
            git(["add", *edits], cwd)
            git(["commit", "-m", args.message], cwd)
            res = git(["push", "origin", args.base], cwd, check=False)
            if res.returncode:
                print(f"  ! push de {args.base} recusado ({res.stderr.strip().splitlines()[-1][:120]})")
                return failed + 1, False
            print(f"  ✓ {args.base} atualizada e publicada")
        base_sha = git_out(["rev-parse", "HEAD"], cwd)

        # 4) merge em cada mutante
        for key, m in mutants:
            br = m["branch"]
            remote = git(["rev-parse", "--verify", "--quiet", f"origin/{br}"], cwd, check=False).stdout.strip()
            if remote != m["head_sha"]:
                print(f"  ! {key}: branch no remoto != registro; rode sync_mutant_branches.py --write")
                failed += 1
                continue
            if is_ancestor(cwd, base_sha, remote):
                print(f"  = {key}: já contém {args.base}")
                continue
            git(["switch", "--detach", f"origin/{br}"], cwd)
            merged = git(["merge", "--no-edit", "-m", f"Merge branch '{args.base}' into {br}", args.base],
                         cwd, check=False)
            if merged.returncode:
                git(["merge", "--abort"], cwd, check=False)
                print(f"  ! {key}: conflito no merge, abortado (branch intacta)")
                failed += 1
                continue
            new = git_out(["rev-parse", "HEAD"], cwd)
            res = git(["push", "origin", f"HEAD:refs/heads/{br}"], cwd, check=False)
            if res.returncode:
                print(f"  ! {key}: push recusado ({res.stderr.strip().splitlines()[-1][:120]})")
                failed += 1
                continue
            print(f"  ✓ {key}: {remote[:8]} -> {new[:8]}")
            m["previous_head_sha"], m["head_sha"], m["base_sha"] = remote, new, base_sha
            m["published"], m["behind_base"] = True, 0
            m["ahead_base"] = int(git_out(["rev-list", "--count", f"{base_sha}..{new}"], cwd))
            changed = True
        if changed and all(m.get("base_sha") == base_sha for m in meta["mutants"].values() if m.get("published")):
            meta["base_sha"] = base_sha
    finally:
        git(["switch", "--detach", original] if re.fullmatch(r"[0-9a-f]{40}", original) else ["switch", original],
            cwd, check=False)
    return failed, changed


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--repo", action="append", help="restringe a um repo (repetível)")
    p.add_argument("--mutant", action="append", help="restringe a um mutante, ex.: ipython-m4267 (repetível)")
    p.add_argument("--workflow", action="append",
                   help=f"modos do workflow_plan a editar (repetível; padrão {', '.join(DEFAULT_WORKFLOWS)})")
    p.add_argument("--base", default=BASE, help=f"branch base (padrão {BASE})")
    p.add_argument("--clones", type=Path, default=CLONES, help=f"pasta dos clones (padrão {CLONES})")
    p.add_argument("--regsmart-sha", help=f"fixa este commit do {PKG_REPO} em vez do mais recente da main")
    p.add_argument("--message", default=MESSAGE, help="mensagem do commit na base")
    p.add_argument("--push", action="store_true", help="aplica: commita, publica e faz os merges (senão só mostra)")
    args = p.parse_args()

    if not BRANCHES_PATH.exists():
        sys.exit(f"{BRANCHES_PATH} não existe")
    registry = json.loads(BRANCHES_PATH.read_text(encoding="utf-8"))
    repo_plan = load_repo_plan(args.repo)
    repos = [r for r in repo_plan if r in registry]
    for r in set(repo_plan) - set(registry):
        print(f"  ! {r}: fora do registro, ignorado")
    modes = args.workflow or DEFAULT_WORKFLOWS
    workflows = workflows_for(load_workflow_cfg(), repo_plan, modes)

    sha = args.regsmart_sha or Api(TOKEN).get(f"/repos/{OWNER}/{PKG_REPO}/commits/main")["sha"]
    pkg = f"git+https://github.com/{OWNER}/{PKG_REPO}@{sha}"
    print(f"{PKG_REPO}: {'commit fixado' if args.regsmart_sha else 'main'} @ {sha[:8]}"
          + ("" if args.push else "  [dry-run]"))

    failed = 0
    for repo in repos:
        cwd = args.clones / repo
        if not (cwd / ".git").is_dir():
            print(f"!! {repo}: clone não encontrado em {cwd} -- pulando", file=sys.stderr)
            failed += 1
            continue
        try:
            f, changed = process_repo(repo, cwd, registry[repo],
                                      {w: s["file"] for w, s in workflows[repo].items()}, pkg, args)
        except Exception as exc:
            print(f"!! {repo}: {exc}", file=sys.stderr)
            failed += 1
            continue
        failed += f
        if changed:
            save_registry(registry)
    if not args.push:
        print("\nNada foi alterado: use --push pra aplicar.")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
