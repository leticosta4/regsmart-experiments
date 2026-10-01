"""
Flaky suite
"""

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("precisa de PyYAML: pip install pyyaml")


OWNER = "leticosta4"
API = "https://api.github.com"
ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "flaky"

PLAN_PATH = DATA / "flaky_plan.json"
MANIFEST_PATH = DATA / "flaky_runs.json"
REPORT_PATH = DATA / "flaky_report.md"
FLAKY_PATH = DATA / "flaky_tests.json"

ACTIVE = {"in_progress", "queued", "waiting", "pending", "requested"}
DONE = {"completed"}


def _gh_token() -> str | None:
    """Fallback pro token do gh CLI, pra nao depender de env var."""
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

    def request(
        self,
        method: str,
        path: str,
        body: dict | None = None,
        raw: bool = False,
        absolute: bool = False,
    ):
        url = path if absolute else f"{API}{path}"
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
                    return payload if raw else (json.loads(payload) if payload else {})
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode()[:200]
                if exc.code in (403, 429):
                    # Rate limit global vs. limite secundario: so espera no 429
                    # e no 403 que veio com Retry-After.
                    retry_after = exc.headers.get("Retry-After")
                    if exc.code == 403 and not retry_after:
                        raise
                    wait = float(retry_after) if retry_after else delay
                elif exc.code >= 500:
                    wait = delay
                else:
                    raise RuntimeError(
                        f"{method} {url} -> HTTP {exc.code}: {detail}"
                    ) from exc
                if attempt == self.max_retries:
                    raise RuntimeError(
                        f"{method} {url} -> desistindo após {attempt + 1} tentativas"
                    ) from exc
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

    def get(self, path: str, **kw):
        return self.request("GET", path, **kw)

    def post(self, path: str, body: dict | None = None, **kw):
        return self.request("POST", path, body=body, **kw)

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

    def paginate(self, path: str, per_page: int = 100, max_pages: int = 10) -> list:
        out = []
        for page in range(1, max_pages + 1):
            sep = "&" if "?" in path else "?"
            chunk = self.get(f"{path}{sep}per_page={per_page}&page={page}")
            if not isinstance(chunk, list) or not chunk:
                break
            out.extend(chunk)
            if len(chunk) < per_page:
                break
        return out


# ---------------------------------------------------------------- job counting


# ---------------------------------------------------------------- plan / state


def load_plan(path: Path, only: list[str] | None, reps_override: int | None):
    entries = json.loads(path.read_text(encoding="utf-8"))
    if only:
        wanted = set(only)
        unknown = wanted - {e["repo"] for e in entries}
        if unknown:
            sys.exit(f"--repo desconhecido no plan: {', '.join(sorted(unknown))}")
        entries = [e for e in entries if e["repo"] in wanted]
    entries = [e for e in entries if e.get("enabled", True)]
    if reps_override is not None:
        for e in entries:
            e["reps"] = reps_override
    for e in entries:
        e.setdefault("branch", "track-flaky")
        e.setdefault("reps", 10)
    return entries


def save_json(path: Path, payload) -> None:
    """Escrita atômica: tmp + rename, pra não corromper o manifest com Ctrl-C."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    tmp.replace(path)


def load_flaky() -> dict | None:
    """Resultado da análise de logs, se ela já tiver sido rodada."""
    if not FLAKY_PATH.exists():
        return None
    return json.loads(FLAKY_PATH.read_text(encoding="utf-8"))


def load_manifest() -> dict:
    if MANIFEST_PATH.exists():
        return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return {"created_utc": now(), "runs": []}


def ref_name(rep: int, prefix: str) -> str:
    """Monta o nome da ref da repetição: prefixo `flaky-r` + rep 1 -> `flaky-r01`.

    O prefixo entra como está (o default já traz o `-r`), então o número é só
    concatenado com zero à esquerda.
    """
    return f"{prefix}{rep:02d}"


def task_key(repo: str, rep: int) -> str:
    return f"{repo}#r{rep:02d}"


def build_tasks(plan: list[dict]) -> list[dict]:
    tasks = []
    for entry in plan:
        for rep in range(1, entry["reps"] + 1):
            tasks.append({**entry, "rep": rep, "task": task_key(entry["repo"], rep)})
    return tasks


# ---------------------------------------------------------------- polling


class Poller:
    """Cache de runs e contagem de jobs em uso.

    `GET /actions/jobs` retorna 404, então a contagem de slots ocupados sai
    de `GET /actions/runs?status=in_progress` + um `/runs/{id}/jobs` por run
    ainda não visto (a contagem de jobs de um run não muda, então cacheia).
    """

    def __init__(self, api: Api, repos: list[str]):
        self.api = api
        self.repos = repos
        self.runs_by_repo: dict[str, dict[int, dict]] = {}
        self.job_count: dict[tuple[str, int], int] = {}
        self.occupied = 0
        self.peak = 0

    def poll(self) -> None:
        occupied = 0
        for repo in self.repos:
            runs = self.api.get(
                f"/repos/{OWNER}/{repo}/actions/runs?per_page=100"
            ).get("workflow_runs", [])
            index = {r["id"]: r for r in runs}
            self.runs_by_repo[repo] = index
            for run in runs:
                if run["status"] not in ACTIVE:
                    continue
                key = (repo, run["id"])
                if key not in self.job_count:
                    self.job_count[key] = self.api.get(
                        f"/repos/{OWNER}/{repo}/actions/runs/{run['id']}/jobs?per_page=100"
                    ).get("total_count", 0)
                occupied += self.job_count[key]
        self.occupied = occupied
        self.peak = max(self.peak, occupied)

    def run(self, repo: str, run_id: int) -> dict | None:
        return self.runs_by_repo.get(repo, {}).get(run_id)

    def runs_for_ref(self, repo: str, ref: str) -> list[dict]:
        return [
            r
            for r in self.runs_by_repo.get(repo, {}).values()
            if r.get("head_branch") == ref
        ]


# ---------------------------------------------------------------- medição


def resolve_sha(api: Api, repo: str, branch: str) -> str:
    data = api.get(f"/repos/{OWNER}/{repo}/branches/{urllib.parse.quote(branch)}")
    return data["commit"]["sha"]


def fetch_workflow(api: Api, repo: str, workflow_file: str, ref: str):
    """YAML do workflow em `ref`.

    O endpoint `/contents/` com `?ref=` retorna um objeto JSON com o conteúdo
    base64 quando usado com o header padrão. Com `Accept: application/vnd.github.raw`
    ele deveria retornar o arquivo cru; em alguns casos, no entanto, ainda devolve
    JSON. Aqui tratamos os dois formatos.
    """
    path = urllib.parse.quote(workflow_file)
    try:
        raw_body = api.get(
            f"/repos/{OWNER}/{repo}/contents/.github/workflows/{path}"
            f"?ref={urllib.parse.quote(ref)}",
            raw=True,
        )
    except RuntimeError:
        raise

    # Se for JSON, extrai o 'content' base64
    try:
        obj = json.loads(raw_body)
    except json.JSONDecodeError:
        # corpo já é YAML
        yaml_doc = yaml.safe_load(raw_body)
        return raw_body, yaml_doc

    if isinstance(obj, dict) and "content" in obj and "encoding" in obj:
        import base64

        body = base64.b64decode(obj["content"]).decode(
            errors="replace"
        )
        return body, yaml.safe_load(body)

    if isinstance(obj, list):
        raise RuntimeError(f"esperava arquivo único para {workflow_file}")

    raise RuntimeError(f"formato inesperado ao ler workflow {workflow_file}")


def read_workflow(api: Api, plan: list[dict]) -> dict:
    """Confere que cada workflow pode ser disparado por `workflow_dispatch`.

    Só isso: lê o YAML e reporta os gatilhos e o bloco `concurrency`. A contagem
    de jobs por repetição foi removida de propósito — ela era uma estimativa
    estática que já divergiu do real (22 previstos, e a conta de jobs em
    andamento medida pelo `Poller` é a fonte de verdade). Custo de execução
    sai dos `started_at`/`completed_at` reais de cada job.
    """
    info = {}
    for entry in plan:
        repo, wf, branch = entry["repo"], entry["workflow_file"], entry["branch"]
        key = f"{repo}/{wf}@{branch}"
        try:
            _, doc = fetch_workflow(api, repo, wf, resolve_sha(api, repo, branch))
        except Exception as exc:
            print(f"   !! {key}: não li o workflow ({exc})")
            info[key] = {"error": str(exc), "has_workflow_dispatch": False}
            continue

        on = (doc or {}).get("on", (doc or {}).get(True))
        triggers = sorted(on) if isinstance(on, dict) else list(on or [])
        info[key] = {
            "sha": entry.get("sha"),
            "triggers": triggers,
            "has_workflow_dispatch": "workflow_dispatch" in triggers,
            "concurrency": (doc or {}).get("concurrency"),
        }
    return info


# ---------------------------------------------------------------- refs


def prep_refs(api: Api, plan: list[dict], prefix: str, repoint: bool) -> dict:
    """Cria/move uma branch `flaky-rNN` por repetição, todas no mesmo SHA.

    Branch e não tag de propósito: `dask` e `pytest-django` declaram
    `push: tags: ["*"]`, então criar uma tag dispara um workflow extra via
    `push` (o GitHub trata tag como push). Nenhum dos 12 dispara `push` em
    branch fora da default, então a branch isola a repetição sem ruído.

    O isolamento também vem de `github.ref`, que entra no nome do grupo de
    `concurrency`: cada repetição cai num grupo diferente, então elas não se
    cancelam entre si — e `cancel-in-progress` continua valendo para push/PR
    de verdade, sem precisar mexer no bloco `concurrency` de nenhum workflow.
    """
    result = {}
    for entry in plan:
        repo, branch, sha = entry["repo"], entry["branch"], entry["sha"]
        wanted = {ref_name(r, prefix): sha for r in range(1, entry["reps"] + 1)}
        existing = {
            b["name"]: b["commit"]["sha"]
            for b in api.paginate(f"/repos/{OWNER}/{repo}/branches")
        }
        stale = {
            name: target
            for name, target in wanted.items()
            if existing.get(name) not in (None, target)
        }
        to_create = [n for n in wanted if n not in existing]
        entry["refs_created"] = len(to_create)
        entry["refs_moved"] = len(stale)
        entry["refs"] = wanted
        result[repo] = {"created": len(to_create), "moved": len(stale), "sha": sha}
        if not to_create and not stale:
            print(f"   {repo:18} {len(wanted)} branches já no lugar ({sha[:8]})")
            continue
        # Só mover uma branch que já existe é destrutivo e por isso exige
        # --repoint. Criar branch nova não toca em nada existente, então segue
        # sem a flag. Antes as duas coisas eram tratadas igual, o que fazia um
        # `run` limpo (sem branches) pedir --repoint à toa.
        if stale and not repoint:
            sys.exit(
                f"{repo}: as branches {sorted(stale)} apontam para outro SHA que "
                f"{sha[:8]}. Rode com --repoint pra mover."
            )
        # apontar uma ref num commit que já existe é só POST /git/refs — não
        # precisa montar blob/tree/commit, então nenhum clone é necessário.
        # Mover é DELETE + POST; não é atômico, mas recriar é idempotente e
        # barato, então basta rodar de novo se o processo morrer no meio.
        for name in stale:
            api.request(
                "DELETE", f"/repos/{OWNER}/{repo}/git/refs/heads/{name}"
            )
        for name in list(stale) + to_create:
            api.post(
                f"/repos/{OWNER}/{repo}/git/refs",
                {"ref": f"refs/heads/{name}", "sha": sha},
            )
        print(
            f"   {repo:18} {len(to_create)} branches criadas, "
            f"{len(stale)} movidas -> {sha[:8]}"
        )
    return result


# ---------------------------------------------------------------- dispatch


def dispatch(api: Api, repo: str, workflow_file: str, ref: str) -> None:
    path = urllib.parse.quote(workflow_file)
    api.post(
        f"/repos/{OWNER}/{repo}/actions/workflows/{path}/dispatches", {"ref": ref}
    )


def correlate(
    poller: Poller,
    repo: str,
    ref: str,
    since: str,
    wait_seconds: float = 0.0,
) -> tuple[int | None, str]:
    """Acha o run_id da repetição disparada em `ref`.

    O nome da branch já é único por repetição, então casar `head_branch == ref`
    basta — não precisa de fallback por `head_sha`.

    Dois filtros são obrigatórios, ambos vindos de bugs reais do teste no dask:
      - `event == workflow_dispatch`: a API lista também runs de `push`/`schedule`
        na mesma branch, e sem isso o run escolhido era o errado.
      - `created_at >= since`: a mesma ref pode ter runs antigos de uma execução
        anterior (`--restart`, ou branch reaproveitada); sem esse corte o "mais
        antigo" seria sempre o run velho.

    O GitHub leva ~10-20s pra materializar o run depois do 204 do dispatch, então
    com `wait_seconds` > 0 isso tenta algumas vezes antes de desistir.
    """
    deadline = time.monotonic() + max(0.0, wait_seconds)
    while True:
        poller.poll()
        hits = [
            r
            for r in poller.runs_for_ref(repo, ref)
            if r.get("event") == "workflow_dispatch" and r["created_at"] >= since
        ]
        if hits:
            hits.sort(key=lambda r: r["created_at"], reverse=True)
            method = "head_branch_match" if len(hits) == 1 else "head_branch_match_multi"
            return hits[0]["id"], method

        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return None, "unmatched"
        time.sleep(min(10, remaining))


def fmt_hms(seconds: float | None) -> str:
    if seconds is None:
        return "-"
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h:d}h{m:02d}m{s:02d}s" if h else f"{m:d}m{s:02d}s"


def job_intervals(runs: list[dict]) -> list[tuple[float, float]]:
    """Intervalos (início, fim) de cada job que de fato rodou.

    Base das métricas de custo/concorrência do relatório: em vez de estimar
    pelo YAML, usa os `started_at`/`completed_at` reais de cada job.
    """
    out = []
    for r in runs:
        for job in r.get("jobs") or []:
            start, end = job.get("started_at"), job.get("completed_at")
            if not start or not end:
                continue
            try:
                out.append((datetime.fromisoformat(start).timestamp(),
                            datetime.fromisoformat(end).timestamp()))
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
    """Relatório Markdown: custo da execução + testes flaky por repo.

    Custo vem dos `started_at`/`completed_at` reais de cada job, não de
    estimativa de YAML. Flaky vem de `flaky` (nodeid -> contagem por outcome),
    preenchido na fase de análise de logs.
    """
    runs = manifest["runs"]
    by_task = {r["task"]: r for r in runs}
    counters = manifest.get("counters", {})
    wall = manifest.get("wall_clock", {})
    slots = manifest.get("slots", {})

    intervals = job_intervals(runs)
    minutes = runner_minutes(intervals)

    dispatched = sorted(r["dispatched_at_utc"] for r in runs if r.get("dispatched_at_utc"))
    concluded = sorted(r["conclusion_at_utc"] for r in runs if r.get("conclusion_at_utc"))
    makespan = None
    if dispatched and concluded:
        makespan = (
            datetime.fromisoformat(concluded[-1]) - datetime.fromisoformat(dispatched[0])
        ).total_seconds()

    L = [
        "# Flaky runner — relatório",
        "",
        "## Custo",
        "",
        f"- Início: `{wall.get('started_utc', '-')}`",
        f"- Fim: `{wall.get('finished_utc', '-')}`",
        f"- Wall-clock do processo: **{fmt_hms(wall.get('total_seconds'))}**",
        f"- Janela real dos runs (1º dispatch → última conclusão): **{fmt_hms(makespan)}**",
        f"- Minutos de runner somados: **{minutes} min**",
        f"- Pico de concorrência medido: **{peak_concurrency(intervals)}** jobs",
        f"- Teto configurado: {slots.get('budget', '-')} slots",
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

    for entry in plan:
        repo = entry["repo"]
        rows = [by_task[task_key(repo, r)] for r in range(1, entry["reps"] + 1)
                if task_key(repo, r) in by_task]
        if not rows:
            continue
        fin = [r["conclusion_at_utc"] for r in rows if r.get("conclusion_at_utc")]
        sta = [r["dispatched_at_utc"] for r in rows if r.get("dispatched_at_utc")]
        repo_ms = (
            (datetime.fromisoformat(max(fin)) - datetime.fromisoformat(min(sta))).total_seconds()
            if fin and sta
            else None
        )
        L.append("| " + " | ".join([
            repo,
            str(entry["reps"]),
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
        L += [
            "| repo | testes | flaky | taxa |",
            "|---|---|---|---|",
        ]
        for entry in plan:
            rows = (flaky.get(entry["repo"]) or {}).get("tests") or {}
            total = (flaky.get(entry["repo"]) or {}).get("total_seen") or 0
            if not total:
                continue
            n = len(rows)
            L.append(
                f"| {entry['repo']} | {total} | {n} | "
                f"{(100.0 * n / total):.1f}% |"
            )
        L.append("")
        for entry in plan:
            rows = (flaky.get(entry["repo"]) or {}).get("tests") or {}
            if not rows:
                continue
            L += [
                f"### {entry['repo']}",
                "",
                "| teste | reps | falhou | passou |",
                "|---|---|---|---|",
            ]
            for nodeid, counts in sorted(rows.items(), key=lambda kv: -kv[1]["failed"]):
                L.append(
                    f"| `{nodeid}` | {counts['reps']} | {counts['failed']} | "
                    f"{counts['passed']} |"
                )
            L.append("")

    bad = [r for r in runs if r.get("conclusion") == "cancelled"]
    if bad:
        L += ["## Canceladas (investigar)", "",
              "| repo | rep | ref | run_id |", "|---|---|---|---|"]
        for r in bad:
            L.append(
                f"| {r['repo']} | r{r['rep']:02d} | `{r['ref']}` | {r.get('run_id', '-')} |"
            )
        L.append("")

    unmatched = [r for r in runs if not r.get("run_id")]
    if unmatched:
        L += [
            "## Sem run_id localizado",
            "",
            "Repetição despachada cujo run não foi encontrado: a análise de flaky "
            "abaixo fica **incompleta** para esses repos.",
            "",
            "| repo | rep | ref | despachado_em |",
            "|---|---|---|---|",
        ]
        for r in unmatched:
            L.append(
                f"| {r['repo']} | r{r['rep']:02d} | `{r['ref']}` | {r['dispatched_at_utc']} |"
            )
        L.append("")

    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- commands


def cmd_verify(api: Api, args) -> int:
    """Pré-flight: confere que cada workflow aceita `workflow_dispatch`."""
    plan = load_plan(PLAN_PATH, args.repo, args.reps)
    print(f"Plano: {len(plan)} repos, {sum(e['reps'] for e in plan)} repetições\n")

    print("Rate limit inicial:", api.rate_limit())
    print("\nPré-requisitos:")
    info = read_workflow(api, plan)
    blockers = 0
    for entry in plan:
        key = f"{entry['repo']}/{entry['workflow_file']}@{entry['branch']}"
        wf = info.get(key) or {}
        if wf.get("error"):
            print(f"   {key:46} FALHOU ao ler o workflow: {wf['error']}")
            blockers += 1
            continue
        if not wf["has_workflow_dispatch"]:
            print(f"   {key:46} FALTA 'workflow_dispatch:' no on:")
            blockers += 1
            continue
        conc = wf.get("concurrency")
        group = conc.get("group") if isinstance(conc, dict) else conc
        print(f"   {key:46} ok  group={str(group)[:40]}")

    if blockers:
        print(f"\n{blockers} repo(s) bloqueado(s): sem workflow_dispatch não dá "
              f"para disparar.")
        return 1

    print("\nTudo pronto para rodar.")
    return 0


def refresh_status(poller: Poller, manifest: dict) -> list[dict]:
    """Relê o estado de cada run do manifest (status/conclusion/attempts).

    Usado tanto pelo drain do `run` quanto por `status`/`report`, pra que rodar
    com `--no-wait` não deixe as conclusões permanentemente vazias.
    """
    poller.poll()
    rows = [r for r in manifest["runs"] if r.get("run_id")]
    for r in rows:
        run = poller.run(r["repo"], r["run_id"])
        if not run:
            continue
        r["status"] = run["status"]
        r["conclusion"] = run["conclusion"]
        r["run_attempt"] = run["run_attempt"]
        r["conclusion_at_utc"] = run["updated_at"]
        r["html_url"] = run["html_url"]
        jobs = poller.api.get(
            f"/repos/{OWNER}/{r['repo']}/actions/runs/{r['run_id']}/jobs?per_page=100"
        )
        r["jobs_total"] = jobs.get("total_count", 0)
        r["jobs"] = [
            {"name": j["name"], "conclusion": j["conclusion"],
             "started_at": j["started_at"], "completed_at": j["completed_at"]}
            for j in jobs.get("jobs", [])
        ]
    return rows


def cmd_status(api: Api, args) -> int:
    manifest = load_manifest()
    runs = manifest["runs"]
    if not runs:
        print("manifest vazio")
        return 0
    poller = Poller(api, sorted({r["repo"] for r in runs}))
    refresh_status(poller, manifest)
    save_json(MANIFEST_PATH, manifest)
    by_conclusion: dict[str, int] = {}
    for r in runs:
        key = r.get("conclusion") or r.get("status") or "desconhecido"
        by_conclusion[key] = by_conclusion.get(key, 0) + 1
    print(f"repetições no manifest: {len(runs)}")
    for key, count in sorted(by_conclusion.items()):
        print(f"   {key:12} {count}")
    print(f"slots ocupados agora: {poller.occupied} (pico {poller.peak})")

    unmatched = [r for r in runs if not r.get("run_id")]
    if unmatched:
        print(f"\n{len(unmatched)} sem run_id (reconciliar com --repoint + run):")
        for r in unmatched:
            print(f"   {r['task']} ref={r['ref']} despachado={r.get('dispatched_at_utc')}")
    return 0


def cmd_report(api: Api, args) -> int:
    manifest = load_manifest()
    if manifest["runs"] and not args.no_refresh:
        poller = Poller(api, sorted({r["repo"] for r in manifest["runs"]}))
        refresh_status(poller, manifest)
        save_json(MANIFEST_PATH, manifest)
    plan = load_plan(PLAN_PATH, args.repo, args.reps)
    text = build_report(manifest, plan, load_flaky())
    REPORT_PATH.write_text(text, encoding="utf-8")
    save_json(DATA / "flaky_report.json", manifest)
    print(text)
    print(f"\nSalvo em {REPORT_PATH}")
    return 0


def cmd_run(api: Api, args) -> int:
    plan = load_plan(PLAN_PATH, args.repo, args.reps)
    manifest = load_manifest()

    # pré-requisitos
    wf_info = read_workflow(api, plan)
    blocked = []
    for entry in plan:
        key = f"{entry['repo']}/{entry['workflow_file']}@{entry['branch']}"
        info = wf_info.get(key) or {}
        if not info.get("has_workflow_dispatch"):
            blocked.append(entry["repo"])
    if blocked and not args.force:
        sys.exit(
            "workflow_dispatch ausente em: "
            + ", ".join(blocked)
            + "\nRode `flaky_runner.py verify` e aplique os patches, ou use --force."
        )

    # SHA fixo + uma branch por repetição
    for entry in plan:
        entry["sha"] = args.sha or resolve_sha(api, entry["repo"], entry["branch"])
    if args.dry_run:
        for entry in plan:
            print(
                f"   {entry['repo']:18} {entry['sha'][:8]}  "
                f"{entry['reps']} reps -> {ref_name(1, args.prefix)}.."
                f"{ref_name(entry['reps'], args.prefix)}"
            )
        total = sum(e["reps"] for e in plan)
        print(f"\nDRY RUN: {total} execuções de workflow, {args.budget} slots")
        return 0

    print("\nPreparando branches das repetições:")
    prep_refs(api, plan, args.prefix, args.repoint)

    tasks = build_tasks(plan)
    by_task = {r["task"]: r for r in manifest["runs"]}
    todo = list(tasks)
    if not args.restart:
        already = {
            key for key, row in by_task.items() if row.get("dispatched_at_utc")
        }
        skipped = [t for t in todo if t["task"] in already]
        if skipped:
            print(f"\n--resume: {len(skipped)} repetição(ões) já despachada(s), pulando")
        todo = [t for t in todo if t["task"] not in already]

    started = time.time()
    manifest.setdefault("wall_clock", {})["started_utc"] = now()
    manifest["rate_limit"] = {"initial": api.rate_limit()}
    manifest.setdefault("slots", {})["budget"] = args.budget
    poller = Poller(api, [e["repo"] for e in plan])

    def persist() -> None:
        manifest["runs"] = sorted(
            manifest["runs"], key=lambda r: r["task"]
        )
        manifest["counters"] = api.counters
        wall = manifest["wall_clock"]
        wall["updated_utc"] = now()
        wall["elapsed_seconds"] = round(time.time() - started, 1)
        save_json(MANIFEST_PATH, manifest)

    def estimate_jobs(repo: str) -> int:
        """Maior nº de jobs já observado nesse repo; 1 enquanto não se sabe.

        A estimativa estática do YAML foi removida. Em vez de adivinhar antes,
        a trava de orçamento aprende com o que o GitHub de fato criou: depois
        da primeira repetição de cada repo o número já é exato.
        """
        seen = [r.get("jobs_total") or 0 for r in manifest["runs"] if r["repo"] == repo]
        return max(seen) or 1

    print(f"\nDespachando {len(todo)} repetições (budget={args.budget})...\n")
    for i, task in enumerate(todo, 1):
        repo, ref = task["repo"], ref_name(task["rep"], args.prefix)
        jobs_needed = estimate_jobs(repo)
        since = now()
        row = by_task.get(task["task"]) or {
            "task": task["task"],
            "repo": repo,
            "rep": task["rep"],
            "ref": ref,
            "workflow_file": task["workflow_file"],
            "branch": task["branch"],
            "sha": task["sha"],
            "jobs_expected": jobs_needed,
        }
        by_task[task["task"]] = row
        if row not in manifest["runs"]:
            manifest["runs"].append(row)

        if args.budget:
            waited = 0.0
            while True:
                poller.poll()
                free = args.budget - poller.occupied
                if free >= jobs_needed:
                    break
                wait = min(args.poll_interval, max(5, (jobs_needed - free) * 15))
                waited += wait
                print(
                    f"   ⏳ {ref:<14} ocupado={poller.occupied}/{args.budget} "
                    f"preciso={jobs_needed} → espero {wait:.0f}s"
                )
                time.sleep(wait)
                persist()

        try:
            dispatch(api, repo, task["workflow_file"], ref)
            row["dispatched_at_utc"] = now()
            row["dispatch_window_start_utc"] = since
            print(
                f"   [{i}/{len(todo)}] {repo:18} {ref:<14} "
                f"{jobs_needed:>2} jobs (ocupado={poller.occupied})"
            )
        except Exception as exc:
            row["dispatch_error"] = str(exc)
            print(f"   [{i}/{len(todo)}] {repo:18} {ref:<14} FALHOU: {exc}")

        # localiza o run_id, tolerando a demora do GitHub pra criar o run
        try:
            run_id, method = correlate(
                poller, repo, ref, since, wait_seconds=args.correlate_wait
            )
            row["run_id"] = run_id
            row["correlation_method"] = method
            row["html_url"] = (
                f"https://github.com/{OWNER}/{repo}/actions/runs/{run_id}"
                if run_id
                else None
            )
            if run_id is None:
                print(
                    f"       ! run_id não localizado para {ref}; "
                    f"rode `status`/`report` depois pra reconciliar"
                )
        except Exception as exc:
            row["correlation_error"] = str(exc)
        persist()

    # drain: espera as repetições já despachadas terminarem
    if not args.no_wait:
        print("\nAguardando as repetições já despachadas terminarem (Ctrl-C para sair)...")
        while True:
            pending = refresh_status(poller, manifest)
            done = sum(1 for r in pending if r.get("status") in DONE)
            print(
                f"   {done}/{len(pending)} concluídas, "
                f"{poller.occupied} slots ocupados",
                end="\r",
            )
            persist()
            outstanding = [r for r in manifest["runs"] if r.get("status") not in DONE]
            if not outstanding:
                break
            time.sleep(args.poll_interval)
        print()

    manifest["wall_clock"]["finished_utc"] = now()
    manifest["wall_clock"]["total_seconds"] = round(time.time() - started, 1)
    manifest["rate_limit"]["final"] = api.rate_limit()
    persist()
    print(f"\nManifesto: {MANIFEST_PATH}")
    print("Relatório:  python flaky_runner.py report")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Dispara N repetições do workflow de teste de cada fork, uma branch "
            "por repetição, respeitando o teto de jobs simultâneos da conta."
        )
    )
    # Flags aceitos antes ou depois do subcomando: definimos no parser principal
    # e replicamos nos subparsers com default SUPPRESS, para o default do
    # subparser não sobrescrever o valor já parseado.
    flags = [
        ("--repo", dict(action="append", help="restringe a um repo (repetível)")),
        ("--reps", dict(type=int, help="sobrescreve o número de repetições")),
        ("--sha", dict(help="fixa o SHA em vez de resolver a branch")),
        ("--budget", dict(type=int, default=20, help="máx de jobs simultâneos")),
        ("--prefix", dict(default="flaky-r", help="prefixo das branches")),
        ("--poll-interval", dict(type=float, default=60.0)),
        ("--correlate-wait", dict(
            type=float, default=60.0,
            help="espera até N s pelo run_id aparecer após o dispatch")),
        ("--repoint", dict(action="store_true", help="move branches divergentes")),
        ("--restart", dict(action="store_true", help="redespacha tudo")),
        ("--no-wait", dict(action="store_true", help="sai sem aguardar o drain")),
        ("--dry-run", dict(action="store_true")),
        ("--force", dict(action="store_true", help="ignora pré-requisitos")),
        ("--no-refresh", dict(
            action="store_true",
            help="report: não relê o estado dos runs antes de gerar")),
    ]
    for name, opts in flags:
        parser.add_argument(name, **opts)

    sub = parser.add_subparsers(dest="cmd", required=True)
    for name, fn, help_ in (
        ("verify", cmd_verify, "confere que cada workflow aceita workflow_dispatch"),
        ("run", cmd_run, "cria as branches e despacha as repetições"),
        ("status", cmd_status, "mostra o estado do manifest"),
        ("report", cmd_report, "gera o relatório markdown"),
    ):
        p = sub.add_parser(name, help=help_)
        for flag, opts in flags:
            sub_opts = dict(opts)
            if flag in ("--budget", "--prefix", "--poll-interval", "--correlate-wait"):
                sub_opts.pop("default")
            p.add_argument(flag, default=argparse.SUPPRESS, **sub_opts)
        p.set_defaults(func=fn)
    args = parser.parse_args()

    if not TOKEN:
        print(
            "AVISO: sem token. Defina GITHUB_TOKEN_REGSMART (ou rode gh auth login).",
            file=sys.stderr,
        )
    if args.cmd != "verify" and not TOKEN:
        sys.exit("token obrigatório para criar branches e despachar")

    api = Api(TOKEN)
    sys.exit(args.func(api, args))


if __name__ == "__main__":
    main()
