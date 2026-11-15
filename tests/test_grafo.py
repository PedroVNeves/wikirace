import numpy as np
import pytest

from wikirace.grafo import Grafo


def grafo_aleatorio(n, m, semente=0):
    rng = np.random.default_rng(semente)
    return Grafo.de_arestas(n, rng.integers(0, n, m), rng.integers(0, n, m))


def test_exemplo_pequeno():
    g = Grafo.de_dicionario({"A": ["B", "C"], "B": ["C"], "C": ["A"]})
    a, b, c = (g.id_de(x) for x in "ABC")
    assert g.n == 3 and g.m == 4
    assert sorted(g.vizinhos(a)) == [b, c]
    assert g.tem_aresta(c, a) and not g.tem_aresta(a, a) and not g.tem_aresta(b, a)


def test_remove_duplicadas_e_lacos():
    g = Grafo.de_arestas(3, [0, 0, 0, 1, 2], [1, 1, 0, 2, 2])
    assert g.m == 2
    assert list(g.vizinhos(0)) == [1]
    assert list(g.vizinhos(2)) == []


@pytest.mark.parametrize("semente", range(5))
def test_lema_aperto_de_maos_dirigido(semente):
    # soma dos graus de saída = soma dos graus de entrada = |E|
    g = grafo_aleatorio(200, 1500, semente)
    assert g.grau_saida().sum() == g.grau_entrada().sum() == g.m


def test_transposto():
    g = grafo_aleatorio(100, 600)
    t = g.transposto()
    assert t.m == g.m
    for u in range(g.n):
        for v in g.vizinhos(u):
            assert t.tem_aresta(v, u)
    np.testing.assert_array_equal(t.grau_saida(), g.grau_entrada())
    # transpor duas vezes volta ao original
    tt = Grafo.de_arestas(t.n, *_arestas(t)).transposto()
    np.testing.assert_array_equal(tt.indptr, g.indptr)
    np.testing.assert_array_equal(tt.indices, g.indices)


def _arestas(g):
    origens = np.repeat(np.arange(g.n), g.grau_saida())
    return origens, g.indices


def test_sem_vertices():
    g = Grafo.de_dicionario({"A": ["B"], "B": ["C"], "C": ["A", "B"]})
    h = g.sem_vertices([g.id_de("B")])
    assert h.n == g.n
    assert h.m == 1  # só sobra C -> A
    assert h.tem_aresta(g.id_de("C"), g.id_de("A"))


def test_id_de_aceita_espaco_e_minuscula():
    g = Grafo.de_dicionario({"Mecânica_quântica": ["Pelé"]})
    assert g.id_de("mecânica quântica") == g.id_de("Mecânica_quântica")
    with pytest.raises(KeyError):
        g.id_de("Inexistente")


def test_salvar_e_carregar(tmp_path):
    g = Grafo.de_dicionario({"A": ["B"], "B": ["A", "C"]})
    g.salvar(tmp_path / "g.npz", tmp_path / "t.txt")
    h = Grafo.carregar(tmp_path / "g.npz", tmp_path / "t.txt")
    np.testing.assert_array_equal(g.indptr, h.indptr)
    np.testing.assert_array_equal(g.indices, h.indices)
    assert h.titulos == g.titulos


def test_validacao():
    with pytest.raises(ValueError):
        Grafo.de_arestas(2, [0], [5])
    with pytest.raises(ValueError):
        Grafo([0, 2], [1])
