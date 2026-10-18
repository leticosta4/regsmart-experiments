"""
mutation_testing/insert_mutations.py

Cria **uma branch por mutante**, `mut-<repo>-mNNNN`, com **um commit** que aplica só
aquele patch (data/mutmut/mutants.json, gerado por `mutation_gen.py`) sobre o
**default branch do próprio fork** (main/master -- resolvido por `origin/HEAD`, nunca
escrito "main" no código, porque `apscheduler`, `pytest-xdist` e `pytorch-lightning`
usam `master`). Cada commit vira um `head_sha` (para o faults.yaml), gravado em
`data/mutmut/mutant_branches.json`.

A branch intermediária `insert-mutations` (antiga fase 1) não existe mais: subir algo
na main, atualizar a insert-mutations e depois as branches mut-* era redundante.
Agora, quando a main muda (workflows, REGSMART_PACKAGE...), basta fazer
`git merge main` nas mut-* (ver sync_regsmart.py) e rodar fetch_mut_branches.py
--write para realinhar o registro.

Não mexe no seu working tree nem cria branches locais: monta o commit com comandos
de baixo nível do git (índice temporário + commit-tree) e publica direto por SHA.
Para uma mesma base, o commit é determinístico (mesma base + mesmo patch = mesmo SHA).

Branches de mutante que JÁ existem no fork são mantidas como estão (podem ter
recebido merge da main ou ter sido trocadas na mão). Só `--reset` reconstrói a
branch a partir do patch original e sobrescreve (force) o que está no remoto.

Não abre PR sem `--pr`. Nada é publicado sem `--push`.

USO:
    python3 -m mutation_testing.insert_mutations --dry-run                       # mostra o plano
    python3 -m mutation_testing.insert_mutations --repo pytest-xdist --limit 3 --push   # teste pequeno
    python3 -m mutation_testing.insert_mutations --push --pr                     # todos (e abre draft)
    python3 -m mutation_testing.insert_mutations --reset --push                  # refaz (sobrescreve)

ATENÇÃO: os workflows na main precisam excluir `mut-*` do gatilho `push`
(`branches: ['**', '!mut-*']`), senão cada branch de mutante publicada dispara um
run sozinha.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# Os 12 projetos do dataset.
repos = ["librosa", "apscheduler", "pytest-django", "trimesh",
         "networkx", "pytest-xdist", "pytorch-lightning", "aeon",
         "dvc", "dask", "ultralytics", "ipython"]

MUTANT_PREFIX = "mut-"
CLONES = Path("/home/Letícia/Projetos/tcc-experiments/effective-validation")

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "mutmut"
MUTANTS_PATH = DATA / "mutants.json"            # gerado por mutation_gen.py
BRANCHES_PATH = DATA / "mutant_branches.json"   # head_sha de cada mutante
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
                    push: bool, limit: int | None, pr: bool = False,
                    base_override: str | None = None) -> dict | None:
    repo_dir = CLONES / name
    if not (repo_dir / ".git").is_dir():
        print(f"!! {name}: clone não encontrado em {repo_dir} -- pulando", file=sys.stderr)
        return None
    meta = all_meta.get(name)
    if not meta or not meta.get("mutants"):
        print(f"!! {name}: sem mutantes em {MUTANTS_PATH.name} (rode python -m mutation_testing.mutation_gen gen) -- pulando",
              file=sys.stderr)
        return None
    items = meta["mutants"][:limit] if limit else meta["mutants"]

    if dry_run:
        print(f"== {name}: [dry-run] {len(items)} mutante(s) -> branches "
              f"{mutant_branch(items[0]['key'])} .. {mutant_branch(items[-1]['key'])} "
              f"(sobre o default branch do fork)")
        return None

    run(["git", "fetch", "--prune", "origin"], repo_dir)
    run(["git", "remote", "set-head", "origin", "-a"], repo_dir, check=False)  # atualiza origin/HEAD
    base_ref = f"origin/{base_override}" if base_override else origin_default_ref(repo_dir)
    base_name = base_ref.removeprefix("origin/")
    try:
        base_sha = run(["git", "rev-parse", "--verify", base_ref], repo_dir)
    except subprocess.CalledProcessError:
        print(f"!! {name}: {base_ref} não existe", file=sys.stderr)
        return None
    when = run(["git", "log", "-1", "--format=%cI", base_sha], repo_dir)
    remote = remote_mutant_refs(repo_dir, name)

    entries, todo = {}, {}
    kept = 0
    failed: list[str] = []
    for m in items:
        branch = mutant_branch(m["key"])
        current = remote.get(branch)
        base_entry = {"branch": branch, "file": m["file"], "line": m.get("line"), "patch": m["patch"]}

        if current and not reset:
            # já existe no fork: mantém (pode ter recebido merge da base ou troca manual)
            entries[m["key"]] = {**base_entry, "head_sha": current, "published": True}
            kept += 1
            continue

        message = (f"mutante {m['key']}\n\n{m['file']}:{m.get('line')} "
                   f"(mutmut id {m['mutmut_id']})\nbase: {base_sha}")
        try:
            sha = build_mutant_commit(repo_dir, base_sha, ROOT / m["patch"], message, when)
        except Exception as exc:
            failed.append(m["key"])
            print(f"   ! {m['key']}: patch não aplica na base ({err(exc)}) -- regenere com python -m mutation_testing.mutation_gen gen",
                  file=sys.stderr)
            continue
        entries[m["key"]] = {**base_entry, "head_sha": sha, "published": False, "rebuilt": reset}
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
        for e in entries.values():
            if e["branch"] in todo:
                e["published"] = True

    prs_new = prs_failed = 0
    if pr:
        slug = fork_slug(repo_dir)
        for key, e in entries.items():
            if not e["published"]:
                continue
            m = next(x for x in items if x["key"] == key)
            body = (f"Mutante `{key}` (mutmut id {m['mutmut_id']})\n\n"
                    f"- arquivo: `{m['file']}:{m.get('line')}`\n"
                    f"- commit sobre: `{base_name}@{base_sha}`\n"
                    f"- patch: `{m['patch']}`")
            try:
                url, created = ensure_draft_pr(repo_dir, slug, e["branch"], base_name,
                                               f"mutante {key}", body)
                e["pr"] = url
                if created:
                    prs_new += 1
                    time.sleep(1)  # evita o rate limit secundário do GitHub
            except Exception as exc:
                prs_failed += 1
                print(f"   ! {key}: PR não criado ({err(exc)})", file=sys.stderr)

    state = f"{pushed} publicada(s)" if push else f"{len(todo)} a publicar (use --push)"
    print(f"== {name}: {len(entries)}/{len(items)} mutantes sobre {base_name}@{base_sha[:7]} "
          f"-> {state}, {kept} já existiam (mantidas), {len(failed)} falha(s)"
          + (f", {prs_new} PR(s) criados, {prs_failed} falha(s)" if pr else ""))
    return {"repo": name, "base_branch": base_name, "base_sha": base_sha, "entries": entries,
            "partial": bool(limit), "failed": failed, "pr_failed": prs_failed}


def write_branches_registry(results: list[dict]) -> None:
    """Atualiza o registro preservando o que já se sabe de cada mutante (altered, pr,
    original_head_sha...). Só uma reconstrução (--reset) começa a entrada do zero."""
    registry = json.loads(BRANCHES_PATH.read_text(encoding="utf-8")) if BRANCHES_PATH.exists() else {}
    for r in results:
        prev = registry.get(r["repo"], {})
        prev_m = prev.get("mutants", {})
        if r["partial"]:
            mutants = dict(prev_m)  # rodada parcial (--limit): não perde os outros
        else:  # mantém só o que o fetch_mut_branches trouxe do remoto
            mutants = {k: v for k, v in prev_m.items() if v.get("source") == "remote"}
        for key, e in r["entries"].items():
            e = dict(e)
            rebuilt = e.pop("rebuilt", False)
            mutants[key] = {**({} if rebuilt else prev_m.get(key, {})), **e}
        registry[r["repo"]] = {
            "base_branch": r["base_branch"], "base_sha": r["base_sha"],
            "mutants": mutants,
        }
    save_json(BRANCHES_PATH, registry)


def main() -> None:
    global CLONES

    parser = argparse.ArgumentParser(
        description="cria uma branch por mutante (mut-<repo>-mNNNN) sobre o default branch do fork")
    parser.add_argument("--repo", action="append", help="restringe a um repo (repetível)")
    parser.add_argument("--branch", default=None,
                        help="branch base (default: o default branch de cada fork, main/master)")
    parser.add_argument("--mutants", action="store_true",
                        help="(ignorado, mantido por compatibilidade: agora é o único modo)")
    parser.add_argument("--limit", type=int, help="só os N primeiros mutantes de cada repo (teste)")
    parser.add_argument("--reset", action="store_true",
                        help="reconstrói a branch do mutante a partir do patch e sobrescreve a existente "
                             "(apaga merges da base e trocas manuais!)")
    parser.add_argument("--push", action="store_true",
                        help="publica no fork (não abre PR)")
    parser.add_argument("--clones", type=Path, default=CLONES,
                        help=f"pasta dos clones (default: {CLONES})")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--pr", action="store_true",
                        help="abre um PR draft por mutante (head mut-*, base = default branch); "
                             "exige --push e `gh` autenticado")
    args = parser.parse_args()
    if args.pr and not args.push:
        sys.exit("--pr só vale com --push")

    CLONES = args.clones

    selected = args.repo or repos
    unknown = [r for r in selected if r not in repos]
    if unknown:
        print(f"!! {unknown} não está(ão) na lista de {repos} -- use a lista do arquivo "
              f"ou passe --repo com um repo dela", file=sys.stderr)
        sys.exit(1)

    if not MUTANTS_PATH.exists():
        sys.exit(f"{MUTANTS_PATH} não existe: rode `python -m mutation_testing.mutation_gen gen` antes")
    all_meta = json.loads(MUTANTS_PATH.read_text(encoding="utf-8"))

    results = []
    for name in selected:
        try:
            res = prepare_mutants(name, all_meta, args.reset, args.dry_run, args.push,
                                  args.limit, args.pr, args.branch)
        except Exception as exc:
            print(f"!! {name}: {err(exc)}", file=sys.stderr)
            continue
        if res:
            results.append(res)

    if not results:
        if not args.dry_run:
            print("\nNada registrado.", file=sys.stderr)
        return

    write_branches_registry(results)
    print(f"\nHead SHAs em {BRANCHES_PATH}.")
    if args.push:
        print("Confira que o `on.push` dos workflows exclui `mut-*`, "
              "senão cada branch publicada dispara um run.")
    sys.exit(1 if any(r["failed"] or r["pr_failed"] for r in results) else 0)


if __name__ == "__main__":
    main()
