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
    python -m mutation_testing.mutation_gen gen                       # todos os repos do plano
    python -m mutation_testing.mutation_gen gen --repo dask --n 15    # um repo
    python -m mutation_testing.mutation_gen gen --repo dask --append  # completa o que já existe
    python -m mutation_testing.mutation_gen list                      # resumo do que foi gerado

Sem `--append`, `gen` é destrutivo no repo: apaga data/mutmut/patches/<repo>/ e
reescreve o bloco do repo em mutants.json. Com `--append`, os mutantes já
registrados são preservados e o run só completa até o `n` alvo, pulando os
`mutmut_id` que já foram usados.

Custo: o `mutmut run` testa ~8 mutantes/s (medido), então a enumeração é a parte
lenta. O `.mutmut-cache` é guardado em data/mutmut/mutcache/<repo>-<base>.cache e
reaproveitado no run seguinte desde que o `base_sha` seja o mesmo — aí o mutmut
só replaya o status e a fase 4 cai de ~53min para segundos no ipython.

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
import os
import random
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

OWNER = "leticosta4"
ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "mutmut"
PLAN_PATH = DATA / "mutation_plan.json"
FLAKY_PLAN_PATH = ROOT / "data" / "flaky" / "flaky_plan.json"
MUTANTS_PATH = DATA / "mutants.json"
MUTMUT_VERSION = "2.5.1"
DEFAULT_N = 15
TOTAL_PHASES = 6
MUTCACHE_DIR = DATA / "mutcache"
MUTCACHE_NAME = ".mutmut-cache"


def run(args: list[str], cwd: Path | None = None, check: bool = True) -> str:
    res = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    if check and res.returncode:
        raise RuntimeError(f"{' '.join(args)} (rc={res.returncode}):\n{res.stdout}\n{res.stderr}")
    return res.stdout


def run_streaming(cmd: list[str], cwd: Path | None = None, passthrough: bool = True,
                  tail: int = 8192) -> tuple[int, str]:
    """Roda `cmd` repassando o stdout ao vivo e devolve (rc, cauda do output).

    O `mutmut run` é a fase mais longa da geração (medido: ~8 mutantes/s, então
    ~20min em 10k mutantes) e o progresso dele é uma linha em stdout com \\r. Com
    `capture_output=True` esse \\r fica preso no buffer e o terminal parece travado;
    aqui os bytes vão direto no fd 1 e a barra anda na tela. Só a cauda é guardada,
    que é o bastante para o regex de "Failed while creating mutations" e para a
    mensagem de erro.
    """
    proc = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    buf = bytearray()
    fd = proc.stdout.fileno()
    while True:
        chunk = os.read(fd, 65536)
        if not chunk:
            break
        if passthrough:
            sys.stdout.flush()
            os.write(1, chunk)
        buf.extend(chunk)
        if len(buf) > tail:
            del buf[:-tail]
    proc.wait()
    return proc.returncode, buf.decode("utf-8", "replace")


class Progress:
    """Heartbeat de linha única, no estilo de uma barra de progresso.

    Em TTY reescreve a mesma linha com \\r; fora de TTY (pipe, `> log.txt`) imprime
    uma linha nova a cada intervalo, senão o log vira sopa de \\r. Dispara por
    tempo (`every_s`) ou por contagem (`every_n`), o que vier primeiro.
    """

    def __init__(self, label: str, total: int | None = None, enabled: bool = True,
                 every_n: int = 50, every_s: float = 2.0, indent: int = 3):
        self.label = label
        self.total = total
        self.enabled = enabled
        self.every_n = every_n
        self.every_s = every_s
        self.indent = indent
        self.t0 = time.monotonic()
        self.live = False
        self._last_n = -1
        self._last_t = 0.0

    def elapsed(self) -> float:
        return time.monotonic() - self.t0

    def render(self, done: int, extra: str, eta: str | None = None) -> str:
        head = f"{self.label}: {done}" + (f"/{self.total}" if self.total else "")
        parts = [p for p in (head, extra) if p]
        line = " | ".join(parts)
        if eta is not None:
            line += f" | ETA {eta}"
        elif self.total:
            secs = self.elapsed()
            if done < self.total and secs > 0.5:
                line += f" | ETA {(self.total - done) * secs / done:.0f}s"
            line += f" | {secs:.0f}s"
        return " " * self.indent + line

    def update(self, done: int, extra: str = "", eta: str | None = None) -> None:
        if not self.enabled:
            return
        now = time.monotonic()
        if self._last_n >= 0 and done - self._last_n < self.every_n \
                and now - self._last_t < self.every_s:
            return
        self._last_n, self._last_t = done, now
        line = self.render(done, extra, eta)
        if sys.stdout.isatty():
            sys.stdout.write("\r\033[2K" + line[: shutil.get_terminal_size((100, 24)).columns - 1])
            sys.stdout.flush()
            self.live = True
        else:
            print(line, flush=True)

    def clear(self) -> None:
        if self.live:
            sys.stdout.write("\r\033[2K")
            sys.stdout.flush()
            self.live = False


class Phase:
    """Cronometra uma fase da geração: imprime `[k/6] rótulo` ao entrar e
    `[k/6] rótulo  tempo` ao sair. O cabeçalho sai no começo de propósito: nas
    fases longas (mutmut run, amostragem) o usuário precisa saber em qual está.
    """

    def __init__(self, index: int, label: str):
        self.index = index
        self.label = label
        self.t0 = time.monotonic()
        self._live: Progress | None = None

    def __enter__(self) -> "Phase":
        self.t0 = time.monotonic()
        self._clear()
        print(f"   [{self.index}/{TOTAL_PHASES}] {self.label}", flush=True)
        return self

    def __exit__(self, *exc) -> bool:
        self._clear()
        return False

    def heartbeat(self, enabled: bool, total: int | None = None,
                  every_n: int = 50, every_s: float = 2.0) -> Progress:
        prog = Progress(self.label, total, enabled, every_n, every_s)
        self._live = prog
        return prog

    def _clear(self) -> None:
        if self._live is not None:
            self._live.clear()

    def end(self, result: str = "") -> None:
        self._clear()
        header = f"   [{self.index}/{TOTAL_PHASES}] {self.label}"
        print(f"{header}  fim, {time.monotonic() - self.t0:.1f}s", flush=True)
        if result:
            print(f"          {result}", flush=True)


def save_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def rel(path: Path) -> str:
    """Path relativo ao projeto quando dá, senão absoluto (--workdir pode ser fora)."""
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def stash_path(repo: str, base_sha: str) -> Path:
    return MUTCACHE_DIR / f"{repo}-{base_sha}.cache"


def stash_cache(clone: Path, repo: str, base_sha: str) -> Path | None:
    """Tira o .mutmut-cache do clone antes do `git clean -fdxq` (que apagaria) e
    guarda em data/mutmut/mutcache/<repo>-<base>.cache. Devolve o stash, ou None."""
    src = clone / MUTCACHE_NAME
    if not src.is_file():
        return None
    dst = stash_path(repo, base_sha)
    dst.parent.mkdir(parents=True, exist_ok=True)
    with contextlib.suppress(OSError):
        dst.unlink()
    shutil.copy2(src, dst)
    sidecar = dst.with_suffix(".json")
    save_json(sidecar, {
        "repo": repo,
        "base_sha": base_sha,
        "mutmut_version": MUTMUT_VERSION,
        "saved_utc": datetime.now(timezone.utc).isoformat(),
        "size_bytes": dst.stat().st_size,
    })
    return dst


def hide_pyproject(clone: Path) -> Path | None:
    """O mutmut 2.x lê o pyproject.toml com a lib `toml` (parser antigo) no import e
    quebra com TOML válido que ela não entende (ex.: strings multilinha com `\\`).
    Toda a config vai por CLI, então o arquivo é escondido enquanto o mutmut roda."""
    src = clone / "pyproject.toml"
    if not src.is_file():
        return None
    bak = clone / "pyproject.toml.mutgen-bak"
    src.rename(bak)
    return bak


def unhide_pyproject(clone: Path, bak: Path | None) -> None:
    if bak is not None and bak.exists():
        bak.rename(clone / "pyproject.toml")


def restore_cache(clone: Path, repo: str, base_sha: str) -> Path | None:
    """Repõe no clone o cache stashed da MESMA base. Base diferente não casa de
    propósito: o mutmut só valida a versão do schema do cache (cache.py), não o
    código-fonte, então reaproveitar cache de outro commit associaria status aos
    mutantes errados (os ids são posicionais e deslocam quando o código muda)."""
    src = stash_path(repo, base_sha)
    if not src.is_file():
        return None
    dst = clone / MUTCACHE_NAME
    with contextlib.suppress(OSError):
        dst.unlink()
    shutil.copy2(src, dst)
    return dst


def load_plan(only: list[str] | None, default_n: int | None) -> list[dict]:
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
        # --n explícito ganha do plano; senão vale o `n` do plano ou o default
        if default_n is None:
            e.setdefault("n", DEFAULT_N)
        else:
            e["n"] = default_n
    return entries


def ensure_clone(repo: str, branch: str, workdir: Path, url_template: str) -> tuple[Path, str, bool]:
    """Clone (ou atualiza) o fork em workdir/<repo>, limpo e na branch pedida.

    Devolve (caminho, "clone"|"fetch", cache_stashed). O `.mutmut-cache` é salvo
    antes do `git clean -fdxq` (que o apagaria) e pode ser reposto na fase 4.
    """
    dest = workdir / repo
    if not dest.exists():
        workdir.mkdir(parents=True, exist_ok=True)
        run(["git", "clone", "--quiet", "--branch", branch, url_template.format(repo=repo), str(dest)])
        return dest, "clone", False
    base_sha = run(["git", "rev-parse", "HEAD"], cwd=dest).strip()
    stashed = stash_cache(dest, repo, base_sha)
    run(["git", "fetch", "--quiet", "origin", branch], cwd=dest)
    run(["git", "checkout", "--quiet", branch], cwd=dest)
    run(["git", "reset", "--quiet", "--hard", f"origin/{branch}"], cwd=dest)
    run(["git", "clean", "-fdxq"], cwd=dest)
    # Handle case-insensitive filesystem conflicts
    run(["git", "reset", "--quiet", "--hard", f"origin/{branch}"], cwd=dest, check=False)
    run(["git", "clean", "-fdxq"], cwd=dest, check=False)
    return dest, "fetch", stashed is not None


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


FAIL_REASONS = ("apply", "sem_arquivo", "vazio", "check")


def harvest(clone: Path, args, repo: str, mid: int, ids: dict[int, str], out_dir: Path) -> tuple[dict | None, str]:
    """Tenta materializar o mutante `mid` como patch. Devolve (registro, "") ou
    (None, motivo) com motivo em FAIL_REASONS. Deixa a árvore do clone limpa."""
    key = f"{repo}-m{mid:04d}"
    mfile = ids.get(mid)
    try:
        run([args.mutmut, "apply", str(mid)], cwd=clone)
    except Exception:
        if mfile:
            run(["git", "checkout", "--quiet", "--", mfile], cwd=clone)
        return None, "apply"
    try:
        if mfile is None:
            return None, "sem_arquivo"
        patch = run(["git", "diff", "--", mfile], cwd=clone)
    finally:
        if mfile:
            run(["git", "checkout", "--quiet", "--", mfile], cwd=clone)
    if not patch.strip():
        return None, "vazio"
    patch_path = out_dir / f"{key}.patch"
    patch_path.write_text(patch, encoding="utf-8")
    try:
        run(["git", "apply", "--check", str(patch_path)], cwd=clone)
    except Exception:
        with contextlib.suppress(OSError):
            patch_path.unlink()
        return None, "check"
    line = re.search(r"^@@ -(\d+)", patch, re.M)
    return {
        "key": key,
        "mutmut_id": mid,
        "file": mfile,
        "line": int(line.group(1)) if line else None,
        "patch": rel(patch_path),
    }, ""


def _generate(entry: dict, args, existing: list[dict] | None = None) -> dict:
    existing = list(existing or [])
    repo = entry["repo"]
    t_repo = time.monotonic()
    print(f"\n== {repo}", flush=True)

    with Phase(1, "clone") as ph:
        clone, how, had_cache = ensure_clone(repo, args.branch, Path(args.workdir), args.url_template)
        base_sha = run(["git", "rev-parse", "HEAD"], cwd=clone).strip()
        detail = f"{how}: {rel(clone)} @ {args.branch} = {base_sha[:8]}"
        if how == "fetch":
            detail += f" | cache {('guardado' if had_cache else 'inexistente')}"
        ph.end(detail)

    with Phase(2, "selecionar arquivos") as ph:
        srcs = entry.get("src")
        if not srcs:
            raise RuntimeError("defina `src` no mutation_plan.json")
        srcs = [srcs] if isinstance(srcs, str) else srcs
        files = source_files(clone, srcs)
        if not files:
            raise RuntimeError(f"nenhum .py encontrado em {srcs}")
        ph.end(f"{len(files)} .py em {', '.join(srcs)} (testes fora)")

    # o mutmut 2 usa o parso, que não lê sintaxe mais nova (ex.: f-strings aninhadas
    # do 3.12) e ABORTA a execução inteira no primeiro arquivo que não parseia. Então
    # filtra antes, com o próprio parser dele, e registra o que ficou de fora. Custa
    # ~0.15s por arquivo, por isso mostra progresso: em dask são ~1min de silêncio.
    skipped: list[str] = []
    check = mutable_checker()
    with Phase(3, f"parseabilidade (parso): {len(files)} arquivos") as ph:
        if not check:
            ph.end("mutmut não está neste Python: pulado")
        else:
            prog = ph.heartbeat(args.progress, total=len(files), every_n=25)
            ok_n = 0
            for done, f in enumerate(files, 1):
                if check(clone / f):
                    ok_n += 1
                else:
                    skipped.append(f)
                prog.update(done, extra=f"ok={ok_n} skip={len(skipped)}")
            files = [f for f in files if f not in set(skipped)]
            ph.end(f"{ok_n} mutável(is), {len(skipped)} ignorado(s) (parso não lê)")

    bak = hide_pyproject(clone)

    # o mutmut exige uma pasta tests/ ou test/ na raiz; em vários forks os testes
    # ficam dentro do pacote, então cria uma vazia (não versionada)
    if not (clone / "tests").exists() and not (clone / "test").exists():
        (clone / "tests").mkdir()

    # `--runner true`: o "teste" é um no-op, então o mutmut só enumera os mutantes
    # (todos aparecem como sobreviventes) sem rodar a suíte de verdade. O exit code
    # é um bitmask (2 = sobreviventes, 4 = timeout, 8 = suspeitos): só o bit 1 é erro.
    # Rede de segurança: se ainda assim um arquivo falhar, tira da lista e repete.
    # Não passa --no-progress pro mutmut quando quer progresso: a barra dele é o
    # único sinal de vida durante a fase mais longa, e ela vem por stdout.
    with Phase(4, "mutmut run --runner true (enumerando; a barra abaixo é do mutmut)") as ph:
        reused = restore_cache(clone, repo, base_sha) if args.reuse_cache else None
        if reused:
            print(f"          cache reusado de {rel(stash_path(repo, base_sha))} "
                  f"(base {base_sha[:8]}) -- mutmut só replaya status, não testa de novo",
                  flush=True)
        elif args.reuse_cache:
            print(f"          cache não encontrado para a base {base_sha[:8]}: "
                  f"reenumerando do zero (é a parte lenta, ~8 mutantes/s)",
                  flush=True)
        retries = 0
        for _ in range(MAX_RETRIES):
            if not files:
                raise RuntimeError("nenhum arquivo mutável sobrou")
            cmd = [args.mutmut, "run", "--runner", "true", "--paths-to-mutate", ",".join(files)]
            if not args.progress:
                cmd.append("--no-progress")
            rc, out = run_streaming(cmd, cwd=clone, passthrough=args.progress)
            if not rc & 1:
                break
            m = re.search(r"Failed while creating mutations for (.+?), for line", out)
            if not m or m.group(1) not in files:
                raise RuntimeError(f"mutmut run falhou (rc={rc}):\n{out[-800:]}")
            files.remove(m.group(1))
            skipped.append(m.group(1))
            retries += 1
        else:
            raise RuntimeError(f"mais de {MAX_RETRIES} arquivos não parseiam")
        ids = parse_results(run([args.mutmut, "results"], cwd=clone))
        if not ids:
            raise RuntimeError(f"{repo}: nenhum mutante encontrado (confira `src` no plano)")
        # o cache é do base atual: salva pra próxima run não precisar reenumar
        stash_cache(clone, repo, base_sha)
        extra = f"{len(ids)} mutantes enumerados em {len(files)} arquivo(s)"
        if reused:
            extra += f" (reaproveitando o cache de {base_sha[:8]})"
        if retries:
            extra += f" (+{retries} reenumeração(ões) por arquivo que o mutmut recusou)"
        ph.end(extra)

    target_n = entry["n"]
    rng = random.Random(f"{args.seed}:{repo}")
    # embaralha todos os mutantes (sem reposição) para amostragem adaptativa
    candidate_ids = list(ids.keys())
    rng.shuffle(candidate_ids)

    # teto de tentativas independente do `n`: com n=5 o teto antigo (150) gastava
    # 0,6% do pool e o run terminava com 2 mutantes, sem explicar por quê
    max_attempts = min(len(ids), max(target_n * 30, args.max_attempts))

    out_dir = DATA / "patches" / repo
    if args.append:
        out_dir.mkdir(parents=True, exist_ok=True)
    else:
        if out_dir.exists():
            shutil.rmtree(out_dir)
        out_dir.mkdir(parents=True)

    if existing:
        missing = [m["key"] for m in existing if not (ROOT / m["patch"]).exists()]
        if missing:
            print(f"   !! {len(missing)} patch(es) de mutants.json sumiram do disco: "
                  f"{', '.join(missing[:5])}{'...' if len(missing) > 5 else ''}", flush=True)

    # no append os mutantes já registrados vêm primeiro e os ids já usados não
    # gastam tentativa: o run só completa a lista até o n alvo
    taken = {m["mutmut_id"] for m in existing}
    mutants: list[dict] = list(existing)
    tally = dict.fromkeys(FAIL_REASONS, 0)
    attempts = 0
    tried: set[int] = set()

    goal = target_n - len(existing)
    label = (f"amostrar {len(existing)}/{target_n} (append), faltam {goal}"
             if args.append else f"amostrar {target_n} de {len(ids)} (max tentativas={max_attempts})")

    with Phase(5, label) as ph:
        prog = ph.heartbeat(args.progress, total=max_attempts, every_n=25, every_s=2.0)

        def extra() -> str:
            novos = len(mutants) - len(existing)
            parts = [f"novos={novos}/{goal}", f"total={len(mutants)}/{target_n}"]
            parts += [f"{k}={v}" for k, v in tally.items() if v]
            return " | ".join(parts)

        for mid in candidate_ids:
            if len(mutants) >= target_n or attempts >= max_attempts:
                break
            if mid in tried:
                continue
            tried.add(mid)
            if mid in taken:
                continue
            attempts += 1
            mutant, reason = harvest(clone, args, repo, mid, ids, out_dir)
            if mutant is None:
                tally[reason] += 1
            else:
                mutants.append(mutant)
                print(f"          + {mutant['key']:<22} {mutant['file']}:{mutant['line']}", flush=True)
            # ETA até bater o n (e não até esgotar max_attempts, que quase nunca
            # acontece): só é confiável depois de algumas dezenas de tentativas
            novos = len(mutants) - len(existing)
            eta = f"{(goal - novos) * attempts / novos:.0f}s" if novos >= 3 else None
            prog.update(attempts, extra=extra(), eta=eta)

        viab = 100.0 * (len(mutants) - len(existing)) / attempts if attempts else 0.0
        detail = (f"{attempts} tentativa(s), viabilidade {viab:.2f}%, "
                  f"rejeitados: {', '.join(f'{k}={v}' for k, v in tally.items() if v) or 'nenhum'}")
        ph.end(detail)

    if len(mutants) < target_n:
        print(f"   !! só {len(mutants)}/{target_n} mutantes; aumente --max-attempts "
              f"(atual {max_attempts}) ou --n", flush=True)

    print(f"   [{TOTAL_PHASES}/{TOTAL_PHASES}] {repo}: {len(mutants)} mutante(s) em "
          f"{rel(out_dir)} | {(time.monotonic() - t_repo) / 60:.1f} min no total",
          flush=True)

    unhide_pyproject(clone, bak)

    return {
        "base_branch": args.branch,
        "base_sha": base_sha,
        "mutmut_version": MUTMUT_VERSION,
        "seed": args.seed,
        "total_generated": len(ids),
        "source_files": len(files) + len(skipped),
        "skipped_files": sorted(skipped),
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "mutants": mutants[:target_n],
    }


def generate(entry: dict, args, existing: list[dict] | None = None) -> dict:
    clone = Path(args.workdir) / entry["repo"]
    try:
        return _generate(entry, args, existing)
    finally:
        unhide_pyproject(clone, clone / "pyproject.toml.mutgen-bak")


def cmd_gen(args) -> int:
    check_mutmut(args.mutmut)
    all_meta = json.loads(MUTANTS_PATH.read_text(encoding="utf-8")) if MUTANTS_PATH.exists() else {}
    for entry in load_plan(args.repo, args.n):
        repo = entry["repo"]
        prev = all_meta.get(repo) or {}
        # sem --append a entrada antiga é descartada de propósito (regerar do zero)
        existing = prev.get("mutants", []) if args.append else []
        try:
            meta = generate(entry, args, existing)
            prev_sha = prev.get("base_sha")
            if existing and prev_sha and prev_sha != meta["base_sha"]:
                print(f"   !! {repo}: a base mudou ({prev_sha[:8]} -> {meta['base_sha'][:8]}); "
                      f"os {len(existing)} mutante(s) preservado(s) vêm da base anterior",
                      flush=True)
            all_meta[repo] = meta
        except Exception as exc:
            print(f"   !! {repo}: {exc}", flush=True)
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
    g.add_argument("--n", type=int, default=None,
                   help=f"mutantes por repo; se omitido vale o `n` do plano ou {DEFAULT_N}")
    g.add_argument("--append", action="store_true",
                   help="preserva o que já está em mutants.json e completa até o `n` alvo")
    g.add_argument("--max-attempts", type=int, default=5000,
                   help="teto de tentativas de amostragem por repo (default 5000)")
    g.add_argument("--reuse-cache", dest="reuse_cache", action="store_true", default=True,
                   help="reaproveita o .mutmut-cache da mesma base (default ligado)")
    g.add_argument("--no-reuse-cache", dest="reuse_cache", action="store_false",
                   help="sempre reenumera mesmo com cache da mesma base")
    g.add_argument("--no-progress", dest="progress", action="store_false", default=True,
                   help="desliga os heartbeats e a barra do mutmut")
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
