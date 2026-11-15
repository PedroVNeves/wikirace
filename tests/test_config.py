from wikirace import config


def test_caminhos_basicos():
    assert config.RAIZ.joinpath("wikirace", "config.py").exists()
    assert set(config.TABELAS) == {"page", "linktarget", "pagelinks", "redirect"}
    assert "{tabela}" in config.DUMP_URL
