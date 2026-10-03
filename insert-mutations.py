"""
insert-mutations.py

Cria a branch `insert-mutations` em cada fork da lista, **baseada no default branch
do próprio fork** (main/master/etc. -- resolvido por `origin/HEAD`, nunca escrito
"main" no código, porque `apscheduler`, `pytest-xdist` e `pytorch-lightning` usam
`master`).

A branch é o ponto de partida do experimento de mutação: os mutantes do mutmut serão
injetados **em cima** dela, e cada commit de mutação vira um `head_sha` do
`faults.yaml`. Por isso o script grava o SHA-base em `data/insert_mutations_bases.csv`.

Não abre PR. Push só com `--push`. A mutação em si (mutmut) e a entrega por PR
ficam para os próximos passos.

USO:
    python insert-mutations.py --dry-run     # mostra o plano, não muda nada
    python insert-mutations.py               # cria/aponta a branch local
    python insert-mutations.py --push        # além disso, publica no fork
    python insert-mutations.py --repo trimesh --reset   # restringe e reaponta
"""

import argparse
import csv
import subprocess
import sys
from datetime import date
from pathlib import Path

# Os 4 projetos do primeiro lote (4 branches de mutation em vez de 12 de uma vez).
repos = ["librosa", "apscheduler", "pytest-django", "trimesh",
         "networkx", "pytest-xdist", "pytorch-lightning", "aeon",
         "dvc", "dask", "ultralytics", "ipython"]

BRANCH = "insert-mutations"
CLONES = Path("/home/Letícia/Projetos/tcc-experiments/effective-validation")
RECORD_PATH = Path(__file__).resolve().parent / "data" / "mutmut" / "insert_mutations_bases.csv"


def run(cmd: list[str], cwd: Path, check: bool = True) -> str:
    proc = subprocess.run(cmd, cwd=cwd, check=check, text=True, capture_output=True)
    return proc.stdout.strip()


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

    run(["git", "checkout", "-B", BRANCH, base_ref], repo_dir)

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


def main() -> None:
    global BRANCH, CLONES

    parser = argparse.ArgumentParser(
        description="cria a branch insert-mutations nos forks listados, "
                    "baseada no default branch de cada um")
    parser.add_argument("--repo", action="append", help="restringe a um repo (repetível)")
    parser.add_argument("--branch", default=BRANCH, help=f"nome da branch (default: {BRANCH})")
    parser.add_argument("--reset", action="store_true",
                        help="reaponta a branch mesmo se já existir em outro SHA")
    parser.add_argument("--push", action="store_true",
                        help="publica a branch no fork (não abre PR)")
    parser.add_argument("--clones", type=Path, default=CLONES,
                        help=f"pasta dos clones (default: {CLONES})")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    BRANCH, CLONES = args.branch, args.clones

    selected = args.repo or repos
    unknown = [r for r in selected if r not in repos]
    if unknown:
        print(f"!! {unknown} não está(ão) na lista de {repos} -- use a lista do arquivo "
              f"ou passe --repo com um repo dela", file=sys.stderr)
        sys.exit(1)

    rows = []
    for name in selected:
        row = prepare(name, args.reset, args.dry_run, args.push)
        if row:
            rows.append(row)

    if not rows:
        print("\nNada registrado.", file=sys.stderr)
        return

    if not args.dry_run:
        RECORD_PATH.parent.mkdir(parents=True, exist_ok=True)
        with RECORD_PATH.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["repo", "base_branch", "base_sha", "branch", "branch_sha", "data"])
            for row in sorted(rows, key=lambda r: r["repo"]):
                writer.writerow([row["repo"], row["base"], row["base_sha"],
                                 row["branch"], row["branch_sha"], date.today().isoformat()])

    touched = sum(1 for row in rows if row["changed"])
    print(f"\n{len(rows)} repo(s) no padrão, {touched} alterado(s) nesta execução."
          + ("" if args.dry_run else f" Bases em {RECORD_PATH}.")
          + "  Próximo passo: injetar os mutantes em cima dessas branches.")


if __name__ == "__main__":
    main()