"""Bônus: para qual ciclo converge quem clica sempre no primeiro link?

"Primeiro link" define uma função f: V -> V (um grafo funcional). Partindo de
artigos sorteados, aplico f até repetir um artigo — pela casa dos pombos
isso sempre acontece — e anoto o ciclo final.

A ordem dos links não está nos dumps, então isso usa a API (com cache em
disco, pra rodar de novo sem refazer as requisições).

Uso:
    python scripts/primeiro_link.py [--inicios 150]
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from wikirace import analises, config  # noqa: E402
from wikirace.api import Cache, WikipediaAPI  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inicios", type=int, default=150)
    ap.add_argument("--semente", type=int, default=2026)
    ap.add_argument("--pausa", type=float, default=1.0,
                    help="segundos entre requisições (a API devolve 429 se for rápido demais)")
    args = ap.parse_args()

    titulos = config.TITULOS_TXT.read_text(encoding="utf-8").splitlines()
    rng = np.random.default_rng(args.semente)
    inicios = [titulos[i] for i in rng.choice(len(titulos), args.inicios, replace=False)]

    api = WikipediaAPI(cache=Cache(config.DADOS / "cache_api.sqlite"), pausa=args.pausa)
    f = {}  # o pedaço do grafo funcional que a gente descobriu

    def primeiro(t):
        if t not in f:
            f[t] = api.primeiro_link(t)
        return f[t]

    corridas, falhas = [], []
    for i, t in enumerate(inicios):
        try:
            cauda, ciclo = analises.segue_ate_ciclo(primeiro, t, max_passos=500)
        except RuntimeError as e:  # API fora do ar mesmo depois das tentativas
            falhas.append({"inicio": t, "erro": str(e)})
            continue
        corridas.append({"inicio": t, "passos_ate_ciclo": len(cauda),
                         "ciclo": list(analises.ciclo_canonico(ciclo))})
        if (i + 1) % 25 == 0:
            print(f"  {i + 1}/{len(inicios)} ({api.requisicoes} requisições)", flush=True)

    ciclos = Counter(tuple(c["ciclo"]) for c in corridas)
    filosofia = sum("Filosofia" in c["ciclo"] or "Filosofia" in _caminho(f, c["inicio"])
                    for c in corridas)
    # confere o lema: no pedaço descoberto (fechado por f), cada componente tem 1 ciclo
    fechado = {v: w for v, w in f.items() if w is not None}
    while any(w not in fechado for w in fechado.values()):
        fechado = {v: w for v, w in fechado.items() if w in fechado}
    comps = analises.componentes_funcionais(fechado)
    saida = {
        "inicios": len(inicios),
        "falhas_de_rede": falhas,
        "artigos_visitados": len(f),
        "requisicoes": api.requisicoes,
        "sem_primeiro_link": sum(1 for c in corridas if not c["ciclo"]),
        "passaram_por_filosofia": filosofia,
        "ciclos": [{"ciclo": list(c), "quantos_chegam": n} for c, n in ciclos.most_common()],
        "passos_ate_ciclo_media": float(np.mean([c["passos_ate_ciclo"] for c in corridas])),
        "passos_ate_ciclo_max": int(max(c["passos_ate_ciclo"] for c in corridas)),
        "componentes_no_pedaco_fechado": len(comps),
        "todas_com_um_ciclo": all(len(c) == 1 for _, c in comps),
        "corridas": corridas,
    }
    destino = config.RESULTADOS / "analises" / "primeiro_link.json"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(saida, ensure_ascii=False, indent=2), encoding="utf-8")
    for c, n in ciclos.most_common(5):
        print(n, " → ".join(c) if c else "(sem link)")


def _caminho(f, t, limite=500):
    visto = []
    while t is not None and t not in visto and len(visto) < limite:
        visto.append(t)
        t = f.get(t)
    return visto


if __name__ == "__main__":
    main()
