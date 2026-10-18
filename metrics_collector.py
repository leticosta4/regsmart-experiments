"""
metrics_collector.py: coleta as métricas do TCC dos runs do flaky_runner/experiment_runner
e gera as tabelas (linhas = repos, colunas = modos).

Métricas (uma linha por "leg" = job de teste de um run):
  tsr_s       duração do step de teste (API de jobs, steps[])
  job_s       duração do job inteiro (setup + testes + post). É o "tempo do workflow" por modo;
              wf_s guarda o tempo do run (1º job iniciado -> último concluído)
  rts_s/rtp_s tempos impressos no resumo do plugin (regex configurável, ver `probe`)
  ttff_s      time to first fault: custo acumulado (s) até a 1ª falta esperada, na ordem executada
  detected / hidden (+ _pct)   faltas esperadas que o modo pegou / deixou escapar
  apfdc       APFDc (Elbaum et al.), 1 falta = 1 teste. Falta oculta contribui 0 e conta no m;
              nos modos com seleção (RTS) o n é só o conjunto selecionado, então o APFDc de
              RTS e o de RTP não são diretamente comparáveis.

"Falta esperada" = teste que falha em TODAS as repetições do baseline do mutante (>= 2).
"Flaky" = falha em algumas repetições do baseline e passa em outras: fora das faltas, mas
fica no custo/ordem. Falha que só aparece em modo de plugin vai para `plugin_only`.

Uso:
  python metrics_collector.py probe     --campaign experiment --repo ipython
  python metrics_collector.py collect   --campaign experiment [--test-step REGEX] [--rts-re ..] [--rtp-re ..]
  python metrics_collector.py aggregate --campaign experiment [--rep-stat median] [--mut-stat mean]

Pré-requisito nos workflows: ver workflow_snippet.yml (report-log + artifact `reportlog-<label>`,
job com `name: test (<label>)`, `fail-fast: false`).
"""

import argparse
import collections
import csv
import json
import re
import statistics
import subprocess
import sys
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from flaky_runner import Api, OWNER, TOKEN, Campaign, load_manifest, parse_ts, save_json

WF_ORDER = ["baseline", "ranking", "regsmart", "regsmart-no-rank"]
ART_PREFIX = "reportlog-"
DEFAULT_TEST_STEP = r"(?i)^(run .*(test|pytest)|test\b)"
# Chute: ajuste ao formato real do resumo do plugin (use `probe` pra ver as linhas).
DEFAULT_RTS = r"(?i)\bRTS\b[^\n\d]*(?P<v>\d+(?:\.\d+)?)\s*(?P<u>ms|s)\b"
DEFAULT_RTP = r"(?i)\bRTP\b[^\n\d]*(?P<v>\d+(?:\.\d+)?)\s*(?P<u>ms|s)\b"

ID_FIELDS = ["repo", "mutant", "workflow", "mode", "rep", "phase", "run_id", "job_id", "conclusion"]
VALUE_FIELDS = ["tsr_s", "job_s", "wf_s", "rts_s", "rtp_s", "n_tests", "n_failed", "faults", "flaky",
                "detected", "hidden", "hidden_not_selected", "detected_pct", "hidden_pct",
                "ttff_s", "ttff_pos", "apfdc", "plugin_only", "internalerror", "has_reportlog"]
FIELDS = ID_FIELDS + VALUE_FIELDS
FAULT_METRICS = ("detected", "hidden", "hidden_not_selected", "detected_pct", "hidden_pct",
                 "ttff_s", "ttff_pos", "apfdc")

# (campo, título, casas decimais)
METRICS = [
    ("tsr_s", "TSR time (s)", 2),
    ("rts_s", "RTS time (s)", 3),
    ("rtp_s", "RTP time (s)", 3),
    ("ttff_s", "Time to first fault (s)", 2),
    ("detected", "Faltas detectadas (média)", 1),
    ("detected_pct", "Faltas detectadas (\\%)", 1),
    ("hidden", "Faltas ocultas (média)", 1),
    ("hidden_pct", "Faltas ocultas (\\%)", 1),
    ("apfdc", "APFDc", 3),
    ("job_s", "Tempo do workflow por modo (s)", 1),
]
RATIO_METRICS = {"tsr_s", "job_s", "ttff_s"}


def mdir(c: Campaign) -> Path:
    return c.dir / "metrics"


def secs(a, b):
    return (parse_ts(b) - parse_ts(a)).total_seconds() if a and b else None


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def gh_bytes(path: str):
    res = subprocess.run(["gh", "api", path], capture_output=True)
    return res.stdout if res.returncode == 0 else None


def throttle(api: Api, min_left: int = 150) -> None:
    rl = api.rate_limit()
    if rl and rl["remaining"] < min_left:
        wait = (parse_ts(rl["reset_utc"]) - datetime.now(timezone.utc)).total_seconds() + 5
        print(f"\n  rate limit baixo ({rl['remaining']}), esperando {wait:.0f}s")
        time.sleep(max(wait, 5))


def cached_json(path: Path, fetch):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    data = fetch()
    path.write_text(json.dumps(data), encoding="utf-8")
    return data


# ---------------------------------------------------------------- parsing

def read_reportlog(raw: bytes):
    """pytest-reportlog (jsonl) -> (ordem dos nodeids, duração por teste, nodeids que falharam)."""
    order, dur, failed, seen = [], {}, set(), set()
    for line in raw.decode("utf-8", "replace").splitlines():
        if not line.startswith("{"):
            continue
        try:
            o = json.loads(line)
        except ValueError:
            continue
        kind = o.get("$report_type")
        if kind == "TestReport":
            nid = o["nodeid"]
            if nid not in seen:
                seen.add(nid)
                order.append(nid)
            dur[nid] = dur.get(nid, 0.0) + float(o.get("duration") or 0)
            if o.get("outcome") == "failed":  # setup/call/teardown
                failed.add(nid)
        elif kind == "CollectReport" and o.get("outcome") == "failed":
            failed.add(o.get("nodeid") or "<collect>")
    return order, dur, failed


def read_artifact(path):
    if not path or not Path(path).exists():
        return None
    with zipfile.ZipFile(path) as z:
        name = next((n for n in z.namelist() if n.endswith(".jsonl")), None)
        return read_reportlog(z.read(name)) if name else None


def job_log(zlog, job_name: str) -> str:
    if not zlog or not Path(zlog).exists():
        return ""
    key = norm(job_name)
    with zipfile.ZipFile(zlog) as z:
        for n in z.namelist():
            if "/" not in n and norm(re.sub(r"^\d+_", "", n).removesuffix(".txt")) == key:
                return z.read(n).decode("utf-8", "replace")
    return ""


def plugin_time(text: str, rx: re.Pattern):
    last = None
    for m in rx.finditer(text):
        last = m
    if not last:
        return None
    v = float(last.group("v"))
    return v / 1000 if (last.groupdict().get("u") or "s").lower() == "ms" else v


def leg_metrics(order, dur, failed, faults) -> dict:
    """Métricas de uma execução dado o conjunto de faltas esperadas do mutante."""
    out = {"n_tests": len(order), "n_failed": len(failed)}
    if not faults:  # mutante sem falta esperada: só as métricas de tempo valem
        return {**out, **{k: None for k in FAULT_METRICS}}
    cost = [dur.get(t, 0.0) for t in order]
    total = sum(cost)
    pos = {t: i for i, t in enumerate(order)}
    detected = [f for f in faults if f in failed]
    missed = [f for f in faults if f not in failed]
    m = len(faults)
    positions = sorted(pos[f] for f in detected if f in pos)
    suffix = [0.0] * (len(order) + 1)
    for i in range(len(order) - 1, -1, -1):
        suffix[i] = suffix[i + 1] + cost[i]
    num = sum(suffix[p] - cost[p] / 2 for p in positions)
    out.update(
        detected=len(detected), hidden=len(missed),
        hidden_not_selected=sum(1 for f in missed if f not in pos),
        detected_pct=100 * len(detected) / m, hidden_pct=100 * len(missed) / m,
        ttff_s=sum(cost[:positions[0] + 1]) if positions else None,
        ttff_pos=positions[0] + 1 if positions else None,
        apfdc=num / (total * m) if total > 0 else None,
    )
    return out


# ---------------------------------------------------------------- coleta

def build_legs(api: Api, c: Campaign, r: dict, step_rx: re.Pattern) -> list[dict]:
    """Baixa (com cache) jobs, logs e artifacts de um run e devolve um dict por leg."""
    d = mdir(c) / "cache" / str(r["run_id"])
    d.mkdir(parents=True, exist_ok=True)
    base = f"/repos/{OWNER}/{r['repo']}/actions/runs/{r['run_id']}"
    jobs = cached_json(d / "jobs.json", lambda: api.get(f"{base}/jobs?per_page=100")["jobs"])
    arts = cached_json(d / "artifacts.json", lambda: api.get(f"{base}/artifacts?per_page=100")["artifacts"])
    zlog = c.raw / r["repo"] / f"{r['run_id']}.zip"
    if not zlog.exists():
        data = gh_bytes(f"repos/{OWNER}/{r['repo']}/actions/runs/{r['run_id']}/logs")
        if data:
            zlog.parent.mkdir(parents=True, exist_ok=True)
            zlog.write_bytes(data)
    starts = [parse_ts(j["started_at"]) for j in jobs if j.get("started_at")]
    ends = [parse_ts(j["completed_at"]) for j in jobs if j.get("completed_at")]
    wf_s = (max(ends) - min(starts)).total_seconds() if starts and ends else None
    by_label = {a["name"][len(ART_PREFIX):]: a for a in arts
                if a["name"].startswith(ART_PREFIX) and not a.get("expired")}
    cands = []
    for j in jobs:
        if j.get("conclusion") not in ("success", "failure"):
            continue
        step = next((s for s in j.get("steps") or [] if step_rx.search(s["name"])), None)
        if step is not None:  # job sem step de teste (lint, etc.) fica de fora
            cands.append((j, step))
    # Workflow de uma perna só (baseline, no-rank): não depende do nome do job nem do artifact.
    single = len(cands) == 1 and len(by_label) == 1
    legs, seen = [], set()
    for j, step in cands:
        m = re.search(r"\((.*)\)\s*$", j["name"])
        label = "main" if single else (m.group(1) if m else "main")
        if label in seen:
            print(f"\n  ! {r['repo']} run {r['run_id']}: dois jobs com label '{label}', ignorando o 2º")
            continue
        seen.add(label)
        leg = {
            "repo": r["repo"], "mutant": r["mutant"], "workflow": r["workflow"],
            "mode": r["workflow"] if label == "main" else f"{r['workflow']}:{label}",
            "rep": r["rep"], "phase": r["phase"], "run_id": r["run_id"], "job_id": j["id"],
            "conclusion": j["conclusion"], "job_name": j["name"],
            "tsr_s": secs(step.get("started_at"), step.get("completed_at")),
            "job_s": secs(j.get("started_at"), j.get("completed_at")),
            "wf_s": wf_s, "zlog": str(zlog) if zlog.exists() else None, "reportlog": None,
        }
        art = next(iter(by_label.values())) if single else by_label.get(label)
        if art:
            p = d / (ART_PREFIX + re.sub(r"[^\w.-]+", "_", label) + ".zip")
            if not p.exists():
                data = gh_bytes(f"repos/{OWNER}/{r['repo']}/actions/artifacts/{art['id']}/zip")
                if data:
                    p.write_bytes(data)
            leg["reportlog"] = str(p) if p.exists() else None
        legs.append(leg)
    return legs


def cmd_collect(args) -> int:
    c = Campaign(args.campaign)
    api = Api(TOKEN)
    step_rx = re.compile(args.test_step)
    rts_rx, rtp_rx = re.compile(args.rts_re), re.compile(args.rtp_re)
    manifest = load_manifest(c)
    runs = [r for r in manifest["runs"] if r.get("mutant") and r.get("run_id")
            and r.get("conclusion") in ("success", "failure")]
    if args.exclude_warmup:
        runs = [r for r in runs if r["phase"] != "warmup"]
    if args.repo:
        runs = [r for r in runs if r["repo"] in args.repo]
    print(f"{len(runs)} runs concluídos (success/failure); baixando o que falta (cache em {mdir(c)}/cache)")

    legs = []
    for i, r in enumerate(runs, 1):
        if i % 20 == 0:
            throttle(api)
        legs += build_legs(api, c, r, step_rx)
        print(f"  {i}/{len(runs)} runs, {len(legs)} legs", end="\r")
    print()

    # Passo 1: faltas esperadas e flaky de cada mutante, a partir do baseline.
    base_failed = collections.defaultdict(list)
    for leg in legs:
        if leg["workflow"] == "baseline":
            data = read_artifact(leg["reportlog"])
            if data:
                base_failed[(leg["repo"], leg["mutant"])].append(data[2])
    truth = {}
    for key, sets in base_failed.items():
        if len(sets) >= 2:
            faults = set.intersection(*sets)
            truth[key] = (faults, set.union(*sets) - faults)
    skipped = sorted(k for k in base_failed if k not in truth)
    if skipped:
        print(f"  ! {len(skipped)} mutante(s) com < 2 repetições de baseline com report-log: sem métricas de falta")

    # Passo 2: métricas por leg.
    rows, miss = [], collections.Counter()
    for leg in legs:
        text = job_log(leg["zlog"], leg["job_name"])
        data = read_artifact(leg["reportlog"])
        row = {k: leg[k] for k in ID_FIELDS}
        row.update(tsr_s=leg["tsr_s"], job_s=leg["job_s"], wf_s=leg["wf_s"],
                   internalerror=int("INTERNALERROR" in text), has_reportlog=int(data is not None))
        if leg["workflow"].startswith("regsmart"):
            row["rts_s"] = plugin_time(text, rts_rx)
            miss["rts"] += row["rts_s"] is None
        if leg["workflow"] in ("ranking", "regsmart"):
            row["rtp_s"] = plugin_time(text, rtp_rx)
            miss["rtp"] += row["rtp_s"] is None
        if leg["tsr_s"] is None:
            miss["tsr"] += 1
        t = truth.get((leg["repo"], leg["mutant"]))
        if data:
            order, dur, failed = data
            if t:
                row.update(leg_metrics(order, dur, failed, t[0]))
                row.update(faults=len(t[0]), flaky=len(t[1]), plugin_only=len(failed - t[0] - t[1]))
            else:
                row.update(n_tests=len(order), n_failed=len(failed))
        else:
            miss["sem_reportlog"] += 1
        rows.append(row)

    out = mdir(c)
    out.mkdir(parents=True, exist_ok=True)
    with (out / "runs.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, restval="")
        w.writeheader()
        w.writerows(rows)
    tj: dict = {}
    for (repo, mut), (faults, flaky) in sorted(truth.items()):
        tj.setdefault(repo, {})[mut] = {"faults": sorted(faults), "flaky": sorted(flaky)}
    save_json(out / "faults.json", tj)
    print(f"\n{len(rows)} legs -> {out / 'runs.csv'}; faltas/flaky por mutante -> {out / 'faults.json'}")
    print(f"campos ausentes: {dict(miss)} (rts/rtp ausentes = regex não casou; confira com `probe`; "
          f"tsr ausente = ajuste --test-step; sem_reportlog = artifact faltando)")
    flagged = sum(1 for r in rows if r.get("internalerror"))
    if flagged:
        print(f"! {flagged} leg(s) com INTERNALERROR no log (candidatos a erro do plugin)")
    return 0


def cmd_probe(args) -> int:
    """Mostra, nos logs de um run, as linhas que parecem resumo do plugin."""
    c = Campaign(args.campaign)
    manifest = load_manifest(c)
    runs = [r for r in manifest["runs"] if r.get("run_id") and r.get("status") == "completed"
            and (not args.repo or r["repo"] in args.repo)
            and (not args.workflow or r["workflow"] in args.workflow)
            and r["workflow"] != "baseline"]
    if not runs:
        sys.exit("nenhum run concluído de workflow de plugin com esses filtros")
    r = runs[0]
    zlog = c.raw / r["repo"] / f"{r['run_id']}.zip"
    if not zlog.exists():
        data = gh_bytes(f"repos/{OWNER}/{r['repo']}/actions/runs/{r['run_id']}/logs")
        if not data:
            sys.exit("falha ao baixar o log")
        zlog.parent.mkdir(parents=True, exist_ok=True)
        zlog.write_bytes(data)
    print(f"{r['repo']} / {r['workflow']} / run {r['run_id']}\n")
    kw = re.compile(r"(?i)regsmart|ranking|\bRTS\b|\bRTP\b|select|overhead")
    with zipfile.ZipFile(zlog) as z:
        for n in sorted(x for x in z.namelist() if "/" not in x):
            lines = [re.sub(r"^\S+Z ", "", ln) for ln in z.read(n).decode("utf-8", "replace").splitlines()
                     if kw.search(ln)]
            if lines:
                print(f"== {n}")
                print("\n".join(lines[-args.lines:]))
    return 0


# ---------------------------------------------------------------- agregação

def num(x):
    return None if x in ("", None) else float(x)


def stat(vals, kind):
    vals = [v for v in vals if v is not None]
    if not vals:
        return None
    return statistics.median(vals) if kind == "median" else statistics.fmean(vals)


def sd(vals):
    vals = [v for v in vals if v is not None]
    return statistics.stdev(vals) if len(vals) > 1 else None


def mode_key(mode: str):
    wf, _, label = mode.partition(":")
    return (WF_ORDER.index(wf) if wf in WF_ORDER else 99, label)


def fmt(v, dec):
    return "-" if v is None else f"{v:.{dec}f}"


def tex(s: str) -> str:
    return s.replace("\\%", "%").replace("_", "\\_").replace("%", "\\%").replace("&", "\\&")


def write_tex(path: Path, title: str, label: str, modes, rows) -> None:
    L = ["\\begin{table}[htbp]", "\\centering", "\\small", f"\\caption{{{title}}}", f"\\label{{tab:{label}}}",
         "\\resizebox{\\textwidth}{!}{%", "\\begin{tabular}{l" + "r" * len(modes) + "}", "\\toprule",
         "Repositório & " + " & ".join(tex(m) for m in modes) + " \\\\", "\\midrule"]
    for name, cells in rows:
        if name.startswith("@"):
            L.append("\\midrule")
            name = name[1:]
        L.append(tex(name) + " & " + " & ".join(cells) + " \\\\")
    L += ["\\bottomrule", "\\end{tabular}%", "}", "\\end{table}", ""]
    path.write_text("\n".join(L), encoding="utf-8")


def cmd_aggregate(args) -> int:
    c = Campaign(args.campaign)
    src = mdir(c) / "runs.csv"
    if not src.exists():
        sys.exit(f"{src} não existe: rode `collect`")
    rows = list(csv.DictReader(src.open(encoding="utf-8")))
    if args.exclude_warmup:
        rows = [r for r in rows if r["phase"] != "warmup"]
    fields = [m for m, _, _ in METRICS] + ["faults"]

    # Passo 1: por (repo, mutante, modo), estatística entre as repetições.
    groups = collections.defaultdict(list)
    for r in rows:
        groups[(r["repo"], r["mutant"], r["mode"])].append(r)
    cell1 = {k: {m: stat([num(r[m]) for r in rs], args.rep_stat) for m in fields} for k, rs in groups.items()}

    # Passo 2: por (repo, modo), estatística entre os mutantes.
    by_cell = collections.defaultdict(list)
    for (repo, _mut, mode), d in cell1.items():
        by_cell[(repo, mode)].append(d)
    repos = sorted({k[0] for k in by_cell})
    modes = sorted({k[1] for k in by_cell}, key=mode_key)
    table = {}  # metric -> repo -> mode -> (centro, desvio)
    for m, _, _ in METRICS:
        table[m] = {}
        for repo in repos:
            table[m][repo] = {}
            for mode in modes:
                ds = by_cell.get((repo, mode), [])
                if m == "detected_pct":  # agregado por contagem: sum(detectadas) / sum(faltas)
                    ok = [d for d in ds if d["detected"] is not None and d["faults"]]
                    tot = sum(d["faults"] for d in ok)
                    v = 100 * sum(d["detected"] for d in ok) / tot if tot else None
                    table[m][repo][mode] = (v, None)
                elif m == "hidden_pct":
                    v = table["detected_pct"][repo][mode][0]
                    table[m][repo][mode] = (None if v is None else 100 - v, None)
                else:
                    vals = [d[m] for d in ds]
                    table[m][repo][mode] = (stat(vals, args.mut_stat), sd(vals))

    out = mdir(c) / "tables"
    out.mkdir(parents=True, exist_ok=True)
    for m, title, dec in METRICS:
        body, body_sd = [], []
        for repo in repos:
            body.append((repo, [fmt(table[m][repo][mo][0], dec) for mo in modes]))
            body_sd.append((repo, [fmt(table[m][repo][mo][1], dec) for mo in modes]))
        mean_row = [fmt(stat([table[m][r][mo][0] for r in repos], "mean"), dec) for mo in modes]
        body.append(("@Média entre repos", mean_row))
        if m in RATIO_METRICS:
            ratios = []
            for mo in modes:
                rs = []
                for repo in repos:
                    b, v = table[m][repo].get("baseline", (None, None))[0], table[m][repo][mo][0]
                    if b and v is not None:
                        rs.append(v / b)
                ratios.append(fmt(stat(rs, "mean"), 2))
            body.append(("Razão média vs baseline", ratios))
        with (out / f"{m}.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["repo"] + modes)
            for name, cells in body:
                w.writerow([name.lstrip("@")] + cells)
        with (out / f"{m}_sd.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["repo"] + modes)
            for name, cells in body_sd:
                w.writerow([name] + cells)
        write_tex(out / f"{m}.tex", f"{title}: {args.mut_stat} entre mutantes ({args.rep_stat} entre repetições)",
                  m, modes, body)

    print(f"{len(repos)} repos x {len(modes)} modos -> {out}/<metrica>.csv|.tex (+ _sd.csv)")
    for repo in repos:
        muts = {k[1] for k in cell1 if k[0] == repo}
        with_f = {k[1] for k, d in cell1.items() if k[0] == repo and d["faults"]}
        print(f"  {repo:18} mutantes com falta esperada: {len(with_f)}/{len(muts)} "
              f"(só esses entram nas métricas de falta)")
    return 0


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--campaign", choices=["flaky", "experiment"], default="experiment")
    common.add_argument("--repo", action="append", help="restringe a um repo (repetível)")
    common.add_argument("--exclude-warmup", action="store_true")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("collect", parents=[common], help="baixa e calcula as métricas por leg")
    s.add_argument("--test-step", default=DEFAULT_TEST_STEP, help="regex do nome do step de teste")
    s.add_argument("--rts-re", default=DEFAULT_RTS, help="regex (grupos v e u) do tempo de RTS no log")
    s.add_argument("--rtp-re", default=DEFAULT_RTP, help="regex (grupos v e u) do tempo de RTP no log")
    s.set_defaults(func=cmd_collect)

    s = sub.add_parser("probe", parents=[common], help="mostra linhas do resumo do plugin em um log")
    s.add_argument("--workflow", action="append")
    s.add_argument("--lines", type=int, default=25)
    s.set_defaults(func=cmd_probe)

    s = sub.add_parser("aggregate", parents=[common], help="gera as tabelas CSV/LaTeX")
    s.add_argument("--rep-stat", choices=["mean", "median"], default="median", help="entre repetições")
    s.add_argument("--mut-stat", choices=["mean", "median"], default="mean", help="entre mutantes")
    s.set_defaults(func=cmd_aggregate)

    args = p.parse_args()
    if args.cmd == "collect" and not TOKEN:
        sys.exit("token obrigatório: defina GITHUB_TOKEN_REGSMART ou rode `gh auth login`")
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
