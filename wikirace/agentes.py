"""Os agentes que jogam Wikirace.

Todos jogam num *ambiente*, que sabe dar os links de um artigo
(``vizinhos``), o grau de saída de artigos (``grau``) e a similaridade de
texto entre artigos (``similaridade``). Cada vez que o agente lê os links de
um artigo conta como uma **consulta** — é a medida de "quanto ele explorou".

Dois tipos de agente:

* **Caminhantes** (aleatório, guloso por grau, guloso semântico): andam um
  clique por vez, como um humano. Os cliques contados são os da caminhada.
* **Buscadores** (BFS bidirecional, A*): exploram o grafo "de cabeça" e só no
  fim dizem o caminho. Os cliques são o tamanho do caminho achado e a
  exploração aparece nas consultas.

Regra comum: se o destino aparece entre os links do artigo atual, o
caminhante clica nele (qualquer humano faria isso).
"""

from __future__ import annotations

import heapq
import itertools
import time
from dataclasses import dataclass, field

import numpy as np

from .busca import bfs_bidirecional


def _py(x):
    """numpy.int32 -> int; strings (ambiente ao vivo) passam direto."""
    return x.item() if isinstance(x, np.generic) else x


# ----------------------------------------------------------------- ambiente
class AmbienteGrafo:
    """Ambiente offline: o grafo dos dumps + (opcional) embeddings dos títulos."""

    def __init__(self, g, embeddings=None):
        self.g = g
        self.emb = embeddings  # matriz n x d, linhas normalizadas (pode ser memmap)
        self._gt = None

    def vizinhos(self, u):
        return self.g.vizinhos(u)

    def predecessores(self, v):
        if self._gt is None:
            self._gt = self.g.transposto()
        return self._gt.vizinhos(v)

    def grau(self, vs):
        vs = np.asarray(vs, dtype=np.int64)
        return self.g.indptr[vs + 1] - self.g.indptr[vs]

    def similaridade(self, vs, t):
        if self.emb is None:
            raise RuntimeError("esse agente precisa de embeddings")
        vs = np.asarray(vs, dtype=np.int64)
        return np.asarray(self.emb[vs], dtype=np.float32) @ np.asarray(self.emb[t], dtype=np.float32)

    def nome(self, u):
        return self.g.titulo(int(u))


# ----------------------------------------------------------------- partida
@dataclass
class Partida:
    agente: str
    origem: object
    destino: object
    caminho: list | None
    consultados: int
    segundos: float = 0.0
    extra: dict = field(default_factory=dict)

    @property
    def sucesso(self):
        return self.caminho is not None and self.caminho[-1] == self.destino

    @property
    def cliques(self):
        return len(self.caminho) - 1 if self.sucesso else None


class _Leitor:
    """Conta quantos artigos diferentes tiveram os links lidos numa partida."""

    def __init__(self, amb, max_consultas):
        self.amb, self.max = amb, max_consultas
        self.lidos = {}

    def __call__(self, u):
        if u not in self.lidos:
            if self.max is not None and len(self.lidos) >= self.max:
                raise _Estouro
            self.lidos[u] = np.asarray(self.amb.vizinhos(u))
        return self.lidos[u]

    @property
    def n(self):
        return len(self.lidos)


class _Estouro(Exception):
    pass


class Agente:
    nome = "agente"

    def jogar(self, amb, s, t, max_cliques=50, max_consultas=None, semente=0):
        leitor = _Leitor(amb, max_consultas)
        inicio = time.perf_counter()
        try:
            caminho, extra = self._jogar(amb, leitor, s, t, max_cliques,
                                         np.random.default_rng(semente))
        except _Estouro:
            caminho, extra = None, {"motivo": "limite de consultas"}
        return Partida(self.nome, s, t, caminho, leitor.n,
                       time.perf_counter() - inicio, extra)

    def _jogar(self, amb, ler, s, t, max_cliques, rng):
        raise NotImplementedError


# -------------------------------------------------------------- caminhantes
class Caminhante(Agente):
    """Anda clique a clique. Se cai num beco (sem link novo), aperta "voltar",
    que também conta como clique."""

    evita_repetir = True

    def escolher(self, amb, candidatos, t, rng):
        raise NotImplementedError

    def _jogar(self, amb, ler, s, t, max_cliques, rng):
        caminho, pilha, visitados = [s], [s], {s}
        while len(caminho) - 1 < max_cliques:
            atual = pilha[-1]
            if atual == t:
                return caminho, {}
            viz = ler(atual)
            if np.any(viz == t):
                caminho.append(t)
                return caminho, {}
            if self.evita_repetir:
                cand = viz[[v not in visitados for v in viz.tolist()]] if len(viz) else viz
            else:
                cand = viz
            if len(cand) == 0:
                pilha.pop()
                if not pilha:
                    return None, {"motivo": "sem saída"}
                caminho.append(pilha[-1])
                continue
            v = self.escolher(amb, cand, t, rng)
            caminho.append(v)
            pilha.append(v)
            visitados.add(v)
        return None, {"motivo": "limite de cliques", "caminhada": caminho}


class PasseioAleatorio(Caminhante):
    """Linha de base: clica num link qualquer (pode repetir artigo)."""
    nome = "aleatorio"
    evita_repetir = False

    def escolher(self, amb, candidatos, t, rng):
        return _py(candidatos[rng.integers(len(candidatos))])


class GulosoGrau(Caminhante):
    """Vai sempre para o artigo com mais links (os hubs, tipo "Brasil")."""
    nome = "guloso_grau"

    def escolher(self, amb, candidatos, t, rng):
        return _py(candidatos[int(np.argmax(amb.grau(candidatos)))])


class GulosoSemantico(Caminhante):
    """Vai para o link cujo título é mais parecido com o destino."""
    nome = "guloso_semantico"

    def escolher(self, amb, candidatos, t, rng):
        return _py(candidatos[int(np.argmax(amb.similaridade(candidatos, t)))])


# --------------------------------------------------------------- buscadores
class BFSBidirecional(Agente):
    """O gabarito: sempre acha o caminho mínimo."""
    nome = "bfs_bidirecional"

    def _jogar(self, amb, ler, s, t, max_cliques, rng):
        r = bfs_bidirecional(lambda u: ler(u).tolist(),
                             lambda v: amb.predecessores(v).tolist(), s, t)
        # a BFS de trás também lê artigos ("quem linka pra cá"); somo no extra
        return r.caminho, {"expansoes": r.consultados}

    def jogar(self, amb, s, t, max_cliques=50, max_consultas=None, semente=0):
        p = super().jogar(amb, s, t, max_cliques, max_consultas, semente)
        p.consultados = p.extra.get("expansoes", p.consultados)
        return p


class AEstrela(Agente):
    """A* com f(v) = g(v) + w * h(v), onde h(v) = (1 - cos(v, t)) / 2.

    Como os embeddings são normalizados, cos ∈ [-1, 1] e h ∈ [0, 1], com
    h(t) = 0. Para v ≠ t vale d(v, t) >= 1 >= h(v), então h é admissível e
    com w = 1 o A* acha o ótimo. Com w > 1 o caminho fica no máximo w vezes
    o ótimo, mas a busca fica bem mais "gulosa" e consulta menos artigos.
    """

    def __init__(self, w=1.0):
        self.w = w
        self.nome = f"a_estrela_w{w:g}"

    def h(self, amb, vs, t):
        h = (1.0 - amb.similaridade(vs, t)) / 2.0
        h = np.clip(h, 0.0, 1.0)
        h[np.asarray(vs) == t] = 0.0
        return h

    def _jogar(self, amb, ler, s, t, max_cliques, rng):
        desempate = itertools.count()
        g = {s: 0}
        pai = {s: None}
        h_s = float(self.h(amb, [s], t)[0])
        aberta = [(self.w * h_s, h_s, next(desempate), s)]
        while aberta:
            f, hu, _, u = heapq.heappop(aberta)
            if f > g[u] + self.w * hu + 1e-12:   # entrada velha na fila
                continue
            if u == t:
                cam = []
                while u is not None:
                    cam.append(u)
                    u = pai[u]
                return cam[::-1], {}
            viz = ler(u)
            if len(viz) == 0:
                continue
            hs = self.h(amb, viz, t)
            gu = g[u] + 1
            for v, hv in zip(viz.tolist(), hs.tolist()):
                if gu < g.get(v, float("inf")):   # achou caminho melhor: (re)abre
                    g[v] = gu
                    pai[v] = u
                    heapq.heappush(aberta, (gu + self.w * hv, hv, next(desempate), v))
        return None, {"motivo": "sem caminho"}


def todos_os_agentes(pesos_a_estrela=(1, 2, 4)):
    return ([BFSBidirecional()] + [AEstrela(w) for w in pesos_a_estrela]
            + [GulosoSemantico(), GulosoGrau(), PasseioAleatorio()])
