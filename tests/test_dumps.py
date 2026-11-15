"""Testa o pipeline dos dumps com arquivos falsos, no mesmo formato dos reais."""

import gzip

import pytest

from wikirace import dumps

CABECALHO = """-- MySQL dump 10.19
/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
DROP TABLE IF EXISTS `{t}`;
CREATE TABLE `{t}` (
  `x` int(8) unsigned NOT NULL DEFAULT 0
) ENGINE=InnoDB;
"""
RODAPE = "/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;\nUNLOCK TABLES;\n"


def escreve(pasta, tabela, linhas):
    """Escreve no formato atual: um INSERT com uma tupla por linha."""
    corpo = f"INSERT INTO `{tabela}` VALUES\n" + ",\n".join(linhas) + ";\n"
    caminho = pasta / f"ptwiki-latest-{tabela}.sql.gz"
    with gzip.open(caminho, "wt", encoding="utf-8") as f:
        f.write(CABECALHO.format(t=tabela) + corpo + RODAPE)
    return caminho


def pag(pid, ns, titulo, redir):
    datas = "'20261101000000','20261101000000'"
    return f"({pid},{ns},'{titulo}',{redir},0,0.5,{datas},1,10,'wikitext',NULL)"


@pytest.fixture
def pasta_dumps(tmp_path):
    escreve(tmp_path, "page", [
        pag(1, 0, "Pelé", 0),
        pag(2, 0, "Inglaterra", 0),
        pag(3, 0, "Mecânica_quântica", 0),
        pag(4, 0, "Rei_do_Futebol", 1),        # -> Pelé
        pag(5, 0, "Redir2", 1),                # -> Rei_do_Futebol -> Pelé
        pag(6, 2, "Fulano", 0),                # página de usuário (ns 2)
        pag(7, 0, "Rock_\\'n\\'_Roll", 0),     # aspas escapadas
        pag(8, 0, "Mercúrio_(planeta)", 0),    # parênteses no título
        pag(9, 0, "Quebrado", 1),              # -> artigo que não existe
        pag(12, 0, "Ciclo_A", 1),              # Ciclo_A -> Ciclo_B -> Ciclo_A
        pag(13, 0, "Ciclo_B", 1),
    ])
    escreve(tmp_path, "redirect", [
        "(4,0,'Pelé','','')",
        "(5,0,'Rei_do_Futebol',NULL,NULL)",
        "(9,0,'Inexistente','','')",
        "(12,0,'Ciclo_B','','')",
        "(13,0,'Ciclo_A','','')",
    ])
    escreve(tmp_path, "linktarget", [
        "(10,0,'Inglaterra')", "(11,0,'Mecânica_quântica')", "(12,0,'Rei_do_Futebol')",
        "(13,0,'Página_vermelha')", "(14,2,'Fulano')", "(15,0,'Rock_\\'n\\'_Roll')",
        "(16,0,'Redir2')", "(17,0,'Mercúrio_(planeta)')", "(18,0,'Quebrado')",
        "(19,0,'Pelé')", "(20,0,'Ciclo_A')",
    ])
    escreve(tmp_path, "pagelinks", [
        "(1,0,10)",   # Pelé -> Inglaterra
        "(2,0,11)",   # Inglaterra -> Mecânica quântica
        "(2,0,12)",   # Inglaterra -> Rei do Futebol (= Pelé)
        "(2,0,19)",   # Inglaterra -> Pelé (repetida depois de resolver)
        "(3,0,13)",   # link vermelho: some
        "(3,0,14)",   # link para usuário: some
        "(6,2,10)",   # sai de página de usuário: some
        "(7,0,16)",   # Rock -> Redir2 -> Pelé
        "(8,0,18)",   # Mercúrio -> redirecionamento quebrado: some
        "(8,0,15)",   # Mercúrio -> Rock
        "(8,0,20)",   # Mercúrio -> redirecionamento em ciclo: some
        "(1,0,12)",   # Pelé -> Rei do Futebol (= laço): some
        "(4,0,19)",   # sai de um redirecionamento: some
        "(99,0,10)",  # página que nem existe no dump: some
    ])
    return tmp_path


def test_desescapa():
    assert dumps.desescapa(b"Rock_\\'n\\'_Roll") == b"Rock_'n'_Roll"
    assert dumps.desescapa(b"a\\\\b") == b"a\\b"
    assert dumps.desescapa(b"normal") == b"normal"


def test_ler_paginas(pasta_dumps):
    ids, titulos, redir = dumps.ler_paginas(pasta_dumps / "ptwiki-latest-page.sql.gz")
    assert 6 not in ids  # namespace 2 fica de fora
    assert b"Rock_'n'_Roll" in titulos and b"Merc\xc3\xbario_(planeta)" in titulos
    assert redir.sum() == 5


def test_blocos_nao_quebram_tuplas(tmp_path):
    linhas = [f"({i},0,{i + 1})" for i in range(5000)]
    caminho = escreve(tmp_path, "pagelinks", linhas)
    total = sum(len(dumps.PADRAO_PAGELINKS.findall(b))
                for b in dumps.blocos(caminho, tamanho=1000))
    assert total == 5000


def test_construir_grafo(pasta_dumps):
    g = dumps.construir_grafo(pasta_dumps)
    assert sorted(g.titulos) == sorted(
        ["Pelé", "Inglaterra", "Mecânica_quântica", "Rock_'n'_Roll", "Mercúrio_(planeta)"])
    arestas = {(g.titulo(u), g.titulo(int(v))) for u in range(g.n) for v in g.vizinhos(u)}
    assert arestas == {
        ("Pelé", "Inglaterra"),
        ("Inglaterra", "Mecânica_quântica"),
        ("Inglaterra", "Pelé"),
        ("Rock_'n'_Roll", "Pelé"),
        ("Mercúrio_(planeta)", "Rock_'n'_Roll"),
    }
