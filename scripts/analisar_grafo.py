"""Roda as análises estruturais no grafo completo e salva em resultados/analises/.

Uso:
    python scripts/analisar_grafo.py                 # tudo
    python scripts/analisar_grafo.py scc hubs        # só algumas partes

Partes: scc, distancias, hubs, assimetria.
Cada BFS no grafo inteiro leva ~3 s, então as amostras são de algumas dezenas
de fontes — mas cada fonte dá a distância para todos os ~1,2 milhão de
destinos, então são dezenas de milhões de pares.
"""

import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from wikirace import analises, config  # noqa: E402
from wikirace.grafo import Grafo  # noqa: E402

SAIDA = config.RESULTADOS / "analises"
SEMENTE = 2026


def salva(nome, dados):
    SAIDA.mkdir(parents=True, exist_ok=True)
    (SAIDA / f"{nome}.json").write_text(json.dumps(dados, ensure_ascii=False, indent=2),
                                        encoding="utf-8")
    print(f"  -> {nome}.json", flush=True)


def fontes(g, k, semente):
    return np.random.default_rng(semente).choice(g.n, size=k, replace=False)


def parte_scc(g):
    t = time.time()
    rot = analises.componentes_fortes(g)
    seg_nosso = time.time() - t
    from scipy.sparse import csr_matrix
    from scipy.sparse.csgraph import connected_components
    t = time.time()
    mat = csr_matrix((np.ones(g.m, dtype=np.int8), g.indices, g.indptr), shape=(g.n, g.n))
    k, rot_scipy = connected_components(mat, directed=True, connection="strong")
    seg_scipy = time.time() - t
    confere = len(set(zip(rot.tolist(), rot_scipy.tolist()))) == k == rot.max() + 1
    tamanhos = np.bincount(rot)
    dag = analises.condensacao(g, rot)
    gigante = int(tamanhos.argmax())
    tam_ord = np.sort(tamanhos)[::-1]
    valores, quantos = np.unique(tamanhos, return_counts=True)
    salva("scc", {
        "num_componentes": int(k),
        "maior_componente": int(tamanhos.max()),
        "fracao_na_maior": float(tamanhos.max() / g.n),
        "segunda_maior": int(tam_ord[1]),
        "componentes_de_1_vertice": int((tamanhos == 1).sum()),
        "distribuicao_tamanhos": {int(a): int(b) for a, b in zip(valores, quantos)},
        "condensacao_vertices": dag.n,
        "condensacao_arestas": dag.m,
        "condensacao_aciclica": bool(analises.eh_aciclico(dag)),
        "gravata_borboleta": analises.gravata_borboleta(g, rot),
        "exemplos_fora_da_maior": [g.titulo(int(v)) for v in
                                   np.flatnonzero(rot != gigante)[:15]],
        "kosaraju_segundos": round(seg_nosso, 1),
        "scipy_segundos": round(seg_scipy, 1),
        "kosaraju_igual_scipy": bool(confere),
    })
    np.save(config.DADOS / "scc_rotulos.npy", rot)


def parte_distancias(g, k=60):
    src = fontes(g, k, SEMENTE)
    t = time.time()
    hist, sem, tot = analises.histograma_distancias(g, src)
    print(f"  wikipedia: {time.time() - t:.0f}s", flush=True)
    er = analises.erdos_renyi_dirigido(g.n, g.m, semente=SEMENTE)
    hist_er, sem_er, tot_er = analises.histograma_distancias(er, src)
    del er
    n, dmed = g.n, g.m / g.n
    salva("distancias", {
        "fontes": int(k), "pares": int(tot),
        "wikipedia": {"hist": hist, "sem_caminho": sem,
                      **analises.resumo_distancias(hist, sem, tot)},
        "erdos_renyi": {"hist": hist_er, "sem_caminho": sem_er,
                        **analises.resumo_distancias(hist_er, sem_er, tot_er)},
        "previsao_ln_n_sobre_ln_grau_medio": float(np.log(n) / np.log(dmed)),
        "moore_log100_n": float(np.log(n) / np.log(100)),
    })


def parte_hubs(g, k=30, cortes=(0, 10, 100, 1000, 10000)):
    gs, ge = g.grau_saida(), g.grau_entrada()

    def distribuicao(graus):
        v, c = np.unique(graus, return_counts=True)
        return {int(a): int(b) for a, b in zip(v, c)}

    top_ent = np.argsort(ge)[::-1]
    top_sai = np.argsort(gs)[::-1]
    src = fontes(g, k, SEMENTE + 1)
    remocao = []
    for c in cortes:
        mask = np.zeros(g.n, dtype=bool)
        mask[top_ent[:c]] = True
        fontes_ok = src[~mask[src]]
        t = time.time()
        hist, sem, tot = analises.histograma_distancias(g, fontes_ok, bloqueados=mask)
        r = analises.resumo_distancias(hist, sem, tot)
        print(f"  sem os {c} maiores hubs: média {r['media']:.2f} ({time.time() - t:.0f}s)",
              flush=True)
        remocao.append({"removidos": c, "hist": hist, **r})
    salva("hubs", {
        "grau_entrada": distribuicao(ge), "grau_saida": distribuicao(gs),
        "top_entrada": [[g.titulo(int(v)), int(ge[v])] for v in top_ent[:25]],
        "top_saida": [[g.titulo(int(v)), int(gs[v])] for v in top_sai[:25]],
        "media_grau": float(g.m / g.n),
        "mediana_grau_entrada": float(np.median(ge)),
        "mediana_grau_saida": float(np.median(gs)),
        "soma_grau_saida": int(gs.sum()), "soma_grau_entrada": int(ge.sum()),
        "arestas": g.m,
        "remocao": remocao,
    })


def parte_assimetria(g, k=40):
    salva("assimetria", {"fontes": k, **analises.assimetria(g, fontes(g, k, SEMENTE + 2))})


PARTES = {"scc": parte_scc, "distancias": parte_distancias, "hubs": parte_hubs,
          "assimetria": parte_assimetria}


def main():
    escolhidas = sys.argv[1:] or list(PARTES)
    g = Grafo.carregar(config.GRAFO_NPZ, config.TITULOS_TXT)
    print(g, flush=True)
    for nome in escolhidas:
        print(f"[{nome}]", flush=True)
        t = time.time()
        PARTES[nome](g)
        print(f"  ({time.time() - t:.0f}s)", flush=True)


if __name__ == "__main__":
    main()
