"""
check_workflows.py: confere (SOMENTE LEITURA, via API) se os 4 workflows de cada repo já têm
as mudanças necessárias para o experimento e para o metrics_collector.py.

Lê repos e arquivos só do data/workflow_plan.json (chave `overrides`), o mesmo que o runner usa
pros 4 modos; não depende do flaky_plan.json e não adivinha nomes de arquivo.

Por workflow, checa:
  - workflow_dispatch; flags do modo (--regsmart, --rank, --no-rank); xdist
  - pytest-reportlog instalado (no tox: via testenv.deps; no pixi: no ambiente) e --report-log
  - job(s) de teste: fail-fast: false, name 'x (${{ matrix.k }})' em matriz, step de teste que
    o coletor reconhece (--test-step)
  - upload-artifact 'reportlog-<label>': label igual ao do job, matrix.<k> existente,
    if: !cancelled(), depois do step de teste, path igual ao do --report-log
  - cache (ranking/regsmart): Restore que de fato acerta (restore-keys), Save com
    if: !cancelled(), caminhos iguais
  - checkout com fetch-depth: 0 (regsmart); concurrency compatível com as lanes do runner

Uso:
  python3 -m gh_automation.check_workflows                          # default branch de todos os repos do plano
  python3 -m gh_automation.check_workflows --repo apscheduler --repo dvc
  python3 -m gh_automation.check_workflows --ref mutants            # 1º mutante publicado de cada repo
  python3 -m gh_automation.check_workflows --ref mutants --all-mutants
  python3 -m gh_automation.check_workflows --ref insert-mutations   # uma branch específica
  python3 -m gh_automation.check_workflows --json out.json

Sai com código 1 se houver algum ERRO (AVISO não conta).
Não altera nada: só chamadas GET.
"""

import argparse
import base64
import json
import re
import sys
import urllib.parse
from pathlib import PurePosixPath

from flaky_runner import Api, OWNER, TOKEN, WORKFLOW_PLAN_PATH, load_registry
from metrics_collector import ART_PREFIX, DEFAULT_TEST_STEP

try:
    import yaml
except ImportError:
    sys.exit("precisa de PyYAML: pip install pyyaml")

MODES = ["baseline", "ranking", "regsmart", "regsmart-no-rank"]
# must / must_not: flags que o comando de teste deve / não deve ter; cache: o modo usa cache do plugin
EXPECT = {
    "baseline": {"must": [], "must_not": ["--regsmart", "--rank"], "cache": False},
    "ranking": {"must": ["--rank"], "must_not": ["--regsmart"], "cache": True},
    "regsmart": {"must": ["--regsmart"], "must_not": ["--no-rank"], "cache": True},
    "regsmart-no-rank": {"must": ["--regsmart", "--no-rank"], "must_not": [], "cache": False},
}
CANCEL_OK = re.compile(r"!\s*cancelled\(\)|always\(\)")


def strip_comments(text: str) -> str:
    return re.sub(r"(?m)(^|\s)#.*$", r"\1", text)


def norm_ws(s: str) -> str:
    return re.sub(r"\s+", "", s)


def triggers(doc: dict) -> set:
    on = doc.get("on", doc.get(True))  # PyYAML lê `on:` como True
    if isinstance(on, dict):
        return set(on)
    if isinstance(on, str):
        return {on}
    return set(on or [])


def matrix_info(job: dict):
    """-> (strategy, chaves da matriz, nº de legs; None = matriz dinâmica). Contagem aproximada."""
    strat = job.get("strategy") or {}
    mx = strat.get("matrix")
    if mx is None:
        return strat, set(), 1
    if not isinstance(mx, dict):
        return strat, set(), None
    axes = {k: v for k, v in mx.items() if k not in ("include", "exclude")}
    inc = mx.get("include") or []
    keys = set(axes) | {k for e in inc if isinstance(e, dict) for k in e}
    base = 1
    for v in axes.values():
        base *= len(v) if isinstance(v, list) else 1
    legs = base if axes else max(len(inc), 1)
    return strat, keys, legs


def check_workflow(mode: str, text: str, step_rx: re.Pattern) -> list[tuple[str, str]]:
    """Devolve [(nível, mensagem)], nível 'ERRO' ou 'AVISO'."""
    out: list[tuple[str, str]] = []

    def err(m): out.append(("ERRO", m))
    def warn(m): out.append(("AVISO", m))

    try:
        doc = yaml.safe_load(text) or {}
    except yaml.YAMLError as exc:
        return [("ERRO", f"YAML inválido: {str(exc)[:80]}")]
    flat = strip_comments(text)
    lines = flat.splitlines()
    exp = EXPECT[mode]

    if "workflow_dispatch" not in triggers(doc):
        err("sem workflow_dispatch")
    for fl in exp["must"]:
        if not re.search(re.escape(fl) + r"(?![\w-])", flat):
            err(f"falta {fl} no comando de teste")
    for fl in exp["must_not"]:
        if re.search(re.escape(fl) + r"(?![\w-])", flat):
            warn(f"{fl} não deveria aparecer no modo {mode}")
    if re.search(r"(?<![\w-])-n\s*(auto|\d+|logical)\b|--numprocesses|-p\s+xdist", flat):
        warn("usa xdist (-n): a ordem do report-log é a de conclusão dos workers (APFDc/TTFF distorcem)")

    if "pytest-reportlog" not in flat:
        err("pytest-reportlog não é instalado")
    rl = re.search(r"--report-log[= ]\s*[^\n]*?([\w.-]+\.jsonl)", flat)
    if not rl:
        err("falta --report-log (no comando ou em PYTEST_ADDOPTS)")
    rl_files = {rl.group(1)} if rl else set()
    if re.search(r"\btox\s+(run|-e)", flat) and not any(
            "testenv.deps" in ln and "pytest-reportlog" in ln for ln in lines):
        err('tox: pytest-reportlog precisa entrar no ambiente do tox (-x "testenv.deps+=pytest-reportlog")')
    if "pixi run" in flat and not any("pixi run" in ln and "pytest-reportlog" in ln for ln in lines):
        warn("pixi: confirme que pytest-reportlog está no ambiente (pip dentro do pixi run, ou pixi.toml)")

    conc = doc.get("concurrency")
    group = str(conc.get("group") if isinstance(conc, dict) else conc or "")
    if group and "${{" not in group:
        err("concurrency com grupo fixo: runs de qualquer branch se cancelam")
    elif group and "github.workflow" not in group:
        warn("concurrency sem github.workflow: os workflows da mesma branch se cancelam entre si "
             "(rode o runner com --serialize-ref)")

    test_jobs = []
    for jid, job in (doc.get("jobs") or {}).items():
        steps = job.get("steps") or []
        ti = next((i for i, s in enumerate(steps) if step_rx.search(str(s.get("name", "")))), None)
        if ti is not None:
            test_jobs.append((jid, job, steps, ti))
    if not test_jobs:
        err("nenhum step de teste casa com --test-step (o coletor não acharia o tempo de teste)")
        return out
    if len(test_jobs) > 1:
        warn(f"{len(test_jobs)} jobs com step de teste ({', '.join(j[0] for j in test_jobs)}): "
             f"o coletor trata cada um como um leg")

    for jid, job, steps, ti in test_jobs:
        tag = f"job '{jid}': "
        strat, keys, legs = matrix_info(job)
        multi = legs is None or legs > 1
        if strat.get("matrix") and strat.get("fail-fast") is not False:
            err(tag + "matriz sem fail-fast: false (um leg que falha cancela os outros)")
        lab = re.search(r"\(([^()]*)\)\s*$", str(job.get("name") or ""))
        if multi and not lab:
            err(tag + "matriz com vários legs, mas sem name 'xxx (${{ matrix.k }})': "
                      "o coletor não consegue parear job e artifact")

        uploads = [(i, s) for i, s in enumerate(steps)
                   if str((s.get("with") or {}).get("name", "")).startswith(ART_PREFIX)
                   and str(s.get("uses", "")).startswith("actions/upload-artifact")]
        if not uploads:
            err(tag + f"sem upload-artifact com name '{ART_PREFIX}...'")
        else:
            i, s = uploads[0]
            w = s.get("with") or {}
            suffix = str(w["name"])[len(ART_PREFIX):].strip()
            used = set(re.findall(r"matrix\.([\w-]+)", suffix))
            ghost = sorted(k for k in used if legs is not None and k not in keys)
            if ghost:
                # Job de um leg só: o coletor pareia sozinho, então é aviso; em matriz, os legs colidem.
                (err if multi else warn)(
                    tag + f"o artifact usa matrix.{ghost[0]}, que não existe nessa matriz "
                          f"(nome vazio ou duplicado; use reportlog-main)")
            elif multi and lab and norm_ws(suffix) != norm_ws(lab.group(1)):
                err(tag + f"label do artifact ('{suffix}') difere do label do job ('{lab.group(1)}')")
            elif multi and not used:
                err(tag + "artifact com nome fixo numa matriz: os legs colidem")
            if not CANCEL_OK.search(str(s.get("if", ""))):
                err(tag + "upload sem if: ${{ !cancelled() }}: não sobe quando o teste falha")
            if i < ti:
                err(tag + "upload-artifact antes do step de teste")
            base = PurePosixPath(str(w.get("path", ""))).name
            if rl_files and base not in rl_files:
                warn(tag + f"path do upload ({base or 'vazio'}) difere do --report-log ({', '.join(rl_files)})")

        cache = [s for s in steps if str(s.get("uses", "")).startswith("actions/cache")]
        restores = [s for s in cache if re.match(r"actions/cache(/restore)?@", str(s["uses"]))]
        saves = [s for s in cache if str(s["uses"]).startswith("actions/cache/save@")]
        if exp["cache"] and not cache:
            warn(tag + "sem cache do plugin: o histórico de QTF/RecentFail não persiste entre runs")
        if any(re.match(r"actions/cache@", str(s["uses"])) for s in cache):
            warn(tag + "actions/cache combinado só salva se o job passar; com mutante o teste falha. "
                       "Use cache/restore + cache/save com if: !cancelled()")
        for sv in saves:
            if not CANCEL_OK.search(str(sv.get("if", ""))):
                warn(tag + "Save cache sem if: !cancelled(): com mutante o teste falha e o cache não é salvo")
        if restores and saves:
            rw, sw = restores[0].get("with") or {}, saves[0].get("with") or {}
            rk, rks, sk = str(rw.get("key", "")), str(rw.get("restore-keys", "")).strip(), str(sw.get("key", ""))
            if "run_id" in sk and "run_id" not in rk and not rks:
                err(tag + "o cache nunca é restaurado: o Save usa run_id na chave e o Restore não tem restore-keys")
            elif rks and not norm_ws(sk).startswith(norm_ws(rks.splitlines()[0])):
                warn(tag + "restore-keys não é prefixo da chave do Save")
            if norm_ws(str(rw.get("path", ""))) != norm_ws(str(sw.get("path", ""))):
                warn(tag + "path do Restore difere do path do Save")

        if mode in ("regsmart", "regsmart-no-rank"):
            co = [s for s in steps if str(s.get("uses", "")).startswith("actions/checkout")]
            if not any(str((s.get("with") or {}).get("fetch-depth", "")) == "0" for s in co):
                warn(tag + "checkout sem fetch-depth: 0 (o Selector usa git diff)")
    return out


def load_plan(only_repos, only_modes) -> dict[str, dict]:
    """{repo: {modo: {file}}} a partir do workflow_plan.json (overrides)."""
    if not WORKFLOW_PLAN_PATH.exists():
        sys.exit(f"{WORKFLOW_PLAN_PATH} não existe")
    overrides = json.loads(WORKFLOW_PLAN_PATH.read_text(encoding="utf-8")).get("overrides") or {}
    unknown = set(only_repos or []) - set(overrides)
    if unknown:
        sys.exit(f"--repo desconhecido no workflow_plan.json: {', '.join(sorted(unknown))}")
    out = {}
    for repo, modes in overrides.items():
        if only_repos and repo not in only_repos:
            continue
        ws = {}
        for mode in MODES:
            spec = modes.get(mode) or {}
            if (only_modes and mode not in only_modes) or spec.get("enabled", True) is False:
                continue
            if not spec.get("file"):
                print(f"  ! {repo}: modo {mode} sem 'file' no workflow_plan.json, ignorado")
                continue
            ws[mode] = {"file": spec["file"]}
        out[repo] = ws
    return out


# ---------------------------------------------------------------- GitHub

def list_workflows(api: Api, repo: str, ref: str):
    try:
        listing = api.get(f"/repos/{OWNER}/{repo}/contents/.github/workflows?ref={urllib.parse.quote(ref)}")
    except RuntimeError:
        return None
    return {e["name"] for e in listing} if isinstance(listing, list) else None


def fetch_text(api: Api, repo: str, file: str, ref: str) -> str:
    d = api.get(f"/repos/{OWNER}/{repo}/contents/.github/workflows/{urllib.parse.quote(file)}"
                f"?ref={urllib.parse.quote(ref)}")
    return base64.b64decode(d["content"]).decode("utf-8", errors="replace")


def refs_for(api: Api, repo: str, args, registry: dict) -> list[str]:
    if args.ref == "default":
        return [api.get(f"/repos/{OWNER}/{repo}")["default_branch"]]
    if args.ref == "mutants":
        items = sorted(((registry.get(repo) or {}).get("mutants") or {}).items())
        branches = [m["branch"] for _, m in items if m.get("published")]
        if not branches:
            print(f"  ! {repo}: sem mutantes publicados no registro")
        return branches if args.all_mutants else branches[:1]
    return [args.ref]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", action="append", help="restringe a um repo (repetível)")
    ap.add_argument("--workflow", action="append", choices=MODES, help="restringe a um modo (repetível)")
    ap.add_argument("--ref", default="default",
                    help="default (padrão), mutants (branches mut-* do registro) ou o nome de uma branch")
    ap.add_argument("--all-mutants", action="store_true", help="com --ref mutants: todas as branches, não só a 1ª")
    ap.add_argument("--test-step", default=DEFAULT_TEST_STEP, help="regex do nome do step de teste")
    ap.add_argument("--json", help="grava o resultado completo neste arquivo")
    args = ap.parse_args()
    if not TOKEN:
        sys.exit("token obrigatório: defina GITHUB_TOKEN_REGSMART ou rode `gh auth login`")

    step_rx = re.compile(args.test_step)
    workflows = load_plan(args.repo, args.workflow)
    registry = load_registry() if args.ref == "mutants" else {}
    api = Api(TOKEN)

    results: dict = {}   # "repo@ref" -> modo -> [{level, msg}]
    summary: dict = {}   # "repo@ref" -> modo -> (erros, avisos) ou None se ausente
    for repo in workflows:
        for ref in refs_for(api, repo, args, registry):
            key = f"{repo}@{ref}"
            names = list_workflows(api, repo, ref)
            print(f"\n{key}")
            results[key], summary[key] = {}, {}
            for mode, spec in workflows[repo].items():
                f = spec["file"]
                if names is None or f not in names:
                    issues = [("ERRO", f"{f} não existe em .github/workflows nessa ref")]
                    summary[key][mode] = None
                else:
                    issues = check_workflow(mode, fetch_text(api, repo, f, ref), step_rx)
                    summary[key][mode] = (sum(1 for lv, _ in issues if lv == "ERRO"),
                                          sum(1 for lv, _ in issues if lv == "AVISO"))
                results[key][mode] = [{"level": lv, "msg": m} for lv, m in issues]
                e, w = sum(1 for lv, _ in issues if lv == "ERRO"), sum(1 for lv, _ in issues if lv == "AVISO")
                status = "OK" if not issues else f"{e} erro(s), {w} aviso(s)"
                print(f"  {mode:17} {f:26} {status}")
                for lv, m in sorted(issues, key=lambda x: x[0] != "ERRO"):
                    print(f"      {lv:6} {m}")

    print("\nResumo (ok = sem pendência; E = erros, W = avisos; - = arquivo ausente)\n")
    print(f"{'repo@ref':44}" + "".join(f"{m:>18}" for m in MODES))
    total_err = 0
    for key, row in summary.items():
        cells = []
        for m in MODES:
            if m not in row:
                cells.append("")
            elif row[m] is None:
                cells.append("-")
            else:
                e, w = row[m]
                total_err += e
                cells.append("ok" if not (e or w) else f"E{e}/W{w}")
        print(f"{key[:43]:44}" + "".join(f"{c:>18}" for c in cells))
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(results, fh, indent=2, ensure_ascii=False)
        print(f"\nDetalhes em {args.json}")
    print(f"\n{total_err} erro(s) no total." if total_err else "\nNenhum erro.")
    return 1 if total_err else 0


if __name__ == "__main__":
    sys.exit(main())
