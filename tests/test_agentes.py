import numpy as np
import pytest

from wikirace.agentes import (AEstrela, AmbienteGrafo, BFSBidirecional, GulosoGrau,
                              GulosoSemantico, PasseioAleatorio, todos_os_agentes)
from wikirace.busca import bfs
from wikirace.grafo import Grafo


def angulos(graus):
    """Embeddings 2D unitários: cos entre dois vértices = cos da diferença de ângulo."""
    r = np.radians(np.asarray(graus, dtype=float))
    return np.stack([np.cos(r), np.sin(r)], axis=1)


def ambiente_aleatorio(n, m, semente, dim=8):
    rng = np.random.default_rng(semente)
    g = Grafo.de_arestas(n, rng.integers(0, n, m), rng.integers(0, n, m))
    e = rng.normal(size=(n, dim))
    e /= np.linalg.norm(e, axis=1, keepdims=True)
    return AmbienteGrafo(g, e)


@pytest.fixture
def contraexemplo():
    """O guloso semântico erra: o artigo "parecido" com o destino é uma volta longa.

        s -> a -> x -> y -> t      (a, x, y "parecem" com t)
        s -> b -> t                (b não parece, mas é o atalho)
    """
    g = Grafo.de_dicionario({"s": ["a", "b"], "a": ["x"], "x": ["y"], "y": ["t"],
                             "b": ["t"]})
    graus = {"t": 0, "a": 10, "x": 20, "y": 30, "b": 90, "s": 120}
    emb = angulos([graus[g.titulo(i)] for i in range(g.n)])
    return g, AmbienteGrafo(g, emb)


def test_contraexemplo_do_guloso(contraexemplo):
    g, amb = contraexemplo
    s, t = g.id_de("s"), g.id_de("t")
    guloso = GulosoSemantico().jogar(amb, s, t)
    otimo = BFSBidirecional().jogar(amb, s, t)
    assert [g.titulo(v) for v in guloso.caminho] == ["s", "a", "x", "y", "t"]
    assert guloso.cliques == 4 and otimo.cliques == 2
    # o A* com h admissível não cai na armadilha
    assert AEstrela(w=1).jogar(amb, s, t).cliques == 2


def test_guloso_por_grau_vai_pro_hub():
    # o hub tem muitos links, mas nenhum leva rápido ao destino
    adj = {"s": ["hub", "atalho"], "atalho": ["t"],
           "hub": [f"f{i}" for i in range(10)] + ["longe"], "longe": ["t"]}
    g = Grafo.de_dicionario(adj)
    p = GulosoGrau().jogar(AmbienteGrafo(g), g.id_de("s"), g.id_de("t"))
    assert [g.titulo(v) for v in p.caminho] == ["s", "hub", "longe", "t"]


@pytest.mark.parametrize("semente", range(6))
def test_a_estrela_w1_eh_otimo_e_w_respeita_limite(semente):
    amb = ambiente_aleatorio(80, 240, semente)
    rng = np.random.default_rng(100 + semente)
    for _ in range(15):
        s, t = rng.integers(0, 80, 2).tolist()
        d = bfs(amb.g, s)[0][t]
        for w in (1, 2, 4, 8):
            p = AEstrela(w).jogar(amb, s, t)
            if d < 0:
                assert not p.sucesso
            elif w == 1:
                assert p.cliques == d
            else:
                assert d <= p.cliques <= w * d  # teorema do A* ponderado


@pytest.mark.parametrize("semente", range(4))
def test_todos_os_caminhos_sao_validos(semente):
    amb = ambiente_aleatorio(60, 300, semente)
    rng = np.random.default_rng(semente)
    for _ in range(10):
        s, t = rng.integers(0, 60, 2).tolist()
        d = bfs(amb.g, s)[0][t]
        for ag in todos_os_agentes():
            p = ag.jogar(amb, s, t, max_cliques=200, semente=semente)
            if p.sucesso:
                assert p.caminho[0] == s and p.caminho[-1] == t
                # caminhada válida: cada passo é um link ou um "voltar"
                for u, v in zip(p.caminho, p.caminho[1:]):
                    assert amb.g.tem_aresta(u, v) or amb.g.tem_aresta(v, u)
                assert p.cliques >= d
            if ag.nome == "bfs_bidirecional":
                assert p.sucesso == (d >= 0)


def test_aleatorio_respeita_limite_e_semente():
    g = Grafo.de_arestas(4, [0, 1, 2, 1], [1, 2, 0, 0])  # 3 nunca é alcançado
    amb = AmbienteGrafo(g)
    p = PasseioAleatorio().jogar(amb, 0, 3, max_cliques=25, semente=1)
    assert not p.sucesso and p.extra["motivo"] == "limite de cliques"
    assert len(p.extra["caminhada"]) == 26
    q = PasseioAleatorio().jogar(amb, 0, 3, max_cliques=25, semente=1)
    assert q.extra["caminhada"] == p.extra["caminhada"]


def test_caminhante_volta_quando_cai_em_beco():
    # s -> beco (sem saída) e s -> m -> t; o guloso por grau... prefere m (grau 1 > 0),
    # então uso o semântico apontando pro beco
    g = Grafo.de_dicionario({"s": ["beco", "m"], "m": ["t"]})
    graus = {"t": 0, "beco": 5, "m": 80, "s": 100}
    amb = AmbienteGrafo(g, angulos([graus[g.titulo(i)] for i in range(g.n)]))
    p = GulosoSemantico().jogar(amb, g.id_de("s"), g.id_de("t"))
    assert [g.titulo(v) for v in p.caminho] == ["s", "beco", "s", "m", "t"]
    assert p.cliques == 4  # o "voltar" conta como clique


def test_limite_de_consultas():
    amb = ambiente_aleatorio(200, 400, 3)
    p = AEstrela(1).jogar(amb, 0, 1, max_consultas=2)
    assert p.consultados <= 2
    if not p.sucesso:
        assert p.extra["motivo"] in ("limite de consultas", "sem caminho")


def test_origem_igual_destino():
    amb = ambiente_aleatorio(10, 20, 0)
    for ag in todos_os_agentes():
        assert ag.jogar(amb, 4, 4).cliques == 0
