import numpy as np
import pytest
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components

from wikirace import analises
from wikirace.busca import bfs, bfs_niveis
from wikirace.grafo import Grafo


def grafo_aleatorio(n, m, semente):
    rng = np.random.default_rng(semente)
    return Grafo.de_arestas(n, rng.integers(0, n, m), rng.integers(0, n, m))


def mesma_particao(a, b):
    """Duas rotulações descrevem a mesma partição (a menos do nome dos rótulos)."""
    pares = set(zip(a.tolist(), b.tolist()))
    return len(pares) == len(set(a.tolist())) == len(set(b.tolist()))


@pytest.mark.parametrize("n,m,semente", [(50, 60, 0), (100, 150, 1), (200, 400, 2),
                                         (300, 1200, 3), (1000, 1500, 4)])
def test_kosaraju_igual_scipy(n, m, semente):
    g = grafo_aleatorio(n, m, semente)
    nosso = analises.componentes_fortes(g)
    mat = csr_matrix((np.ones(g.m), g.indices, g.indptr), shape=(n, n))
    _, deles = connected_components(mat, directed=True, connection="strong")
    assert mesma_particao(nosso, deles)


@pytest.mark.parametrize("semente", range(5))
def test_alcancar_mutuamente_eh_equivalencia(semente):
    # u ~ v  <=>  u alcança v e v alcança u  <=>  mesmo rótulo de componente
    g = grafo_aleatorio(40, 70, semente)
    rot = analises.componentes_fortes(g)
    alcanca = np.array([bfs(g, s)[0] >= 0 for s in range(g.n)])
    mutuo = alcanca & alcanca.T
    np.testing.assert_array_equal(mutuo, rot[:, None] == rot[None, :])


@pytest.mark.parametrize("semente", range(5))
def test_grafo_de_componentes_eh_aciclico(semente):
    g = grafo_aleatorio(300, 500, semente)
    rot = analises.componentes_fortes(g)
    dag = analises.condensacao(g, rot)
    assert dag.n == rot.max() + 1
    assert analises.eh_aciclico(dag)
    assert not analises.eh_aciclico(Grafo.de_arestas(3, [0, 1, 2], [1, 2, 0]))


def test_gravata_borboleta():
    # IN -> {a <-> b} -> OUT, e um vértice solto
    g = Grafo.de_dicionario({"in": ["a"], "a": ["b"], "b": ["a", "out"], "solto": []})
    r = analises.gravata_borboleta(g, analises.componentes_fortes(g))
    assert r == {"SCC": 2, "IN": 1, "OUT": 1, "OUTROS": 1}


def test_bfs_com_bloqueados_igual_a_remover_vertices():
    g = grafo_aleatorio(200, 800, 7)
    removidos = np.array([3, 10, 50, 51])
    mask = np.zeros(g.n, dtype=bool)
    mask[removidos] = True
    h = g.sem_vertices(removidos)
    for s in (0, 3, 99):
        esperado = bfs_niveis(h, s)
        esperado[removidos] = -1
        np.testing.assert_array_equal(bfs_niveis(g, s, bloqueados=mask), esperado)


def test_histograma_distancias_caminho():
    g = Grafo.de_arestas(4, [0, 1, 2], [1, 2, 3])  # 0 -> 1 -> 2 -> 3
    hist, sem, total = analises.histograma_distancias(g, [0, 3])
    assert hist == {1: 1, 2: 1, 3: 1}
    assert total == 6 and sem == 3
    r = analises.resumo_distancias(hist, sem, total)
    assert r["media"] == 2 and r["mediana"] == 2 and r["fracao_sem_caminho"] == 0.5


def test_erdos_renyi_tem_n_e_m_certos():
    g = analises.erdos_renyi_dirigido(1000, 5000, semente=1)
    assert g.n == 1000 and g.m == 5000
    assert g.grau_saida().sum() == g.grau_entrada().sum() == 5000


def test_assimetria():
    # 0 -> 1 -> 2 -> 0 : d(0,1) = 1 mas d(1,0) = 2
    g = Grafo.de_arestas(3, [0, 1, 2], [1, 2, 0])
    r = analises.assimetria(g, [0])
    assert r["pares_com_algum_caminho"] == 2
    assert r["fracao_simetrica"] == 0 and r["hist_diferenca_absoluta"] == {1: 2}


def test_segue_ate_ciclo():
    f = {1: 2, 2: 3, 3: 4, 4: 2, 5: None}
    cauda, ciclo = analises.segue_ate_ciclo(f.get, 1)
    assert cauda == [1] and ciclo == [2, 3, 4]
    assert analises.segue_ate_ciclo(f.get, 5) == ([5], [])
    assert analises.ciclo_canonico([3, 4, 2]) == (2, 3, 4)


@pytest.mark.parametrize("semente", range(10))
def test_grafo_funcional_tem_um_ciclo_por_componente(semente):
    rng = np.random.default_rng(semente)
    n = 60
    f = {v: int(rng.integers(n)) for v in range(n)}
    for comp, ciclos in analises.componentes_funcionais(f):
        assert len(ciclos) == 1
        (ciclo,) = ciclos
        assert len(ciclo) >= 1 and set(ciclo) <= comp
