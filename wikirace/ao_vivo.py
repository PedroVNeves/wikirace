"""Ambiente "ao vivo": os agentes jogam direto na Wikipédia, pela API.

Os vértices aqui são títulos (strings), não ids do grafo. O mesmo código dos
agentes funciona, porque eles só usam ``vizinhos``, ``grau``,
``similaridade`` e ``predecessores``.

O grau de um link (pro guloso por grau) exigiria uma requisição por link.
Então uso o grau que veio do dump, se o grafo offline for passado — é como
um humano que "sabe" que Brasil é um artigo enorme sem precisar abrir.
"""

from __future__ import annotations

import numpy as np

from .api import normaliza


class AmbienteAPI:
    def __init__(self, api, codificador=None, grafo=None):
        self.api = api
        self.codificador = codificador  # semantica.CodificadorComCache
        self.grafo = grafo

    def vizinhos(self, u):
        return np.array(self.api.links(u), dtype=object)

    def predecessores(self, v):
        return np.array(self.api.afluentes(v), dtype=object)

    def grau(self, vs):
        if self.grafo is None:
            raise RuntimeError("guloso por grau ao vivo precisa do grafo offline")
        saida = np.zeros(len(vs), dtype=np.int64)
        for i, t in enumerate(vs):
            try:
                saida[i] = len(self.grafo.vizinhos(self.grafo.id_de(t)))
            except KeyError:  # artigo novo, que não estava no dump
                saida[i] = 0
        return saida

    def similaridade(self, vs, t):
        if self.codificador is None:
            raise RuntimeError("esse agente precisa do modelo de embeddings")
        vs = list(vs)
        e = self.codificador(vs + [t])
        return e[:-1] @ e[-1]

    def nome(self, u):
        return u

    def resolve(self, titulo):
        return self.api.resolve(normaliza(titulo))
