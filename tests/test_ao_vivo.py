import numpy as np
import pytest

from wikirace.agentes import todos_os_agentes
from wikirace.ao_vivo import AmbienteAPI
from wikirace.grafo import Grafo

ADJ = {"Pelé": ["Inglaterra", "Futebol", "Brasil"],
       "Inglaterra": ["Mecânica_quântica", "Londres"],
       "Futebol": ["Inglaterra"], "Brasil": ["Futebol"],
       "Mecânica_quântica": ["Física"], "Londres": [], "Física": ["Mecânica_quântica"]}


class APIFalsa:
    def links(self, t):
        return ADJ.get(t, [])

    def afluentes(self, t):
        return sorted(u for u, vs in ADJ.items() if t in vs)

    def resolve(self, t):
        return t if t in ADJ else None


def codificador_falso(titulos):
    e = np.array([[len(t), t.count("a"), t.count("i") + 1] for t in titulos], dtype=float)
    return e / np.linalg.norm(e, axis=1, keepdims=True)


@pytest.mark.parametrize("agente", todos_os_agentes(), ids=lambda a: a.nome)
def test_agentes_jogam_com_titulos(agente):
    amb = AmbienteAPI(APIFalsa(), codificador_falso, Grafo.de_dicionario(ADJ))
    p = agente.jogar(amb, "Pelé", "Mecânica_quântica", max_cliques=30, semente=1)
    if agente.nome in ("bfs_bidirecional", "a_estrela_w1"):
        assert p.caminho == ["Pelé", "Inglaterra", "Mecânica_quântica"]
    if p.sucesso:
        assert p.caminho[0] == "Pelé" and p.caminho[-1] == "Mecânica_quântica"


def test_grau_sem_grafo_da_erro():
    amb = AmbienteAPI(APIFalsa(), codificador_falso)
    with pytest.raises(RuntimeError):
        amb.grau(["Pelé"])
