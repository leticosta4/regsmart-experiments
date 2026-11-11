"""tabelas_eixos.py: gera as tabelas do Cap. 7 (Validação Experimental), uma por eixo,
prontas para colar na monografia. Usa a mesma agregação do tabela_final.py
(mediana entre repetições, média entre mutantes; ver --rep-stat/--mut-stat).

Tabelas (padrão em data/<campanha>/metrics/tables/eixos/):
  tab_selecao.tex      Segurança da RTS (baseline + 4 modos do regsmart, blocos lado a lado)
  tab_instaveis.tex    Testes flaky (intermitentes e dependentes de ordem) por plugin; projetos sem flaky vão para a nota
  tab_tempo.tex        Tempo da suíte e do job por projeto e modo
  tab_overhead.tex     Tempo de RTS e de RTP como % do tempo da suíte, por projeto e modo
  tab_priorizacao.tex  APFDc e TTFF por projeto e modo
  tabelas_cap7.tex     todas as anteriores, na ordem do capítulo
  tabelas_eixos.csv    números sem formatação, para conferência

Formato: \\begin{center} + minipage (mantém título e tabela juntos) + \\captionof{table} + \\caption*{Fonte}, como a tab:modos-exec.
No preâmbulo: booktabs e caption (para \\captionof).

Uso:
  python3 tabelas_eixos.py
  python3 tabelas_eixos.py --mut-stat median
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tabela_final import CAMPAIGN_DIRS, MODES, MODE_KEYS, ROOT, build, fmt, num, tex_escape, tex_header  # noqa: E402

RTS_MODES = [m for m in MODE_KEYS if m.startswith("regsmart")]           # 4 modos com RTS
RTS_ONLY = "regsmart-no-rank"
RANK_MODES = [m for m in MODE_KEYS if m.startswith("ranking:")]
RTS_RANK_MODES = [m for m in MODE_KEYS if m.startswith("regsmart:")]
FONTE = r"\caption*{\small Fonte: Elaborado pela autora (2026).}"


def mean(v):
    v = [x for x in v if x is not None]
    return statistics.fmean(v) if v else None


def wrap(caption, label, colspec, body, fontsize, tabcolsep, nota=None):
    out = ["% gerado por tabelas_eixos.py; não edite à mão", r"\begin{center}", r"\begin{minipage}{\textwidth}", r"\centering",
           rf"\captionof{{table}}{{{caption}}}", rf"\label{{{label}}}",
           "{" + fontsize, rf"\setlength{{\tabcolsep}}{{{tabcolsep}}}", rf"\begin{{tabular}}{{{colspec}}}"]
    out += body + [r"\bottomrule", r"\end{tabular}", "}"]
    out.append(FONTE)
    if nota:
        out.append(rf"\caption*{{\small Nota: {nota}}}")
    out += [r"\end{minipage}", r"\end{center}"]
    return "\n".join(out) + "\n"


def row(cells):
    return " & ".join(cells) + r" \\"


# ---------------------------------------------------------------- eixos por modo (9 colunas)
def subset_header(keys):
    """Cabeçalho agrupado (Baseline | pytest-ranking | pytest-regsmart) só com os modos em keys."""
    names = {k: n for k, n, _ in MODES}
    groups = [("Baseline", [k for k in keys if k == "baseline"]),
              ("pytest-ranking", [k for k in keys if k.startswith("ranking")]),
              ("pytest-regsmart", [k for k in keys if k.startswith("regsmart")])]
    top, rules, col = [r"\textbf{Projeto}"], [], 2
    for g, ks in groups:
        if not ks:
            continue
        top.append(rf"\textbf{{{g}}}" if len(ks) == 1 else rf"\multicolumn{{{len(ks)}}}{{c}}{{\textbf{{{g}}}}}")
        if len(ks) > 1:
            rules.append(rf"\cmidrule(lr){{{col}-{col + len(ks) - 1}}}")
        col += len(ks)
    def h(n):
        if " + " in n:
            a, b = n.split(" + ")
            return rf"\shortstack[r]{{{a} +\\{b}}}"
        return n
    sub = [""] + [rf"\textbf{{{h(names[k])}}}" for k in keys]
    return [r"\toprule", " & ".join(top) + r" \\", "".join(rules), " & ".join(sub) + r" \\", r"\midrule"], 1 + len(keys)


def mode_table(blocks_by_col, spec, caption, label, fontsize, tabcolsep, nota=None, keys=None):
    """spec: [(col, título, mostrar linhas por repo?)]; keys: subconjunto de modos (padrão: os nove)."""
    keys = keys or MODE_KEYS
    if keys == MODE_KEYS:
        head, ncol = tex_header("Projeto")
    else:
        head, ncol = subset_header(keys)
    body = list(head)

    def line(label_, vals, dec, style=""):
        cells = [fmt(vals[m], dec) for m in keys]
        if style == "bf":
            label_, cells = rf"\textbf{{{label_}}}", [rf"\textbf{{{c}}}" for c in cells]
        elif style == "it":
            label_, cells = rf"\textit{{{label_}}}", [rf"\textit{{{c}}}" for c in cells]
        return " & ".join([label_] + cells) + r" \\"

    for i, (col, title, full) in enumerate(spec):
        b = blocks_by_col[col]
        if i:
            body.append(r"\midrule")
        body.append(rf"\multicolumn{{{ncol}}}{{l}}{{\textbf{{\textit{{{tex_escape(title)}}}}}}} \\")
        if full:
            for repo, vals in b["rows"]:
                body.append(line(r"\quad " + tex_escape(repo), vals, b["dec"]))
        for lab, vals in b["summary"]:
            body.append(line(r"\quad " + lab, vals, 2 if lab.startswith("Relativo") else b["dec"],
                             "it" if lab.startswith("Relativo") else ("bf" if full else "")))
    return wrap(caption, label, "l" + "r" * len(keys), body, fontsize, tabcolsep, nota)



SUB5 = ["baseline"] + [m for m in MODE_KEYS if m.startswith("regsmart")]


def side_table(blocks_by_col, parts, caption, label, fontsize, tabcolsep, nota=None, keys=SUB5):
    """Métricas lado a lado (cada uma com as colunas de keys), uma linha por projeto.
    parts: lista de partes empilhadas; cada parte é uma lista de (col, título)."""
    names = {k: n for k, n, _ in MODES}
    nk = len(keys)
    def h(n):
        if " + " in n:
            a, b = n.split(" + ")
            return rf"\textbf{{\shortstack[r]{{{a} +\\{b}}}}}"
        return rf"\textbf{{{n}}}"
    body = []
    for pi, part in enumerate(parts):
        top, mid, rules1, rules2, sub = [r"\textbf{Projeto}" if pi == 0 else ""], [""], [], [], [""]
        for j, (col, title) in enumerate(part):
            c0 = 2 + j * nk
            top.append(rf"\multicolumn{{{nk}}}{{c}}{{\textbf{{\textit{{{tex_escape(title)}}}}}}}")
            rules1.append(rf"\cmidrule(lr){{{c0}-{c0 + nk - 1}}}")
            mid += [r"\textbf{Baseline}", rf"\multicolumn{{{nk - 1}}}{{c}}{{\textbf{{pytest-regsmart}}}}"]
            rules2.append(rf"\cmidrule(lr){{{c0 + 1}-{c0 + nk - 1}}}")
            sub += [h(names[k]) for k in keys]
        body += ([r"\toprule"] if pi == 0 else [r"\midrule"]) + [row(top), "".join(rules1), row(mid), "".join(rules2),
                 row(sub), r"\midrule"]
        repos = [r for r, _ in blocks_by_col[part[0][0]]["rows"]]
        tabs = [(dict(blocks_by_col[c]["rows"]), blocks_by_col[c]) for c, _ in part]
        for repo in repos:
            cells = [r"\quad " + tex_escape(repo)]
            for t, b in tabs:
                cells += [fmt(t[repo][k], b["dec"]) for k in keys]
            body.append(row(cells))
        cells = []
        for t, b in tabs:
            l, vals = b["summary"][0]
            cells += [rf"\textbf{{{fmt(vals[k], b['dec'])}}}" for k in keys]
        labs = sorted({b["summary"][0][0] for _, b in tabs})
        body.append(row([rf"\textbf{{{' / '.join(labs)}}}"] + cells))
    return wrap(caption, label, "l" + "r" * (nk * max(len(p) for p in parts)), body, fontsize, tabcolsep, nota)


# ---------------------------------------------------------------- instáveis (comparação entre plugins)
WF = {"ranking": "rk", "regsmart": "rp", "regsmart-no-rank": "rts"}


def instaveis(path: Path, repos):
    """Testes distintos por projeto, classe exclusiva por prioridade (falha em todas as execuções > flaky >
    ambiente > dependente de ordem); para OD e 'em todas as execuções', em quais workflows o teste falhou
    (um teste pode aparecer em mais de uma coluna)."""
    data = json.loads(path.read_text(encoding="utf-8"))
    prio = ["fixa", "flaky", "amb", "od"]
    cols = [("flaky",), ("od", "rk"), ("od", "ambos"), ("od", "rp"), ("od", "tot"), ("od", "rts"), ("fixa",), ("amb",)]
    lines, csvrows, tot, zeros = [], [], defaultdict(int), []
    for repo in repos:
        cls, wfs = {}, defaultdict(set)
        for mut, v in data.get(repo, {}).items():
            ctl = mut == "control"
            for t, info in v.get("tests", {}).items():
                c = info["class"]
                k = ("fixa" if c == "só no plugin (fixa)" else "flaky" if c == "flaky" else
                     "amb" if (ctl and c == "esperada") or c == "ambiente (controle)" else
                     "od" if c in ("só no plugin (flaky)", "dependente de ordem (controle)") else None)
                if not k:
                    continue
                if t not in cls or prio.index(k) < prio.index(cls[t]):
                    cls[t] = k
                for w, st in info.get("wf", {}).items():
                    if w in WF and st.get("failed", 0) > 0:
                        wfs[t].add(WF[w])
        n = defaultdict(int)
        for t, k in cls.items():
            if k == "od":
                w = wfs[t]
                g = ("od", "rk") if w == {"rk"} else ("od", "rp") if "rk" not in w else ("od", "ambos")
                n[g] += 1
                n[("od", "tot")] += 1
                if "rts" in w:
                    n[("od", "rts")] += 1
            else:
                n[(k,)] += 1
        for c in cols:
            tot[c] += n[c]
        show = [("flaky",), ("od", "rk"), ("od", "ambos"), ("od", "rp"), ("od", "tot")]
        csvrows.append(["instaveis", repo] + [n[c] for c in cols])
        if any(n[c] for c in show):
            lines.append(row([r"\quad " + tex_escape(repo)] + [str(n[c]) for c in show]
                             + [str(n[("flaky",)] + n[("od", "tot")])]))
        else:
            zeros.append(repo)
    csvrows.append(["instaveis", "Total"] + [tot[c] for c in cols])
    show = [("flaky",), ("od", "rk"), ("od", "ambos"), ("od", "rp"), ("od", "tot")]
    head = [r"\toprule",
            r" & & \multicolumn{4}{c}{\textbf{Dependentes de ordem}} & \\",
            r"\cmidrule(lr){3-6}",
            row([r"\textbf{Projeto}", r"\textbf{Intermitentes}", r"\textbf{só \textit{ranking}}",
                 r"\textbf{ambos}", r"\textbf{só \textit{regsmart}}", r"\textbf{total}", r"\textbf{Total \textit{flaky}}"]),
            r"\midrule"]
    last = row([r"\textbf{Total}"] + [rf"\textbf{{{tot[c]}}}" for c in show]
               + [rf"\textbf{{{tot[('flaky',)] + tot[('od', 'tot')]}}}"])
    nomes = ", ".join(rf"\textit{{{tex_escape(z)}}}" for z in zeros[:-1]) + (rf" e \textit{{{tex_escape(zeros[-1])}}}" if zeros else "")
    nota = ("número de testes \\textit{flaky} distintos por projeto, somando as \\textit{branches} de mutante e a de "
            "controle; cada teste é contado uma única vez. Entre os dependentes de ordem, \\textit{ambos} indica os que "
            f"falharam sob os dois \\textit{{plugins}}; {tot[('od', 'rts')]} deles também falhou no modo do "
            "\\textit{pytest-regsmart} sem RTP. "
            + (f"Os projetos {nomes} não tiveram testes \\textit{{flaky}} e foram omitidos." if zeros else ""))
    tex = wrap(r"Testes \textit{flaky} por projeto e \textit{plugin}", "tab:testes-flaky",
               "lrrrrrr", head + lines + [r"\midrule", last], r"\small", "3pt", nota)
    return tex, csvrows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--campaign", choices=sorted(CAMPAIGN_DIRS), default="flaky")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--repo", action="append")
    ap.add_argument("--rep-stat", choices=["median", "mean"], default="median")
    ap.add_argument("--mut-stat", choices=["mean", "median"], default="mean")
    ap.add_argument("--fontsize", default=r"\scriptsize")
    ap.add_argument("--tabcolsep", default="2pt")
    a = ap.parse_args()
    base = ROOT / "data" / CAMPAIGN_DIRS[a.campaign]
    rows = list(csv.DictReader((base / "metrics" / "runs.csv").open(encoding="utf-8")))
    repos = a.repo or sorted({r["repo"] for r in rows})
    out = a.out or base / "metrics" / "tables" / "eixos"
    out.mkdir(parents=True, exist_ok=True)

    blocks = build(rows, repos, a.rep_stat, a.mut_stat)
    byc = {b["col"]: b for b in blocks}

    w = {"median": "mediana", "mean": "média"}
    agg = f"{w[a.rep_stat]} das repetições, {w[a.mut_stat]} entre os mutantes"
    t_sel = side_table(byc, [[("n_tests", "Testes executados (por mutante)"),
                              ("detected_pct", "Falhas detectadas (%)")],
                             [("hidden", "Falhas omitidas (total)"),
                              ("hidden_not_selected", "Falhas omitidas por não seleção da RTS")]],
                       rf"Segurança da RTS por projeto: \textit{{baseline}} e modos do \textit{{pytest-regsmart}} ({agg})",
                       "tab:selecao-rts", a.fontsize, a.tabcolsep,
                       "o \\textit{pytest-ranking} não aparece porque executa a suíte completa (ver Tabela~\\ref{tab:resultados-completos}). "
                       "Falhas omitidas são falhas esperadas que não ocorreram no modo; as omitidas por não seleção são aquelas "
                       "cujo teste não foi selecionado pela RTS. As demais vêm de testes \\textit{flaky}. Os quatro modos do "
                       "\\textit{pytest-regsmart} selecionam os mesmos testes; falhas somadas entre os cinco mutantes.")
    t_ins, c_ins = instaveis(base / "flaky_tests.json", repos)
    t_tmp = mode_table(byc, [("suite_s", "Tempo de execução da suíte (s)", True),
                             ("job_s", "Tempo total do job (s)", True)],
                       rf"Tempo de execução da suíte e do \textit{{job}} por projeto e modo ({agg})", "tab:tempo",
                       a.fontsize, a.tabcolsep,
                       "a linha \\textit{Relativo ao baseline} é a média, entre os projetos, do tempo do modo dividido pelo tempo do "
                       "\\textit{baseline} no mesmo projeto; valores abaixo de 1 indicam execução mais rápida que o \\textit{baseline}.")
    # overhead em % do tempo da suíte do próprio modo, calculado por execução e agregado como as demais métricas
    for r in rows:
        su = num(r.get("suite_s"))
        for c in ("rts", "rtp"):
            v = num(r.get(f"{c}_s"))
            r[f"{c}_pct"] = "" if v is None or not su else str(100 * v / su)
    ovb = build(rows, repos, a.rep_stat, a.mut_stat,
                spec=[("RTS (% do tempo da suíte)", "rts_pct", 1, False, "agg"),
                        ("RTP (% do tempo da suíte)", "rtp_pct", 2, False, "agg")],
                extra=("rts_pct", "rtp_pct"))
    t_ovh = mode_table({b["col"]: b for b in ovb},
                       [("rts_pct", "Tempo de seleção -- RTS (% do tempo da suíte)", True),
                        ("rtp_pct", "Tempo de priorização -- RTP (% do tempo da suíte)", True)],
                       rf"Custo das etapas de RTS e RTP em relação ao tempo da suíte, por projeto e modo ({agg})",
                       "tab:overhead", a.fontsize, a.tabcolsep,
                       "percentual do tempo de execução da suíte do próprio modo ocupado por cada etapa, calculado em cada "
                       "execução. A seleção ocorre na coleta dos testes, dentro da sessão do \\textit{pytest}, e por isso "
                       "faz parte do tempo da suíte. Os valores em segundos constam da Tabela~\\ref{tab:resultados-completos}.")
    t_pri = mode_table(byc, [("apfdc", "APFDc", True), ("ttff_s", "Tempo até a primeira falha -- TTFF (s)", True)],
                       rf"APFDc e TTFF por projeto e modo ({agg})", "tab:priorizacao", a.fontsize, a.tabcolsep,
                       "nos modos do \\textit{pytest-regsmart}, o APFDc é calculado sobre os testes selecionados e "
                       "o TTFF inclui os tempos de RTS e RTP.")
    files = [("tab_selecao.tex", t_sel, "Segurança da RTS"),
             ("tab_instaveis.tex", t_ins, "Segurança da RTS > Testes flaky"),
             ("tab_tempo.tex", t_tmp, "Impacto no tempo de execução"),
             ("tab_overhead.tex", t_ovh, "Impacto no tempo de execução"),
             ("tab_priorizacao.tex", t_pri, "Eficácia da RTP")]
    allx = []
    for name, tex, where in files:
        (out / name).write_text(tex, encoding="utf-8")
        allx.append(f"%% ===== {name} -- seção: {where}\n{tex}")
    (out / "tabelas_cap7.tex").write_text("\n".join(allx), encoding="utf-8")
    with (out / "tabelas_eixos.csv").open("w", newline="", encoding="utf-8") as f:
        wcsv = csv.writer(f, lineterminator="\n")
        wcsv.writerow(["tabela", "projeto", "flaky_intermitentes", "od_so_ranking", "od_ambos", "od_so_regsmart",
                       "od_total", "od_tambem_regsmart_sem_rtp", "so_com_plugin_sempre", "ambiente"])
        for r in c_ins:
            wcsv.writerow([("" if v is None else (round(v, 4) if isinstance(v, float) else v)) for v in r])
    print(f"{len(rows)} legs, {len(repos)} repos -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
