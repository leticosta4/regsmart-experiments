"""
Flaky runner (v2): dispara repetições dos workflows de cada MUTANTE e acha
quais testes falham de forma intermitente.

Mudanças em relação à v1 (que rodava na `track-flaky`, sem mutação):
  - o alvo agora é cada branch `mut-<repo>-mNNNN` (lida de
    data/mutmut/mutant_branches.json, só as `published`);
  - roda TODOS os workflows configurados (baseline, pytest-ranking,
    pytest-regsmart, regsmart --no-rank), não só o de teste original;
  - não existem mais as branches `flaky-rNN`: as repetições de um mesmo
    (mutante, workflow) rodam em sequência, na própria branch do mutante
    ("lane"), então o `concurrency` não cancela nada e o cache do Actions
    fica no escopo da branch do mutante;
  - opcionalmente roda uma execução de aquecimento (warm-up) antes das
    repetições, pra popular o cache do QTF/RecentFail.

Uso (todos aceitam --repo/--mutant/--workflow, repetíveis, e --reps):

  python flaky_runner.py verify          # confere dispatch, push, concurrency, cache
  python flaky_runner.py run --dry-run   # mostra o plano
  python flaky_runner.py run             # dispara e espera (lanes sequenciais)
  python flaky_runner.py status          # progresso, sem API
  python flaky_runner.py flaky           # baixa logs e acha testes flaky
  python flaky_runner.py report          # gera relatório markdown

O `experiment_runner.py` usa este mesmo motor com outros padrões (3 reps +
warm-up) e outro diretório de dados.

Acima de 20 jobs simultâneos (plano Free) o GitHub enfileira sozinho;
`--max-active` limita quantos runs ficam em andamento ao mesmo tempo, o que
também reduz o tempo de fila embutido nas medições de makespan.
"""

import argparse
import base64
import collections
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

OWNER = "leticosta4"
API = "https://api.github.com"
ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
REPO_PLAN_PATH = DATA / "flaky_mut" / "flaky_plan.json"  # repos + workflow baseline (já existe)
WORKFLOW_PLAN_PATH = DATA / "workflow_plan.json"  # opcional: arquivos dos workflows por modo
BRANCHES_PATH = DATA / "mutmut" / "mutant_branches.json"  # gerado pelo insert_mutations.py

FREE_PLAN_JOBS = 20
ACTIVE = {"in_progress", "queued", "waiting", "pending", "requested"}
LOST_AFTER_S = 15 * 60  # dispatch feito e nenhum run apareceu: dá o run como perdido

# Um diretório de dados por campanha: os manifestos não se misturam.
CAMPAIGNS = {
    "flaky": {"dir": DATA / "flaky_mut", "reps": 3, "warmup": False, "title": "Flaky runner"},
    "experiment": {"dir": DATA / "experiment", "reps": 3, "warmup": True, "title": "Experimento"},
}

# `file: None` no baseline = usa o `workflow_file` do flaky_plan.json.
# `warmup: true` = o workflow usa cache do Actions (QTF/RecentFail) e ganha
# uma execução prévia. Ajuste os nomes em data/workflow_plan.json.
DEFAULT_WORKFLOWS = {
    "baseline": {"file": None, "warmup": False},
    "ranking": {"file": "pytest-ranking.yml", "warmup": True},
    "regsmart": {"file": "pytest-regsmart.yml", "warmup": True},
    "regsmart-no-rank": {"file": "regsmart-no-rank.yml", "warmup": False},
}

STATIC_FIELDS = ("task", "repo", "mutant", "ref", "sha", "workflow", "workflow_file",
                 "phase", "rep", "lane")


class Campaign:
    def __init__(self, name: str):
        cfg = CAMPAIGNS[name]
        self.name = name
        self.title = cfg["title"]
        self.reps = cfg["reps"]
        self.warmup = cfg["warmup"]
        self.dir = cfg["dir"]
        self.raw = self.dir / "raw"
        self.manifest_path = self.dir / "runs.json"
        self.flaky_path = self.dir / "flaky_tests.json"
        self.report_path = self.dir / "report.md"


def _gh_token() -> str | None:
    """Fallback pro token do gh CLI, pra não depender de env var."""
    try:
        out = subprocess.run(
            ["gh", "auth", "token"], capture_output=True, text=True, timeout=15
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout.strip() or None


TOKEN = (
    os.environ.get("GITHUB_TOKEN_REGSMART")
    or os.environ.get("GH_TOKEN")
    or os.environ.get("GITHUB_TOKEN")
    or _gh_token()
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_ts(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


# ---------------------------------------------------------------- API client

class Api:
    """Client REST do GitHub com contadores, retry e backoff."""

    def __init__(self, token: str | None, max_retries: int = 3):
        self.token = token
        self.max_retries = max_retries
        self.counters = {"get": 0, "post": 0, "retries": 0, "rate_limit": 0}

    @property
    def headers(self) -> dict:
        h = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "regsmart-metrics",
        }
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def request(self, method: str, path: str, body: dict | None = None):
        url = f"{API}{path}"
        data = json.dumps(body).encode() if body is not None else None
        self.counters["get" if method == "GET" else "post"] += 1
        delay = 2.0
        for attempt in range(self.max_retries + 1):
            req = urllib.request.Request(
                url, data=data, headers=self.headers, method=method
            )
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    payload = resp.read().decode()
                    return json.loads(payload) if payload else {}
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode()[:200]
                retry_after = exc.headers.get("Retry-After")
                retryable = (
                    exc.code == 429
                    or exc.code >= 500
                    or (exc.code == 403 and (retry_after or "rate limit" in detail.lower()))
                )
                if not retryable or attempt == self.max_retries:
                    raise RuntimeError(
                        f"{method} {url} -> HTTP {exc.code}: {detail}"
                    ) from exc
                wait = float(retry_after) if retry_after else delay
                self.counters["retries"] += 1
                print(f"  ! HTTP {exc.code}, esperando {wait:.0f}s ({attempt + 1})")
                time.sleep(wait)
                delay = min(delay * 2, 60)
            except urllib.error.URLError as exc:
                if attempt == self.max_retries:
                    raise RuntimeError(f"{method} {url} -> {exc.reason}") from exc
                self.counters["retries"] += 1
                time.sleep(delay)
                delay = min(delay * 2, 60)

    def get(self, path: str):
        return self.request("GET", path)

    def post(self, path: str, body: dict | None = None):
        return self.request("POST", path, body=body)

    def rate_limit(self) -> dict:
        self.counters["rate_limit"] += 1
        try:
            core = self.get("/rate_limit")["resources"]["core"]
        except Exception:
            return {}
        return {
            "limit": core["limit"],
            "remaining": core["remaining"],
            "used": core["limit"] - core["remaining"],
            "reset_utc": datetime.fromtimestamp(
                core["reset"], timezone.utc
            ).isoformat(),
        }


# ---------------------------------------------------------------- plano

def save_json(path: Path, payload) -> None:
    """Escrita atômica: tmp + rename, pra não corromper com Ctrl-C."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    tmp.replace(path)


def load_manifest(c: Campaign) -> dict:
    if c.manifest_path.exists():
        return json.loads(c.manifest_path.read_text(encoding="utf-8"))
    return {"created_utc": now(), "campaign": c.name, "runs": []}


def load_repo_plan(only: list[str] | None) -> dict[str, dict]:
    """{repo: entrada do flaky_plan.json}, só os `enabled`, na ordem do arquivo."""
    entries = json.loads(REPO_PLAN_PATH.read_text(encoding="utf-8"))
    if only:
        unknown = set(only) - {e["repo"] for e in entries}
        if unknown:
            sys.exit(f"--repo desconhecido no plan: {', '.join(sorted(unknown))}")
        entries = [e for e in entries if e["repo"] in set(only)]
    return {e["repo"]: e for e in entries if e.get("enabled", True)}


def load_workflow_cfg() -> dict:
    if WORKFLOW_PLAN_PATH.exists():
        return json.loads(WORKFLOW_PLAN_PATH.read_text(encoding="utf-8"))
    print(f"  (sem {WORKFLOW_PLAN_PATH.relative_to(ROOT)}: usando nomes de workflow "
          f"padrão, confira com `verify`)")
    return {}


def workflows_for(cfg: dict, repo_plan: dict[str, dict], only: list[str] | None) -> dict[str, dict]:
    """{repo: {modo: {file, warmup}}}. `overrides` por repo vencem os padrões."""
    base = {k: dict(v) for k, v in DEFAULT_WORKFLOWS.items()}
    for k, v in (cfg.get("workflows") or {}).items():
        base.setdefault(k, {}).update(v)
    out = {}
    for repo, entry in repo_plan.items():
        ws = {k: dict(v) for k, v in base.items()}
        for k, v in ((cfg.get("overrides") or {}).get(repo) or {}).items():
            ws.setdefault(k, {}).update(v)
        if ws["baseline"].get("file") is None:
            ws["baseline"]["file"] = entry["workflow_file"]
        ws = {k: v for k, v in ws.items() if v.get("file") and v.get("enabled", True)}
        if only:
            unknown = set(only) - set(ws)
            if unknown and repo == next(iter(repo_plan)):
                sys.exit(f"--workflow desconhecido: {', '.join(sorted(unknown))} "
                         f"(opções: {', '.join(ws)})")
            ws = {k: v for k, v in ws.items() if k in set(only)}
        out[repo] = ws
    return out


def load_registry() -> dict:
    if not BRANCHES_PATH.exists():
        sys.exit(f"{BRANCHES_PATH} não existe: rode `python insert_mutations.py --mutants --push`")
    return json.loads(BRANCHES_PATH.read_text(encoding="utf-8"))


def select_mutants(registry: dict, repos: list[str], only: list[str] | None,
                   limit: int | None) -> dict[str, list[tuple[str, dict]]]:
    """{repo: [(key, meta)]} só com branches de mutante já publicadas."""
    out = {}
    for repo in repos:
        items = sorted(((registry.get(repo) or {}).get("mutants") or {}).items())
        published = [(k, m) for k, m in items if m.get("published")]
        if len(published) < len(items):
            print(f"  ! {repo}: {len(items) - len(published)} mutante(s) sem `published` "
                  f"no registro, ignorados")
        if only:
            published = [(k, m) for k, m in published if k in only or m["branch"] in only]
        out[repo] = published[:limit] if limit else published
    return out


def task_id(repo: str, who: str, workflow: str, rep: int) -> str:
    return f"{repo}/{who}/{workflow}/r{rep:02d}"


def build_tasks(repos: list[str], workflows: dict, mutants: dict, reps: int, warmup: bool,
                warmup_ref: str, serialize_ref: bool) -> list[dict]:
    """Uma tarefa por run a disparar, já na ordem de cada lane.

    lane = sequência de runs que NÃO podem rodar ao mesmo tempo: por padrão
    (repo, branch, workflow); com `serialize_ref`, (repo, branch) inteiro, pro
    caso de workflows cujo `concurrency` não inclui github.workflow.
    Tarefa só dispara quando todas as `deps` terminaram.
    """
    tasks: list[dict] = []
    last: dict[str, str] = {}  # lane -> última tarefa

    def add(repo, who, ref, sha, w, spec, rep, phase, extra_deps=()):
        lane = f"{repo}@{ref}" if serialize_ref else f"{repo}@{ref}/{w}"
        deps = ([last[lane]] if lane in last else []) + list(extra_deps)
        t = {
            "task": task_id(repo, who, w, rep), "repo": repo, "mutant": None if who.startswith("@") else who,
            "ref": ref, "sha": sha, "workflow": w, "workflow_file": spec["file"],
            "phase": phase, "rep": rep, "lane": lane, "deps": deps,
        }
        tasks.append(t)
        last[lane] = t["task"]
        return t["task"]

    for repo in repos:
        base_warm: dict[str, str] = {}
        if warmup and warmup_ref != "mutant":
            for w, spec in workflows[repo].items():
                if spec.get("warmup"):
                    base_warm[w] = add(repo, f"@{warmup_ref}", warmup_ref, None, w, spec, 0, "warmup")
        for key, m in mutants.get(repo, []):
            for w, spec in workflows[repo].items():
                if warmup and spec.get("warmup") and warmup_ref == "mutant":
                    add(repo, key, m["branch"], m["head_sha"], w, spec, 0, "warmup")
                for rep in range(1, reps + 1):
                    deps = [base_warm[w]] if w in base_warm else []
                    add(repo, key, m["branch"], m["head_sha"], w, spec, rep, "rep", deps)
    return tasks


def sync_rows(manifest: dict, tasks: list[dict]) -> dict[str, dict]:
    rows = {r["task"]: r for r in manifest["runs"]}
    for t in tasks:
        if t["task"] not in rows:
            r = {k: t[k] for k in STATIC_FIELDS}
            manifest["runs"].append(r)
            rows[t["task"]] = r
    return rows


# ---------------------------------------------------------------- GitHub helpers

_WF_IDS: dict[tuple[str, str], int] = {}


def resolve_sha(api: Api, repo: str, branch: str) -> str:
    data = api.get(f"/repos/{OWNER}/{repo}/branches/{urllib.parse.quote(branch, safe='')}")
    return data["commit"]["sha"]


def workflow_id(api: Api, repo: str, workflow_file: str) -> int:
    key = (repo, workflow_file)
    if key not in _WF_IDS:
        _WF_IDS[key] = api.get(
            f"/repos/{OWNER}/{repo}/actions/workflows/{urllib.parse.quote(workflow_file)}"
        )["id"]
    return _WF_IDS[key]


def list_runs(api: Api, repo: str) -> list[dict]:
    return api.get(
        f"/repos/{OWNER}/{repo}/actions/runs?event=workflow_dispatch&per_page=100"
    ).get("workflow_runs", [])


def dispatch(api: Api, repo: str, workflow_file: str, ref: str) -> None:
    path = urllib.parse.quote(workflow_file)
    api.post(f"/repos/{OWNER}/{repo}/actions/workflows/{path}/dispatches", {"ref": ref})


def is_done(row: dict) -> bool:
    return bool(row.get("dispatch_failed") or row.get("status") == "completed")


def refresh(api: Api, manifest: dict) -> None:
    """Acha o run_id das tarefas despachadas e atualiza status/conclusão.

    Como cada lane é sequencial, o único run novo de (workflow, branch) depois
    do dispatch é o da tarefa: casa por workflow_id + head_branch + created_at.
    Jobs só são buscados uma vez, quando o run termina.
    """
    rows = manifest["runs"]
    watch = [r for r in rows if r.get("dispatched_at_utc")
             and not (r.get("status") == "completed" and "jobs" in r)]
    claimed = {r["run_id"] for r in rows if r.get("run_id")}
    for repo in sorted({r["repo"] for r in watch}):
        listed = list_runs(api, repo)
        by_id = {x["id"]: x for x in listed}
        for r in (r for r in watch if r["repo"] == repo):
            if not r.get("run_id"):
                wid = workflow_id(api, repo, r["workflow_file"])
                since = parse_ts(r["dispatch_window_start_utc"]).timestamp() - 2
                hits = sorted(
                    (x for x in listed
                     if x["workflow_id"] == wid and x["head_branch"] == r["ref"]
                     and x["id"] not in claimed
                     and parse_ts(x["created_at"]).timestamp() >= since),
                    key=lambda x: x["created_at"],
                )
                if not hits:
                    waited = time.time() - parse_ts(r["dispatched_at_utc"]).timestamp()
                    if waited > LOST_AFTER_S:
                        r["dispatch_failed"] = True
                        r["dispatch_error"] = f"nenhum run apareceu em {LOST_AFTER_S // 60} min"
                    continue
                r["run_id"] = hits[0]["id"]
                r["html_url"] = hits[0]["html_url"]
                claimed.add(r["run_id"])
            run = by_id.get(r["run_id"]) or api.get(
                f"/repos/{OWNER}/{repo}/actions/runs/{r['run_id']}"
            )
            r["status"] = run["status"]
            r["conclusion"] = run["conclusion"]
            r["run_attempt"] = run["run_attempt"]
            r["conclusion_at_utc"] = run["updated_at"]
            r["html_url"] = run["html_url"]
            if run["status"] == "completed" and "jobs" not in r:
                jobs = api.get(
                    f"/repos/{OWNER}/{repo}/actions/runs/{r['run_id']}/jobs?per_page=100"
                )
                r["jobs_total"] = jobs.get("total_count", 0)
                r["jobs"] = [
                    {
                        "name": j["name"],
                        "conclusion": j["conclusion"],
                        "started_at": j["started_at"],
                        "completed_at": j["completed_at"],
                    }
                    for j in jobs.get("jobs", [])
                ]


def flush_counters(api: Api, manifest: dict) -> None:
    """Soma os contadores desta execução no manifest (acumula entre execuções)."""
    total = manifest.setdefault("counters", {})
    for key, value in api.counters.items():
        total[key] = total.get(key, 0) + value
        api.counters[key] = 0


def reset_row(r: dict) -> None:
    """Zera uma tarefa pra ser despachada de novo, guardando o histórico."""
    r.setdefault("history", []).append({
        k: r.get(k) for k in ("run_id", "html_url", "status", "conclusion", "dispatched_at_utc",
                              "dispatch_error")
    })
    for k in ("run_id", "html_url", "status", "conclusion", "run_attempt", "conclusion_at_utc",
              "jobs", "jobs_total", "dispatched_at_utc", "dispatch_window_start_utc",
              "dispatch_error", "dispatch_failed", "dispatch_attempts"):
        r.pop(k, None)


# ---------------------------------------------------------------- custo

def fmt_hms(seconds: float | None) -> str:
    if seconds is None:
        return "-"
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h:d}h{m:02d}m{s:02d}s" if h else f"{m:d}m{s:02d}s"


def job_intervals(runs: list[dict]) -> list[tuple[float, float]]:
    """Intervalos (início, fim) reais de cada job que rodou."""
    out = []
    for r in runs:
        for job in r.get("jobs") or []:
            start, end = job.get("started_at"), job.get("completed_at")
            if not start or not end:
                continue
            try:
                out.append((parse_ts(start).timestamp(), parse_ts(end).timestamp()))
            except ValueError:
                continue
    return out


def peak_concurrency(intervals: list[tuple[float, float]]) -> int:
    """Maior número de jobs sobrepostos no tempo (sweep line)."""
    events = []
    for start, end in intervals:
        events.append((start, 1))
        events.append((end, -1))
    events.sort(key=lambda e: (e[0], -e[1]))
    best = cur = 0
    for _, delta in events:
        cur += delta
        best = max(best, cur)
    return best


def runner_minutes(intervals: list[tuple[float, float]]) -> float:
    """Minutos de runner somados (um job de 3 min em 2 jobs = 6 min)."""
    return round(sum(e - s for s, e in intervals) / 60, 1)


def span(rows: list[dict]) -> float | None:
    fin = [r["conclusion_at_utc"] for r in rows if r.get("conclusion_at_utc")]
    sta = [r["dispatched_at_utc"] for r in rows if r.get("dispatched_at_utc")]
    if not (fin and sta):
        return None
    return (parse_ts(max(fin)) - parse_ts(min(sta))).total_seconds()


WF_ORDER = ["baseline", "ranking", "regsmart", "regsmart-no-rank"]
MAX_ROWS = 40  # linhas de detalhe por mutante; o resto fica no flaky_tests.json
LEGEND = [
    ("flaky", "falha em algumas execuções do baseline e passa em outras"),
    ("só no plugin (flaky)", "baseline nunca falhou; falha às vezes sob plugin (provável dependência de ordem exposta pelo reordenamento)"),
    ("só no plugin (fixa)", "baseline nunca falhou; falha em todas as execuções de algum plugin (investigar o plugin)"),
    ("esperada, diverge", "falha sempre no baseline, mas não em todos os workflows (RTS não selecionou ou a ordem mudou o resultado)"),
    ("esperada", "falha sempre em todos os workflows: efeito do mutante (ou falha pré-existente); só contada"),
    ("indeterminado / sem baseline", "poucas execuções ou baseline ausente"),
]


def flaky_section(flaky: dict, show_expected: bool) -> list[str]:
    if not flaky:
        return ["_Análise de logs ainda não rodada. Use `flaky`._"]
    L = ["Cada teste que falhou é classificado comparando o **baseline** com os workflows de "
         "plugin, no mesmo SHA do mutante. Células = falhas/execuções (do job que mais falhou).",
         "", "| classe | significado |", "|---|---|"]
    L += [f"| {k} | {v} |" for k, v in LEGEND]
    L += ["", "### Resumo", "",
          "| repo | mutante | flaky | só plugin (flaky) | só plugin (fixa) | esperada, diverge | esperada | outros |",
          "|---|---|---|---|---|---|---|---|"]
    for repo, muts in sorted(flaky.items()):
        for mut, info in sorted(muts.items()):
            k = collections.Counter(t["class"] for t in info["tests"].values())
            L.append(f"| {repo} | {mut} | {k['flaky']} | {k['só no plugin (flaky)']} | "
                     f"{k['só no plugin (fixa)']} | {k['esperada, diverge']} | {k['esperada']} | "
                     f"{k['indeterminado'] + k['sem baseline']} |")
    combos = sorted({k for muts in flaky.values() for info in muts.values()
                     for k in plugin_breakdown(info["tests"])}, key=_combo_key)
    if combos:
        L += ["", "### Só no plugin: em quais workflows falhou", "",
              "Testes que nunca falharam no baseline (flaky + fixa), cada um contado uma vez, "
              "na combinação exata de workflows em que falhou. `ranking+regsmart` = falhou nos dois.", "",
              "| repo | mutante | " + " | ".join(combos) + " | total |",
              "|---|---|" + "---|" * (len(combos) + 1)]
        for repo, muts in sorted(flaky.items()):
            for mut, info in sorted(muts.items()):
                bd = plugin_breakdown(info["tests"])
                L.append(f"| {repo} | {mut} | " + " | ".join(str(bd[k]) for k in combos)
                         + f" | {sum(bd.values())} |")
    for repo, muts in sorted(flaky.items()):
        blocks = []
        for mut, info in sorted(muts.items()):
            rows = [(t["class"], nid, t) for nid, t in info["tests"].items()
                    if show_expected or t["class"] != "esperada"]
            if not rows:
                continue
            rows.sort(key=lambda r: (CLASS_ORDER.index(r[0]), r[1]))
            cols = [w for w in WF_ORDER if w in info["runs"]] + \
                   sorted(w for w in info["runs"] if w not in WF_ORDER)
            blocks += [f"#### {mut}", "", "| teste | " + " | ".join(cols) + " | classe |",
                       "|---|" + "---|" * (len(cols) + 1)]
            for cls, nid, t in rows[:MAX_ROWS]:
                cells = [f"{t['wf'][w]['failed']}/{t['wf'][w]['runs']}" if w in t["wf"]
                         else f"0/{info['runs'][w]}" for w in cols]
                blocks.append(f"| `{nid.replace('|', chr(92) + '|')}` | " + " | ".join(cells) + f" | {cls} |")
            if len(rows) > MAX_ROWS:
                blocks.append(f"| _+{len(rows) - MAX_ROWS} teste(s), ver flaky_tests.json_ |" + " |" * (len(cols) + 1))
            blocks.append("")
        if blocks:
            L += ["", f"### {repo}", ""] + blocks
    return L


def build_report(c: Campaign, manifest: dict, flaky: dict | None,
                 show_expected: bool = False) -> str:
    runs = manifest["runs"]
    sent = [r for r in runs if r.get("dispatched_at_utc")]
    counters = manifest.get("counters", {})
    wall = manifest.get("wall_clock", {})
    intervals = job_intervals(runs)

    L = [
        f"# {c.title} — relatório",
        "",
        "## Custo",
        "",
        f"- Início: `{wall.get('started_utc', '-')}`",
        f"- Fim: `{wall.get('finished_utc', '-')}`",
        f"- Tempo ativo do script: **{fmt_hms(wall.get('total_seconds'))}**",
        f"- Janela real dos runs (1º dispatch → última conclusão): **{fmt_hms(span(runs))}** (inclui fila)",
        f"- Minutos de runner somados: **{runner_minutes(intervals)} min**",
        f"- Pico de concorrência medido: **{peak_concurrency(intervals)}** jobs "
        f"(teto do plano Free: {FREE_PLAN_JOBS})",
        "",
        "## API / rate limit",
        "",
        f"- Requisições: {counters.get('get', 0)} GET, {counters.get('post', 0)} POST",
        f"- Retries: {counters.get('retries', 0)}",
    ]
    rl = (manifest.get("rate_limit") or {}).get("final") or {}
    if rl:
        L.append(
            f"- Rate limit (final): {rl.get('used', '?')}/{rl.get('limit', '?')} "
            f"consumidos, reseta em `{rl.get('reset_utc', '-')}`"
        )

    def n(rows, **kw):
        return sum(1 for r in rows if all(r.get(k) == v for k, v in kw.items()))

    L += [
        "",
        "## Saúde da execução",
        "",
        "| Métrica | warm-up | repetições |",
        "|---|---|---|",
    ]
    for label, fn in [
        ("Tarefas no plano", lambda rs: len(rs)),
        ("Despachadas", lambda rs: sum(1 for r in rs if r.get("dispatched_at_utc"))),
        ("Com run_id", lambda rs: sum(1 for r in rs if r.get("run_id"))),
        ("Sucesso", lambda rs: n(rs, conclusion="success")),
        ("Falha (testes falharam)", lambda rs: n(rs, conclusion="failure")),
        ("Canceladas", lambda rs: n(rs, conclusion="cancelled")),
        ("Em andamento", lambda rs: sum(1 for r in rs if r.get("status") in ACTIVE)),
        ("Dispatch falhou / run perdido", lambda rs: sum(1 for r in rs if r.get("dispatch_failed"))),
    ]:
        L.append(f"| {label} | {fn([r for r in runs if r['phase'] == 'warmup'])} | "
                 f"{fn([r for r in runs if r['phase'] == 'rep'])} |")

    L += ["", "## Por repositório", "",
          "| repo | runs | success | failure | cancelled | em andamento | makespan | min runner |",
          "|---|---|---|---|---|---|---|---|"]
    for repo in sorted({r["repo"] for r in sent}):
        rows = [r for r in sent if r["repo"] == repo]
        L.append("| " + " | ".join([
            repo, str(len(rows)), str(n(rows, conclusion="success")),
            str(n(rows, conclusion="failure")), str(n(rows, conclusion="cancelled")),
            str(sum(1 for r in rows if r.get("status") in ACTIVE)),
            fmt_hms(span(rows)), str(runner_minutes(job_intervals(rows))),
        ]) + " |")

    L += ["", "## Por workflow", "", "| workflow | runs | min runner |", "|---|---|---|"]
    for w in sorted({r["workflow"] for r in sent}):
        rows = [r for r in sent if r["workflow"] == w]
        L.append(f"| {w} | {len(rows)} | {runner_minutes(job_intervals(rows))} |")

    L += ["", "## Testes flaky", ""]
    L += flaky_section(flaky, show_expected)
    L.append("")

    bad = [r for r in runs if r.get("conclusion") == "cancelled"]
    if bad:
        L += ["## Canceladas (investigar; `run --redo` redispara)", "",
              "| repo | mutante | workflow | rep | run_id |", "|---|---|---|---|---|"]
        for r in bad:
            L.append(f"| {r['repo']} | {r.get('mutant') or r['ref']} | {r['workflow']} | "
                     f"r{r['rep']:02d} | {r.get('run_id', '-')} |")
        L.append("")
    lost = [r for r in runs if r.get("dispatch_failed")]
    if lost:
        L += ["## Dispatch falhou / run perdido", "",
              "| repo | mutante | workflow | rep | erro |", "|---|---|---|---|---|"]
        for r in lost:
            L.append(f"| {r['repo']} | {r.get('mutant') or r['ref']} | {r['workflow']} | "
                     f"r{r['rep']:02d} | {str(r.get('dispatch_error', '-'))[:80]} |")
        L.append("")
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- flaky (logs)

ANSI = re.compile(r"\x1b\[[0-9;]*m")
TS = re.compile(r"^\d{4}-\d\d-\d\dT[\d:.]+Z ")
FAILED = re.compile(r"^(?:FAILED|ERROR) (.+?)(?: - .*)?$")
SUMMARY = re.compile(r"\d+ (?:failed|passed|errors?).* in [\d.:]+s")
NO_TESTS = re.compile(r"no tests ran in [\d.:]+s")  # RTS que não selecionou nada
COUNT = re.compile(r"(\d+) (?:failed|passed|errors?)")


def parse_run(c: Campaign, repo: str, run_id: int) -> list[tuple[str, set, int]]:
    """Por job: (nome do job, nodeids que falharam, total de testes).

    Usa só o que o pytest imprime por padrão: as linhas `FAILED <nodeid>` do
    resumo final e a linha de contagem (`3 failed, 1200 passed in 90s`).
    """
    zpath = c.raw / repo / f"{run_id}.zip"
    if not zpath.exists():
        zpath.parent.mkdir(parents=True, exist_ok=True)
        res = subprocess.run(
            ["gh", "api", f"repos/{OWNER}/{repo}/actions/runs/{run_id}/logs"],
            capture_output=True,
        )
        if res.returncode:
            print(f"  ! {repo} run {run_id}: falha ao baixar log")
            return []
        zpath.write_bytes(res.stdout)
    out = []
    with zipfile.ZipFile(zpath) as z:
        for name in z.namelist():
            if "/" in name:  # só o log completo de cada job (arquivo na raiz do zip)
                continue
            job = re.sub(r"^\d+_", "", name).removesuffix(".txt")
            failed, total, seen = set(), 0, False
            for line in z.read(name).decode(errors="replace").splitlines():
                line = ANSI.sub("", TS.sub("", line.lstrip("\ufeff"))).strip()
                m = FAILED.match(line)
                if m:
                    failed.add(m.group(1))
                elif SUMMARY.search(line):
                    seen = True
                    total += sum(int(n) for n in COUNT.findall(line))
                elif NO_TESTS.search(line):
                    seen = True
            if seen:  # job sem resumo do pytest (lint, infra quebrou) não conta
                out.append((job, failed, total))
    return out


CLASS_ORDER = ["flaky", "só no plugin (flaky)", "só no plugin (fixa)", "esperada, diverge",
               "indeterminado", "sem baseline", "esperada"]


def classify(cells: dict, runs: dict) -> tuple[str, str]:
    """Classifica um teste que falhou em algum workflow, usando o baseline de referência.

    cells = {workflow: {failed, runs, jobs, intermittent}} só dos workflows em que
    o teste falhou; runs = {workflow: nº de execuções analisadas}.
    """
    base = cells.get("baseline")
    plug = {w: c for w, c in cells.items() if w != "baseline"}
    if "baseline" not in runs:
        if any(c["intermittent"] for c in cells.values()):
            return "flaky", "intermitente, mas sem baseline pra comparar"
        return "sem baseline", "baseline não rodou/analisado neste mutante"
    if base and base["intermittent"]:
        return "flaky", "falha em algumas execuções do baseline e passa em outras"
    if base:  # falhou em todas as execuções do baseline
        if runs["baseline"] < 2:
            return "indeterminado", "baseline com 1 execução só"
        diverge = [w for w in runs if w != "baseline"
                   and not (w in plug and plug[w]["failed"] == plug[w]["runs"])]
        if not diverge:
            return "esperada", "falha sempre, em todos os workflows"
        return "esperada, diverge", "não falhou sempre em: " + ", ".join(sorted(diverge))
    onde = ", ".join(sorted(plug))
    if any(c["intermittent"] for c in plug.values()):
        return "só no plugin (flaky)", f"baseline nunca falhou; intermitente sob plugin, em: {onde}"
    return "só no plugin (fixa)", f"baseline nunca falhou; falha em todas as execuções em: {onde}"


def plugin_breakdown(tests: dict) -> collections.Counter:
    """Testes `só no plugin` por combinação EXATA de workflows em que falharam.

    É uma partição: cada teste conta uma vez (ex.: `ranking`, `regsmart`,
    `ranking+regsmart`), então a soma bate com flaky + fixa.
    """
    out: collections.Counter = collections.Counter()
    for t in tests.values():
        if t["class"].startswith("só no plugin"):
            out["+".join(sorted(w for w in t["wf"] if w != "baseline"))] += 1
    return out


def _combo_key(combo: str):
    ws = combo.split("+")
    return (len(ws), [WF_ORDER.index(w) if w in WF_ORDER else 99 for w in ws], combo)


def analyze_flaky(c: Campaign, manifest: dict, exclude_warmup: bool,
                  only: dict) -> dict:
    """{repo: {mutante: {runs, total_seen, tests: {nodeid: {class, why, wf}}}}}.

    Dentro de cada workflow, a unidade é (job, nodeid): o nome do job inclui a
    perna da matriz, então um modo/SO que falha sozinho não vira flaky de outro.
    Por workflow o teste ganha uma célula (falhas/execuções do job que mais falhou,
    `intermittent` se algum job falhou em umas execuções e passou em outras).
    A classe vem de comparar o baseline com os plugins (ver `classify`).
    `runs` = execuções analisadas por workflow (o warm-up conta, a menos que
    --exclude-warmup); no plugin o teste pode não ter sido selecionado, e o log não
    distingue "passou" de "não rodou".
    """
    groups = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in manifest["runs"]:
        if not (r.get("mutant") and r.get("run_id") and r.get("status") == "completed"):
            continue
        if exclude_warmup and r["phase"] == "warmup":
            continue
        if only["repo"] and r["repo"] not in only["repo"]:
            continue
        if only["mutant"] and r["mutant"] not in only["mutant"]:
            continue
        if only["workflow"] and r["workflow"] not in only["workflow"]:
            continue
        groups[(r["repo"], r["mutant"])][r["workflow"]].append(r)

    out: dict = {}
    for (repo, mut), wfs in sorted(groups.items()):
        runs, total_seen = {}, {}
        cells: dict = collections.defaultdict(dict)  # nodeid -> workflow -> célula
        for wf, rs in sorted(wfs.items()):
            legs = collections.defaultdict(list)  # job -> [(falhas, total), ...]
            for r in rs:
                for job, failed, total in parse_run(c, repo, r["run_id"]):
                    legs[job].append((failed, total))
            if not legs:  # nenhum log com resumo do pytest
                continue
            runs[wf] = max(len(v) for v in legs.values())
            total_seen[wf] = sum(max(t for _, t in v) for v in legs.values())
            for job, reps in sorted(legs.items()):
                n = len(reps)
                for nid, k in collections.Counter(nid for failed, _ in reps for nid in failed).items():
                    cur = cells[nid].get(wf)
                    if cur is None:
                        cells[nid][wf] = {"failed": k, "runs": n, "jobs": 1, "intermittent": k < n}
                        continue
                    cur["jobs"] += 1
                    cur["intermittent"] = cur["intermittent"] or k < n
                    if (k / n, n) > (cur["failed"] / cur["runs"], cur["runs"]):
                        cur["failed"], cur["runs"] = k, n
        tests = {}
        for nid, cs in sorted(cells.items()):
            cls, why = classify(cs, runs)
            tests[nid] = {"class": cls, "why": why, "wf": cs}
        out.setdefault(repo, {})[mut] = {"runs": runs, "total_seen": total_seen, "tests": tests}
        counts = collections.Counter(t["class"] for t in tests.values())
        resumo = ", ".join(f"{counts[k]} {k}" for k in CLASS_ORDER if counts[k]) or "nenhuma falha"
        onde = plugin_breakdown(tests)
        if onde:
            resumo += "  [só no plugin, por onde falhou: " + ", ".join(
                f"{k} {n}" for k, n in sorted(onde.items(), key=lambda kv: _combo_key(kv[0]))) + "]"
        print(f"  {repo:18} {mut:24} {sum(runs.values())} runs: {resumo}")
    return out


# ---------------------------------------------------------------- comandos

def plan_from_args(c: Campaign, args):
    repo_plan = load_repo_plan(args.repo)
    cfg = load_workflow_cfg()
    workflows = workflows_for(cfg, repo_plan, args.workflow)
    registry = load_registry()
    mutants = select_mutants(registry, list(repo_plan), args.mutant, getattr(args, "limit_mutants", None))
    reps = args.reps if args.reps is not None else c.reps
    warmup = c.warmup if getattr(args, "warmup", None) is None else args.warmup
    warmup_ref = getattr(args, "warmup_ref", None) or cfg.get("warmup_ref") or "mutant"
    tasks = build_tasks(list(repo_plan), workflows, mutants, reps, warmup, warmup_ref,
                        getattr(args, "serialize_ref", False))
    return repo_plan, workflows, mutants, tasks, warmup, warmup_ref, reps


def fetch_workflow(api: Api, repo: str, workflow_file: str, ref: str) -> dict:
    try:
        import yaml
    except ImportError:
        sys.exit("verify precisa de PyYAML: pip install pyyaml")
    d = api.get(
        f"/repos/{OWNER}/{repo}/contents/.github/workflows/"
        f"{urllib.parse.quote(workflow_file)}?ref={urllib.parse.quote(ref)}"
    )
    return yaml.safe_load(base64.b64decode(d["content"]).decode(errors="replace")) or {}


def cmd_verify(api: Api, args) -> int:
    """Confere, na branch base dos mutantes, cada workflow do plano."""
    repo_plan = load_repo_plan(args.repo)
    cfg = load_workflow_cfg()
    workflows = workflows_for(cfg, repo_plan, args.workflow)
    registry = load_registry()
    warmup_ref = getattr(args, "warmup_ref", None) or cfg.get("warmup_ref") or "mutant"
    blockers = warns = 0
    for repo in repo_plan:
        meta = registry.get(repo) or {}
        base = meta.get("base_branch", "insert-mutations")
        n_pub = sum(1 for m in (meta.get("mutants") or {}).values() if m.get("published"))
        default_branch = api.get(f"/repos/{OWNER}/{repo}")["default_branch"]
        print(f"\n{repo}  (base {base}, {n_pub} mutantes publicados, default {default_branch})")
        if n_pub == 0:
            print("  ! sem mutantes publicados")
            blockers += 1
        if warmup_ref not in ("mutant", default_branch):
            print(f"  ! warm-up em `{warmup_ref}`: o cache dessa branch NÃO é visível pra "
                  f"dispatch em mut-* (só branch própria e default `{default_branch}`)")
            warns += 1
        groups = {}
        for w, spec in workflows[repo].items():
            key = f"{w} ({spec['file']})"
            try:
                doc = fetch_workflow(api, repo, spec["file"], base)
            except Exception as exc:
                print(f"  {key:44} FALHOU ao ler em {base}: {str(exc)[:80]}")
                blockers += 1
                continue
            on = doc.get("on", doc.get(True))  # PyYAML lê `on:` como True
            triggers = sorted(on) if isinstance(on, dict) else (
                [on] if isinstance(on, str) else list(on or []))
            notes = []
            if "workflow_dispatch" not in triggers:
                notes.append("FALTA workflow_dispatch")
                blockers += 1
            if "push" in triggers and isinstance(on, dict):
                push = on.get("push") or {}
                br = push.get("branches") or []
                ign = push.get("branches-ignore") or []
                if "!mut-*" not in br and not any(str(i).startswith("mut-") for i in ign):
                    notes.append("push não exclui mut-*")
                    warns += 1
            conc = doc.get("concurrency")
            group = str(conc.get("group") if isinstance(conc, dict) else conc or "")
            groups[w] = group
            if group and "${{" not in group:
                notes.append("concurrency FIXO: runs de qualquer branch se cancelam")
                blockers += 1
            uses_cache = any(
                "actions/cache" in str(s.get("uses", ""))
                for j in (doc.get("jobs") or {}).values() for s in (j.get("steps") or [])
            )
            if spec.get("warmup") and not uses_cache:
                notes.append("marcado com warm-up mas SEM actions/cache")
                warns += 1
            if uses_cache and not spec.get("warmup"):
                notes.append("usa actions/cache mas sem warm-up no plano")
                warns += 1
            print(f"  {key:44} {'ok' if not notes else '; '.join(notes)}"
                  f"  [concurrency={group[:40] or '-'} cache={'sim' if uses_cache else 'não'}]")
        weak = [w for w, g in groups.items() if g and "github.workflow" not in g and "github.ref" in g]
        if len(weak) > 1:
            print(f"  ! concurrency sem github.workflow em {weak}: no mesmo branch eles se "
                  f"cancelam; use `run --serialize-ref`")
            warns += 1
    print(f"\n{blockers} bloqueio(s), {warns} aviso(s).")
    return 1 if blockers else 0


def check_refs(api: Api, rows: dict, todo: list[dict]) -> None:
    """Garante que cada branch ainda aponta pro SHA esperado (mesmo SHA em todas as reps)."""
    seen: dict[tuple[str, str], str] = {}
    problems = []
    for t in todo:
        k = (t["repo"], t["ref"])
        if k not in seen:
            seen[k] = resolve_sha(api, *k)
        row = rows[t["task"]]
        if row.get("sha") and row["sha"] != seen[k]:
            problems.append(f"{t['repo']}/{t['ref']}: esperado {row['sha'][:8]}, está em {seen[k][:8]}")
        row["sha"] = row.get("sha") or seen[k]
    if problems:
        sys.exit("branches mudaram desde o registro (mutante trocado na mão?): rode "
                 "`python sync_mutant_branches.py --write` pra atualizar o "
                 "mutant_branches.json:\n  " + "\n  ".join(sorted(set(problems))))


def cmd_run(api: Api, args) -> int:
    c: Campaign = args.campaign_obj
    repo_plan, workflows, mutants, tasks, warmup, warmup_ref, reps = plan_from_args(c, args)
    phases = {"all": {"warmup", "rep"}, "warmup": {"warmup"}, "rep": {"rep"}}[args.phase]
    sel = [t for t in tasks if t["phase"] in phases]
    n_warm = sum(1 for t in sel if t["phase"] == "warmup")

    print(f"\n{c.title}: {len(sel)} runs ({n_warm} warm-up + {len(sel) - n_warm} repetições), "
          f"reps={reps}, warm-up={'sim, em ' + warmup_ref if warmup else 'não'}, fase={args.phase}")
    for repo in repo_plan:
        mine = [t for t in sel if t["repo"] == repo]
        print(f"  {repo:18} {len(mutants.get(repo, []))} mutantes × {len(workflows[repo])} workflows "
              f"-> {len(mine)} runs")
    if not sel:
        sys.exit("nada a rodar (confira --repo/--mutant/--workflow e se há mutantes `published`)")

    manifest = load_manifest(c)
    rows = sync_rows(manifest, tasks)
    if args.redo:
        redo = [t for t in sel if rows[t["task"]].get("conclusion") == "cancelled"
                or rows[t["task"]].get("dispatch_failed")]
        for t in redo:
            reset_row(rows[t["task"]])
        print(f"  --redo: {len(redo)} tarefa(s) canceladas/perdidas serão redespachadas")

    todo = [t for t in sel if not rows[t["task"]].get("dispatched_at_utc")
            and not rows[t["task"]].get("dispatch_failed")]
    selected_ids = {t["task"] for t in sel}
    for t in todo:  # dependência fora da seleção e ainda não feita = nunca vai liberar
        for d in t["deps"]:
            if d not in selected_ids and not is_done(rows[d]) and not rows[d].get("dispatched_at_utc"):
                sys.exit(f"{t['task']} depende de {d}, que ainda não rodou: use --phase all "
                         f"(ou rode --phase warmup antes)")
    skipped = len(sel) - len(todo)
    if skipped:
        print(f"  {skipped} run(s) já despachado(s), pulando (apague {c.manifest_path.name} "
              f"pra recomeçar do zero)")
    check_refs(api, rows, todo)
    if args.dry_run:
        print("\nDRY RUN: nada foi disparado.")
        return 0

    started = time.time()
    wall = manifest.setdefault("wall_clock", {})
    wall.setdefault("started_utc", now())
    manifest.setdefault("rate_limit", {}).setdefault("initial", api.rate_limit())
    save_json(c.manifest_path, manifest)

    print(f"\nDespachando (máx. {args.max_active} runs ativos, lanes sequenciais)...\n")
    total = len(sel)
    try:
        while True:
            refresh(api, manifest)
            active = sum(1 for r in rows.values() if r.get("dispatched_at_utc") and not is_done(r))
            sent = 0
            for t in sel:
                r = rows[t["task"]]
                if r.get("dispatched_at_utc") or r.get("dispatch_failed"):
                    continue
                if not all(is_done(rows[d]) for d in t["deps"]):
                    continue
                if active >= args.max_active:
                    break
                r["dispatch_window_start_utc"] = now()
                try:
                    dispatch(api, t["repo"], t["workflow_file"], t["ref"])
                    r["dispatched_at_utc"] = now()
                    r.pop("dispatch_error", None)
                    active += 1
                    sent += 1
                    print(f"  {t['repo']:18} {(t['mutant'] or t['ref']):24} {t['workflow']:18} "
                          f"{'warm-up' if t['phase'] == 'warmup' else 'r%02d' % t['rep']}")
                except Exception as exc:
                    r["dispatch_attempts"] = r.get("dispatch_attempts", 0) + 1
                    r["dispatch_error"] = str(exc)
                    if r["dispatch_attempts"] >= 3:
                        r["dispatch_failed"] = True
                    print(f"  {t['task']} FALHOU ({r['dispatch_attempts']}/3): {exc}")
                save_json(c.manifest_path, manifest)
                time.sleep(1)  # evita o limite secundário de requisições
            save_json(c.manifest_path, manifest)
            finished = sum(1 for t in sel if is_done(rows[t["task"]]))
            print(f"  {finished}/{total} concluídas, {active} ativas", end="\r")
            if finished == total:
                break
            if args.no_wait:
                time.sleep(20)  # dá tempo do GitHub criar os runs pra casar os run_ids
                refresh(api, manifest)
                break
            time.sleep(args.poll_interval)
        print()
    except KeyboardInterrupt:
        print("\nInterrompido: o manifesto está salvo, rode `run` de novo pra retomar.")
    finally:
        wall["finished_utc"] = now()
        wall["total_seconds"] = round(wall.get("total_seconds", 0) + time.time() - started, 1)
        manifest["rate_limit"]["final"] = api.rate_limit()
        flush_counters(api, manifest)
        save_json(c.manifest_path, manifest)
    left = sum(1 for t in sel if not is_done(rows[t["task"]]))
    if left:
        print(f"\n{left} run(s) ainda não terminaram/despacharam: rode `run` de novo pra continuar.")
    print(f"\nManifesto: {c.manifest_path}")
    return 0


def cmd_status(api: Api, args) -> int:
    c: Campaign = args.campaign_obj
    rows = load_manifest(c)["runs"]
    if not rows:
        print("manifesto vazio")
        return 0
    print(f"{'repo':18} {'workflow':18} {'fase':7} {'plano':>5} {'disp.':>5} {'ativas':>6} "
          f"{'ok':>4} {'falha':>5} {'canc.':>5}")
    keys = sorted({(r["repo"], r["workflow"], r["phase"]) for r in rows})
    for repo, wf, ph in keys:
        rs = [r for r in rows if (r["repo"], r["workflow"], r["phase"]) == (repo, wf, ph)]
        print(f"{repo:18} {wf:18} {ph:7} {len(rs):5d} "
              f"{sum(1 for r in rs if r.get('dispatched_at_utc')):5d} "
              f"{sum(1 for r in rs if r.get('dispatched_at_utc') and not is_done(r)):6d} "
              f"{sum(1 for r in rs if r.get('conclusion') == 'success'):4d} "
              f"{sum(1 for r in rs if r.get('conclusion') == 'failure'):5d} "
              f"{sum(1 for r in rs if r.get('conclusion') == 'cancelled'):5d}")
    return 0


def cmd_flaky(api: Api, args) -> int:
    """Atualiza o status dos runs, baixa os logs e acha os testes flaky."""
    c: Campaign = args.campaign_obj
    manifest = load_manifest(c)
    refresh(api, manifest)
    pending = [r for r in manifest["runs"] if r.get("dispatched_at_utc") and not is_done(r)]
    if pending:
        print(f"  {len(pending)} run(s) não concluído(s): a análise fica parcial.\n")
    only = {"repo": set(args.repo or []), "mutant": set(args.mutant or []),
            "workflow": set(args.workflow or [])}
    result = analyze_flaky(c, manifest, args.exclude_warmup, only)
    save_json(c.flaky_path, result)
    manifest.setdefault("rate_limit", {})["final"] = api.rate_limit()
    flush_counters(api, manifest)
    save_json(c.manifest_path, manifest)
    print(f"\nSalvo em {c.flaky_path}. Rode `report` pra incluir no relatório.")
    return 0


def cmd_report(api: Api, args) -> int:
    c: Campaign = args.campaign_obj
    flaky = json.loads(c.flaky_path.read_text(encoding="utf-8")) if c.flaky_path.exists() else None
    text = build_report(c, load_manifest(c), flaky, getattr(args, "show_expected", False))
    c.report_path.write_text(text, encoding="utf-8")
    print(text)
    print(f"\nSalvo em {c.report_path}")
    return 0


def main(campaign: str = "flaky") -> None:
    c = Campaign(campaign)
    script = "experiment_runner.py" if campaign == "experiment" else "flaky_runner.py"
    parser = argparse.ArgumentParser(
        prog=script,
        description=f"{c.title}: dispara repetições dos workflows em cada mutante "
                    f"(dados em {c.dir.relative_to(ROOT)}/).",
    )
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--repo", action="append", help="restringe a um repo (repetível)")
    common.add_argument("--mutant", action="append", help="restringe a um mutante, ex.: dask-m0003 (repetível)")
    common.add_argument("--workflow", action="append",
                        help="restringe a um modo: baseline, ranking, regsmart, regsmart-no-rank (repetível)")
    common.add_argument("--reps", type=int, help=f"repetições medidas (padrão {c.reps})")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("verify", parents=[common], help="confere dispatch/push/concurrency/cache").set_defaults(func=cmd_verify)

    p = sub.add_parser("run", parents=[common], help="dispara e espera (lanes sequenciais)")
    p.add_argument("--phase", choices=["all", "warmup", "rep"], default="all",
                   help="all (padrão), só o warm-up, ou só as repetições (exige warm-up já feito)")
    p.add_argument("--warmup", action=argparse.BooleanOptionalAction, default=None,
                   help=f"liga/desliga o warm-up nos workflows com cache (padrão: {'ligado' if c.warmup else 'desligado'})")
    p.add_argument("--warmup-ref", help="onde rodar o warm-up: `mutant` (padrão, na própria branch do "
                                       "mutante) ou o nome de uma branch (ex.: a default), 1x por repo+workflow")
    p.add_argument("--serialize-ref", action="store_true",
                   help="trata todos os workflows de uma branch como uma lane só (concurrency compartilhado)")
    p.add_argument("--limit-mutants", type=int, help="só os N primeiros mutantes de cada repo (teste)")
    p.add_argument("--max-active", type=int, default=30, help="máx. de runs em andamento (padrão 30)")
    p.add_argument("--redo", action="store_true", help="redispara runs cancelados ou perdidos")
    p.add_argument("--no-wait", action="store_true", help="uma passada de dispatch e sai")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--poll-interval", type=float, default=30.0)
    p.set_defaults(func=cmd_run)

    sub.add_parser("status", parents=[common], help="progresso por repo/workflow (offline)").set_defaults(func=cmd_status)
    p = sub.add_parser("flaky", parents=[common], help="analisa os logs e acha testes flaky")
    p.add_argument("--exclude-warmup", action="store_true", help="não conta o warm-up como execução")
    p.set_defaults(func=cmd_flaky)
    p = sub.add_parser("report", parents=[common], help="gera o relatório markdown")
    p.add_argument("--show-expected", action="store_true", help="lista também as falhas esperadas")
    p.set_defaults(func=cmd_report)

    args = parser.parse_args()
    args.campaign_obj = c
    if args.cmd not in ("report", "status") and not TOKEN:
        sys.exit("token obrigatório: defina GITHUB_TOKEN_REGSMART ou rode `gh auth login`")
    sys.exit(args.func(Api(TOKEN), args))


if __name__ == "__main__":
    main("flaky")
