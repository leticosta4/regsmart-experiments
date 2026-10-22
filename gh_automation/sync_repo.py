#!/usr/bin/env python3
"""
Sincroniza o REGSMART_PACKAGE dos workflows *-regsmart.yml/yaml e *-regsmart-nr.yml/yaml
com o commit mais recente do pytest-regsmart, nos 12 repos.

Para cada repo:
  1. clona/atualiza em ./_regsmart_sync/<repo> e vai para a branch base (main)
  2. confere o REGSMART_PACKAGE de cada workflow; se estiver desatualizado, corrige,
     faz commit e push na base
  3. (somente se houve atualização, ou com --always-sync) faz, em cada branch mut-*:
     git merge origin/<base> + git push origin mut-*

Uso:
    python3 -m gh_automation.sync_repo --dry-run          # só mostra o que seria feito
    python3 -m gh_automation.sync_repo                    # executa
    python3 -m gh_automation.sync_repo --only ipython,dask
    python3 -m gh_automation.sync_repo --sha <sha>        # força um SHA em vez do HEAD do plugin
    python3 -m gh_automation.sync_repo --always-sync      # faz o merge nas mut-* mesmo sem bump

Usa o git da máquina (as credenciais/SSH que você já tem configuradas).
"""
import argparse
import fnmatch
import re
import subprocess
import sys
from pathlib import Path

# ====== CONFIGURE AQUI ======
OWNER = "leticosta4"
REPOS = [
    "aeon",
    "apscheduler",
    "dask",
    "dvc",
    "ipython",
    "librosa",
    "networkx",
    "pytest-django",
    "pytest-xdist",
    "pytorch-lightning",
    "trimesh",
    "ultralytics",
]
PLUGIN_REPO = "leticosta4/pytest-regsmart"
# Usado só quando o valor atual NÃO tem o formato "...@<sha>"
PACKAGE_TEMPLATE = "git+https://github.com/" + PLUGIN_REPO + ".git@{sha}"
CLONE_URL = "https://github.com/{owner}/{repo}.git"  # ou "git@github.com:{owner}/{repo}.git"
BASE_BRANCH = "main"
MUT_PREFIX = "mut-"
WORKDIR = Path("./_regsmart_sync")
WORKFLOW_PATTERNS = [
    "*regsmart.yml",
    "*regsmart.yaml",
    "*regsmart-nr.yml",
    "*regsmart-nr.yaml",
]
# ============================

PKG_RE = re.compile(
    r'^(?P<pre>[ \t]*REGSMART_PACKAGE[ \t]*:[ \t]*)(?P<q>["\']?)(?P<val>[^"\'\s#]+)(?P=q)',
    re.M,
)
SHA_RE = re.compile(r"^(?P<prefix>.*@)(?P<sha>[0-9a-fA-F]{7,40})$")


def run(args, cwd=None, check=True):
    p = subprocess.run(args, cwd=cwd, text=True, capture_output=True)
    if check and p.returncode != 0:
        raise RuntimeError(f"{' '.join(map(str, args))}\n{p.stdout}{p.stderr}".strip())
    return p


def git(d, *args, check=True):
    return run(["git", *args], cwd=d, check=check)


def latest_plugin_sha():
    url = f"https://github.com/{PLUGIN_REPO}.git"
    out = run(["git", "ls-remote", url, "HEAD"]).stdout.split()
    if not out:
        raise RuntimeError(f"Não consegui obter o HEAD de {url}")
    return out[0].lower()


def compute_new(val, sha):
    """Retorna o novo valor de REGSMART_PACKAGE (igual a val se já estiver atualizado)."""
    m = SHA_RE.match(val)
    if m:
        if sha.startswith(m.group("sha").lower()):
            return val
        return m.group("prefix") + sha
    return PACKAGE_TEMPLATE.format(sha=sha)


def process_file(path, sha):
    """Devolve (n_ocorrencias, [(antigo, novo)], texto_novo)."""
    with open(path, encoding="utf-8", newline="") as f:
        text = f.read()
    found = 0
    changes = []

    def repl(m):
        nonlocal found
        found += 1
        old = m.group("val")
        new = compute_new(old, sha)
        if new != old:
            changes.append((old, new))
        q = m.group("q")
        return f'{m.group("pre")}{q}{new}{q}'

    new_text = PKG_RE.sub(repl, text)  # precisa rodar antes de ler `found`
    return found, changes, new_text


def prepare_repo(repo, base_pref):
    """Clona/atualiza o repo e deixa a branch base limpa e igual ao remoto."""
    d = WORKDIR / repo
    if not d.exists():
        WORKDIR.mkdir(parents=True, exist_ok=True)
        run(["git", "clone", "--no-tags", CLONE_URL.format(owner=OWNER, repo=repo), str(d)])
    else:
        git(d, "merge", "--abort", check=False)
        git(d, "reset", "--hard")
        git(d, "clean", "-fd")
        git(d, "fetch", "origin", "--prune", "--no-tags")

    base = base_pref
    if git(d, "rev-parse", "--verify", f"origin/{base}", check=False).returncode != 0:
        head = git(d, "symbolic-ref", "--short", "refs/remotes/origin/HEAD", check=False)
        if head.returncode != 0:
            raise RuntimeError(f"Branch '{base_pref}' não existe e não achei a default do repo")
        base = head.stdout.strip().split("/", 1)[1]
        print(f"      (aviso: '{base_pref}' não existe, usando '{base}')")

    git(d, "checkout", "-B", base, f"origin/{base}")
    return d, base


def mut_branches(d):
    out = git(d, "for-each-ref", "--format=%(refname:short)", f"refs/remotes/origin/{MUT_PREFIX}*").stdout
    return sorted(line.strip().split("/", 1)[1] for line in out.splitlines() if line.strip())


def sync_mut_branches(d, base, dry_run, pending_bump=False):
    results = []
    for br in mut_branches(d):
        # No dry-run o commit de bump não existe de verdade, então nenhuma mut-*
        # vai conter ele: todas precisariam do merge.
        if pending_bump:
            up_to_date = False
        else:
            up_to_date = git(d, "merge-base", "--is-ancestor", f"origin/{base}", f"origin/{br}", check=False).returncode == 0
        if up_to_date:
            print(f"      [--] {br}: já contém {base}")
            results.append((br, "ok"))
            continue
        if dry_run:
            print(f"      [DRY] {br}: faria merge de {base} + push")
            results.append((br, "ok"))
            continue
        git(d, "checkout", "-B", br, f"origin/{br}")
        merge = git(d, "merge", f"origin/{base}", "--no-edit", check=False)
        if merge.returncode != 0:
            git(d, "merge", "--abort", check=False)
            print(f"      [CONFLITO] {br}: merge abortado, resolva manualmente")
            results.append((br, "conflito"))
            continue
        push = git(d, "push", "origin", br, check=False)
        if push.returncode != 0:
            print(f"      [ERRO] {br}: push falhou\n{push.stderr.strip()}")
            results.append((br, "erro"))
            continue
        print(f"      [OK]  {br}: merge + push")
        results.append((br, "ok"))
    git(d, "checkout", base)
    return results


def process_repo(repo, sha, args):
    d, base = prepare_repo(repo, args.base)
    wf_dir = d / ".github" / "workflows"
    files = []
    if wf_dir.is_dir():
        files = sorted(p for p in wf_dir.iterdir()
                       if p.is_file() and any(fnmatch.fnmatch(p.name, pat) for pat in WORKFLOW_PATTERNS))
    if not files:
        print("      [AVISO] nenhum workflow *-regsmart / *-regsmart-nr encontrado")

    updated_files = []
    for p in files:
        found, changes, new_text = process_file(p, sha)
        if found == 0:
            print(f"      [AVISO] {p.name}: REGSMART_PACKAGE não encontrado")
        elif not changes:
            print(f"      [OK]  {p.name}: atualizado")
        else:
            for old, new in changes:
                print(f"      [ATUALIZAR] {p.name}: {old} -> {new}")
            if not args.dry_run:
                with open(p, "w", encoding="utf-8", newline="") as f:
                    f.write(new_text)
            updated_files.append(p)

    bumped = bool(updated_files)
    if bumped and not args.dry_run:
        git(d, "add", "--", *[str(p.relative_to(d)) for p in updated_files])
        git(d, "commit", "-m", f"chore: atualiza REGSMART_PACKAGE para pytest-regsmart@{sha[:7]}")
        git(d, "push", "origin", base)
        print(f"      [PUSH] {base}")

    if bumped or args.always_sync:
        muts = sync_mut_branches(d, base, args.dry_run, pending_bump=bumped and args.dry_run)
    else:
        muts = []

    bad = [b for b, s in muts if s != "ok"]
    status = "atualizado" if bumped else "já estava ok"
    if args.dry_run and bumped:
        status = "precisa atualizar"
    if bad:
        status += f" | problemas em: {', '.join(bad)}"
    return status, not bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--sha", help="usa este SHA em vez do HEAD do pytest-regsmart")
    ap.add_argument("--only", help="lista de repos separados por vírgula")
    ap.add_argument("--base", default=BASE_BRANCH)
    ap.add_argument("--always-sync", action="store_true",
                    help="faz merge da base nas mut-* mesmo quando não houve bump")
    args = ap.parse_args()

    sha = (args.sha or latest_plugin_sha()).lower()
    print(f"pytest-regsmart alvo: {sha}\n")

    repos = [r.strip() for r in args.only.split(",")] if args.only else REPOS
    summary, failures = [], 0

    for repo in repos:
        print(f"==> {repo}")
        try:
            status, ok = process_repo(repo, sha, args)
        except Exception as e:  # noqa: BLE001
            print(f"      [ERRO] {e}")
            status, ok = "erro", False
        summary.append((repo, status))
        failures += 0 if ok else 1

    print("\n===== Resumo =====")
    for repo, status in summary:
        print(f"{repo:20} {status}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
