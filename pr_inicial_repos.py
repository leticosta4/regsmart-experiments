"""
Uso:
    python track_flaky.py /caminho/para/pasta-com-os-clones
 
Requisitos:
    - gh CLI autenticado (gh auth login) com acesso de push aos seus forks
    - git configurado (user.name / user.email)
    - cada repo já clonado localmente com esse mesmo nome, remote "origin"
      apontando pro seu fork
 
Para cada repo:
    1. checkout na branch default e git pull
    2. cria (ou reseta) a branch track-flaky a partir dela
    3. escolhe um .py "de código" (evita tests/, docs/, examples/, setup.py, conftest.py)
    4. adiciona um comentário no fim do arquivo
    5. commita e dá push --force-with-lease
    6. abre PR (não-draft) via gh, ou avisa que já existe

OBS.: esse script teve melhor uso para buscar testes flaky depois da limpeza de workflow dos projetos,
já que a conta free do github só permite 20 jobs simultaneos no GActions

"""
 
import random
import subprocess
import sys
from datetime import date
from pathlib import Path
 
REPOS = [
    "aeon", "librosa", "trimesh", "apscheduler",
    "ultralytics", "ipython", "dask", "dvc",
    "networkx", "pytest-xdist", "pytest-django", "pytorch-lightning",
]
 
EXCLUDE_PATTERNS = (
    "test", "tests", "doc", "docs", "example", "examples",
    "benchmark", "benchmarks", "conftest.py", "setup.py",
)
 
 
def run(cmd: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess:
    print(f"   $ {' '.join(cmd)}")
    return subprocess.run(
        cmd, cwd=cwd, check=check, text=True, capture_output=True,
    )
 
 
def get_default_branch(repo_dir: Path) -> str:
    out = run(["git", "remote", "show", "origin"], repo_dir).stdout
    for line in out.splitlines():
        line = line.strip()
        if line.startswith("HEAD branch:"):
            return line.split(":", 1)[1].strip()
    raise RuntimeError("não consegui identificar a branch default")
 
 
def pick_target_file(repo_dir: Path) -> Path | None:
    out = run(["git", "ls-files", "*.py"], repo_dir).stdout
    candidates = []
    for rel in out.splitlines():
        rel_lower = rel.lower()
        parts = rel_lower.split("/")
        if any(p in EXCLUDE_PATTERNS for p in parts) or rel_lower.endswith(
            tuple(f"/{p}" for p in EXCLUDE_PATTERNS if p.endswith(".py"))
        ):
            continue
        if Path(rel).name in ("setup.py", "conftest.py"):
            continue
        candidates.append(rel)
    if not candidates:
        return None
    return Path(random.choice(candidates))
 
 
def process_repo(base_dir: Path, name: str) -> None:
    repo_dir = base_dir / name
    if not (repo_dir / ".git").is_dir():
        print(f"== {name}: pasta não encontrada em {repo_dir}, pulando ==")
        return
 
    print(f"== {name} ==")
 
    default_branch = get_default_branch(repo_dir)
    run(["git", "checkout", "-q", default_branch], repo_dir)
    run(["git", "pull", "-q", "origin", default_branch], repo_dir)
 
    # apaga track-flaky local se existir (ignora erro se não existir)
    run(["git", "branch", "-D", "track-flaky"], repo_dir, check=False)
    run(["git", "checkout", "-q", "-b", "track-flaky"], repo_dir)
 
    target = pick_target_file(repo_dir)
    if target is None:
        print(f"   !! não achei .py candidato em {name}, pulando")
        return
 
    print(f"   arquivo escolhido: {target}")
    full_path = repo_dir / target
    with full_path.open("a", encoding="utf-8") as f:
        f.write(f"\n# track-flaky: commit trivial para disparar CI ({date.today().isoformat()})\n")
 
    run(["git", "add", str(target)], repo_dir)
    run(["git", "commit", "-q", "-m", "track-flaky: trigger CI"], repo_dir)
    run(["git", "push", "-q", "--force-with-lease", "origin", "track-flaky"], repo_dir)
 
    pr_exists = run(
        ["gh", "pr", "view", "track-flaky", "--repo", f"leticosta4/{name}"],
        repo_dir, check=False,
    ).returncode == 0
 
    if pr_exists:
        print("   PR já existe, reaproveitado (push atualizou)")
    else:
        run(
            [
                "gh", "pr", "create",
                "--repo", f"leticosta4/{name}",
                "--head", f"leticosta4:track-flaky",
                "--base", default_branch,
                "--title", "track-flaky: trigger CI",
                "--body", "Commit trivial em arquivo .py para observar execuções do workflow e mapear flaky tests.",
                "--draft=false",
            ],
            repo_dir,
        )
 
 
def main() -> None:
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
 
    base_dir = Path(sys.argv[1]).expanduser().resolve()
    for name in REPOS:
        try:
            process_repo(base_dir, name)
        except subprocess.CalledProcessError as e:
            print(f"   !! erro em {name}: {e.stderr.strip() or e}")
        except RuntimeError as e:
            print(f"   !! erro em {name}: {e}")
 
    print("Pronto. Confira as Actions de cada repo.")
 
 
if __name__ == "__main__":
    main()
