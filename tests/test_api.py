import pytest

from wikirace.api import Cache, WikipediaAPI, extrai_primeiro_link, normaliza


class RespostaFalsa:
    def __init__(self, dados, status=200):
        self.dados, self.status_code = dados, status

    def json(self):
        return self.dados

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(self.status_code)


class SessaoFalsa:
    """Responde de acordo com uma função e guarda as chamadas feitas."""

    def __init__(self, responder):
        self.responder = responder
        self.headers = {}
        self.chamadas = []

    def get(self, url, params, timeout):
        self.chamadas.append(dict(params))
        return self.responder(params)


def test_normaliza():
    assert normaliza(" mecânica quântica ") == "Mecânica_quântica"


def test_links_segue_continue_e_usa_cache():
    def responder(p):
        if "gplcontinue" not in p:
            return RespostaFalsa({
                "continue": {"gplcontinue": "x", "continue": "gplcontinue||"},
                "query": {"pages": [{"ns": 0, "title": "Inglaterra"},
                                    {"ns": 0, "title": "Link vermelho", "missing": True}]}})
        return RespostaFalsa({"query": {"pages": [{"ns": 0, "title": "Brasil"},
                                                  {"ns": 0, "title": "Pelé"}]}})

    sessao = SessaoFalsa(responder)
    api = WikipediaAPI(sessao=sessao)
    assert api.links("Pelé") == ["Brasil", "Inglaterra"]  # sem o próprio e sem vermelho
    assert len(sessao.chamadas) == 2
    assert api.links("pelé") == ["Brasil", "Inglaterra"]  # veio do cache
    assert len(sessao.chamadas) == 2


def test_afluentes_inclui_redirecionamentos():
    resposta = {"query": {"backlinks": [
        {"ns": 0, "title": "Futebol"},
        {"ns": 0, "title": "Rei do Futebol", "redirect": True,
         "redirlinks": [{"ns": 0, "title": "Santos FC"}]},
    ]}}
    api = WikipediaAPI(sessao=SessaoFalsa(lambda p: RespostaFalsa(resposta)))
    assert api.afluentes("Pelé") == ["Futebol", "Santos_FC"]


def test_tenta_de_novo_depois_de_429(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)
    respostas = iter([RespostaFalsa({}, 429),
                      RespostaFalsa({"query": {"pages": [{"ns": 0, "title": "Pelé"}]}})])
    api = WikipediaAPI(sessao=SessaoFalsa(lambda p: next(respostas)))
    assert api.resolve("Rei do Futebol") == "Pelé"


def test_resolve_inexistente():
    resposta = {"query": {"pages": [{"ns": 0, "title": "Xyz", "missing": True}]}}
    api = WikipediaAPI(sessao=SessaoFalsa(lambda p: RespostaFalsa(resposta)))
    assert api.resolve("Xyz") is None


def test_cache_em_disco(tmp_path):
    c = Cache(tmp_path / "c.sqlite")
    c.set("links:A", ["B"])
    assert Cache(tmp_path / "c.sqlite").get("links:A") == ["B"]


HTML_ARTIGO = """
<div class="mw-parser-output">
  <div class="hatnote">Não confundir com <a href="/wiki/Outra_coisa">outra coisa</a>.</div>
  <table class="infobox"><tr><td><a href="/wiki/Infobox_link">x</a></td></tr></table>
  <p><b>Edson Arantes do Nascimento</b> (<a href="/wiki/Tr%C3%AAs_Cora%C3%A7%C3%B5es">Três
  Corações</a>, 23 de outubro de 1940), conhecido como <i><a href="/wiki/Apelido">Pelé</a></i>,
  <sup class="reference"><a href="#cite_note-1">[1]</a></sup>
  foi um <a href="/wiki/Ficheiro:Bola.png">img</a> <a href="/wiki/Futebolista" title="Futebolista">futebolista</a>
  <a href="/wiki/Brasil">brasileiro</a>.</p>
</div>
"""


def test_primeiro_link_pula_parenteses_italico_e_caixas():
    assert extrai_primeiro_link(HTML_ARTIGO) == "Futebolista"


def test_primeiro_link_parenteses_dentro_do_link_nao_contam():
    html = '<p>A <a href="/wiki/Merc%C3%BArio_(planeta)">Mercúrio (planeta)</a> b</p>'
    assert extrai_primeiro_link(html) == "Mercúrio_(planeta)"


def test_primeiro_link_ignora_link_vermelho_e_ancora():
    html = ('<p><a class="new" href="/wiki/Nao_existe">x</a> '
            '<a href="/wiki/F%C3%ADsica#Hist%C3%B3ria">física</a></p>')
    assert extrai_primeiro_link(html) == "Física"
    assert extrai_primeiro_link("<p>sem links</p>") is None


@pytest.mark.rede
def test_api_de_verdade():
    api = WikipediaAPI()
    assert "Inglaterra" in api.links("Pelé")
    assert api.resolve("Rei do Futebol") == "Pelé"
    assert api.primeiro_link("Pelé") is not None


def test_respeita_retry_after(monkeypatch):
    esperas = []
    monkeypatch.setattr("time.sleep", esperas.append)

    class Resp429(RespostaFalsa):
        headers = {"Retry-After": "7"}

    respostas = iter([Resp429({}, 429),
                      RespostaFalsa({"query": {"pages": [{"ns": 0, "title": "Pelé"}]}})])
    api = WikipediaAPI(sessao=SessaoFalsa(lambda p: next(respostas)))
    assert api.resolve("Pelé") == "Pelé"
    assert esperas == [7.0]


def test_desiste_com_mensagem(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)
    api = WikipediaAPI(sessao=SessaoFalsa(lambda p: RespostaFalsa({}, 429)))
    with pytest.raises(RuntimeError, match="HTTP 429"):
        api.resolve("Pelé")
