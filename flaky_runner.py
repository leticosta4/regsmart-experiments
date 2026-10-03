"""
Flaky runner: dispara N repetições do workflow de teste de cada fork e acha
quais testes falham de forma intermitente.

Uso (todos aceitam --repo, repetível, e --reps):
    python flaky_runner.py verify   # 1x: confere workflow_dispatch e concurrency
    python flaky_runner.py run      # cria branches flaky-rNN, dispara e espera
    python flaky_runner.py flaky    # baixa os logs e acha os testes flaky
    python flaky_runner.py report   # gera data/flaky/flaky_report.md

Por que uma branch por repetição: o `concurrency` dos workflows costuma agrupar
por github.ref. Com uma branch distinta por rep, cada uma cai num grupo próprio
e nenhuma cancela a outra, sem editar workflow. Branch e não tag porque dask e
pytest-django têm `push: tags: ["*"]`.

Acima de 20 jobs simultâneos (plano Free) o GitHub enfileira sozinho, então o
script não controla orçamento: o pico medido vai saturar em 20 e o makespan
inclui o tempo de fila.
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
DATA = ROOT / "data" / "flaky"
RAW = DATA / "raw"

PLAN_PATH = DATA / "flaky_plan.json"
MANIFEST_PATH = DATA / "flaky_runs.json"
REPORT_PATH = DATA / "flaky_report.md"
FLAKY_PATH = DATA / "flaky_tests.json"

PREFIX = "flaky-r"
FREE_PLAN_JOBS = 20
ACTIVE = {"in_progress", "queued", "waiting", "pending", "requested"}


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

    def __init__(self, token: str | None, max_retries: int = 5):
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
                print(f"   ! HTTP {exc.code}, esperando {wait:.0f}s ({attempt + 1})")
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


# ---------------------------------------------------------------- plan / state


def load_plan(only: list[str] | None, reps_override: int | None) -> list[dict]:
    entries = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    if only:
        unknown = set(only) - {e["repo"] for e in entries}
        if unknown:
            sys.exit(f"--repo desconhecido no plan: {', '.join(sorted(unknown))}")
        entries = [e for e in entries if e["repo"] in set(only)]
    entries = [e for e in entries if e.get("enabled", True)]
    for e in entries:
        e.setdefault("branch", "track-flaky")
        e["reps"] = reps_override if reps_override is not None else e.get("reps", 10)
    return entries


def save_json(path: Path, payload) -> None:
    """Escrita atômica: tmp + rename, pra não corromper com Ctrl-C."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    tmp.replace(path)


def load_manifest() -> dict:
    if MANIFEST_PATH.exists():
        return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return {"created_utc": now(), "runs": []}


def load_flaky() -> dict | None:
    if not FLAKY_PATH.exists():
        return None
    return json.loads(FLAKY_PATH.read_text(encoding="utf-8"))


def ref_name(rep: int) -> str:
    return f"{PREFIX}{rep:02d}"


def task_key(repo: str, rep: int) -> str:
    return f"{repo}#r{rep:02d}"


def build_tasks(plan: list[dict]) -> list[dict]:
    return [
        {**e, "rep": rep, "task": task_key(e["repo"], rep)}
        for e in plan
        for rep in range(1, e["reps"] + 1)
    ]


def flush_counters(api: Api, manifest: dict) -> None:
    """Soma os contadores desta execução no manifest (acumula entre execuções)."""
    total = manifest.setdefault("counters", {})
    for key, value in api.counters.items():
        total[key] = total.get(key, 0) + value
        api.counters[key] = 0


# ---------------------------------------------------------------- GitHub helpers


def resolve_sha(api: Api, repo: str, branch: str) -> str:
    data = api.get(f"/repos/{OWNER}/{repo}/branches/{urllib.parse.quote(branch)}")
    return data["commit"]["sha"]


def list_runs(api: Api, repo: str) -> list[dict]:
    return api.get(
        f"/repos/{OWNER}/{repo}/actions/runs?event=workflow_dispatch&per_page=100"
    ).get("workflow_runs", [])


def prep_refs(api: Api, plan: list[dict], repoint: bool) -> None:
    """Cria uma branch `flaky-rNN` por repetição, todas no SHA da `track-flaky`."""
    for e in plan:
        repo, sha = e["repo"], e["sha"]
        wanted = [ref_name(r) for r in range(1, e["reps"] + 1)]
        existing = {
            x["ref"].removeprefix("refs/heads/"): x["object"]["sha"]
            for x in api.get(f"/repos/{OWNER}/{repo}/git/matching-refs/heads/{PREFIX}")
        }
        stale = [n for n in wanted if n in existing and existing[n] != sha]
        missing = [n for n in wanted if n not in existing]
        if stale and not repoint:
            sys.exit(
                f"{repo}: {stale} apontam para outro SHA que {sha[:8]}. "
                f"Rode com --repoint pra mover."
            )
        for name in stale:  # PATCH com force: move a ref de forma atômica
            api.request(
                "PATCH",
                f"/repos/{OWNER}/{repo}/git/refs/heads/{name}",
                {"sha": sha, "force": True},
            )
        for name in missing:
            api.post(
                f"/repos/{OWNER}/{repo}/git/refs",
                {"ref": f"refs/heads/{name}", "sha": sha},
            )
        print(
            f"   {repo:18} {len(missing)} criadas, {len(stale)} movidas, "
            f"{len(wanted) - len(missing) - len(stale)} já ok -> {sha[:8]}"
        )


def dispatch(api: Api, repo: str, workflow_file: str, ref: str) -> None:
    path = urllib.parse.quote(workflow_file)
    api.post(f"/repos/{OWNER}/{repo}/actions/workflows/{path}/dispatches", {"ref": ref})


def correlate_all(api: Api, manifest: dict, attempts: int = 8, wait: float = 15.0) -> None:
    """Acha o run_id de cada repetição despachada, numa passada por repo.

    O GitHub leva ~10-20s pra criar o run depois do dispatch. Como a branch é
    única por repetição, casar `head_branch == ref` basta. O corte por
    `created_at` evita pegar run antigo da mesma branch de uma execução anterior.
    """
    for _ in range(attempts):
        pending = [
            r for r in manifest["runs"]
            if r.get("dispatched_at_utc") and not r.get("run_id")
        ]
        if not pending:
            return
        time.sleep(wait)
        by_repo = {repo: list_runs(api, repo) for repo in {r["repo"] for r in pending}}
        for r in pending:
            since = parse_ts(r["dispatch_window_start_utc"]).timestamp() - 2
            hits = sorted(
                (
                    x for x in by_repo[r["repo"]]
                    if x["head_branch"] == r["ref"]
                    and parse_ts(x["created_at"]).timestamp() >= since
                ),
                key=lambda x: x["created_at"],
            )
            if hits:
                r["run_id"] = hits[0]["id"]
                r["html_url"] = hits[0]["html_url"]
    left = [r["task"] for r in manifest["runs"] if r.get("dispatched_at_utc") and not r.get("run_id")]
    if left:
        print(f"   ! sem run_id: {', '.join(left)} (rode `flaky` depois pra tentar de novo)")


def refresh_status(api: Api, manifest: dict) -> None:
    """Atualiza status/conclusão dos runs. Jobs só são buscados uma vez, quando o run termina."""
    rows = [r for r in manifest["runs"] if r.get("run_id")]
    for repo in sorted({r["repo"] for r in rows}):
        listed = {x["id"]: x for x in list_runs(api, repo)}
        for r in (r for r in rows if r["repo"] == repo):
            if r.get("status") == "completed" and "jobs" in r:
                continue
            run = listed.get(r["run_id"]) or api.get(
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


def build_report(manifest: dict, plan: list[dict], flaky: dict | None = None) -> str:
    runs = manifest["runs"]
    by_task = {r["task"]: r for r in runs}
    counters = manifest.get("counters", {})
    wall = manifest.get("wall_clock", {})

    intervals = job_intervals(runs)
    dispatched = sorted(r["dispatched_at_utc"] for r in runs if r.get("dispatched_at_utc"))
    concluded = sorted(r["conclusion_at_utc"] for r in runs if r.get("conclusion_at_utc"))
    makespan = None
    if dispatched and concluded:
        makespan = (parse_ts(concluded[-1]) - parse_ts(dispatched[0])).total_seconds()

    L = [
        "# Flaky runner — relatório",
        "",
        "## Custo",
        "",
        f"- Início: `{wall.get('started_utc', '-')}`",
        f"- Fim: `{wall.get('finished_utc', '-')}`",
        f"- Tempo ativo do script: **{fmt_hms(wall.get('total_seconds'))}**",
        f"- Janela real dos runs (1º dispatch → última conclusão): **{fmt_hms(makespan)}** (inclui fila)",
        f"- Minutos de runner somados: **{runner_minutes(intervals)} min**",
        f"- Pico de concorrência medido: **{peak_concurrency(intervals)}** jobs "
        f"(teto do plano Free: {FREE_PLAN_JOBS})",
        "",
        "## API / rate limit",
        "",
        f"- Requisições: {counters.get('get', 0)} GET, {counters.get('post', 0)} POST/PATCH",
        f"- Retries: {counters.get('retries', 0)}",
    ]
    rl = (manifest.get("rate_limit") or {}).get("final") or {}
    if rl:
        L.append(
            f"- Rate limit (final): {rl.get('used', '?')}/{rl.get('limit', '?')} "
            f"consumidos, reseta em `{rl.get('reset_utc', '-')}`"
        )

    L += [
        "",
        "## Saúde da execução",
        "",
        "| Métrica | Valor |",
        "|---|---|",
        f"| Repetições pedidas | {len(build_tasks(plan))} |",
        f"| Repetições despachadas | {sum(1 for r in runs if r.get('dispatched_at_utc'))} |",
        f"| Com run_id localizado | {sum(1 for r in runs if r.get('run_id'))} |",
        f"| Sem run_id localizado | {sum(1 for r in runs if not r.get('run_id'))} |",
        f"| Concluídas com sucesso | {sum(1 for r in runs if r.get('conclusion') == 'success')} |",
        f"| Concluídas com falha | {sum(1 for r in runs if r.get('conclusion') == 'failure')} |",
        f"| Canceladas | {sum(1 for r in runs if r.get('conclusion') == 'cancelled')} |",
        f"| Ainda em andamento | {sum(1 for r in runs if r.get('status') in ACTIVE)} |",
        f"| Jobs executados (com timestamps) | {len(intervals)} |",
        "",
        "## Por repositório",
        "",
        "| repo | reps | success | failure | cancelled | em andamento | makespan | min runner |",
        "|---|---|---|---|---|---|---|---|",
    ]

    for e in plan:
        repo = e["repo"]
        rows = [
            by_task[task_key(repo, r)]
            for r in range(1, e["reps"] + 1)
            if task_key(repo, r) in by_task
        ]
        if not rows:
            continue
        fin = [r["conclusion_at_utc"] for r in rows if r.get("conclusion_at_utc")]
        sta = [r["dispatched_at_utc"] for r in rows if r.get("dispatched_at_utc")]
        repo_ms = (
            (parse_ts(max(fin)) - parse_ts(min(sta))).total_seconds()
            if fin and sta
            else None
        )
        L.append("| " + " | ".join([
            repo,
            str(e["reps"]),
            str(sum(1 for r in rows if r.get("conclusion") == "success")),
            str(sum(1 for r in rows if r.get("conclusion") == "failure")),
            str(sum(1 for r in rows if r.get("conclusion") == "cancelled")),
            str(sum(1 for r in rows if r.get("status") in ACTIVE)),
            fmt_hms(repo_ms),
            str(runner_minutes(job_intervals(rows))),
        ]) + " |")

    L += ["", "## Testes flaky", ""]
    if not flaky:
        L.append("_Análise de logs ainda não rodada. Use `flaky_runner.py flaky`._")
    else:
        L += ["| repo | testes | flaky | taxa |", "|---|---|---|---|"]
        for e in plan:
            info = flaky.get(e["repo"]) or {}
            total = info.get("total_seen") or 0
            n = len(info.get("tests") or {})
            if total:
                L.append(f"| {e['repo']} | {total} | {n} | {100.0 * n / total:.1f}% |")
        L.append("")
        for e in plan:
            rows = (flaky.get(e["repo"]) or {}).get("tests") or {}
            if not rows:
                continue
            L += [f"### {e['repo']}", "", "| teste | reps | falhou | passou |", "|---|---|---|---|"]
            for nodeid, c in sorted(rows.items(), key=lambda kv: -kv[1]["failed"]):
                L.append(f"| `{nodeid}` | {c['reps']} | {c['failed']} | {c['passed']} |")
            L.append("")

    bad = [r for r in runs if r.get("conclusion") == "cancelled"]
    if bad:
        L += ["## Canceladas (investigar)", "", "| repo | rep | ref | run_id |", "|---|---|---|---|"]
        for r in bad:
            L.append(f"| {r['repo']} | r{r['rep']:02d} | `{r['ref']}` | {r.get('run_id', '-')} |")
        L.append("")

    unmatched = [r for r in runs if not r.get("run_id")]
    if unmatched:
        L += [
            "## Sem run_id localizado",
            "",
            "Repetição despachada cujo run não foi encontrado: a análise de flaky "
            "fica **incompleta** para esses repos.",
            "",
            "| repo | rep | ref | despachado_em |",
            "|---|---|---|---|",
        ]
        for r in unmatched:
            L.append(f"| {r['repo']} | r{r['rep']:02d} | `{r['ref']}` | {r.get('dispatched_at_utc', '-')} |")
        L.append("")

    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- flaky (logs)

ANSI = re.compile(r"\x1b\[[0-9;]*m")
TS = re.compile(r"^\d{4}-\d\d-\d\dT[\d:.]+Z ")
FAILED = re.compile(r"^(?:FAILED|ERROR) (.+?)(?: - .*)?$")
SUMMARY = re.compile(r"\d+ (?:failed|passed|errors?).* in [\d.:]+s")
COUNT = re.compile(r"(\d+) (?:failed|passed|errors?)")


def parse_run(repo: str, run_id: int) -> list[tuple[str, set, int]]:
    """Por job: (nome do job, nodeids que falharam, total de testes).

    Usa só o que o pytest imprime por padrão: as linhas `FAILED <nodeid>` do
    resumo final e a linha de contagem (`3 failed, 1200 passed in 90s`).
    """
    zpath = RAW / repo / f"{run_id}.zip"
    if not zpath.exists():
        zpath.parent.mkdir(parents=True, exist_ok=True)
        res = subprocess.run(
            ["gh", "api", f"repos/{OWNER}/{repo}/actions/runs/{run_id}/logs"],
            capture_output=True,
        )
        if res.returncode:
            print(f"   ! {repo} run {run_id}: falha ao baixar log")
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
            if seen:  # job sem resumo do pytest (lint, infra quebrou) não conta
                out.append((job, failed, total))
    return out


def analyze_flaky(manifest: dict, plan: list[dict]) -> dict:
    out = {}
    for e in plan:
        repo = e["repo"]
        legs = collections.defaultdict(list)  # job -> [(falhas, total), ...]
        for r in manifest["runs"]:
            if r["repo"] == repo and r.get("run_id") and r.get("status") == "completed":
                for job, failed, total in parse_run(repo, r["run_id"]):
                    legs[job].append((failed, total))

        tests, total_seen = {}, 0
        for job, reps in legs.items():
            n = len(reps)
            total_seen += max(t for _, t in reps)
            counts = collections.Counter(nid for failed, _ in reps for nid in failed)
            for nid, k in counts.items():
                if k < n:  # falhou em algumas reps e passou em outras = flaky
                    tests[f"{nid} [{job}]"] = {"reps": n, "failed": k, "passed": n - k}
        out[repo] = {"total_seen": total_seen, "tests": tests}
        status = (
            f"{len(tests)} flaky / {total_seen} testes"
            if total_seen
            else "SEM resumo do pytest no log"
        )
        print(f"   {repo:18} {status}")
    return out


# ---------------------------------------------------------------- commands


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
    """Confere workflow_dispatch e mostra o `concurrency` de cada workflow."""
    plan = load_plan(args.repo, args.reps)
    print(f"Plano: {len(plan)} repos, {sum(e['reps'] for e in plan)} repetições\n")
    blockers = 0
    for e in plan:
        key = f"{e['repo']}/{e['workflow_file']}@{e['branch']}"
        try:
            doc = fetch_workflow(api, e["repo"], e["workflow_file"], e["branch"])
        except Exception as exc:
            print(f"   {key:46} FALHOU ao ler: {exc}")
            blockers += 1
            continue
        on = doc.get("on", doc.get(True))  # PyYAML lê `on:` como True
        triggers = sorted(on) if isinstance(on, dict) else list(on or [])
        if "workflow_dispatch" not in triggers:
            print(f"   {key:46} FALTA 'workflow_dispatch:' no on:")
            blockers += 1
            continue
        conc = doc.get("concurrency")
        group = conc.get("group") if isinstance(conc, dict) else conc
        print(f"   {key:46} ok  concurrency={str(group)[:50]}")
    if blockers:
        print(f"\n{blockers} repo(s) bloqueado(s).")
        return 1
    print("\nTudo pronto. Se nenhum workflow tem concurrency por github.ref, "
          "as branches flaky-rNN seriam dispensáveis.")
    return 0


def cmd_run(api: Api, args) -> int:
    plan = load_plan(args.repo, args.reps)
    for e in plan:
        e["sha"] = resolve_sha(api, e["repo"], e["branch"])
    if args.dry_run:
        for e in plan:
            print(f"   {e['repo']:18} {e['sha'][:8]}  {e['reps']} reps")
        print(f"\nDRY RUN: {sum(e['reps'] for e in plan)} execuções")
        return 0

    manifest = load_manifest()
    started = time.time()
    wall = manifest.setdefault("wall_clock", {})
    wall.setdefault("started_utc", now())
    manifest.setdefault("rate_limit", {}).setdefault("initial", api.rate_limit())

    print("\nPreparando branches das repetições:")
    prep_refs(api, plan, args.repoint)

    rows = {r["task"]: r for r in manifest["runs"]}
    todo = [t for t in build_tasks(plan) if not (rows.get(t["task"]) or {}).get("dispatched_at_utc")]
    skipped = len(build_tasks(plan)) - len(todo)
    if skipped:
        print(f"\n{skipped} repetição(ões) já despachada(s), pulando "
              f"(apague {MANIFEST_PATH.name} pra recomeçar do zero)")

    print(f"\nDespachando {len(todo)} repetições...\n")
    for i, t in enumerate(todo, 1):
        ref = ref_name(t["rep"])
        row = rows.get(t["task"])
        if row is None:
            row = rows[t["task"]] = {
                "task": t["task"], "repo": t["repo"], "rep": t["rep"], "ref": ref,
                "workflow_file": t["workflow_file"], "branch": t["branch"], "sha": t["sha"],
            }
            manifest["runs"].append(row)
        row["dispatch_window_start_utc"] = now()
        try:
            dispatch(api, t["repo"], t["workflow_file"], ref)
            row["dispatched_at_utc"] = now()
            row.pop("dispatch_error", None)
            print(f"   [{i}/{len(todo)}] {t['repo']:18} {ref}")
        except Exception as exc:
            row["dispatch_error"] = str(exc)
            print(f"   [{i}/{len(todo)}] {t['repo']:18} {ref} FALHOU: {exc}")
        save_json(MANIFEST_PATH, manifest)
        time.sleep(1)  # evita o limite secundário de requisições

    print("\nLocalizando run_ids...")
    correlate_all(api, manifest)
    save_json(MANIFEST_PATH, manifest)

    if not args.no_wait:
        print("\nAguardando os runs terminarem (Ctrl-C para sair; `flaky` retoma depois)...")
        while True:
            refresh_status(api, manifest)
            save_json(MANIFEST_PATH, manifest)
            rows_ = [r for r in manifest["runs"] if r.get("run_id")]
            pending = [r for r in rows_ if r.get("status") != "completed"]
            print(f"   {len(rows_) - len(pending)}/{len(rows_)} concluídas", end="\r")
            if not pending:
                break
            time.sleep(args.poll_interval)
        print()

    wall["finished_utc"] = now()
    wall["total_seconds"] = round(wall.get("total_seconds", 0) + time.time() - started, 1)
    manifest["rate_limit"]["final"] = api.rate_limit()
    flush_counters(api, manifest)
    save_json(MANIFEST_PATH, manifest)
    print(f"\nManifesto: {MANIFEST_PATH}\nPróximo: python flaky_runner.py flaky")
    return 0


def cmd_flaky(api: Api, args) -> int:
    """Atualiza o status dos runs, baixa os logs e acha os testes flaky."""
    manifest = load_manifest()
    plan = load_plan(args.repo, args.reps)
    correlate_all(api, manifest, attempts=1, wait=0)
    refresh_status(api, manifest)

    pending = [r for r in manifest["runs"] if r.get("status") != "completed"]
    if pending:
        print(f"   {len(pending)} run(s) não concluído(s): a análise fica parcial.\n")

    save_json(FLAKY_PATH, analyze_flaky(manifest, plan))
    manifest.setdefault("rate_limit", {})["final"] = api.rate_limit()
    flush_counters(api, manifest)
    save_json(MANIFEST_PATH, manifest)
    print(f"\nSalvo em {FLAKY_PATH}. Rode `report` pra incluir no relatório.")
    return 0


def cmd_report(api: Api, args) -> int:
    plan = load_plan(args.repo, args.reps)
    text = build_report(load_manifest(), plan, load_flaky())
    REPORT_PATH.write_text(text, encoding="utf-8")
    print(text)
    print(f"\nSalvo em {REPORT_PATH}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Dispara N repetições do workflow de cada fork e acha testes flaky."
    )
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--repo", action="append", help="restringe a um repo (repetível)")
    common.add_argument("--reps", type=int, help="sobrescreve o número de repetições")

    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("verify", parents=[common], help="confere workflow_dispatch/concurrency").set_defaults(func=cmd_verify)
    p = sub.add_parser("run", parents=[common], help="cria branches, dispara e espera")
    p.add_argument("--repoint", action="store_true", help="move branches que apontam pra outro SHA")
    p.add_argument("--no-wait", action="store_true", help="sai sem esperar os runs terminarem")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--poll-interval", type=float, default=60.0)
    p.set_defaults(func=cmd_run)
    sub.add_parser("flaky", parents=[common], help="analisa os logs e acha testes flaky").set_defaults(func=cmd_flaky)
    sub.add_parser("report", parents=[common], help="gera o relatório markdown").set_defaults(func=cmd_report)

    args = parser.parse_args()
    if args.cmd != "report" and not TOKEN:
        sys.exit("token obrigatório: defina GITHUB_TOKEN_REGSMART ou rode `gh auth login`")
    sys.exit(args.func(Api(TOKEN), args))


if __name__ == "__main__":
    main()
