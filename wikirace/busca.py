"""Buscas exatas: BFS clássica, BFS em níveis (numpy) e BFS bidirecional.

* ``bfs`` é a versão "de livro", com fila. É a que está provada no relatório
  (nível = distância, pais formam caminho mínimo, tempo O(|V| + |E|)).
* ``bfs_niveis`` faz a mesma coisa camada por camada com operações vetoriais
  do numpy. Dá as mesmas distâncias, mas é umas 50x mais rápida no grafo
  inteiro; é a que uso nas análises.
* ``bfs_bidirecional`` é o gabarito do Wikirace: cresce uma bola a partir da
  origem (seguindo links) e outra a partir do destino (seguindo links ao
  contrário) e para no primeiro encontro.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

import numpy as np

INF = -1  # nos vetores de distância, -1 quer dizer "não alcançável"


# --------------------------------------------------------------------- BFS
def bfs(g, s):
    """BFS a partir de ``s``. Devolve ``(dist, pai)`` como vetores numpy.

    ``dist[v] = -1`` e ``pai[v] = -1`` se ``v`` não é alcançável.
    """
    dist = np.full(g.n, INF, dtype=np.int32)
    pai = np.full(g.n, -1, dtype=np.int32)
    dist[s] = 0
    fila = deque([s])
    while fila:
        u = fila.popleft()
        for v in g.vizinhos(u).tolist():
            if dist[v] == INF:
                dist[v] = dist[u] + 1
                pai[v] = u
                fila.append(v)
    return dist, pai


def caminho_pelos_pais(pai, s, t):
    """Reconstrói o caminho s -> t seguindo ``pai`` de trás pra frente."""
    if s == t:
        return [s]
    if pai[t] == -1:
        return None
    cam = [t]
    while cam[-1] != s:
        cam.append(int(pai[cam[-1]]))
    return cam[::-1]


def bfs_niveis(g, s, max_nivel=None):
    """Distâncias a partir de ``s`` (ou de uma lista de fontes) camada por camada.

    Em vez de tirar um vértice por vez da fila, expande a fronteira inteira
    de uma vez: junta todos os vizinhos com fancy indexing, filtra os que já
    têm distância e marca os novos com ``nivel + 1``.
    """
    dist = np.full(g.n, INF, dtype=np.int32)
    fronteira = np.unique(np.atleast_1d(np.asarray(s, dtype=np.int64)))
    dist[fronteira] = 0
    nivel = 0
    while fronteira.size and (max_nivel is None or nivel < max_nivel):
        inicio = g.indptr[fronteira]
        tam = g.indptr[fronteira + 1] - inicio
        total = int(tam.sum())
        if total == 0:
            break
        # posições em ``indices`` de todos os vizinhos da fronteira
        desloc = np.repeat(inicio - (np.cumsum(tam) - tam), tam)
        viz = g.indices[desloc + np.arange(total)]
        novos = np.unique(viz[dist[viz] == INF])
        nivel += 1
        dist[novos] = nivel
        fronteira = novos.astype(np.int64)
    return dist


# ------------------------------------------------------- BFS bidirecional
@dataclass
class Resultado:
    caminho: list | None          # lista de vértices de s até t (ou None)
    consultados: int              # quantos artigos tiveram os links lidos
    detalhes: dict = field(default_factory=dict)

    @property
    def cliques(self):
        return None if self.caminho is None else len(self.caminho) - 1


def bfs_bidirecional(sucessores, predecessores, s, t, max_consultas=None):
    """BFS bidirecional genérica.

    ``sucessores(u)`` devolve os links que saem de ``u`` e ``predecessores(v)``
    os artigos que linkam para ``v`` (no grafo offline é o grafo transposto;
    ao vivo é o "Páginas afluentes" da API). Funciona com qualquer tipo de
    vértice que possa ser chave de dicionário.

    A cada passo expande o nível inteiro do lado com a menor fronteira. Para
    no primeiro vértice visto pelos dois lados. Isso já dá um caminho mínimo:
    se as bolas de raio ``kf`` (frente) e ``kt`` (trás) são disjuntas, então
    ``d(s, t) > kf + kt``; o primeiro encontro ao expandir a frente para
    ``kf + 1`` tem comprimento ``kf + 1 + kt``, que é o mínimo possível.
    """
    if s == t:
        return Resultado([s], 0)
    pai_f = {s: None}   # visitados pela frente, com o pai
    pai_t = {t: None}   # visitados por trás, com o "filho" (próximo no caminho)
    front_f, front_t = [s], [t]
    consultados = 0

    while front_f and front_t:
        if max_consultas is not None and consultados >= max_consultas:
            break
        frente = len(front_f) <= len(front_t)
        fronteira = front_f if frente else front_t
        vizinhos = sucessores if frente else predecessores
        meus, outros = (pai_f, pai_t) if frente else (pai_t, pai_f)
        nova = []
        for u in fronteira:
            consultados += 1
            for v in vizinhos(u):
                if v in meus:
                    continue
                meus[v] = u
                if v in outros:
                    return Resultado(_junta(pai_f, pai_t, v), consultados)
                nova.append(v)
        if frente:
            front_f = nova
        else:
            front_t = nova
    return Resultado(None, consultados)


def _junta(pai_f, pai_t, meio):
    ida = []
    v = meio
    while v is not None:
        ida.append(v)
        v = pai_f[v]
    ida.reverse()
    v = pai_t[meio]
    while v is not None:
        ida.append(v)
        v = pai_t[v]
    return ida


def bfs_bidirecional_grafo(g, s, t, max_consultas=None):
    """Atalho para o grafo offline (usa o transposto para andar de trás)."""
    gt = g.transposto()
    return bfs_bidirecional(lambda u: g.vizinhos(u).tolist(),
                            lambda v: gt.vizinhos(v).tolist(),
                            s, t, max_consultas)


def distancia(g, s, t):
    r = bfs_bidirecional_grafo(g, s, t)
    return r.cliques
