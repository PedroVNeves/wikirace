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


def test_resumir_humanos():
    import pandas as pd

    from wikirace.jogo import resumir_humanos
    pares = pd.DataFrame({"par": [0, 1], "origem": [10, 20], "destino": [11, 21],
                          "titulo_origem": ["A_b", "C"], "titulo_destino": ["D", "E"],
                          "otimo": [2, 3]})
    partidas = pd.DataFrame({
        "par": [0, 0, 1, 1], "agente": ["bfs", "guloso", "bfs", "guloso"],
        "otimo": [2, 2, 3, 3], "sucesso": [True, False, True, True],
        "cliques": [2, None, 3, 6], "consultados": [5, 50, 8, 6]})
    humanos = pd.DataFrame({
        "jogador": ["ana", "ana", "bia"], "origem": ["A b", "Pelé", "A_b"],
        "destino": ["D", "Brasil", "D"], "sucesso": ["True", "True", "False"],
        "cliques": [4, 1, 7], "otimo": [None, 1, 2], "consultados": [4, 1, 7],
        "segundos": [30.0, 10.0, 90.0]})
    r = resumir_humanos(humanos, pares, partidas)
    assert r["humanos"]["partidas"] == 3
    assert r["humanos"]["razao_media"] == pytest.approx((4 / 2 + 1 / 1) / 2)
    assert r["humanos_nos_pares_do_experimento"]["partidas"] == 2
    assert r["pares_do_experimento_jogados"] == [0]
    assert r["partidas_fora_do_experimento"] == 1
    # agentes só no par 0, que foi o que a turma jogou
    assert r["agentes_nos_mesmos_pares"]["guloso"]["taxa_sucesso"] == 0
    assert r["agentes_nos_mesmos_pares"]["bfs"]["razao_media"] == 1
    assert r["por_jogador"]["bia"]["taxa_sucesso"] == 0
