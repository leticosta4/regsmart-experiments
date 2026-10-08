"""
mutation_testing/insert_mutations.py

FASE 1 (padrão): cria a branch `insert-mutations` em cada fork da lista,
**baseada no default branch do próprio fork** (main/master/etc. -- resolvido por
`origin/HEAD`, nunca escrito "main" no código, porque `apscheduler`,
`pytest-xdist` e `pytorch-lightning` usam `master`). Grava o SHA-base em
`data/mutmut/mutation_testing/insert_mutations_bases.csv` (mescla com o que já existe).

FASE 2 (`--mutants`): lê os patches gerados por `mutation_gen.py`
(`data/mutmut/mutants.json`) e cria **uma branch por mutante**,
`mut-<repo>-mNNNN`, com **um commit** que aplica só aquele patch sobre a
`origin/mutation_testing/insert_mutations`. Cada commit vira um `head_sha` (para o faults.yaml),
gravado em `data/mutmut/mutant_branches.json`.

A fase 2 não mexe no seu working tree nem cria branches locais: monta o commit
com comandos de baixo nível do git (índice temporário + commit-tree) e publica
direto por SHA. O commit é determinístico (mesma base + mesmo patch = mesmo SHA),
então rodar de novo é idempotente.

Não abre PR. Nada é publicado sem `--push`.

USO:
    python mutation_testing/insert_mutations.py --dry-run                     # fase 1: mostra o plano
    python mutation_testing/insert_mutations.py --push                        # fase 1: cria e publica a base
    python mutation_testing/insert_mutations.py --repo trimesh --reset --push # reaponta a base (ex.: após atualizar workflows)

    python mutation_testing/insert_mutations.py --mutants --dry-run           # fase 2: mostra o plano
    python mutation_testing/insert_mutations.py --mutants --repo pytest-xdist --limit 3 --push   # teste pequeno
    python mutation_testing/insert_mutations.py --mutants --push --pr         # todos (e abre draft)
    python mutation_testing/insert_mutations.py --mutants --reset --push     # refaz (ex.: base mudou)

ATENÇÃO: os workflows na `insert-mutations` precisam excluir `mut-*` do gatilho
`push` (`branches: ['**', '!mut-*']`), senão cada branch de mutante publicada
dispara um run sozinha.
"""

import argparse
import csv
import json
import os
import subprocess
import sys
import tempfile
import re
import time
from datetime import date
from pathlib import Path

# Os 12 projetos do dataset.
repos = ["librosa", "apscheduler", "pytest-django", "trimesh",
         "networkx", "pytest-xdist", "pytorch-lightning", "aeon",
         "dvc", "dask", "ultralytics", "ipython"]

BRANCH = "insert-mutations"
MUTANT_PREFIX = "mut-"
CLONES = Path("/home/Letícia/Projetos/tcc-experiments/effective-validation")

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "mutmut"
RECORD_PATH = DATA / "mutation_testing/insert_mutations_bases.csv"
MUTANTS_PATH = DATA / "mutants.json"            # gerado por mutation_gen.py
BRANCHES_PATH = DATA / "mutant_branches.json"   # head_sha de cada mutante
CSV_FIELDS = ["repo", "base_branch", "base_sha", "branch", "branch_sha", "data"]
PUSH_BATCH = 40


def run(cmd: list[str], cwd: Path, check: bool = True, env: dict | None = None) -> str:
    proc = subprocess.run(cmd, cwd=cwd, check=check, text=True, capture_output=True,
                          env={**os.environ, **env} if env else None)
    return proc.stdout.strip()


def err(exc: Exception) -> str:
    if isinstance(exc, subprocess.CalledProcessError):
        return (exc.stderr or exc.stdout or str(exc)).strip().splitlines()[-1][:200]
    return str(exc)

def fork_slug(repo_dir: Path) -> str:
    """owner/repo do `origin`. Não usa `gh repo view`: num fork ele pode resolver
    para o repo upstream e abrir o PR no lugar errado."""
    url = run(["git", "remote", "get-url", "origin"], repo_dir)
    m = re.search(r"github\.com[:/]([^/]+)/(.+?)(?:\.git)?$", url)
    if not m:
        raise RuntimeError(f"não consegui extrair owner/repo de {url}")
    return f"{m.group(1)}/{m.group(2)}"


def ensure_draft_pr(repo_dir: Path, slug: str, head: str, base: str,
                    title: str, body: str) -> tuple[str, bool]:
    """Devolve (url, criado). Se já existe PR (aberto, fechado ou mergeado) dessa
    head, reaproveita: rodar de novo é idempotente."""
    found = json.loads(run(["gh", "pr", "list", "--repo", slug, "--head", head,
                            "--base", base, "--state", "all",
                            "--json", "url", "--limit", "1"], repo_dir))
    if found:
        return found[0]["url"], False
    out = run(["gh", "pr", "create", "--repo", slug, "--draft", "--head", head,
               "--base", base, "--title", title, "--body", body], repo_dir)
    return out.splitlines()[-1], True


def save_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)


# ------------------------------------------------------------------ fase 1


def origin_default_ref(repo_dir: Path) -> str:
    """Ref do default branch do fork, via origin/HEAD (ou main/master como fallback)."""
    try:
        head = run(["git", "symbolic-ref", "--short", "refs/remotes/origin/HEAD"], repo_dir)
    except subprocess.CalledProcessError:
        head = ""
    if head:
        return head
    for candidate in ("origin/main", "origin/master"):
        exists = subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", candidate],
            cwd=repo_dir, text=True, capture_output=True,
        )
        if exists.returncode == 0:
            return candidate
    raise RuntimeError("não achei o default branch do fork (origin/HEAD, main ou master)")


def is_dirty(repo_dir: Path) -> bool:
    return bool(run(["git", "status", "--porcelain"], repo_dir))


def local_branch_exists(repo_dir: Path, branch: str) -> bool:
    found = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", f"refs/heads/{branch}"],
        cwd=repo_dir, text=True, capture_output=True,
    )
    return found.returncode == 0


def remote_branch_exists(repo_dir: Path, branch: str) -> bool:
    found = subprocess.run(
        ["git", "ls-remote", "--exit-code", "--heads", "origin", branch],
        cwd=repo_dir, text=True, capture_output=True,
    )
    return found.returncode == 0


def prepare(name: str, reset: bool, dry_run: bool, push: bool) -> dict | None:
    repo_dir = CLONES / name
    if not (repo_dir / ".git").is_dir():
        print(f"!! {name}: clone não encontrado em {repo_dir} -- pulando", file=sys.stderr)
        return None

    if is_dirty(repo_dir):
        print(f"!! {name}: working tree com alterações locais -- pulando "
              f"(commit/stash antes, o script não mexe em trabalho não salvo)",
              file=sys.stderr)
        return None

    # Traz o default do fork pra cima do dia; dry-run não fala com a rede.
    if not dry_run:
        run(["git", "fetch", "--prune", "origin"], repo_dir)

    base_ref = origin_default_ref(repo_dir)
    base_sha = run(["git", "rev-parse", base_ref], repo_dir)
    previous = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], repo_dir)

    exists = local_branch_exists(repo_dir, BRANCH)
    if exists and not reset:
        current = run(["git", "rev-parse", "refs/heads/" + BRANCH], repo_dir)
        if current == base_sha:
            print(f"== {name}: branch {BRANCH} já está em {base_sha[:7]} "
                  f"(base {base_ref}) -- nada a fazer")
            return {"repo": name, "base": base_ref, "base_sha": base_sha,
                    "branch": BRANCH, "branch_sha": base_sha, "changed": False}
        print(f"!! {name}: branch {BRANCH} existe em {current[:7]} e a base "
              f"{base_ref} está em {base_sha[:7]} -- pulando "
              f"(use --reset para reapontar)", file=sys.stderr)
        return None

    if dry_run:
        action = "reapontar" if exists else "criar"
        print(f"== {name}: [dry-run] {action} {BRANCH} a partir de "
              f"{base_ref} ({base_sha[:7]}) -- saindo de {previous}")
        return {"repo": name, "base": base_ref, "base_sha": base_sha,
                "branch": BRANCH, "branch_sha": base_sha, "changed": True}

    # --no-track: a branch não deve rastrear o default (evita um `git push` solto
    # confundir a branch de mutação com a base).
    run(["git", "checkout", "-B", BRANCH, "--no-track", base_ref], repo_dir)

    # Segurança: se a branch já existia no remoto e o push não foi pedido, diz isso
    # em vez de deixar dois estados divergentes sem ninguém notar.
    unpublished = exists and remote_branch_exists(repo_dir, BRANCH)
    if push:
        run(["git", "push", "--force-with-lease", "origin", f"{BRANCH}:{BRANCH}"], repo_dir)
        state = "publicada"
    else:
        state = "local (branch remota intacta)"
        if unpublished:
            state += " -- ATENÇÃO: já existe no remoto, divergindo"
    branch_sha = run(["git", "rev-parse", "HEAD"], repo_dir)
    print(f"== {name}: {BRANCH} @ {branch_sha[:7]} (base {base_ref} "
          f"{base_sha[:7]}) -> {state}")
    return {"repo": name, "base": base_ref, "base_sha": base_sha,
            "branch": BRANCH, "branch_sha": branch_sha, "changed": True}


def write_bases_csv(rows: list[dict]) -> None:
    """Mescla com o CSV existente: rodar com --repo não apaga os outros repos."""
    RECORD_PATH.parent.mkdir(parents=True, exist_ok=True)
    merged = {}
    if RECORD_PATH.exists():
        with RECORD_PATH.open(newline="", encoding="utf-8") as f:
            merged = {r["repo"]: r for r in csv.DictReader(f)}
    for row in rows:
        merged[row["repo"]] = {
            "repo": row["repo"], "base_branch": row["base"], "base_sha": row["base_sha"],
            "branch": row["branch"], "branch_sha": row["branch_sha"],
            "data": date.today().isoformat(),
        }
    with RECORD_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(merged[k] for k in sorted(merged))


# ------------------------------------------------------------------ fase 2


def mutant_branch(key: str) -> str:
    return f"{MUTANT_PREFIX}{key}"


def remote_mutant_refs(repo_dir: Path, name: str) -> dict[str, str]:
    """{branch: sha} das branches de mutante deste repo que já existem no fork."""
    out = run(["git", "ls-remote", "--heads", "origin", f"{MUTANT_PREFIX}{name}-m*"], repo_dir)
    refs = {}
    for line in out.splitlines():
        sha, ref = line.split("\t")
        refs[ref.removeprefix("refs/heads/")] = sha
    return refs


def build_mutant_commit(repo_dir: Path, base_sha: str, patch: Path, message: str, when: str) -> str:
    """Commit = base + patch, sem tocar no working tree nem criar branch.

    Índice temporário -> `git apply --cached` -> write-tree -> commit-tree. Autor,
    committer e datas fixos: mesma base + mesmo patch = mesmo SHA.
    """
    with tempfile.TemporaryDirectory() as tmp:
        env = {
            "GIT_INDEX_FILE": str(Path(tmp) / "index"),
            "GIT_AUTHOR_NAME": "regsmart-metrics", "GIT_AUTHOR_EMAIL": "noreply@localhost",
            "GIT_COMMITTER_NAME": "regsmart-metrics", "GIT_COMMITTER_EMAIL": "noreply@localhost",
            "GIT_AUTHOR_DATE": when, "GIT_COMMITTER_DATE": when,
        }
        run(["git", "read-tree", base_sha], repo_dir, env=env)
        run(["git", "apply", "--cached", str(patch)], repo_dir, env=env)
        tree = run(["git", "write-tree"], repo_dir, env=env)
        return run(["git", "commit-tree", tree, "-p", base_sha, "-m", message], repo_dir, env=env)


def prepare_mutants(name: str, all_meta: dict, reset: bool, dry_run: bool,
                    push: bool, limit: int | None, pr: bool = False) -> dict | None:
    repo_dir = CLONES / name
    if not (repo_dir / ".git").is_dir():
        print(f"!! {name}: clone não encontrado em {repo_dir} -- pulando", file=sys.stderr)
        return None
    meta = all_meta.get(name)
    if not meta or not meta.get("mutants"):
        print(f"!! {name}: sem mutantes em {MUTANTS_PATH.name} (rode mutation_gen.py) -- pulando",
              file=sys.stderr)
        return None
    items = meta["mutants"][:limit] if limit else meta["mutants"]

    if dry_run:
        print(f"== {name}: [dry-run] {len(items)} mutante(s) -> branches "
              f"{mutant_branch(items[0]['key'])} .. {mutant_branch(items[-1]['key'])}")
        return None

    run(["git", "fetch", "--prune", "origin"], repo_dir)
    try:
        base_sha = run(["git", "rev-parse", "--verify", f"origin/{BRANCH}"], repo_dir)
    except subprocess.CalledProcessError:
        print(f"!! {name}: origin/{BRANCH} não existe -- rode a fase 1 com --push antes",
              file=sys.stderr)
        return None
    when = run(["git", "log", "-1", "--format=%cI", base_sha], repo_dir)
    remote = remote_mutant_refs(repo_dir, name)

    entries, todo = {}, {}
    ok = conflicts = 0
    failed: list[str] = []
    for m in items:
        branch = mutant_branch(m["key"])
        message = (f"mutante {m['key']}\n\n{m['file']}:{m.get('line')} "
                   f"(mutmut id {m['mutmut_id']})\nbase: {base_sha}")
        try:
            sha = build_mutant_commit(repo_dir, base_sha, ROOT / m["patch"], message, when)
        except Exception as exc:
            failed.append(m["key"])
            print(f"   ! {m['key']}: patch não aplica na base ({err(exc)}) -- regenere com mutation_gen.py",
                  file=sys.stderr)
            continue
        current = remote.get(branch)
        entries[m["key"]] = {"branch": branch, "head_sha": sha, "file": m["file"],
                             "line": m.get("line"), "patch": m["patch"],
                             "published": current == sha}
        if current == sha:
            ok += 1
        elif current and not reset:
            conflicts += 1
            entries[m["key"]]["published"] = False
            print(f"   ! {branch}: já existe no fork em {current[:7]} (esperado {sha[:7]}) "
                  f"-- use --reset pra sobrescrever", file=sys.stderr)
        else:
            todo[branch] = sha

    pushed = 0
    if push and todo:
        items_todo = list(todo.items())
        for i in range(0, len(items_todo), PUSH_BATCH):
            chunk = items_todo[i:i + PUSH_BATCH]
            cmd = ["git", "push"] + (["--force"] if reset else []) + ["origin"]
            cmd += [f"{sha}:refs/heads/{branch}" for branch, sha in chunk]
            run(cmd, repo_dir)
            pushed += len(chunk)
        for key, e in entries.items():
            if e["branch"] in todo:
                e["published"] = True

    prs_new = prs_failed = 0
    if pr:
        slug = fork_slug(repo_dir)
        pr_base = origin_default_ref(repo_dir).removeprefix("origin/")
        for key, e in entries.items():
            if not e["published"]:
                continue
            m = next(x for x in items if x["key"] == key)
            body = (f"Mutante `{key}` (mutmut id {m['mutmut_id']})\n\n"
                    f"- arquivo: `{m['file']}:{m.get('line')}`\n"
                    f"- commit sobre: `{BRANCH}@{base_sha}`\n"
                    f"- patch: `{m['patch']}`")
            try:
                url, created = ensure_draft_pr(repo_dir, slug, e["branch"], pr_base,
                                               f"mutante {key}", body)
                e["pr"] = url
                if created:
                    prs_new += 1
                    time.sleep(1)  # evita o rate limit secundário do GitHub
            except Exception as exc:
                prs_failed += 1
                print(f"   ! {key}: PR não criado ({err(exc)})", file=sys.stderr)

    state = f"{pushed} publicada(s)" if push else f"{len(todo)} a publicar (use --push)"
    print(f"== {name}: {len(entries)}/{len(items)} commits prontos sobre "
          f"{BRANCH}@{base_sha[:7]} -> {state}, {ok} já ok, {conflicts} conflito(s), {len(failed)} falha(s)"
          + (f", {prs_new} PR(s) criados, {prs_failed} falha(s)" if pr else ""))
    return {"repo": name, "base_sha": base_sha, "entries": entries,
            "partial": bool(limit), "failed": failed, "conflicts": conflicts}


def write_branches_registry(results: list[dict]) -> None:
    registry = json.loads(BRANCHES_PATH.read_text(encoding="utf-8")) if BRANCHES_PATH.exists() else {}
    for r in results:
        prev = registry.get(r["repo"], {})
        keep = prev.get("mutants", {}) if r["partial"] and prev.get("base_sha") == r["base_sha"] else {}
        registry[r["repo"]] = {
            "base_branch": BRANCH, "base_sha": r["base_sha"],
            "mutants": {**keep, **r["entries"]},
        }
    save_json(BRANCHES_PATH, registry)


# ------------------------------------------------------------------ main


def main() -> None:
    global BRANCH, CLONES

    parser = argparse.ArgumentParser(
        description="fase 1: cria a branch insert-mutations nos forks; "
                    "fase 2 (--mutants): cria uma branch por mutante sobre ela")
    parser.add_argument("--repo", action="append", help="restringe a um repo (repetível)")
    parser.add_argument("--branch", default=BRANCH, help=f"nome da branch base (default: {BRANCH})")
    parser.add_argument("--mutants", action="store_true",
                        help="fase 2: cria as branches de mutante a partir dos patches")
    parser.add_argument("--limit", type=int, help="fase 2: só os N primeiros mutantes de cada repo (teste)")
    parser.add_argument("--reset", action="store_true",
                        help="fase 1: reaponta a base; fase 2: sobrescreve branches de mutante existentes")
    parser.add_argument("--push", action="store_true",
                        help="publica no fork (não abre PR)")
    parser.add_argument("--clones", type=Path, default=CLONES,
                        help=f"pasta dos clones (default: {CLONES})")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--pr", action="store_true",
                        help="fase 2: abre um PR draft por mutante (head mut-*, base insert-mutations); exige --push e `gh` autenticado")
    args = parser.parse_args()
    if args.pr and not (args.mutants and args.push):
        sys.exit("--pr só vale com --mutants --push")

    BRANCH, CLONES = args.branch, args.clones

    selected = args.repo or repos
    unknown = [r for r in selected if r not in repos]
    if unknown:
        print(f"!! {unknown} não está(ão) na lista de {repos} -- use a lista do arquivo "
              f"ou passe --repo com um repo dela", file=sys.stderr)
        sys.exit(1)

    if args.mutants:
        if not MUTANTS_PATH.exists():
            sys.exit(f"{MUTANTS_PATH} não existe: rode `python mutation_gen.py gen` antes")
        all_meta = json.loads(MUTANTS_PATH.read_text(encoding="utf-8"))
        results = []
        for name in selected:
            try:
                res = prepare_mutants(name, all_meta, args.reset, args.dry_run, args.push, args.limit, args.pr)
            except Exception as exc:
                print(f"!! {name}: {err(exc)}", file=sys.stderr)
                continue
            if res:
                results.append(res)
        if results:
            write_branches_registry(results)
            print(f"\nHead SHAs em {BRANCHES_PATH}.")
            if args.push:
                print("Confira que o `on.push` dos workflows exclui `mut-*`, "
                      "senão cada branch publicada dispara um run.")
            sys.exit(1 if any(r["failed"] or r["conflicts"] or r.get("pr_failed") for r in results) else 0)

    rows = []
    for name in selected:
        row = prepare(name, args.reset, args.dry_run, args.push)
        if row:
            rows.append(row)

    if not rows:
        print("\nNada registrado.", file=sys.stderr)
        return

    if not args.dry_run:
        write_bases_csv(rows)

    touched = sum(1 for row in rows if row["changed"])
    print(f"\n{len(rows)} repo(s) no padrão, {touched} alterado(s) nesta execução."
          + ("" if args.dry_run else f" Bases em {RECORD_PATH}.")
          + "  Próximo passo: python mutation_testing/insert_mutations.py --mutants --push")


if __name__ == "__main__":
    main()
