#!/usr/bin/env python3
"""
Pega os N PRs mais recentes de cada repo, olha as labels e resume:
só positivo / só negativo / misto / sem classificação (+ flag de limitação).

Uso:
    export GITHUB_TOKEN=ghp_xxx      # opcional, mas evita rate limit
    python3 check_previous_results.py
"""
import csv
import os
from collections import Counter

import requests

# ---------------- CONFIG (ajusta aqui) ----------------
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
# contexto/observações: não entram na classificação, só são contadas
OUTRAS = {
    "ALT-mutante-bugada",
    "ALT-mutante-modificada",
    "PROB-od-flakiness",
}

CSV_SAIDA = "data/previous_results.csv"
# -------------------------------------------------------

TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {"Accept": "application/vnd.github+json"}
if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"

POS = {s.lower() for s in POSITIVAS}
NEG = {s.lower() for s in NEGATIVAS}
LIM = {s.lower() for s in LIMITACOES}
OUT = {s.lower() for s in OUTRAS}
CONHECIDAS = POS | NEG | LIM | OUT


def buscar_prs(repository):
    url = f"https://api.github.com/repos/{repository}/pulls"
    params = {
        "state": ESTADO,
        "sort": "created",
        "direction": "desc",
        "per_page": PRS_POR_REPO,
    }
    r = requests.get(url, headers=HEADERS, params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def classificar(labels):
    if not labels:
        return "sem_label"
    tem_pos, tem_neg = bool(labels & POS), bool(labels & NEG)
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
    limitacoes_total = 0
    desconhecidas = Counter()
    por_label = Counter()
    pendentes = []  # PRs sem label ou sem BOM/MAL

    for repo in REPOS:
        try:
            prs = buscar_prs(repository="leticosta4/" + repo)
        except requests.HTTPError as e:
            print(f"[ERRO] {repo}: {e}")
            continue

        cont = Counter()
        lim_repo = 0
        print(f"\n=== {repo} ({len(prs)} PRs) ===")
        for pr in prs:
            labels = {l["name"].lower() for l in pr["labels"]}
            categoria = classificar(labels)
            tem_lim = bool(labels & LIM)
            desconhecidas.update(labels - CONHECIDAS)
            por_label.update(labels & CONHECIDAS)

            cont[categoria] += 1
            lim_repo += tem_lim
            linhas.append({
                "repo": repo,
                "pr": pr["number"],
                "titulo": pr["title"],
                "estado": "merged" if pr.get("merged_at") else pr["state"],
                "categoria": categoria,
                "limitacao": tem_lim,
                "labels": "; ".join(sorted(labels)),
                "url": pr["html_url"],
            })
            if categoria in ("sem_label", "sem_classificacao"):
                pendentes.append((repo, pr["number"], categoria, pr["html_url"]))
            marca = " [LIMITAÇÃO]" if tem_lim else ""
            if categoria == "sem_label":
                marca += " [SEM LABEL!]"
            elif categoria == "sem_classificacao":
                marca += " [FALTA BOM/MAL!]"
            print(f"  #{pr['number']:<5} {categoria:<18}{marca}  {pr['title'][:60]}")

        total.update(cont)
        limitacoes_total += lim_repo
        print(f"  -> {dict(cont)} | com limitação: {lim_repo}")

        if len(prs) < PRS_POR_REPO:
            print(f"  (!) só {len(prs)} PRs encontrados")

    print("\n================ TOTAL ================")
    for cat in ("so_positivo", "so_negativo", "misto", "sem_classificacao", "sem_label"):
        print(f"{cat:<20} {total[cat]}")
    print(f"{'com limitação':<20} {limitacoes_total}")

    print("\nUso por label:")
    for nome, n in por_label.most_common():
        print(f"  {nome:<28} {n}")

    pos, neg = total["so_positivo"], total["so_negativo"]
    if pos > neg:
        print("\nMaioria (só positivo vs só negativo): POSITIVA")
    elif neg > pos:
        print("\nMaioria (só positivo vs só negativo): NEGATIVA")
    else:
        print("\nEmpate entre só positivo e só negativo")

    if pendentes:
        print(f"\n(!) {len(pendentes)} PR(s) ainda sem classificação BOM/MAL:")
        for repo, num, cat, url in pendentes:
            motivo = "sem nenhuma label" if cat == "sem_label" else "só tem outras labels"
            print(f"  {repo}#{num}  ({motivo})  {url}")
    else:
        print("\nTodos os PRs têm classificação BOM/MAL.")

    if desconhecidas:
        print("\nLabels que não bateram com nenhum conjunto (confere se não é typo):")
        for nome, n in desconhecidas.most_common():
            print(f"  {nome}  ({n}x)")

    if linhas:
        with open(CSV_SAIDA, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=linhas[0].keys())
            w.writeheader()
            w.writerows(linhas)
        print(f"\nCSV salvo em {CSV_SAIDA}")


if __name__ == "__main__":
    main()


    """"
    
    
    """
