"""Experimento principal: vários agentes jogando os mesmos pares de artigos.

Métricas (as da proposta):

* **razão** = cliques usados / cliques do caminho ótimo (BFS) — só nas
  partidas que o agente terminou;
* **consultados** = quantos artigos o agente leu os links;
* **taxa de sucesso** dentro de um limite de cliques L (calculo para vários L).
"""

from __future__ import annotations

import time

import numpy as np
import pandas as pd

from .busca import bfs_bidirecional_grafo


def sortear_pares(g, k=100, semente=0, max_tentativas=100_000):
    """Sorteia ``k`` pares (s, t), s ≠ t, uniformes entre os pares **com caminho**.

    Sorteio uniforme em V × V e descarte de quem não tem caminho (rejeição).
    O número de descartes também é um dado: estima a fração de pares sem
    caminho. Devolve ``(DataFrame dos pares, número de descartados)``.
    """
    rng = np.random.default_rng(semente)
    pares, descartados = [], 0
    for _ in range(max_tentativas):
        if len(pares) == k:
            break
        s, t = (int(x) for x in rng.integers(0, g.n, 2))
        if s == t:
            continue
        r = bfs_bidirecional_grafo(g, s, t)
        if r.caminho is None:
            descartados += 1
            continue
        pares.append({"par": len(pares), "origem": s, "destino": t,
                      "titulo_origem": g.titulo(s), "titulo_destino": g.titulo(t),
                      "otimo": r.cliques,
                      "caminho_otimo": " → ".join(g.titulo(v) for v in r.caminho)})
    return pd.DataFrame(pares), descartados


def rodar(amb, pares, agentes, max_cliques=50, max_consultas=20_000, semente=0,
          verbose=False):
    """Joga todos os pares com todos os agentes. Uma linha por partida."""
    linhas = []
    inicio = time.time()
    for i, par in enumerate(pares.itertuples()):
        for ag in agentes:
            p = ag.jogar(amb, par.origem, par.destino, max_cliques=max_cliques,
                         max_consultas=max_consultas, semente=semente + par.par)
            linhas.append({
                "par": par.par, "agente": ag.nome, "otimo": par.otimo,
                "sucesso": p.sucesso, "cliques": p.cliques,
                "consultados": p.consultados, "segundos": round(p.segundos, 4),
                "motivo": p.extra.get("motivo", ""),
                "caminho": " → ".join(amb.nome(v) for v in p.caminho) if p.sucesso else "",
            })
        if verbose and (i + 1) % 10 == 0:
            print(f"  {i + 1}/{len(pares)} pares ({time.time() - inicio:.0f}s)", flush=True)
    df = pd.DataFrame(linhas)
    df["razao"] = df["cliques"] / df["otimo"]
    return df


def resumo(partidas, limite=None):
    """Tabela por agente: sucesso, razão (média/mediana), consultados.

    Com ``limite``, uma partida só conta como sucesso se usou no máximo
    ``limite`` cliques.
    """
    df = partidas.copy()
    if limite is not None:
        df["sucesso"] = df["sucesso"] & (df["cliques"] <= limite)
    ok = df[df["sucesso"]]
    tab = pd.DataFrame({
        "partidas": df.groupby("agente").size(),
        "taxa_sucesso": df.groupby("agente")["sucesso"].mean(),
        "razao_media": ok.groupby("agente")["razao"].mean(),
        "razao_mediana": ok.groupby("agente")["razao"].median(),
        "fracao_otima": ok.groupby("agente")["razao"].apply(lambda r: (r == 1).mean()),
        "cliques_medio": ok.groupby("agente")["cliques"].mean(),
        "consultados_mediana": df.groupby("agente")["consultados"].median(),
        "consultados_medio": df.groupby("agente")["consultados"].mean(),
        "segundos_medio": df.groupby("agente")["segundos"].mean(),
    })
    return tab.sort_values(["taxa_sucesso", "razao_media"], ascending=[False, True])


def curva_sucesso(partidas, limites=range(1, 51)):
    """Fração de partidas terminadas com no máximo L cliques, para cada L."""
    linhas = []
    for agente, df in partidas.groupby("agente"):
        c = df["cliques"].where(df["sucesso"])
        for L in limites:
            linhas.append({"agente": agente, "limite": L, "taxa": float((c <= L).mean())})
    return pd.DataFrame(linhas)
