"""
metrics_collector.py: coleta as métricas do TCC dos runs do flaky_runner/experiment_runner
e gera as tabelas (linhas = repos, colunas = modos).

Métricas (uma linha por "leg" = job de teste de um run):
  tsr_s       duração do step de teste (API de jobs, steps[])
  suite_s     tempo de execução da suíte: o "in Xs" da última linha final do pytest no log do
              job (sessão principal; sem instalação/tox/coverage que o step também mede)
  job_s       duração do job inteiro (setup + testes + post). É o "tempo do workflow" por modo;
              wf_s guarda o tempo do run (1º job iniciado -> último concluído)
  rts_s/rtp_s tempos impressos no resumo do plugin (regex configurável, ver `probe`)
  ttff_s      time to first fault: RTS + RTP + (fim da 1ª falta esperada detectada - início do
              1º teste executado), pelos timestamps `start`/`stop` do report-log; vale também
              com xdist (-n). Nos modos sem RTS/RTP essas parcelas são 0.
  detected / hidden (+ _pct)   faltas esperadas que o modo pegou / deixou escapar
  apfdc       APFDc (Elbaum et al.), 1 falta = 1 teste. Falta oculta contribui 0 e conta no m;
              nos modos com seleção (RTS) o n é só o conjunto selecionado, então o APFDc de
              RTS e o de RTP não são diretamente comparáveis.

"Falta esperada" = teste que falha em TODAS as repetições do baseline do mutante (>= 2).
"Flaky" = falha em algumas repetições do baseline e passa em outras: fora das faltas, mas
fica no custo/ordem. Falha que só aparece em modo de plugin vai para `plugin_only`.
Controle: se a campanha rodou a branch default como o mutante `control`
(`flaky_runner.py run --control`), todo teste que falhou nela (em qualquer modo) é
ambiente/pré-existente e sai das faltas e do flaky de todos os mutantes do repo; as
linhas do controle não entram em runs.csv.

Uso:
  python metrics_collector.py probe     --campaign experiment --repo ipython
  python metrics_collector.py collect   --campaign experiment [--python aeon=3.13] [--rts-re ..] [--rtp-re ..]
  python metrics_collector.py aggregate --campaign experiment [--rep-stat median] [--mut-stat mean]

Pré-requisito nos workflows: ver workflow_snippet.yml (report-log + artifact `reportlog-<label>`,
`fail-fast: false`). O casamento job <-> artifact tolera os formatos dos forks: label em
qualquer posição do nome do job, artifacts repetidos (matriz de Python) e `reportlog-` sem
sufixo, desempatados pelo horário do upload (ver build_legs). Matriz de versões do Python:
use `--python REPO=X.Y` para ficar com uma só (ex.: aeon=3.13).
"""

import argparse
import collections
import csv
import json
import os
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
# Formato real dos resumos (confira com `probe` se os plugins mudarem):
#   regsmart:  "Time to run the regression test selection (s): 1234.56 ms (1.23456 s)"
#              "Time to run the file-level regression test selection (s): ..."   (fallback)
#              "Time to run the regression test prioritization (s): ..."
#   pytest-ranking: "Time to reorder tests (s): 0.0123"  (sem unidade; pode vir em notação 1e-05)
#              + "Time to compute test-change similarity (s)" e "Time to collect test features (s)"
# Grupo `k` = chave (soma-se a última ocorrência de cada chave); `v` = valor; `u` = unidade.
_NUM = r"[\d.]+(?:[eE][-+]?\d+)?"
DEFAULT_RTS = (r"(?P<k>Time to run the (?:file-level )?regression test selection) \(s\): "
               rf"{_NUM} ms \((?P<v>{_NUM}) (?P<u>s)\)")
DEFAULT_RTP = (r"(?P<k>Time to run the regression test prioritization) \(s\): "
               rf"{_NUM} ms \((?P<v>{_NUM}) (?P<u>s)\)"
               r"|(?P<k2>Time to (?:reorder tests|compute test-change similarity|collect test features))"
               rf" \(s\): (?P<v2>{_NUM})\s*$")

ID_FIELDS = ["repo", "mutant", "workflow", "mode", "rep", "phase", "run_id", "job_id", "conclusion"]
VALUE_FIELDS = ["tsr_s", "suite_s", "job_s", "wf_s", "rts_s", "rtp_s", "n_tests", "n_failed", "faults", "flaky",
                "detected", "hidden", "hidden_not_selected", "detected_pct", "hidden_pct",
                "ttff_s", "ttff_pos", "apfdc", "plugin_only", "internalerror", "has_reportlog",
                "rts_skipped", "rtp_skipped"]
FIELDS = ID_FIELDS + VALUE_FIELDS

# Avisos do pytest-regsmart (runner.py) em que a etapa não roda, e por isso o resumo
# não imprime o tempo dela: o tempo da etapa é 0, não ausente (sem isso o TTFF da leg
# também sai vazio). Ex.: trimesh m13478 seleciona 1 teste -> "RTP skipped".
RTS_SKIPPED = re.compile(r"WARNING: (?:No diff detected in Python files|conftest\.py changed|"
                         r"No shared history with base branch|RTS and RTP skipped|"
                         r"Regression test selection failed)")
RTP_SKIPPED = re.compile(r"WARNING: (?:RTP skipped|RTS and RTP skipped|Test prioritization failed)")
FAULT_METRICS = ("detected", "hidden", "hidden_not_selected", "detected_pct", "hidden_pct",
                 "ttff_s", "ttff_pos", "apfdc")

# (campo, título, casas decimais)
METRICS = [
    ("tsr_s", "TSR time (s)", 2),
    ("suite_s", "Tempo de execução da suíte (s)", 2),
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
RATIO_METRICS = {"tsr_s", "suite_s", "job_s", "ttff_s"}
CONTROL = "control"  # mutante de controle do flaky_runner (`run --control`)
# Linha final de uma sessão do pytest, ancorada (não casa com texto citado em mensagens).
FINAL_LINE = re.compile(r"^(?:=+ )?(?:\d+ (?:failed|passed|errors?|skipped|deselected|xfailed|"
                        r"xpassed|warnings?|rerun)\b.*|no tests ran) in (?P<s>[\d.]+)s"
                        r"(?: \(\d+:\d\d:\d\d\))?(?: =+)?$")


def mdir(c: Campaign) -> Path:
    return c.dir / "metrics"


def secs(a, b):
    return (parse_ts(b) - parse_ts(a)).total_seconds() if a and b else None


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def gh_bytes(path: str):
    """`gh api` com o TOKEN do script: o gh não lê GITHUB_TOKEN_REGSMART."""
    env = dict(os.environ)
    if TOKEN:
        env["GH_TOKEN"] = TOKEN
    res = subprocess.run(["gh", "api", path], capture_output=True, env=env)
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
    """pytest-reportlog (jsonl) -> (ordem dos nodeids, duração por teste, nodeids que falharam,
    tempos). tempos = {"first_start": menor `start`, "fail_stop": {nodeid: `stop` da 1ª falha}}."""
    order, dur, failed, seen = [], {}, set(), set()
    first_start, fail_stop = None, {}
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
            start, stop = o.get("start"), o.get("stop")
            # `start`/`stop` vêm de time.time(): testes que congelam o relógio (time-machine,
            # freezegun, no apscheduler) geram valores falsos. Só vale o par coerente com a
            # `duration`, que vem de um relógio monotônico.
            d = float(o.get("duration") or 0)
            if start is None or stop is None or abs((stop - start) - d) > max(1.0, 0.1 * d):
                start = stop = None
            if start is not None and (first_start is None or start < first_start):
                first_start = start
            if o.get("outcome") == "failed":  # setup/call/teardown
                failed.add(nid)
                if stop is not None and (nid not in fail_stop or stop < fail_stop[nid]):
                    fail_stop[nid] = stop
        elif kind == "CollectReport" and o.get("outcome") == "failed":
            failed.add(o.get("nodeid") or "<collect>")
    return order, dur, failed, {"first_start": first_start, "fail_stop": fail_stop}


def read_artifact(path):
    if not path or not Path(path).exists():
        return None
    with zipfile.ZipFile(path) as z:
        name = next((n for n in z.namelist() if n.endswith(".jsonl")), None)
        return read_reportlog(z.read(name)) if name else None


def job_log(zlog, job_name: str, started_at: str | None = None) -> str:
    """Log de um job dentro do zip de logs do run.

    Se vários jobs têm o mesmo nome (matriz cujo nome não inclui a versão, como no aeon),
    escolhe o arquivo cuja primeira linha tem o timestamp mais perto de ``started_at``."""
    if not zlog or not Path(zlog).exists():
        return ""
    key = norm(job_name)
    with zipfile.ZipFile(zlog) as z:
        texts = [z.read(n).decode("utf-8", "replace") for n in z.namelist()
                 if "/" not in n and norm(re.sub(r"^\d+_", "", n).removesuffix(".txt")) == key]
    if len(texts) <= 1 or not started_at:
        return texts[0] if texts else ""
    t0 = parse_ts(started_at).timestamp()

    def gap(text):
        m = re.match(r"^\ufeff?(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)", text)
        return abs(parse_ts(m.group(1) + "Z").timestamp() - t0) if m else float("inf")

    best = min(texts, key=gap)
    return best if gap(best) <= 120 else ""


def suite_time(text: str):
    """Tempo da sessão principal do pytest (s): o "in Xs" da última linha final do log.

    A última, porque testes que rodam um pytest filho imprimem as linhas finais do filho
    antes, no meio das falhas."""
    last = None
    for line in text.splitlines():
        line = re.sub(r"^\S+Z ", "", re.sub(r"\x1b\[[0-9;]*m", "", line)).strip()
        m = FINAL_LINE.match(line)
        if m:
            last = float(m.group("s"))
    return last


def plugin_time(text: str, rx: re.Pattern):
    """Soma dos tempos do plugin (s): última ocorrência de cada chave.

    RTS do regsmart = seleção por função + seleção por arquivo (quando há fallback);
    RTP do pytest-ranking = similaridade + coleta de features + reordenação.
    Sem grupo `k`, vale só a última ocorrência (regex antigo passado por --rts-re).
    """
    by_key = {}
    for line in text.splitlines():
        line = re.sub(r"^\S+Z ", "", line).rstrip()
        for m in rx.finditer(line):
            g = {k: v for k, v in m.groupdict().items() if v is not None}
            key = g.get("k") or g.get("k2") or "_"
            v = g.get("v") or g.get("v2")
            if v is None:
                continue
            v = float(v)
            by_key[key] = v / 1000 if (g.get("u") or "s").lower() == "ms" else v
    return sum(by_key.values()) if by_key else None


def leg_metrics(order, dur, failed, faults, times=None, overhead=0.0) -> dict:
    """Métricas de uma execução dado o conjunto de faltas esperadas do mutante.

    overhead = RTS + RTP da execução (s), somado ao TTFF; None = tempo do plugin esperado
    mas não encontrado no log, e aí o TTFF fica vazio."""
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
        ttff_s=ttff(times, detected, overhead),
        ttff_pos=positions[0] + 1 if positions else None,
        apfdc=num / (total * m) if total > 0 else None,
    )
    return out


def ttff(times, detected, overhead):
    """RTS + RTP + (fim da 1ª falta detectada - início do 1º teste), em segundos."""
    if not times or overhead is None or times.get("first_start") is None:
        return None
    stops = [times["fail_stop"][f] for f in detected if f in times["fail_stop"]]
    if not stops:
        return None
    return overhead + (min(stops) - times["first_start"])


# ---------------------------------------------------------------- coleta

def last_final_ts(text: str):
    """Timestamp (datetime) da última linha final do pytest no log do job, ou None."""
    last = None
    for line in text.splitlines():
        line = re.sub(r"\x1b\[[0-9;]*m", "", line)
        m = re.match(r"^(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)(?:\.\d+)?Z (.*)$", line)
        if m and FINAL_LINE.match(m.group(2).strip()):
            last = parse_ts(m.group(1) + "Z")
    return last


def python_version(text: str):
    """Versão do Python (\"3.13\") da sessão pytest, pelo cabeçalho \"platform ... -- Python X.Y.Z\"."""
    m = (re.search(r"platform \S+ -- Python (\d+\.\d+)", text)
         or re.search(r"Successfully set up CPython \((\d+\.\d+)", text)
         or re.search(r"python-version:\s*['\"]?(\d+\.\d+)", text))
    return m.group(1) if m else None


def label_for(job_name: str, suffixes: set):
    """Label do job: o sufixo de artifact que aparece como token no nome (o mais longo);
    sem isso, o conteúdo do último parêntese; sem parêntese, \"main\"."""
    hits = [s for s in suffixes if s and re.search(rf"(?<![A-Za-z0-9_]){re.escape(s)}(?![A-Za-z0-9_])", job_name)]
    if hits:
        return max(hits, key=len)
    m = re.findall(r"\(([^()]*)\)", job_name)
    return m[-1] if m else "main"


def build_legs(api: Api, c: Campaign, r: dict, step_rx: re.Pattern, pyver: dict | None = None) -> list[dict]:
    """Baixa (com cache) jobs, logs e artifacts de um run e devolve um dict por leg.

    Casamento job <-> artifact robusto aos formatos dos forks:
    * job de teste = job cujo log tem a linha final do pytest (o step de teste é o que
      contém o timestamp dessa linha); sem log, cai no regex --test-step;
    * label = sufixo do artifact presente no nome do job (``regsmart (rgsm_qtf) py313-...``),
      ou o único sufixo do run, ou o último parêntese;
    * vários artifacts com o mesmo nome (matriz de Python no aeon, ``reportlog-`` vazio no
      pytorch-lightning): cada um vai para o job cujo step de upload contém o created_at
      do artifact (ou o job terminado mais perto dele);
    * ``pyver[repo]`` (``--python aeon=3.13``) descarta legs de outras versões do Python.
    """
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
    arts = [a for a in arts if a["name"].startswith(ART_PREFIX) and not a.get("expired")]
    suffixes = {a["name"][len(ART_PREFIX):] for a in arts}

    def log_of(j) -> Path | None:
        """Log do job salvo em cache: sai do zip do run (nome repetido: pelo horário de
        início); se não estiver lá, log individual do job pela API."""
        f = d / f"job-{j['id']}.txt"
        if not f.exists():
            text = job_log(zlog, j["name"], j.get("started_at"))
            if not text:
                raw = gh_bytes(f"repos/{OWNER}/{r['repo']}/actions/jobs/{j['id']}/logs")
                text = raw.decode("utf-8", "replace") if raw else ""
            if not text:
                return None
            f.write_text(text, encoding="utf-8")
        return f

    def within(ts, s, pad_before=1, pad_after=1):
        if not (ts and s.get("started_at") and s.get("completed_at")):
            return False
        return (parse_ts(s["started_at"]).timestamp() - pad_before <= ts.timestamp()
                <= parse_ts(s["completed_at"]).timestamp() + pad_after)

    cands = []
    for j in jobs:
        if j.get("conclusion") not in ("success", "failure"):
            continue
        steps = j.get("steps") or []
        lf = log_of(j)
        text = lf.read_text(encoding="utf-8") if lf else ""
        fin = last_final_ts(text)
        step = next((s for s in steps if within(fin, s)), None) if fin else None
        if step is None and not text:  # sem log: só o regex do nome do step
            step = next((s for s in steps if step_rx.search(s["name"])), None)
        if step is None:  # job sem sessão pytest (lint, check, package...) fica de fora
            continue
        ver = python_version(text)
        want = (pyver or {}).get(r["repo"])
        if want and ver != want:
            if ver is None:
                print(f"\n  ! {r['repo']} run {r['run_id']}: versão do Python não achada no log de "
                      f"'{j['name']}', leg descartada pelo --python")
            continue
        only = next(iter(suffixes)) if len(suffixes) == 1 else None
        label = only if only else label_for(j["name"], suffixes)
        cands.append(dict(job=j, step=step, log=lf, label=label, pyver=ver))

    # Artifacts -> jobs. Por label; se houver mais de um artifact (ou job) com o mesmo
    # label, desempata pelo horário do upload.
    by_suffix = collections.defaultdict(list)
    for a in arts:
        by_suffix[a["name"][len(ART_PREFIX):]].append(a)
    used = set()
    for cd in cands:
        # artifact sem sufixo ("reportlog-", matrix.mode vazio): vale para qualquer label
        named = by_suffix.get(cd["label"]) or by_suffix.get("", [])
        pool = [a for a in named if a["id"] not in used]
        if not pool and len(arts) == 1 and len(cands) == 1:
            pool = arts
        if not pool:
            cd["art"] = None
            continue
        if len(pool) == 1 and len(named) <= 1:
            cd["art"] = pool[0]
        else:
            up = [s for s in cd["job"].get("steps") or [] if re.search(r"(?i)upload", s["name"])]
            in_up = [a for a in pool if any(within(parse_ts(a["created_at"]), s, 5, 30) for s in up)]
            if in_up:
                cd["art"] = in_up[0]
            else:
                end = parse_ts(cd["job"]["completed_at"]).timestamp()
                cd["art"] = min(pool, key=lambda a: abs(parse_ts(a["created_at"]).timestamp() - end))
        used.add(cd["art"]["id"])

    # O nome do modo (workflow ou workflow:label) é decidido depois, em cmd_collect,
    # olhando todas as execuções do workflow: se uma perna for cancelada ou perder o
    # artifact num run, o modo não muda de nome só naquele run.
    legs, seen = [], set()
    for cd in cands:
        j, step, label = cd["job"], cd["step"], cd["label"]
        if label in seen:
            print(f"\n  ! {r['repo']} run {r['run_id']}: dois jobs com label '{label}', ignorando o 2º "
                  f"({j['name']}; use --python {r['repo']}=X.Y se for matriz de versões)")
            continue
        seen.add(label)
        leg = {
            "repo": r["repo"], "mutant": r["mutant"], "workflow": r["workflow"],
            "label": label,
            "rep": r["rep"], "phase": r["phase"], "run_id": r["run_id"], "job_id": j["id"],
            "conclusion": j["conclusion"], "job_name": j["name"], "python": cd["pyver"],
            "tsr_s": secs(step.get("started_at"), step.get("completed_at")),
            "job_s": secs(j.get("started_at"), j.get("completed_at")),
            "wf_s": wf_s, "zlog": str(zlog) if zlog.exists() else None,
            "log": str(cd["log"]) if cd["log"] else None, "reportlog": None,
            "artifact_id": (cd.get("art") or {}).get("id"),
        }
        art = cd.get("art")
        if art:
            p = d / f"{ART_PREFIX}{art['id']}.zip"
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
    pyver = dict(kv.split("=", 1) for kv in (args.python or []))
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
        legs += build_legs(api, c, r, step_rx, pyver)
        print(f"  {i}/{len(runs)} runs, {len(legs)} legs", end="\r")
    print()
    labels = collections.defaultdict(set)
    for leg in legs:
        labels[(leg["repo"], leg["workflow"])].add(leg["label"])
    for leg in legs:
        one = len(labels[(leg["repo"], leg["workflow"])]) == 1
        leg["mode"] = leg["workflow"] if one else f"{leg['workflow']}:{leg['label']}"

    # Passo 1: faltas esperadas e flaky de cada mutante, a partir do baseline.
    base_failed = collections.defaultdict(list)
    for leg in legs:
        if leg["workflow"] == "baseline":
            data = read_artifact(leg["reportlog"])
            if data:
                base_failed[(leg["repo"], leg["mutant"])].append(data[2])
    # Controle: o que falha na branch default (qualquer modo) é ambiente, não falta.
    env = collections.defaultdict(set)
    for leg in legs:
        if leg["mutant"] == CONTROL:
            data = read_artifact(leg["reportlog"])
            if data:
                env[leg["repo"]] |= data[2]
    truth = {}
    for key, sets in base_failed.items():
        if key[1] == CONTROL:
            continue
        if len(sets) >= 2:
            faults = set.intersection(*sets) - env[key[0]]
            truth[key] = (faults, set.union(*sets) - faults - env[key[0]])
    # o controle nunca entra em `truth` (não tem faltas próprias): não é mutante pulado
    skipped = sorted(k for k in base_failed if k not in truth and k[1] != CONTROL)
    no_base = sorted({(leg["repo"], leg["mutant"]) for leg in legs if leg["mutant"] != CONTROL}
                     - set(base_failed))
    if skipped or no_base:
        names = ", ".join(f"{r}/{m}" for r, m in skipped + no_base)
        print(f"  ! {len(skipped) + len(no_base)} mutante(s) com < 2 repetições de baseline com "
              f"report-log: sem métricas de falta ({names})")

    # Passo 2: métricas por leg.
    rows, miss, skipped_steps = [], collections.Counter(), collections.Counter()
    for leg in legs:
        if leg["mutant"] == CONTROL:
            continue
        text = (Path(leg["log"]).read_text(encoding="utf-8") if leg.get("log")
                else job_log(leg["zlog"], leg["job_name"]))
        data = read_artifact(leg["reportlog"])
        row = {k: leg[k] for k in ID_FIELDS}
        row.update(tsr_s=leg["tsr_s"], suite_s=suite_time(text), job_s=leg["job_s"], wf_s=leg["wf_s"],
                   internalerror=int("INTERNALERROR" in text), has_reportlog=int(data is not None))
        if leg["workflow"].startswith("regsmart"):
            row["rts_s"] = plugin_time(text, rts_rx)
            if row["rts_s"] is None and RTS_SKIPPED.search(text):
                row.update(rts_s=0.0, rts_skipped=1)
                skipped_steps["rts"] += 1
            miss["rts"] += row["rts_s"] is None
        if leg["workflow"] in ("ranking", "regsmart"):
            row["rtp_s"] = plugin_time(text, rtp_rx)
            if (row["rtp_s"] is None and leg["workflow"] == "regsmart"
                    and RTP_SKIPPED.search(text)):
                row.update(rtp_s=0.0, rtp_skipped=1)
                skipped_steps["rtp"] += 1
            miss["rtp"] += row["rtp_s"] is None
        if leg["tsr_s"] is None:
            miss["tsr"] += 1
        t = truth.get((leg["repo"], leg["mutant"]))
        if data:
            order, dur, failed, times = data
            if t:
                parts = [row.get("rts_s") if leg["workflow"].startswith("regsmart") else 0.0,
                         row.get("rtp_s") if leg["workflow"] in ("ranking", "regsmart") else 0.0]
                overhead = None if None in parts else sum(parts)
                row.update(leg_metrics(order, dur, failed, t[0], times, overhead))
                row.update(faults=len(t[0]), flaky=len(t[1]),
                           plugin_only=len(failed - t[0] - t[1] - env[leg["repo"]]))
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
    for repo, tests in sorted(env.items()):
        tj.setdefault(repo, {})["_" + CONTROL] = {"ambiente": sorted(tests)}
    save_json(out / "faults.json", tj)
    print(f"\n{len(rows)} legs -> {out / 'runs.csv'}; faltas/flaky por mutante -> {out / 'faults.json'}")
    if skipped_steps:
        print(f"etapas puladas pelo plugin (tempo = 0, coluna rts_skipped/rtp_skipped): "
              f"{dict(skipped_steps)}")
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
    common.add_argument("--exclude-warmup", action=argparse.BooleanOptionalAction, default=True,
                        help="ignora os runs de warm-up (padrão; cache frio distorce TSR/APFDc). "
                             "--no-exclude-warmup inclui")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("collect", parents=[common], help="baixa e calcula as métricas por leg")
    s.add_argument("--test-step", default=DEFAULT_TEST_STEP,
                   help="regex do nome do step de teste; só usado quando o job não tem log")
    s.add_argument("--python", action="append", metavar="REPO=X.Y",
                   help="mantém só os jobs dessa versão do Python no repo (ex.: aeon=3.13; repetível)")
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
