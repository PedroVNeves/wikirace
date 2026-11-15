"""Cliente simples da API do MediaWiki para jogar "ao vivo" na Wikipédia.

O grafo offline (dumps) é o que uso nas análises, mas a proposta também
pede agentes jogando na Wikipédia de verdade. Aqui ficam:

* ``links(t)``: artigos para onde ``t`` aponta (redirecionamentos já
  resolvidos e links vermelhos de fora);
* ``afluentes(t)``: artigos que apontam para ``t`` (para a BFS de trás);
* ``primeiro_link(t)``: o primeiro link do texto do artigo, pulando o que
  está entre parênteses, em itálico, em caixas e notas. O dump não guarda a
  ordem dos links, então isso só dá pra fazer com o HTML.

Tudo passa por um cache em SQLite, pra não repetir requisição (e não abusar
do servidor da Wikimedia).
"""

from __future__ import annotations

import json
import sqlite3
import time
from html.parser import HTMLParser
from urllib.parse import unquote

import requests

from . import config

API_URL = "https://pt.wikipedia.org/w/api.php"


def normaliza(titulo):
    """Formato dos títulos no dump: espaços viram ``_`` e 1ª letra maiúscula."""
    t = titulo.strip().replace(" ", "_")
    return t[:1].upper() + t[1:]


def _espera(resposta, tentativa):
    """Segundos até tentar de novo: usa o Retry-After do servidor se vier."""
    headers = getattr(resposta, "headers", None) or {}
    try:
        return min(float(headers.get("Retry-After", "")), 60.0)
    except ValueError:
        return min(2.0 ** tentativa, 60.0)


class Cache:
    def __init__(self, caminho=":memory:"):
        self.db = sqlite3.connect(str(caminho))
        self.db.execute("CREATE TABLE IF NOT EXISTS kv (k TEXT PRIMARY KEY, v TEXT)")

    def get(self, chave):
        linha = self.db.execute("SELECT v FROM kv WHERE k = ?", (chave,)).fetchone()
        return None if linha is None else json.loads(linha[0])

    def set(self, chave, valor):
        self.db.execute("INSERT OR REPLACE INTO kv VALUES (?, ?)",
                        (chave, json.dumps(valor, ensure_ascii=False)))
        self.db.commit()


class WikipediaAPI:
    def __init__(self, cache=None, sessao=None, pausa=0.0, url=API_URL):
        self.url = url
        self.cache = cache if cache is not None else Cache()
        self.sessao = sessao or requests.Session()
        self.sessao.headers.update({"User-Agent": config.USER_AGENT})
        self.pausa = pausa
        self.requisicoes = 0

    # ----------------------------------------------------------- baixo nível
    def _get(self, **params):
        params.update(format="json", formatversion=2, maxlag=5)
        motivo = ""
        for tentativa in range(8):
            r = self.sessao.get(self.url, params=params, timeout=30)
            self.requisicoes += 1
            if r.status_code in (429, 503):   # muitas requisições: espera e tenta de novo
                motivo = f"HTTP {r.status_code}"
                time.sleep(_espera(r, tentativa))
                continue
            r.raise_for_status()
            dados = r.json()
            if dados.get("error", {}).get("code") == "maxlag":  # servidor ocupado
                motivo = "maxlag"
                time.sleep(_espera(r, tentativa))
                continue
            if self.pausa:
                time.sleep(self.pausa)
            return dados
        raise RuntimeError(f"API da Wikipédia não respondeu ({motivo})")

    def _consulta_paginada(self, **params):
        """Segue o ``continue`` da API até acabar."""
        cont = {}
        while True:
            dados = self._get(action="query", **params, **cont)
            yield dados
            if "continue" not in dados:
                return
            cont = dados["continue"]

    def _com_cache(self, tipo, titulo, funcao):
        chave = f"{tipo}:{titulo}"
        valor = self.cache.get(chave)
        if valor is None:
            valor = funcao(titulo)
            self.cache.set(chave, valor)
        return valor

    # ------------------------------------------------------------ consultas
    def resolve(self, titulo):
        """Título canônico (segue redirecionamento). ``None`` se não existe."""
        def busca(t):
            dados = self._get(action="query", titles=t, redirects=1)
            pagina = dados["query"]["pages"][0]
            if pagina.get("missing") or pagina.get("invalid") or pagina["ns"] != 0:
                return ""
            return normaliza(pagina["title"])
        return self._com_cache("resolve", normaliza(titulo), busca) or None

    def links(self, titulo):
        def busca(t):
            saida = set()
            for dados in self._consulta_paginada(
                    generator="links", titles=t, gplnamespace=0, gpllimit="max",
                    redirects=1, prop="info"):
                for p in dados.get("query", {}).get("pages", []):
                    if not p.get("missing") and p["ns"] == 0:
                        saida.add(normaliza(p["title"]))
            saida.discard(t)
            return sorted(saida)
        return self._com_cache("links", normaliza(titulo), busca)

    def afluentes(self, titulo):
        """Quem linka para ``titulo`` (incluindo via redirecionamentos)."""
        def busca(t):
            saida = set()
            for dados in self._consulta_paginada(
                    list="backlinks", bltitle=t, blnamespace=0, bllimit="max",
                    blredirect=1):
                for b in dados.get("query", {}).get("backlinks", []):
                    if not b.get("redirect"):
                        saida.add(normaliza(b["title"]))
                    for r in b.get("redirlinks", []):
                        saida.add(normaliza(r["title"]))
            saida.discard(t)
            return sorted(saida)
        return self._com_cache("afluentes", normaliza(titulo), busca)

    def primeiro_link(self, titulo):
        def busca(t):
            # primeiro só a introdução (bem menor); se ela não tiver link
            # nenhum (acontece em artigos curtos), a página inteira
            alvo = None
            for secao in ({"section": 0}, {}):
                dados = self._get(action="parse", page=t, prop="text", redirects=1,
                                  disabletoc=1, **secao)
                if "error" in dados:
                    return ""
                alvo = extrai_primeiro_link(dados["parse"]["text"])
                if alvo is not None:
                    break
            if alvo is None:
                return ""
            return self.resolve(alvo) or ""
        # chave "primeiro2": o cache da versão antiga do parser tinha erros
        return self._com_cache("primeiro2", normaliza(titulo), busca) or None


# ------------------------------------------------- primeiro link do HTML
class _PrimeiroLink(HTMLParser):
    """Acha o primeiro link "de verdade" do texto de um artigo.

    Regras (as mesmas do jogo "todos os caminhos levam à Filosofia"):
    só links no texto corrido — parágrafos ``<p>`` e itens de lista ``<li>``
    (as páginas de desambiguação são só listas); pula tabelas (infobox),
    notas de cabeçalho, referências ``<sup>``, texto em itálico e qualquer
    coisa entre parênteses; e só links para artigos (sem ``:``).

    Os parênteses são contados em todo o texto do parágrafo, inclusive dentro
    de trechos pulados: senão um "(" fora e o ")" dentro de um widget pulado
    (acontecia na pronúncia de "França") deixam a conta desbalanceada. A conta
    zera a cada parágrafo novo.
    """

    PULAR = {"table", "sup", "figure", "style", "script"}
    VAZIAS = {"br", "img", "wbr", "link", "meta", "hr", "input", "source"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.pilha = []          # tags abertas (com marcação de "pular")
        self.em_texto = 0        # dentro de <p> ou <li>
        self.italico = 0
        self.pular = 0
        self.codigo = 0          # dentro de <style>/<script> (CSS tem parênteses)
        self.parenteses = 0
        self.achado = None

    def handle_starttag(self, tag, attrs):
        if self.achado is not None or tag in self.VAZIAS:
            return
        attrs = dict(attrs)
        classes = (attrs.get("class") or "").split()
        pula = (tag in self.PULAR or "hatnote" in classes or "dablink" in classes
                or "noprint" in classes or "reference" in classes
                or (tag == "div" and "mw-parser-output" not in classes)
                or (tag == "span" and "IPA" in classes))
        self.pilha.append((tag, pula))
        self.pular += pula
        self.codigo += tag in ("style", "script")
        if tag in ("p", "li"):
            self.em_texto += 1
            self.parenteses = 0
        if tag in ("i", "em"):
            self.italico += 1
        if (tag == "a" and self.em_texto and not self.pular and not self.italico
                and self.parenteses == 0):
            href = attrs.get("href") or ""
            if href.startswith("/wiki/") and "new" not in classes:
                alvo = unquote(href[len("/wiki/"):]).split("#")[0]
                if alvo and ":" not in alvo:
                    self.achado = alvo

    def handle_endtag(self, tag):
        if self.achado is not None or not any(t == tag for t, _ in self.pilha):
            return  # fechamento sem abertura: ignora em vez de esvaziar a pilha
        while self.pilha:
            t, pula = self.pilha.pop()
            self.pular -= pula
            self.codigo -= t in ("style", "script")
            if t in ("p", "li"):
                self.em_texto -= 1
            if t in ("i", "em"):
                self.italico -= 1
            if t == tag:
                break

    def handle_data(self, data):
        if self.achado is None and self.em_texto and not self.codigo:
            for c in data:
                if c == "(":
                    self.parenteses += 1
                elif c == ")" and self.parenteses:
                    self.parenteses -= 1


def extrai_primeiro_link(html):
    p = _PrimeiroLink()
    p.feed(html)
    return normaliza(p.achado) if p.achado else None
