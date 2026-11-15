import numpy as np
import pytest

from wikirace import experimento
from wikirace.agentes import AmbienteGrafo, todos_os_agentes
from wikirace.busca import bfs
from wikirace.grafo import Grafo


@pytest.fixture
def amb():
    rng = np.random.default_rng(5)
    n = 150
    # um grafo com uma parte "presa" (vértices 140..149 sem links de volta)
    orig = rng.integers(0, 140, 700)
    dest = rng.integers(0, 150, 700)
    g = Grafo.de_arestas(n, orig, dest, titulos=[f"A{i}" for i in range(n)])
    e = rng.normal(size=(n, 6))
    return AmbienteGrafo(g, e / np.linalg.norm(e, axis=1, keepdims=True))


def test_sortear_pares_so_com_caminho(amb):
    pares, descartados = experimento.sortear_pares(amb.g, k=40, semente=1)
    assert len(pares) == 40
    assert descartados > 0  # a parte presa gera pares sem caminho
    for p in pares.itertuples():
        assert p.origem != p.destino
        assert bfs(amb.g, p.origem)[0][p.destino] == p.otimo
        assert p.caminho_otimo.startswith(p.titulo_origem)
    # mesma semente, mesmos pares
    de_novo, _ = experimento.sortear_pares(amb.g, k=40, semente=1)
    assert de_novo.equals(pares)


def test_rodar_e_resumo(amb):
    pares, _ = experimento.sortear_pares(amb.g, k=15, semente=2)
    agentes = todos_os_agentes()
    df = experimento.rodar(amb, pares, agentes, max_cliques=40)
    assert len(df) == 15 * len(agentes)
    bfs_ = df[df.agente == "bfs_bidirecional"]
    assert bfs_.sucesso.all() and (bfs_.razao == 1).all()
    ok = df[df.sucesso]
    assert (ok.razao >= 1).all()
    tab = experimento.resumo(df)
    assert tab.loc["bfs_bidirecional", "taxa_sucesso"] == 1
    assert tab.loc["a_estrela_w1", "razao_media"] == 1
    # com limite, a taxa só pode cair
    tab5 = experimento.resumo(df, limite=5)
    assert (tab5["taxa_sucesso"] <= tab.loc[tab5.index, "taxa_sucesso"] + 1e-12).all()


def test_curva_sucesso_cresce(amb):
    pares, _ = experimento.sortear_pares(amb.g, k=10, semente=3)
    df = experimento.rodar(amb, pares, todos_os_agentes(), max_cliques=30)
    curva = experimento.curva_sucesso(df, limites=range(1, 31))
    for _, c in curva.groupby("agente"):
        assert np.all(np.diff(c["taxa"].to_numpy()) >= 0)
