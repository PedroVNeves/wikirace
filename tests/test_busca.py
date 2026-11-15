import numpy as np
import pytest

from wikirace.busca import (INF, bfs, bfs_bidirecional, bfs_bidirecional_grafo,
                            bfs_niveis, caminho_pelos_pais)
from wikirace.grafo import Grafo


def grafo_aleatorio(n, m, semente):
    rng = np.random.default_rng(semente)
    return Grafo.de_arestas(n, rng.integers(0, n, m), rng.integers(0, n, m))


def floyd_warshall(g):
    """Força bruta O(n^3) só pra conferir as buscas em grafos pequenos."""
    n = g.n
    d = np.full((n, n), np.inf)
    np.fill_diagonal(d, 0)
    for u in range(n):
        d[u, g.vizinhos(u)] = 1
    for k in range(n):
        d = np.minimum(d, d[:, [k]] + d[[k], :])
    return d


def eh_caminho(g, cam):
    return all(g.tem_aresta(u, v) for u, v in zip(cam, cam[1:]))


# grafos esparsos (muitos pares sem caminho) e mais densos
CASOS = [(40, 50, s) for s in range(4)] + [(60, 240, s) for s in range(4)]


@pytest.mark.parametrize("n,m,semente", CASOS)
def test_bfs_da_distancia_correta(n, m, semente):
    g = grafo_aleatorio(n, m, semente)
    d = floyd_warshall(g)
    for s in range(n):
        dist, pai = bfs(g, s)
        esperado = np.where(np.isinf(d[s]), INF, d[s]).astype(int)
        np.testing.assert_array_equal(dist, esperado)
        np.testing.assert_array_equal(bfs_niveis(g, s), esperado)
        for t in range(n):
            cam = caminho_pelos_pais(pai, s, t)
            if dist[t] == INF:
                assert cam is None
            else:
                assert cam[0] == s and cam[-1] == t
                assert len(cam) - 1 == dist[t] and eh_caminho(g, cam)


@pytest.mark.parametrize("n,m,semente", CASOS)
def test_bidirecional_eh_otima(n, m, semente):
    g = grafo_aleatorio(n, m, semente)
    d = floyd_warshall(g)
    for s in range(n):
        for t in range(n):
            r = bfs_bidirecional_grafo(g, s, t)
            if np.isinf(d[s, t]):
                assert r.caminho is None
            else:
                assert r.cliques == d[s, t]
                assert r.caminho[0] == s and r.caminho[-1] == t
                assert eh_caminho(g, r.caminho)


def test_exemplo_da_proposta():
    g = Grafo.de_dicionario({
        "Pelé": ["Inglaterra", "Futebol", "Brasil"],
        "Inglaterra": ["Mecânica_quântica", "Londres"],
        "Futebol": ["Inglaterra"],
        "Brasil": ["Futebol"],
        "Mecânica_quântica": ["Física"],
    })
    r = bfs_bidirecional_grafo(g, g.id_de("Pelé"), g.id_de("Mecânica quântica"))
    assert [g.titulo(v) for v in r.caminho] == ["Pelé", "Inglaterra", "Mecânica_quântica"]
    assert r.cliques == 2
    # o caminho de volta não existe: d(u, v) != d(v, u)
    assert bfs_bidirecional_grafo(g, g.id_de("Mecânica quântica"), g.id_de("Pelé")).caminho is None


def test_bidirecional_funciona_com_strings():
    adj = {"a": ["b"], "b": ["c"], "c": ["d"], "d": []}
    pred = {"a": [], "b": ["a"], "c": ["b"], "d": ["c"]}
    r = bfs_bidirecional(adj.__getitem__, pred.__getitem__, "a", "d")
    assert r.caminho == ["a", "b", "c", "d"]
    assert bfs_bidirecional(adj.__getitem__, pred.__getitem__, "a", "a").cliques == 0


def test_bidirecional_consulta_menos_que_bfs_em_ciclo_longo():
    # num ciclo de 1000 vértices com atalhos, a busca de dois lados olha menos artigos
    n = 1000
    orig = list(range(n)) + list(range(0, n, 10))
    dest = [(i + 1) % n for i in range(n)] + [(i + 37) % n for i in range(0, n, 10)]
    g = Grafo.de_arestas(n, orig, dest)
    r = bfs_bidirecional_grafo(g, 0, 500)
    dist, _ = bfs(g, 0)
    assert r.cliques == dist[500]
    assert r.consultados < np.sum((dist >= 0) & (dist <= dist[500]))


def test_bfs_niveis_varias_fontes_e_limite():
    g = Grafo.de_arestas(5, [0, 1, 2, 3], [1, 2, 3, 4])
    np.testing.assert_array_equal(bfs_niveis(g, [0, 3]), [0, 1, 2, 0, 1])
    np.testing.assert_array_equal(bfs_niveis(g, 0, max_nivel=2), [0, 1, 2, -1, -1])
