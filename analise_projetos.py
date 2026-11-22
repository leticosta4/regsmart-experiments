"""analise_projetos.py: caracteriza, por análise estática, como os testes de cada projeto do dataset chegam ao
código testado. Alimenta a coluna "Como os testes chegam ao código" da tab:perfil-projetos (tabelas_eixos.py).

A análise roda sobre os forks no commit usado no experimento (data/fork_commits.csv) e não executa nada dos
projetos: só lê os arquivos .py e os arquivos de configuração.

Padrões medidos em TODOS os projetos (fração dos arquivos de teste em que o padrão aparece):
  subproc      execução de código em outro processo: subprocess (inclui runpytest_subprocess), Popen,
               check_output, os.system, CliRunner
  pytester     sessões internas do pytest: fixtures pytester/testdir (inclui django_pytester)
  generic_g    módulo auxiliar importado por nome simples: "import generic as g" / "from generic import g"
  yolo_model   objeto de modelo central do ultralytics: YOLO(...)
  trainer      orquestrador do Lightning: Trainer(...) / Fabric(...)
  ip_global    estado global do IPython: _ip / get_ipython / globalipapp
  dvc_fixt     fixtures orquestradoras do dvc (tmp_dir, dvc, scm) como argumento de uma função de teste
e, por projeto:
  dispatchable_decorations  nº de funções do código-fonte decoradas com _dispatchable (camada de despacho)
  doctest      se os doctests são coletados na mesma execução do pytest que roda a suíte: --doctest-modules ou
               --ipdoctest-modules em pyproject.toml, setup.cfg, tox.ini, pytest.ini, conftest.py ou nos
               workflows (.github/workflows). Jobs separados só de doctest (--doctest-only, "pixi r doctest")
               não contam, porque não fazem parte da TSR medida no experimento
  test_files, test_funcs, src_modules, src_loc  tamanho do projeto

Os padrões foram escolhidos a partir da inspeção dos casos discutidos no Cap. 7 (falhas não selecionadas,
seleção de quase toda a suíte, custo de carregamento) e depois medidos em todos os projetos, para verificar se
também aparecem nos projetos com ganho sem perda.

Saída: data/analise_projetos/caracteristicas_projetos.csv

Uso:
  python3 analise_projetos.py --clonar                  # clona os forks (raso) no commit do experimento e analisa
  python3 analise_projetos.py --clones /caminho/forks   # usa clones já existentes (um diretório por repo)
"""
from __future__ import annotations

import argparse
import ast
import csv
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OWNER = "leticosta4"
COMMITS = ROOT / "data" / "fork_commits.csv"
OUT_DIR = ROOT / "data" / "analise_projetos"

# repo: (raiz do código-fonte, pacotes do código-fonte)
CFG = {
    "aeon": (".", ["aeon"]), "apscheduler": ("src", ["apscheduler"]), "dask": (".", ["dask"]),
    "dvc": (".", ["dvc"]), "ipython": (".", ["IPython"]), "librosa": (".", ["librosa"]),
    "networkx": (".", ["networkx"]), "pytest-django": (".", ["pytest_django"]),
    "pytest-xdist": ("src", ["xdist"]), "pytorch-lightning": ("src", ["lightning"]),
    "trimesh": (".", ["trimesh"]), "ultralytics": (".", ["ultralytics"]),
}
SKIP = re.compile(r"/(docs?|examples?|benchmarks?|_notebooks|build|\.git|\.venv|venv)/")

PADROES = {  # regex por arquivo de teste
    "subproc": re.compile(r"subprocess|\bPopen\b|\bcheck_output\b|\bos\.system\(|\bCliRunner\b"),
    "pytester": re.compile(r"pytester|testdir"),
    "generic_g": re.compile(r"\bimport\s+generic\s+as\s+g\b|\bfrom\s+generic\s+import\s+g\b"),
    "yolo_model": re.compile(r"\bYOLO\("),
    "trainer": re.compile(r"\b(?:Trainer|Fabric)\("),
    "ip_global": re.compile(r"\b_ip\b|\bget_ipython\b|\bglobalipapp\b"),
}
DVC_FIXT = {"tmp_dir", "dvc", "scm"}
DOCTEST = re.compile(r"--(?:ip)?doctest-modules")


def is_test(name: str) -> bool:
    return name.startswith("test_") and name.endswith(".py") or name.endswith("_test.py")


def arquivos(root: Path):
    for dp, _dn, fn in os.walk(root):
        if SKIP.search(dp.replace(os.sep, "/") + "/"):
            continue
        for f in fn:
            if f.endswith(".py"):
                yield Path(dp) / f


def ler(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


def usa_fixtures_dvc(tree: ast.AST | None) -> bool:
    if tree is None:
        return False
    for nd in ast.walk(tree):
        if isinstance(nd, (ast.FunctionDef, ast.AsyncFunctionDef)) and nd.name.startswith("test"):
            if DVC_FIXT & {a.arg for a in nd.args.args + nd.args.kwonlyargs}:
                return True
    return False


def decoracoes_dispatchable(tree: ast.AST | None) -> int:
    n = 0
    if tree is None:
        return 0
    for nd in ast.walk(tree):
        if isinstance(nd, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            for d in nd.decorator_list:
                d = d.func if isinstance(d, ast.Call) else d
                nome = d.attr if isinstance(d, ast.Attribute) else getattr(d, "id", "")
                n += nome == "_dispatchable"
    return n


def parse(txt: str):
    try:
        return ast.parse(txt)
    except SyntaxError:
        return None


def doctest_no_pytest(root: Path) -> bool:
    cands = [root / n for n in ("pyproject.toml", "setup.cfg", "tox.ini", "pytest.ini", "conftest.py")]
    wf = root / ".github" / "workflows"
    if wf.is_dir():
        cands += sorted(wf.glob("*.y*ml"))
    return any(p.is_file() and DOCTEST.search(ler(p)) for p in cands)


def analisar(repo: str, root: Path) -> dict:
    sroot, pkgs = CFG[repo]
    base = root / sroot
    testes, src_mods, src_loc, disp = [], 0, 0, 0
    for p in arquivos(root):
        rel = p.relative_to(base).as_posix() if p.is_relative_to(base) else ""
        if is_test(p.name):
            testes.append(p)
        elif rel.split("/")[0] in pkgs and "/tests/" not in "/" + rel and "/testing/" not in "/" + rel \
                and p.name != "conftest.py":
            txt = ler(p)
            src_mods += 1
            src_loc += txt.count("\n")
            disp += decoracoes_dispatchable(parse(txt))
    cont = dict.fromkeys(list(PADROES) + ["dvc_fixt"], 0)
    funcs = 0
    for p in testes:
        txt = ler(p)
        tree = parse(txt)
        for k, rx in PADROES.items():
            cont[k] += bool(rx.search(txt))
        cont["dvc_fixt"] += usa_fixtures_dvc(tree)
        if tree is not None:
            funcs += sum(isinstance(nd, (ast.FunctionDef, ast.AsyncFunctionDef)) and nd.name.startswith("test")
                         for nd in ast.walk(tree))
    n = len(testes) or 1
    row = {"repo": repo, "commit": subprocess.run(["git", "-C", str(root), "rev-parse", "--short", "HEAD"],
                                                    capture_output=True, text=True).stdout.strip(),
           "src_modules": src_mods, "src_loc": src_loc, "test_files": len(testes), "test_funcs": funcs}
    row.update({k: round(v / n, 4) for k, v in cont.items()})
    row["dispatchable_decorations"] = disp
    row["doctest"] = doctest_no_pytest(root)
    return row


def clonar(destino: Path) -> None:
    destino.mkdir(parents=True, exist_ok=True)
    for r in csv.DictReader(COMMITS.open(encoding="utf-8")):
        d = destino / r["repo"]
        if not (d / ".git").is_dir():
            subprocess.run(["git", "init", "-q", str(d)], check=True)
            subprocess.run(["git", "-C", str(d), "remote", "add", "origin",
                            f"https://github.com/{OWNER}/{r['repo']}.git"], check=True)
        subprocess.run(["git", "-C", str(d), "fetch", "-q", "--depth", "1", "origin", r["commit"]], check=True)
        subprocess.run(["git", "-C", str(d), "checkout", "-q", "FETCH_HEAD"], check=True)
        print(f"{r['repo']}: {r['commit'][:7]}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--clones", type=Path, default=OUT_DIR / "forks",
                    help="diretório com um clone por repo (padrão: data/analise_projetos/forks, ignorado no git)")
    ap.add_argument("--clonar", action="store_true", help="clona/atualiza os forks no commit de data/fork_commits.csv")
    ap.add_argument("--out", type=Path, default=OUT_DIR / "caracteristicas_projetos.csv")
    a = ap.parse_args()
    if a.clonar:
        clonar(a.clones)
    esperado = {r["repo"]: r["commit"] for r in csv.DictReader(COMMITS.open(encoding="utf-8"))}
    rows = []
    for repo in CFG:
        d = a.clones / repo
        if not d.is_dir():
            sys.exit(f"falta o clone de {repo} em {d} (use --clonar)")
        row = analisar(repo, d)
        if not esperado[repo].startswith(row["commit"]):
            print(f"aviso: {repo} está em {row['commit']}, e não no commit do experimento {esperado[repo][:7]}")
        rows.append(row)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    with a.out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} projetos -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
