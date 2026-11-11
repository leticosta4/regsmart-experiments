"""tabela_final.py: gera a tabela final dos nove modos, agrupada para todos os repos,
pronta para a monografia (LaTeX) e para conferência (CSV).

Lê o runs.csv do metrics_collector.py (uma linha por leg) e agrega em duas etapas:
  1. por (repo, mutante, modo): estatística entre as repetições (--rep-stat, padrão mediana);
  2. por (repo, modo): estatística entre os mutantes (--mut-stat, padrão média).
     Faltas omitidas são SOMADAS entre os mutantes, e a % de faltas detectadas é
     100 × Σ detectadas / Σ faltas do repo (as duas a partir dos valores da etapa 1).
A linha "Média" é a média entre os repos; "Razão vs. baseline" é a média, entre os
repos, da razão modo/baseline de cada repo (não a razão das médias).

Saídas (padrão em data/<campanha>/metrics/tables/final/):
  tabela_final.tex          tabela completa (longtable): um bloco por métrica, uma linha por repo
  tabela_final_resumo.tex   só as linhas Média/Total/Razão de cada bloco (cabe em uma página)
  tabela_final.csv          mesmos números da completa, sem formatação (ponto decimal)
  tabela_final_resumo.csv   mesmos números do resumo

No preâmbulo da monografia: \\usepackage{booktabs} e \\usepackage{longtable}.

Uso:
  python3 tabela_final.py                                   # campanha flaky, mediana/média
  python3 tabela_final.py --mut-stat median                 # mediana entre mutantes
  python3 tabela_final.py --repo librosa --repo dask        # só alguns repos, nessa ordem
  python3 tabela_final.py --runs-csv outro/runs.csv --out /tmp/tab
"""
from __future__ import annotations

import argparse
import csv
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CAMPAIGN_DIRS = {"flaky": "flaky_mut", "experiment": "experiment"}

# (chave no runs.csv, nome na tabela, grupo) na ordem da tabela de modos (tab:modos-exec) da monografia
MODES = [
    ("baseline", "Padrão", "Baseline"),
    ("ranking:rkn_recentfail", "RecentFail", "pytest-ranking"),
    ("ranking:rkn_qtf", "QTF", "pytest-ranking"),
    ("ranking:rkn_hybrid", "Hybrid", "pytest-ranking"),
    ("ranking:rkn_simchgpath", "SimChgPath", "pytest-ranking"),
    ("regsmart:rgsm_recentfail", "RTS + RecentFail", "pytest-regsmart"),
    ("regsmart:rgsm_qtf", "RTS + QTF", "pytest-regsmart"),
    ("regsmart:rgsm_hybrid", "RTS + Hybrid", "pytest-regsmart"),
    ("regsmart-no-rank", "RTS", "pytest-regsmart"),
]
MODE_KEYS = [m[0] for m in MODES]

# (título do bloco, coluna, casas decimais, linha de razão?, tipo)
#   tipo: agg = estatística entre mutantes; sum = soma entre mutantes; pct = % detectadas
BLOCKS = [
    ("Testes executados (por mutante)", "n_tests", 0, False, "agg"),
    ("Tempo de execução da suíte (s)", "suite_s", 1, True, "agg"),
    ("Tempo total do job (s)", "job_s", 1, True, "agg"),
    ("Tempo até a primeira falha (s)", "ttff_s", 2, True, "agg"),
    ("Overhead: tempo de seleção -- RTS (s)", "rts_s", 2, False, "agg"),
    ("Overhead: tempo de priorização -- RTP (s)", "rtp_s", 3, False, "agg"),
    ("Falhas da mutação detectadas (%)", "detected_pct", 1, False, "pct"),
    ("Falhas da mutação omitidas (soma dos mutantes)", "hidden", 0, False, "sum"),
    (r"\ldots{} das quais não selecionadas pelo RTS", "hidden_not_selected", 0, False, "sum"),
    ("APFDc", "apfdc", 2, False, "agg"),
]
NUMERIC = {"n_tests", "suite_s", "job_s", "ttff_s", "rts_s", "rtp_s", "faults", "detected",
           "hidden", "hidden_not_selected", "apfdc"}


def num(x: str):
    if x is None or x.strip() == "":
        return None
    try:
        return float(x)
    except ValueError:
        return None


def stat(vals, kind: str):
    vals = [v for v in vals if v is not None]
    if not vals:
        return None
    return statistics.median(vals) if kind == "median" else statistics.fmean(vals)


def total(vals):
    vals = [v for v in vals if v is not None]
    return sum(vals) if vals else None


def build(rows: list[dict], repos: list[str], rep_stat: str, mut_stat: str) -> list[dict]:
    """Devolve os blocos: {title, col, dec, kind, rows: [(rótulo, {modo: valor}), ...], summary: [...]}"""
    by_leg = defaultdict(list)
    for r in rows:
        by_leg[(r["repo"], r["mutant"], r["mode"])].append(r)
    # etapa 1: entre repetições
    per_mut = defaultdict(dict)  # (repo, modo) -> {mutante: {col: valor}}
    for (repo, mut, mode), legs in by_leg.items():
        per_mut[(repo, mode)][mut] = {c: stat([num(l.get(c)) for l in legs], rep_stat) for c in NUMERIC}

    blocks = []
    for title, col, dec, ratio, kind in BLOCKS:
        table = {}
        for repo in repos:
            line = {}
            for mode in MODE_KEYS:
                muts = per_mut.get((repo, mode), {})
                if kind == "agg":
                    line[mode] = stat([m[col] for m in muts.values()], mut_stat)
                elif kind == "sum":
                    line[mode] = total([m[col] for m in muts.values()])
                else:  # pct
                    f = total([m["faults"] for m in muts.values()])
                    d = total([m["detected"] for m in muts.values()])
                    line[mode] = 100 * d / f if f else None
            table[repo] = line
        body = [(repo, table[repo]) for repo in repos]
        agg_label = "Total" if kind == "sum" else "Média"
        agg_fn = total if kind == "sum" else (lambda v: stat(v, "mean"))
        summary = [(agg_label, {m: agg_fn([table[r][m] for r in repos]) for m in MODE_KEYS})]
        if ratio:
            rr = {}
            for m in MODE_KEYS:
                vals = [table[r][m] / table[r]["baseline"] for r in repos
                        if table[r][m] is not None and table[r]["baseline"]]
                rr[m] = stat(vals, "mean")
            summary.append(("Razão vs. baseline", rr))
        blocks.append(dict(title=title, col=col, dec=dec, kind=kind, rows=body, summary=summary))
    return blocks


def fmt(v, dec: int) -> str:
    """Formato brasileiro: 1.234,5; '--' para ausente."""
    if v is None:
        return "--"
    s = f"{v:,.{dec}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def tex_escape(s: str) -> str:
    return s.replace("%", r"\%").replace("&", r"\&").replace("_", r"\_")


def mode_header() -> list[str]:
    out = []
    for _, name, _ in MODES:
        if " + " in name:
            a, b = name.split(" + ")
            out.append(rf"\shortstack[r]{{{a} +\\{b}}}")
        else:
            out.append(name)
    return out


def tex_header(first: str = "Projeto") -> list[str]:
    ncol = 1 + len(MODES)
    groups = rf"\textbf{{{first}}} & " + r"\textbf{Baseline} & \multicolumn{4}{c}{\textbf{pytest-ranking}} & " \
             r"\multicolumn{4}{c}{\textbf{pytest-regsmart}} \\"
    return [r"\toprule", groups, r"\cmidrule(lr){3-6}\cmidrule(lr){7-10}",
            " & ".join([""] + [rf"\textbf{{{h}}}" for h in mode_header()]) + r" \\", r"\midrule"], ncol


def tex_row(label: str, vals: dict, dec: int, style: str = "") -> str:
    cells = [fmt(vals[m], dec) for m in MODE_KEYS]
    if style == "bf":
        label, cells = rf"\textbf{{{label}}}", [rf"\textbf{{{c}}}" for c in cells]
    elif style == "it":
        label, cells = rf"\textit{{{label}}}", [rf"\textit{{{c}}}" for c in cells]
    return " & ".join([label] + cells) + r" \\"


def write_tex(path: Path, blocks: list[dict], caption: str, label: str, full: bool, fontsize: str,
              tabcolsep: str):
    head, ncol = tex_header("Projeto" if full else "")
    colspec = "l" + "r" * len(MODES)
    size = [fontsize, rf"\setlength{{\tabcolsep}}{{{tabcolsep}}}"]
    out = ["% gerado por tabela_final.py; não edite à mão", "{"]
    if full:
        out += size + [rf"\begin{{longtable}}{{{colspec}}}",
                rf"\caption{{{caption}}}\label{{{label}}}\\"] + head + [r"\endfirsthead",
                rf"\multicolumn{{{ncol}}}{{l}}{{\small\textit{{(continuação)}}}}\\"] + head + [r"\endhead",
                r"\midrule", rf"\multicolumn{{{ncol}}}{{r}}{{\small\textit{{(continua)}}}}\\", r"\endfoot",
                r"\bottomrule", r"\endlastfoot"]
    else:
        out += [r"\begin{table}[htbp]", r"\centering", rf"\caption{{{caption}}}\label{{{label}}}"] + size + [
                rf"\begin{{tabular}}{{{colspec}}}"] + head
    for i, b in enumerate(blocks):
        if i:
            out.append(r"\midrule")
        out.append(rf"\multicolumn{{{ncol}}}{{l}}{{\textbf{{\textit{{{tex_escape(b['title'])}}}}}}} \\")
        if full:
            for repo, vals in b["rows"]:
                out.append(tex_row(r"\quad " + tex_escape(repo), vals, b["dec"]))
        for j, (lab, vals) in enumerate(b["summary"]):
            out.append(tex_row(r"\quad " + lab, vals, 2 if lab.startswith("Razão") else b["dec"],
                               "bf" if j == 0 and full else ("it" if lab.startswith("Razão") else "")))
    if full:
        out += [r"\end{longtable}", "}"]
    else:
        out += [r"\bottomrule", r"\end{tabular}", r"\end{table}", "}"]
    path.write_text("\n".join(out) + "\n", encoding="utf-8")


def write_csv(path: Path, blocks: list[dict], full: bool):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["metrica", "linha"] + [name for _, name, _ in MODES])
        for b in blocks:
            lines = (b["rows"] if full else []) + b["summary"]
            for lab, vals in lines:
                w.writerow([b["col"], lab] + ["" if vals[m] is None else round(vals[m], 4) for m in MODE_KEYS])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--campaign", choices=sorted(CAMPAIGN_DIRS), default="flaky")
    ap.add_argument("--runs-csv", type=Path, help="padrão: data/<campanha>/metrics/runs.csv")
    ap.add_argument("--out", type=Path, help="padrão: data/<campanha>/metrics/tables/final/")
    ap.add_argument("--repo", action="append", help="restringe/ordena os repos (repetível); padrão: todos, em ordem alfabética")
    ap.add_argument("--rep-stat", choices=["median", "mean"], default="median", help="entre repetições")
    ap.add_argument("--mut-stat", choices=["mean", "median"], default="mean", help="entre mutantes")
    ap.add_argument("--fontsize", default=r"\scriptsize",
                    help=r"tamanho da fonte no LaTeX (padrão \scriptsize, que cabe em 16 cm de largura útil)")
    ap.add_argument("--tabcolsep", default="2pt", help="espaço entre colunas no LaTeX (padrão 2pt)")
    args = ap.parse_args()

    mdir = ROOT / "data" / CAMPAIGN_DIRS[args.campaign] / "metrics"
    src = args.runs_csv or mdir / "runs.csv"
    out = args.out or mdir / "tables" / "final"
    with src.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise SystemExit(f"{src}: vazio")
    present = sorted({r["repo"] for r in rows})
    repos = args.repo or present
    missing = [r for r in repos if r not in present]
    if missing:
        raise SystemExit(f"repo(s) sem linhas em {src}: {', '.join(missing)}")
    unknown = sorted({r["mode"] for r in rows} - set(MODE_KEYS))
    if unknown:
        print(f"aviso: modos ignorados (fora da Tabela 3): {', '.join(unknown)}")

    blocks = build(rows, repos, args.rep_stat, args.mut_stat)
    nmut = len({(r["repo"], r["mutant"]) for r in rows if r["repo"] in repos})
    word = {"median": "mediana", "mean": "média"}
    caption = (f"Comparação dos nove modos em {len(repos)} projetos ({word[args.rep_stat]} das repetições, "
               f"{word[args.mut_stat]} entre os mutantes de cada projeto)")
    out.mkdir(parents=True, exist_ok=True)
    write_tex(out / "tabela_final.tex", blocks, caption, "tab:resultados-completos", True, args.fontsize,
              args.tabcolsep)
    write_tex(out / "tabela_final_resumo.tex", blocks, caption.replace("Comparação", "Resumo da comparação"),
              "tab:resultados-resumo", False, args.fontsize, args.tabcolsep)
    write_csv(out / "tabela_final.csv", blocks, True)
    write_csv(out / "tabela_final_resumo.csv", blocks, False)
    print(f"{len(rows)} legs, {len(repos)} repos, {nmut} mutantes -> {out}/tabela_final{{,_resumo}}.{{tex,csv}}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
