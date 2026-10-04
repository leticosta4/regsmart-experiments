"""
Gera mutantes (mutmut) de cada fork e salva UM PATCH POR MUTANTE.

Não roda a suíte de testes: o mutmut é usado só como gerador. A execução dos
testes (e portanto a descoberta de quais testes cada mutante quebra) acontece
na CI, num passo posterior que cria uma branch por mutante aplicando o patch.

Por que patches e não branches agora: o gerador só precisa da árvore de código
(os workflows não entram), então dá pra rodar antes dos workflows ficarem
prontos. Depois, cada patch é aplicado sobre a base final (git apply) e vira
uma branch/commit.

Uso:
    pip install "mutmut==2.5.1"
    python mutation_gen.py gen                       # todos os repos do plano
    python mutation_gen.py gen --repo dask --n 15    # um repo
    python mutation_gen.py list                      # resumo do que foi gerado

Entradas:
    data/mutmut/mutation_plan.json (opcional): [{"repo": "dask", "src": "dask/", "n": 15}]
        - src: caminho(s) a mutar (string ou lista); sem ele o mutmut tenta descobrir
        - n:   nº de mutantes amostrados; sem ele usa --n
    Sem esse arquivo, usa os repos de data/flaky/flaky_plan.json.

Saídas:
    data/mutmut/patches/<repo>/<repo>-mNNNN.patch
    data/mutmut/mutants.json   (metadados: base_sha, seed, arquivo, linha, patch)
"""

import argparse
import contextlib
import io
import json
import random
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

OWNER = "leticosta4"
ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "mutmut"
PLAN_PATH = DATA / "mutation_plan.json"
FLAKY_PLAN_PATH = ROOT / "data" / "flaky" / "flaky_plan.json"
MUTANTS_PATH = DATA / "mutants.json"
MUTMUT_VERSION = "2.5.1"


def run(args: list[str], cwd: Path | None = None, check: bool = True) -> str:
    res = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    if check and res.returncode:
        raise RuntimeError(f"{' '.join(args)} (rc={res.returncode}):\n{res.stdout}\n{res.stderr}")
    return res.stdout


def save_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def load_plan(only: list[str] | None, default_n: int) -> list[dict]:
    if PLAN_PATH.exists():
        entries = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    elif FLAKY_PLAN_PATH.exists():
        entries = [
            {"repo": e["repo"]}
            for e in json.loads(FLAKY_PLAN_PATH.read_text(encoding="utf-8"))
            if e.get("enabled", True)
        ]
    else:
        sys.exit(f"nenhum plano: crie {PLAN_PATH} ou {FLAKY_PLAN_PATH}")
    if only:
        unknown = set(only) - {e["repo"] for e in entries}
        if unknown:
            sys.exit(f"--repo desconhecido: {', '.join(sorted(unknown))}")
        entries = [e for e in entries if e["repo"] in set(only)]
    for e in entries:
        e.setdefault("n", default_n)
    return entries


def ensure_clone(repo: str, branch: str, workdir: Path, url_template: str) -> Path:
    """Clone (ou atualiza) o fork em workdir/<repo>, limpo e na branch pedida."""
    dest = workdir / repo
    if not dest.exists():
        workdir.mkdir(parents=True, exist_ok=True)
        run(["git", "clone", "--quiet", "--branch", branch, url_template.format(repo=repo), str(dest)])
    else:
        run(["git", "fetch", "--quiet", "origin", branch], cwd=dest)
        run(["git", "checkout", "--quiet", branch], cwd=dest)
        run(["git", "reset", "--quiet", "--hard", f"origin/{branch}"], cwd=dest)
        run(["git", "clean", "-fdxq"], cwd=dest)
    return dest


def parse_results(text: str) -> dict[int, str]:
    """`mutmut results` -> {id: arquivo}. Formato: '---- arq.py (5) ----' seguido de '1-5, 7'."""
    ids: dict[int, str] = {}
    current = None
    for line in text.splitlines():
        s = line.strip()
        m = re.match(r"^-{4} (.+?) \(\d+\) -{4}$", s)
        if m:
            current = m.group(1)
            continue
        if current and s and re.fullmatch(r"[\d\s,\-]+", s):
            for part in s.split(","):
                part = part.strip()
                if "-" in part:
                    a, b = part.split("-")
                    ids.update({i: current for i in range(int(a), int(b) + 1)})
                elif part:
                    ids[int(part)] = current
    return ids


def check_mutmut(mutmut: str) -> None:
    """Avisa se o mutmut instalado neste Python não é a versão validada."""
    try:
        from importlib.metadata import version
        found = version("mutmut")
    except Exception:
        return  # mutmut em outro ambiente (ex.: --mutmut aponta pra um venv): não dá pra checar
    if found != MUTMUT_VERSION:
        print(f"AVISO: mutmut {found} instalado; o parsing de `results`/`apply` foi "
              f"validado só na {MUTMUT_VERSION} (pip install \"mutmut=={MUTMUT_VERSION}\").")


TEST_DIRS = {"tests", "test", "testing", "__pycache__"}
MAX_RETRIES = 200


def source_files(clone: Path, srcs: list[str]) -> list[str]:
    """Arquivos .py a mutar (relativos ao clone), sem testes.

    O mutmut 2 só ignora `tests/` e `test/` na raiz; testes dentro do pacote
    (dask/tests, aeon/testing, ...) seriam mutados, e mutante em teste não serve.
    """
    files = []
    for src in srcs:
        base = clone / src
        candidates = [base] if base.is_file() else sorted(base.rglob("*.py"))
        for f in candidates:
            rel = f.relative_to(clone)
            if set(rel.parts[:-1]) & TEST_DIRS:
                continue
            if f.name.startswith("test_") or f.name.endswith("_test.py") or f.name in ("conftest.py", "setup.py"):
                continue
            files.append(rel.as_posix())
    return files


def mutable_checker():
    """Função que diz se o mutmut consegue gerar mutantes de um arquivo (mesmo parser
    dele, em processo). None se o mutmut não estiver neste Python."""
    try:
        from mutmut import Context, list_mutations
    except ImportError:
        return None

    def check(path: Path) -> bool:
        try:
            ctx = Context(source=path.read_text(), filename=str(path), dict_synonyms=[], config=None)
            with contextlib.redirect_stdout(io.StringIO()):
                list_mutations(ctx)
            return True
        except Exception:
            return False

    return check


def generate(entry: dict, args) -> dict:
    repo = entry["repo"]
    print(f"\n== {repo}")
    clone = ensure_clone(repo, args.branch, Path(args.workdir), args.url_template)
    base_sha = run(["git", "rev-parse", "HEAD"], cwd=clone).strip()

    srcs = entry.get("src")
    if not srcs:
        raise RuntimeError("defina `src` no mutation_plan.json")
    srcs = [srcs] if isinstance(srcs, str) else srcs
    files = source_files(clone, srcs)
    if not files:
        raise RuntimeError(f"nenhum .py encontrado em {srcs}")

    # o mutmut 2 usa o parso, que não lê sintaxe mais nova (ex.: f-strings aninhadas
    # do 3.12) e ABORTA a execução inteira no primeiro arquivo que não parseia. Então
    # filtra antes, com o próprio parser dele, e registra o que ficou de fora.
    skipped: list[str] = []
    check = mutable_checker()
    if check:
        skipped = [f for f in files if not check(clone / f)]
        files = [f for f in files if f not in set(skipped)]

    # o mutmut exige uma pasta tests/ ou test/ na raiz; em vários forks os testes
    # ficam dentro do pacote, então cria uma vazia (não versionada)
    if not (clone / "tests").exists() and not (clone / "test").exists():
        (clone / "tests").mkdir()

    # `--runner true`: o "teste" é um no-op, então o mutmut só enumera os mutantes
    # (todos aparecem como sobreviventes) sem rodar a suíte de verdade. O exit code
    # é um bitmask (2 = sobreviventes, 4 = timeout, 8 = suspeitos): só o bit 1 é erro.
    # Rede de segurança: se ainda assim um arquivo falhar, tira da lista e repete.
    for _ in range(MAX_RETRIES):
        if not files:
            raise RuntimeError("nenhum arquivo mutável sobrou")
        cmd = [args.mutmut, "run", "--runner", "true", "--no-progress",
               "--paths-to-mutate", ",".join(files)]
        res = subprocess.run(cmd, cwd=clone, capture_output=True, text=True)
        if not res.returncode & 1:
            break
        m = re.search(r"Failed while creating mutations for (.+?), for line", res.stdout + res.stderr)
        if not m or m.group(1) not in files:
            raise RuntimeError(f"mutmut run falhou (rc={res.returncode}):\n{res.stdout[-800:]}\n{res.stderr[-800:]}")
        files.remove(m.group(1))
        skipped.append(m.group(1))
    else:
        raise RuntimeError(f"mais de {MAX_RETRIES} arquivos não parseiam")
    if skipped:
        print(f"   {len(skipped)} arquivo(s) ignorado(s) (parso não lê), {len(files)} mutável(is)")
    ids = parse_results(run([args.mutmut, "results"], cwd=clone))
    if not ids:
        raise RuntimeError(f"{repo}: nenhum mutante encontrado (confira `src` no plano)")

    rng = random.Random(f"{args.seed}:{repo}")
    chosen = sorted(rng.sample(sorted(ids), min(entry["n"], len(ids))))
    print(f"   {len(ids)} mutantes gerados, amostrando {len(chosen)} (seed={args.seed})")

    out_dir = DATA / "patches" / repo
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    mutants = []
    for mid in chosen:
        key = f"{repo}-m{mid:04d}"
        run([args.mutmut, "apply", str(mid)], cwd=clone)
        # só o arquivo mutado: o patch não pode carregar nada além dele (ex.: .mutmut-cache)
        patch = run(["git", "diff", "--", ids[mid]], cwd=clone)
        run(["git", "checkout", "--quiet", "--", ids[mid]], cwd=clone)  # volta o arquivo mutado
        if not patch.strip():
            print(f"   ! {key}: patch vazio, ignorado")
            continue
        patch_path = out_dir / f"{key}.patch"
        patch_path.write_text(patch, encoding="utf-8")
        # garante que o patch reaplica limpo na base
        run(["git", "apply", "--check", str(patch_path)], cwd=clone)
        line = re.search(r"^@@ -(\d+)", patch, re.M)
        mutants.append({
            "key": key,
            "mutmut_id": mid,
            "file": ids[mid],
            "line": int(line.group(1)) if line else None,
            "patch": str(patch_path.relative_to(ROOT)),
        })
    print(f"   {len(mutants)} patches salvos em {out_dir.relative_to(ROOT)}")
    return {
        "base_branch": args.branch,
        "base_sha": base_sha,
        "mutmut_version": MUTMUT_VERSION,
        "seed": args.seed,
        "total_generated": len(ids),
        "source_files": len(files) + len(skipped),
        "skipped_files": sorted(skipped),
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "mutants": mutants,
    }


def cmd_gen(args) -> int:
    check_mutmut(args.mutmut)
    all_meta = json.loads(MUTANTS_PATH.read_text(encoding="utf-8")) if MUTANTS_PATH.exists() else {}
    for entry in load_plan(args.repo, args.n):
        try:
            all_meta[entry["repo"]] = generate(entry, args)
        except Exception as exc:
            print(f"   !! {entry['repo']}: {exc}")
        save_json(MUTANTS_PATH, all_meta)
    print(f"\nMetadados: {MUTANTS_PATH}")
    return 0


def cmd_list(args) -> int:
    if not MUTANTS_PATH.exists():
        print("nada gerado ainda")
        return 0
    for repo, meta in json.loads(MUTANTS_PATH.read_text(encoding="utf-8")).items():
        print(f"{repo:18} {len(meta['mutants']):>4} de {meta['total_generated']:>6} gerados  base={meta['base_sha'][:8]}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera patches de mutantes (mutmut) para cada fork.")
    sub = parser.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("gen", help="gera os mutantes e salva um patch por mutante")
    g.add_argument("--repo", action="append", help="restringe a um repo (repetível)")
    g.add_argument("--n", type=int, default=15, help="mutantes amostrados por repo (default 15)")
    g.add_argument("--seed", default="42", help="semente da amostragem (reprodutível)")
    g.add_argument("--branch", default="insert-mutations", help="branch base de cada fork")
    g.add_argument("--workdir", default=str(ROOT / "work"), help="onde clonar os forks")
    g.add_argument("--url-template", default=f"https://github.com/{OWNER}/{{repo}}.git")
    g.add_argument("--mutmut", default=shutil.which("mutmut") or "mutmut")
    g.set_defaults(func=cmd_gen)
    sub.add_parser("list", help="resume o que foi gerado").set_defaults(func=cmd_list)
    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
