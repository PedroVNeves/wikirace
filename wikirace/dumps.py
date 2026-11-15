"""Monta o grafo completo da Wikipédia em português a partir dos dumps SQL.

Tabelas usadas (https://dumps.wikimedia.org/ptwiki/latest/):

* ``page``       (page_id, namespace, título, é_redirecionamento, ...)
* ``redirect``   (rd_from, namespace, título_destino, interwiki, ...)
* ``linktarget`` (lt_id, namespace, título)  — desde 2024 o pagelinks aponta
  para cá em vez de guardar o título direto
* ``pagelinks``  (pl_from, pl_from_namespace, pl_target_id)

Regras do grafo:

1. Vértices = artigos (namespace 0) que **não** são redirecionamentos.
2. Um link para um redirecionamento vira um link para o artigo final
   (seguindo cadeias de redirecionamento).
3. Links que saem de páginas de redirecionamento são ignorados.
4. Links para artigos que não existem (links vermelhos), para outros
   namespaces ou para redirecionamentos quebrados são descartados.
5. Laços e arestas repetidas são removidos (feito em ``Grafo.de_arestas``).

Os arquivos são lidos em blocos de alguns MB, porque o pagelinks
descomprimido tem alguns GB e não cabe inteiro na memória.
"""

from __future__ import annotations

import gzip
import re
import time
from pathlib import Path

import numpy as np
import requests

from . import config
from .grafo import Grafo

# string do MySQL entre aspas simples, com escapes do tipo \' e \\
_STR = rb"'((?:[^'\\]|\\.)*)'"
PADRAO_PAGE = re.compile(rb"\((\d+),(-?\d+)," + _STR + rb",([01]),", re.S)
PADRAO_REDIRECT = re.compile(rb"\((\d+),(-?\d+)," + _STR + rb",(NULL|'[^']*')", re.S)
PADRAO_LINKTARGET = re.compile(rb"\((\d+),(-?\d+)," + _STR + rb"\)", re.S)
PADRAO_PAGELINKS = re.compile(rb"\((\d+),0,(\d+)\)")  # só links saindo do ns 0

_ESCAPES = {b"0": b"\0", b"n": b"\n", b"r": b"\r", b"t": b"\t", b"Z": b"\x1a"}


def desescapa(b):
    """Desfaz os escapes do mysqldump (``Rock_\\'n\\'_Roll`` -> ``Rock_'n'_Roll``)."""
    if b"\\" not in b:
        return b
    return re.sub(rb"\\(.)", lambda m: _ESCAPES.get(m.group(1), m.group(1)), b,
                  flags=re.S)


def blocos(caminho, tamanho=16 * 2**20, verbose=False):
    """Lê o .sql.gz em blocos que sempre terminam numa quebra de linha."""
    inicio = time.time()
    with open(caminho, "rb") as bruto, gzip.open(bruto) as f:
        sobra = b""
        n = 0
        while True:
            b = f.read(tamanho)
            if not b:
                if sobra:
                    yield sobra
                break
            b = sobra + b
            corte = b.rfind(b"\n")
            if corte == -1:
                sobra = b
                continue
            yield b[:corte]
            sobra = b[corte + 1:]
            n += 1
            if verbose and n % 20 == 0:
                print(f"  {Path(caminho).name}: {bruto.tell() / 2**20:.0f} MB "
                      f"comprimidos lidos ({time.time() - inicio:.0f}s)", flush=True)


def tuplas(caminho, padrao, verbose=False):
    for bloco in blocos(caminho, verbose=verbose):
        yield from padrao.findall(bloco)


# ------------------------------------------------------------ cada tabela
def ler_paginas(caminho, verbose=False):
    """Páginas do namespace 0: ``(ids, titulos, eh_redirect)``."""
    ids, titulos, redir = [], [], []
    for pid, ns, titulo, r in tuplas(caminho, PADRAO_PAGE, verbose):
        if ns == b"0":
            ids.append(int(pid))
            titulos.append(desescapa(titulo))
            redir.append(r == b"1")
    return np.array(ids, dtype=np.int64), titulos, np.array(redir, dtype=bool)


def ler_redirects(caminho, verbose=False):
    """``{page_id do redirecionamento: título de destino}`` (só destino no ns 0)."""
    destino = {}
    for pid, ns, titulo, interwiki in tuplas(caminho, PADRAO_REDIRECT, verbose):
        if ns == b"0" and interwiki in (b"NULL", b"''"):
            destino[int(pid)] = desescapa(titulo)
    return destino


def resolver_redirects(ids, titulos, eh_redirect, destino_redirect, max_saltos=10):
    """Dá um vértice para cada título do namespace 0.

    Os artigos (não-redirecionamentos), em ordem de page_id, viram os vértices
    ``0..n-1``. Cada redirecionamento herda o vértice do artigo final da
    cadeia; se a cadeia quebra ou dá volta, ele fica de fora.

    Devolve ``(titulo_para_vertice, pagina_para_vertice, titulos_dos_vertices)``.
    """
    ordem = np.argsort(ids, kind="stable")
    ids, eh_redirect = ids[ordem], eh_redirect[ordem]
    titulos = [titulos[i] for i in ordem]

    vertice_da_pagina = {}
    titulos_vertices = []
    for pid, t, r in zip(ids.tolist(), titulos, eh_redirect.tolist()):
        if not r:
            vertice_da_pagina[pid] = len(titulos_vertices)
            titulos_vertices.append(t)
    pagina_do_titulo = dict(zip(titulos, ids.tolist()))

    titulo_para_vertice = {t: i for i, t in enumerate(titulos_vertices)}
    for pid, t, r in zip(ids.tolist(), titulos, eh_redirect.tolist()):
        if not r:
            continue
        atual = pid
        for _ in range(max_saltos):
            alvo = destino_redirect.get(atual)
            if alvo is None or alvo not in pagina_do_titulo:
                break
            atual = pagina_do_titulo[alvo]
            if atual in vertice_da_pagina:
                titulo_para_vertice[t] = vertice_da_pagina[atual]
                break

    pagina_para_vertice = np.full(int(ids.max()) + 1 if len(ids) else 1, -1,
                                  dtype=np.int32)
    for pid, v in vertice_da_pagina.items():
        pagina_para_vertice[pid] = v
    return titulo_para_vertice, pagina_para_vertice, titulos_vertices


def ler_linktargets(caminho, titulo_para_vertice, verbose=False):
    """Vetor denso ``lt_id -> vértice`` (``-1`` se o alvo não é artigo)."""
    lt_ids, vertices = [], []
    for lt, ns, titulo in tuplas(caminho, PADRAO_LINKTARGET, verbose):
        if ns != b"0":
            continue
        v = titulo_para_vertice.get(desescapa(titulo))
        if v is not None:
            lt_ids.append(int(lt))
            vertices.append(v)
    lt_ids = np.array(lt_ids, dtype=np.int64)
    mapa = np.full(int(lt_ids.max()) + 1 if len(lt_ids) else 1, -1, dtype=np.int32)
    mapa[lt_ids] = vertices
    return mapa


def ler_pagelinks(caminho, pagina_para_vertice, lt_para_vertice, verbose=False):
    """Arestas ``(origens, destinos)`` já traduzidas para vértices."""
    origens, destinos = [], []
    for bloco in blocos(caminho, verbose=verbose):
        achados = PADRAO_PAGELINKS.findall(bloco)
        if not achados:
            continue
        a = np.array(achados, dtype=np.int64)
        de, para = a[:, 0], a[:, 1]
        de = np.where(de < len(pagina_para_vertice),
                      pagina_para_vertice[np.minimum(de, len(pagina_para_vertice) - 1)], -1)
        para = np.where(para < len(lt_para_vertice),
                        lt_para_vertice[np.minimum(para, len(lt_para_vertice) - 1)], -1)
        ok = (de >= 0) & (para >= 0)
        origens.append(de[ok].astype(np.int32))
        destinos.append(para[ok].astype(np.int32))
    if not origens:
        return np.zeros(0, np.int32), np.zeros(0, np.int32)
    return np.concatenate(origens), np.concatenate(destinos)


# --------------------------------------------------------------- tudo junto
def construir_grafo(pasta, verbose=False):
    pasta = Path(pasta)
    arq = {t: pasta / f"ptwiki-latest-{t}.sql.gz" for t in config.TABELAS}

    def log(msg):
        if verbose:
            print(msg, flush=True)

    log("[1/4] page")
    ids, titulos, eh_redirect = ler_paginas(arq["page"], verbose)
    log(f"      {len(ids):,} páginas no ns 0, {eh_redirect.sum():,} redirecionamentos")
    log("[2/4] redirect")
    destino = ler_redirects(arq["redirect"], verbose)
    t2v, p2v, titulos_v = resolver_redirects(ids, titulos, eh_redirect, destino)
    del ids, titulos, eh_redirect, destino
    log(f"      {len(titulos_v):,} artigos (vértices)")
    log("[3/4] linktarget")
    lt2v = ler_linktargets(arq["linktarget"], t2v, verbose)
    del t2v
    log("[4/4] pagelinks")
    origens, destinos = ler_pagelinks(arq["pagelinks"], p2v, lt2v, verbose)
    del p2v, lt2v
    log(f"      {len(origens):,} links entre artigos (antes de tirar repetidos)")
    titulos_str = [t.decode("utf-8", errors="replace") for t in titulos_v]
    return Grafo.de_arestas(len(titulos_str), origens, destinos, titulos_str)


# --------------------------------------------------------------- download
def baixar(tabela, pasta=config.DUMPS, verbose=True):
    """Baixa ``ptwiki-latest-<tabela>.sql.gz`` (pula se já está completo).

    O servidor de dumps responde 429 se abrirmos muitas conexões ao mesmo
    tempo, então baixo um arquivo por vez.
    """
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    url = config.DUMP_URL.format(tabela=tabela)
    destino = pasta / Path(url).name
    cab = {"User-Agent": config.USER_AGENT}
    tamanho = int(requests.head(url, headers=cab, timeout=30).headers["Content-Length"])
    if destino.exists() and destino.stat().st_size == tamanho:
        if verbose:
            print(f"{destino.name} já existe")
        return destino
    with requests.get(url, headers=cab, stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(destino, "wb") as f:
            for pedaco in r.iter_content(2**20):
                f.write(pedaco)
    if destino.stat().st_size != tamanho:
        raise IOError(f"download incompleto de {destino.name}")
    if verbose:
        print(f"{destino.name}: {tamanho / 2**20:.0f} MB")
    return destino
