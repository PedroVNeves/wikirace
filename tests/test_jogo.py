import csv

import pytest

from wikirace.agentes import AmbienteGrafo
from wikirace.grafo import Grafo
from wikirace.jogo import PartidaHumana, salvar_registro, sem_acento


@pytest.fixture
def amb():
    return AmbienteGrafo(Grafo.de_dicionario({
        "Pelé": ["Inglaterra", "Futebol", "Brasil"],
        "Inglaterra": ["Mecânica_quântica", "Londres"],
        "Futebol": ["Inglaterra"], "Brasil": ["Futebol"]}))


def test_sem_acento():
    assert sem_acento("Mecânica_Quântica") == "mecanica quantica"


def test_partida_completa(amb):
    g = amb.g
    p = PartidaHumana(amb, g.id_de("Pelé"), g.id_de("Mecânica quântica"), "turma")
    assert [n for n, _ in p.opcoes("ing")] == ["Inglaterra"]
    assert [n for n, _ in p.opcoes("")] == ["Brasil", "Futebol", "Inglaterra"]
    p.clicar(g.id_de("Futebol"))
    p.voltar()
    assert p.atual == g.id_de("Pelé")
    p.clicar(g.id_de("Inglaterra"))
    with pytest.raises(ValueError):
        p.clicar(g.id_de("Brasil"))  # não tem esse link na Inglaterra
    p.clicar(g.id_de("Mecânica quântica"))
    assert p.terminou and p.cliques == 4
    r = p.registro(otimo=2)
    assert r["caminho"] == "Pelé → Futebol → Pelé → Inglaterra → Mecânica_quântica"
    assert r["consultados"] == 2  # Futebol foi clicado mas não lido (voltou direto)


def test_nao_volta_da_origem(amb):
    p = PartidaHumana(amb, 0, 1)
    with pytest.raises(ValueError):
        p.voltar()


def test_salvar_registro_acumula(tmp_path, amb):
    arq = tmp_path / "humanos.csv"
    for _ in range(2):
        salvar_registro(arq, PartidaHumana(amb, 0, 1).registro())
    with open(arq, encoding="utf-8") as f:
        assert len(list(csv.DictReader(f))) == 2
