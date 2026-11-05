#!/usr/bin/env python3
"""
Pega os N PRs de experimento mais recentes de cada repo, olha as labels e resume:
só positivo / só negativo / misto / sem classificação (+ flags de limitação e fallback).

PRs de infraestrutura (sem nenhuma label de experimento, ex.: "track-flaky: trigger CI",
"Ajeita workflows") são ignorados antes de pegar os N mais recentes.

Uso:
    export GITHUB_TOKEN=ghp_xxx      # opcional, mas evita rate limit
    python3 check_previous_results.py
"""
import csv
import os
import re
from collections import Counter

import requests

# ---------------- CONFIG (ajusta aqui) ----------------
OWNER = "leticosta4"
REPOS = ["librosa", "apscheduler", "pytest-django", "trimesh",
         "networkx", "pytest-xdist", "pytorch-lightning", "aeon",
         "dvc", "dask", "ultralytics", "ipython"]
PRS_POR_REPO = 5
ESTADO = "all"  # "open", "closed" ou "all"

# nomes EXATOS das labels (a comparação ignora maiúsculas/minúsculas)
POSITIVAS = {
    "BOM-menor-tempo-geral",
    "BOM-regsmart-recentfail",
    "BOM-regsmart-rts-only",
    "BOM-regsmart-QTF",
}
NEGATIVAS = {
    "MAL-baseline-melhor",
    "MAL-demorou-mais",
    "MAL-selecao-bugada",
}
LIMITACOES = {
    "SAD-limitacao-callgraph",
    "SAD-limitacao-gitdiff",
}
FALLBACKS = {
    "fallback-nivel-arquivo",
    "fallback-suite-inteira",
}
# contexto/observações: não entram na classificação, só são contadas
OUTRAS = {
    "ALT-mutante-bugada",
    "ALT-mutante-modificada",
    "PROB-od-flakiness",
}

CSV_SAIDA = os.path.join("data", "previous_results.csv")
# -------------------------------------------------------

TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {"Accept": "application/vnd.github+json",
           "X-GitHub-Api-Version": "2022-11-28"}
if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"


def _lower(s):
    return {x.lower() for x in s}


POS, NEG, LIM, FALL, OUT = map(_lower, (POSITIVAS, NEGATIVAS, LIMITACOES, FALLBACKS, OUTRAS))
CONHECIDAS = POS | NEG | LIM | FALL | OUT
RE_MUTANTE = re.compile(r"\bm(?:utation\s*)?(\d{3,})\b", re.IGNORECASE)


def buscar_prs(repository):
    """Todos os PRs do repo (paginado), do mais recente pro mais antigo."""
    url = f"https://api.github.com/repos/{repository}/pulls"
    params = {"state": ESTADO, "sort": "created", "direction": "desc", "per_page": 100}
    prs = []
    while url:
        r = requests.get(url, headers=HEADERS, params=params, timeout=30)
        r.raise_for_status()
        prs.extend(r.json())
        url = r.links.get("next", {}).get("url")
        params = None  # a URL "next" já traz os parâmetros
    return prs


def eh_experimento(labels):
    """PR de mutante = tem alguma label conhecida ou com prefixo de experimento."""
    return bool(labels & CONHECIDAS) or any(
        l.startswith(("bom-", "mal-", "sad-", "alt-", "prob-", "fallback-")) for l in labels)


def classificar(labels):
    if not labels:
        return "sem_label"
    # prefixo também conta, pra uma label nova "BOM-..." não cair em sem_classificacao
    tem_pos = bool(labels & POS) or any(l.startswith("bom-") for l in labels)
    tem_neg = bool(labels & NEG) or any(l.startswith("mal-") for l in labels)
    if tem_pos and tem_neg:
        return "misto"
    if tem_pos:
        return "so_positivo"
    if tem_neg:
        return "so_negativo"
    return "sem_classificacao"


def main():
    linhas = []
    total = Counter()
    limitacoes_total = fallbacks_total = 0
    desconhecidas = Counter()
    por_label = Counter()
    pendentes = []  # PRs sem BOM/MAL

    for repo in REPOS:
        try:
            todos = buscar_prs(f"{OWNER}/{repo}")
        except requests.RequestException as e:
            print(f"[ERRO] {repo}: {e}")
            continue

        candidatos = [p for p in todos if eh_experimento(_lower(l["name"] for l in p["labels"]))]
        ignorados = [p for p in todos if p not in candidatos]
        prs = candidatos[:PRS_POR_REPO]

        cont = Counter()
        lim_repo = fall_repo = 0
        print(f"\n=== {repo} ({len(prs)} PRs de {len(candidatos)} de experimento; "
              f"{len(ignorados)} sem label ignorados) ===")
        for pr in prs:
            labels = _lower(l["name"] for l in pr["labels"])
            categoria = classificar(labels)
            tem_lim = bool(labels & LIM)
            tem_fall = bool(labels & FALL)
            desconhecidas.update(labels - CONHECIDAS)
            por_label.update(labels & CONHECIDAS)

            cont[categoria] += 1
            lim_repo += tem_lim
            fall_repo += tem_fall
            m = RE_MUTANTE.search(pr["title"])
            linhas.append({
                "repo": repo,
                "pr": pr["number"],
                "mutante": f"m{m.group(1)}" if m else "",
                "titulo": pr["title"],
                "estado": "merged" if pr.get("merged_at") else pr["state"],
                "criado_em": pr["created_at"][:10],
                "categoria": categoria,
                "limitacao": tem_lim,
                "fallback": tem_fall,
                "labels": "; ".join(sorted(labels)),
                "url": pr["html_url"],
            })
            if categoria in ("sem_label", "sem_classificacao"):
                pendentes.append((repo, pr["number"], categoria, pr["html_url"]))
            marca = " [LIMITAÇÃO]" if tem_lim else ""
            marca += " [FALLBACK]" if tem_fall else ""
            if pr["state"] == "closed":
                marca += " [FECHADO]"
            if categoria == "sem_classificacao":
                marca += " [FALTA BOM/MAL!]"
            print(f"  #{pr['number']:<5} {categoria:<18}{marca}  {pr['title'][:60]}")

        total.update(cont)
        limitacoes_total += lim_repo
        fallbacks_total += fall_repo
        print(f"  -> {dict(cont)} | com limitação: {lim_repo} | com fallback: {fall_repo}")
        if ignorados:
            print("  ignorados:", ", ".join(f"#{p['number']}" for p in ignorados))
        if len(prs) < PRS_POR_REPO:
            print(f"  (!) só {len(prs)} PRs de experimento encontrados")

    n_prs = sum(total.values())
    print(f"\n================ TOTAL ({n_prs} PRs) ================")
    for cat in ("so_positivo", "so_negativo", "misto", "sem_classificacao", "sem_label"):
        print(f"{cat:<20} {total[cat]}")
    print(f"{'com limitação':<20} {limitacoes_total}")
    print(f"{'com fallback':<20} {fallbacks_total}")

    print("\nUso por label:")
    for nome, n in por_label.most_common():
        print(f"  {nome:<28} {n}")

    pos, neg = total["so_positivo"], total["so_negativo"]
    if pos > neg:
        veredito = "POSITIVA"
    elif neg > pos:
        veredito = "NEGATIVA"
    else:
        veredito = "EMPATE"
    print(f"\nMaioria (só positivo {pos} vs só negativo {neg}; misto {total['misto']} fora): {veredito}")

    if pendentes:
        print(f"\n(!) {len(pendentes)} PR(s) ainda sem classificação BOM/MAL:")
        for repo, num, cat, url in pendentes:
            print(f"  {repo}#{num}  {url}")
    else:
        print("\nTodos os PRs têm classificação BOM/MAL.")

    if desconhecidas:
        print("\nLabels que não bateram com nenhum conjunto (confere se não é typo):")
        for nome, n in desconhecidas.most_common():
            print(f"  {nome}  ({n}x)")

    if linhas:
        os.makedirs(os.path.dirname(CSV_SAIDA) or ".", exist_ok=True)
        with open(CSV_SAIDA, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(linhas[0].keys()))
            w.writeheader()
            w.writerows(linhas)
        print(f"\nCSV salvo em {CSV_SAIDA}")


if __name__ == "__main__":
    main()
