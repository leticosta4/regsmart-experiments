"""graficos_monografia.py: gera as três figuras de resultado do Cap. 7 da monografia a partir do runs.csv.

  fig_tempos_log         tempo de execução da suíte (s) por projeto: baseline, pytest-ranking (RecentFail) e
                         pytest-regsmart (RTS + RecentFail), um marcador por configuração na mesma linha,
                         escala logarítmica
  fig_falhas_detectadas  falhas detectadas / não detectadas por projeto, em % do total de falhas de cada
                         projeto (barras 100% empilhadas, verde/vermelho), com "x de y" ao lado
                         (pytest-regsmart, RTS + RecentFail)
  fig_tempo_deteccao     dispersão: tempo de execução relativo ao baseline × % de falhas detectadas
                         (pytest-regsmart, RTS + RecentFail)

Os números saem da mesma agregação das tabelas (tabela_final.build): estatística entre as repetições de cada
(repo, mutante, modo) (--rep-stat, padrão mediana) e depois entre os mutantes de cada repo (--mut-stat, padrão
média). Faltas e detectadas são somadas entre os mutantes, e a % detectada é 100 × Σ detectadas / Σ faltas.
O tempo relativo é a razão tempo do modo / tempo do baseline no mesmo projeto.

Saídas (padrão em data/<campanha>/metrics/figures/): <figura>.png (300 dpi).

Requer matplotlib (pip install matplotlib). Importa o tabela_final.py, que precisa estar na mesma pasta.

Uso:
  python3 graficos_monografia.py                       # campanha flaky, mediana/média
  python3 graficos_monografia.py --out /tmp/figs
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib as mpl  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tabela_final import CAMPAIGN_DIRS, ROOT, build  # noqa: E402

BASE = "baseline"
RK = "ranking:rkn_recentfail"        # pytest-ranking (RecentFail)
RG = "regsmart:rgsm_recentfail"      # pytest-regsmart (RTS + RecentFail)

# ordem dos projetos nas figuras (de cima para baixo)
ORDEM = ["librosa", "dask", "aeon", "apscheduler", "trimesh", "ultralytics", "networkx", "dvc", "ipython",
         "pytorch-lightning", "pytest-django", "pytest-xdist"]

COR_BASE, COR_RK, COR_RG = "#333333", "#0072B2", "#D55E00"
VERDE, VERMELHO = "#2E8B57", "#C0392B"
SERIFA = ["Times New Roman", "Times", "Nimbus Roman", "DejaVu Serif"]

# estilo das figuras 1 e 2 (fonte 9/8/7 pt, eixos abertos, ticks para fora, legenda sem moldura)
ESTILO_BARRAS = {
    "font.family": "serif", "font.serif": SERIFA,
    "font.size": 9, "axes.labelsize": 9, "axes.titlesize": 9, "legend.fontsize": 8,
    "xtick.labelsize": 7, "ytick.labelsize": 7,
    "axes.linewidth": 0.6, "xtick.direction": "out", "ytick.direction": "out",
    "xtick.major.size": 3, "ytick.major.size": 3, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": False,
    "legend.frameon": False, "savefig.dpi": 300, "axes.titlelocation": "left",
    "lines.linewidth": 1.2, "patch.linewidth": 0.6,
}
# estilo da figura 3 (fonte 9 pt em tudo, eixos abertos)
ESTILO_DISPERSAO = {
    "font.family": "serif", "font.serif": SERIFA, "font.size": 9,
    "axes.spines.top": False, "axes.spines.right": False,
    "savefig.dpi": 300,
}


def br(v: float, dec: int) -> str:
    """Número no formato brasileiro (vírgula decimal)."""
    return f"{v:.{dec}f}".replace(".", ",")


def milhar(n: float) -> str:
    """Inteiro com ponto de milhar: 1952 -> 1.952."""
    return f"{int(round(n)):,}".replace(",", ".")


def dados(rows: list[dict], repos: list[str], rep_stat: str, mut_stat: str) -> dict:
    spec = [("tsr", "suite_s", 1, False, "agg"), ("f", "faults", 0, False, "sum"),
            ("d", "detected", 0, False, "sum")]
    b = {blk["col"]: dict(blk["rows"]) for blk in build(rows, repos, rep_stat, mut_stat, spec=spec)}
    out = {}
    for r in repos:
        su, f, d = b["suite_s"][r], b["faults"][r][RG], b["detected"][r][RG]
        out[r] = dict(base_s=su[BASE], rk_s=su[RK], rg_s=su[RG], rg_rel=su[RG] / su[BASE],
                      faltas=f, detectadas=d, pct_det=100 * d / f, pct_nd=100 * (f - d) / f)
    return out


def salvar(fig, out: Path, nome: str):
    fig.savefig(out / f"{nome}.png", bbox_inches="tight")
    plt.close(fig)


def fig_tempos_log(D: dict, out: Path):
    yy = list(range(len(ORDEM)))
    with mpl.rc_context(ESTILO_BARRAS):
        fig, ax = plt.subplots(figsize=(6.3, 4.2))
        for i, r in enumerate(ORDEM):
            v = [D[r]["base_s"], D[r]["rk_s"], D[r]["rg_s"]]
            ax.plot([min(v), max(v)], [i, i], color="#cccccc", lw=1.2, zorder=1)
            ax.axhline(i, color="#f0f0f0", lw=0.6, zorder=0)
        h_rk = ax.scatter([D[r]["rk_s"] for r in ORDEM], yy, marker="s", s=30, color=COR_RK, zorder=4,
                          label="pytest-ranking (RecentFail)")
        h_rg = ax.scatter([D[r]["rg_s"] for r in ORDEM], yy, marker="D", s=30, color=COR_RG, zorder=5,
                          label="pytest-regsmart (RTS + RecentFail)")
        h_b = ax.scatter([D[r]["base_s"] for r in ORDEM], yy, marker="o", s=36, facecolor="none",
                         edgecolor=COR_BASE, lw=1.3, zorder=6, label="Baseline (suíte completa)")
        ax.set_xscale("log")
        ax.set_xticks([40, 60, 100, 200, 400, 600, 1000, 1500])
        ax.minorticks_off()
        ax.xaxis.set_major_formatter(FuncFormatter(lambda v, p: f"{v:.0f}"))
        ax.set_xlim(35, 1700)
        ax.set_yticks(yy)
        ax.set_yticklabels(ORDEM, fontstyle="italic")
        ax.set_ylim(len(ORDEM) - 0.4, -0.6)
        ax.tick_params(axis="y", length=0)
        ax.set_xlabel("Tempo de execução da suíte (s, escala logarítmica)")
        ax.legend([h_b, h_rk, h_rg], [h.get_label() for h in (h_b, h_rk, h_rg)], loc="lower left",
                  bbox_to_anchor=(0, 1.0), ncol=3, frameon=False, fontsize=7.5, handletextpad=0.3,
                  columnspacing=1.0)
        salvar(fig, out, "fig_tempos_log")


def fig_falhas_detectadas(D: dict, out: Path):
    yy = list(range(len(ORDEM)))
    with mpl.rc_context(ESTILO_BARRAS):
        fig, ax = plt.subplots(figsize=(6.3, 4.2))
        h = 0.62
        pdet = [D[r]["pct_det"] for r in ORDEM]
        pnd = [D[r]["pct_nd"] for r in ORDEM]
        ax.barh(yy, pdet, color=VERDE, height=h, zorder=2, label="Detectadas")
        ax.barh(yy, pnd, left=pdet, color=VERMELHO, height=h, zorder=2, label="Não detectadas")
        for i, r in enumerate(ORDEM):
            pd_, pn = D[r]["pct_det"], D[r]["pct_nd"]
            ax.text(2, i, f"{br(pd_, 1) if pd_ < 99.95 else '100'}%", ha="left", va="center", fontsize=7,
                    color="white", fontweight="bold")
            if pn >= 6:
                ax.text(pd_ + pn / 2, i, f"{br(pn, 1)}%", ha="center", va="center", fontsize=7, color="white",
                        fontweight="bold")
            ax.text(102, i, f"{milhar(D[r]['detectadas'])} de {milhar(D[r]['faltas'])}", ha="left",
                    va="center", fontsize=7, clip_on=False)
        ax.text(102, -0.75, "falhas detectadas / total", ha="left", va="center", fontsize=7, fontstyle="italic",
                clip_on=False)
        ax.set_xlim(0, 100)
        ax.set_xticks([0, 25, 50, 75, 100])
        ax.xaxis.set_major_formatter(FuncFormatter(lambda v, p: f"{v:.0f}%"))
        ax.set_yticks(yy)
        ax.set_yticklabels(ORDEM, fontstyle="italic")
        ax.set_ylim(len(ORDEM) - 0.4, -0.6)
        ax.tick_params(axis="y", length=0)
        ax.set_xlabel("Falhas esperadas dos mutantes (%) — pytest-regsmart (RTS + RecentFail)")
        ax.spines["right"].set_visible(False)
        ax.legend(loc="lower left", bbox_to_anchor=(0, 1.02), ncol=2, frameon=False, fontsize=8)
        salvar(fig, out, "fig_falhas_detectadas")


# posição de cada rótulo na dispersão: (x do texto, y do texto, alinhamento, linha de chamada)
#   "ponto"  -> linha do ponto até logo acima do texto (rótulos abaixo do aglomerado em 100%)
#   "acima"  -> traço curto do ponto até logo abaixo do texto (rótulos acima do aglomerado)
#   None     -> rótulo ao lado do ponto, sem linha
ROTULOS = {
    "librosa": (0.32, 104, "center", None), "aeon": (0.72, 104, "center", "acima"),
    "apscheduler": (0.837, 104, "center", "acima"), "dvc": (1.045, 104, "left", None),
    "pytest-django": (1.373, 104, "center", None), "dask": (0.60, 90, "right", "ponto"),
    "networkx": (0.80, 88, "center", "ponto"), "pytorch-lightning": (0.95, 91.5, "center", "ponto"),
    "ipython": (1.05, 94.7, "left", None), "pytest-xdist": (1.305, 96.4, "left", None),
    "ultralytics": (0.835, 79.1, "left", None), "trimesh": (0.34, 41.7, "left", None),
}


def fig_tempo_deteccao(D: dict, out: Path):
    with mpl.rc_context(ESTILO_DISPERSAO):
        fig, ax = plt.subplots(figsize=(6.3, 4.2))
        ax.axvline(1, color="#555", lw=0.9, ls="--", zorder=0)
        ax.axhline(100, color="#bbb", lw=0.7, ls=":", zorder=0)
        ax.scatter([D[r]["rg_rel"] for r in ORDEM], [D[r]["pct_det"] for r in ORDEM], s=34, color=COR_RG,
                   edgecolor="white", lw=0.6, zorder=3)
        for r in ORDEM:
            x, y = D[r]["rg_rel"], D[r]["pct_det"]
            tx, ty, ha, linha = ROTULOS.get(r, (x + 0.02, y, "left", None))
            if linha == "ponto":
                ax.plot([x, tx], [y, ty + 1.0], color="#999", lw=0.6, zorder=1)
            elif linha == "acima":
                ax.plot([x, tx], [y + 0.6, ty - 1.2], color="#999", lw=0.6, zorder=1)
            ax.text(tx, ty, r, ha=ha, va="center", fontsize=7.5, fontstyle="italic", zorder=5,
                    bbox=dict(fc="white", ec="none", pad=0.4))
        ax.set_xlim(0.2, 1.5)
        ax.set_ylim(35, 107)
        ax.xaxis.set_major_formatter(FuncFormatter(lambda v, p: br(v, 2)))
        ax.set_xlabel("Tempo de execução relativo ao baseline (1 = baseline)")
        ax.set_ylabel("Falhas detectadas (%)")
        ax.text(0.98, 36.5, "← mais rápido que o baseline", ha="right", fontsize=7, color="#555")
        ax.set_title("pytest-regsmart (RTS + RecentFail)", fontsize=8.5, loc="left")
        salvar(fig, out, "fig_tempo_deteccao")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--campaign", choices=sorted(CAMPAIGN_DIRS), default="flaky")
    ap.add_argument("--runs-csv", type=Path, help="padrão: data/<campanha>/metrics/runs.csv")
    ap.add_argument("--out", type=Path, help="padrão: data/<campanha>/metrics/figures/")
    ap.add_argument("--rep-stat", choices=["median", "mean"], default="median", help="entre repetições")
    ap.add_argument("--mut-stat", choices=["mean", "median"], default="mean", help="entre mutantes")
    a = ap.parse_args()

    mdir = ROOT / "data" / CAMPAIGN_DIRS[a.campaign] / "metrics"
    src = a.runs_csv or mdir / "runs.csv"
    out = a.out or mdir / "figures"
    with src.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    faltando = [r for r in ORDEM if r not in {row["repo"] for row in rows}]
    if faltando:
        raise SystemExit(f"repo(s) sem linhas em {src}: {', '.join(faltando)}")
    out.mkdir(parents=True, exist_ok=True)

    D = dados(rows, ORDEM, a.rep_stat, a.mut_stat)
    fig_tempos_log(D, out)
    fig_falhas_detectadas(D, out)
    fig_tempo_deteccao(D, out)
    print(f"3 figuras (png) -> {out}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
