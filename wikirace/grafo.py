"""Grafo dirigido em formato CSR (compressed sparse row).

Com ~10^6 vértices e dezenas de milhões de arestas, uma lista de adjacência
em dicionários do Python não cabe bem na memória. No CSR guardamos dois
vetores:

* ``indices``: todos os destinos, agrupados por origem;
* ``indptr``: ``indptr[u]:indptr[u+1]`` é o trecho de ``indices`` com os
  vizinhos de saída de ``u``.

Assim ``deg+(u) = indptr[u+1] - indptr[u]`` e a memória é O(|V| + |E|).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np


class Grafo:
    def __init__(self, indptr, indices, titulos=None):
        self.indptr = np.asarray(indptr, dtype=np.int64)
        self.indices = np.asarray(indices, dtype=np.int32)
        if self.indptr.ndim != 1 or self.indptr[0] != 0:
            raise ValueError("indptr precisa ser 1D e começar em 0")
        if self.indptr[-1] != len(self.indices):
            raise ValueError("indptr[-1] precisa ser igual ao número de arestas")
        if titulos is not None and len(titulos) != self.n:
            raise ValueError("um título por vértice")
        self.titulos = list(titulos) if titulos is not None else None
        self._indice_titulos = None
        self._transposto = None

    # ------------------------------------------------------------ construção
    @classmethod
    def de_arestas(cls, n, origens, destinos, titulos=None, remover_lacos=True):
        """Monta o CSR a partir de duas listas paralelas de arestas.

        Arestas repetidas viram uma só (o grafo é simples) e, por padrão,
        laços ``u -> u`` são descartados: clicar no próprio artigo não ajuda
        ninguém no Wikirace.
        """
        origens = np.asarray(origens)
        destinos = np.asarray(destinos)
        if len(origens) != len(destinos):
            raise ValueError("origens e destinos com tamanhos diferentes")
        if len(origens) and (min(origens.min(), destinos.min()) < 0
                             or max(origens.max(), destinos.max()) >= n):
            raise ValueError("vértice fora do intervalo [0, n)")
        # codifica (u, v) num inteiro só: u * n + v. Ordenar as chaves agrupa
        # por origem (e ordena os vizinhos), e repetidas ficam lado a lado.
        # Faço tudo in-place porque no grafo inteiro são ~10^8 arestas.
        chave = origens.astype(np.int64) * n
        chave += destinos
        if remover_lacos:
            chave = chave[origens != destinos]
        chave.sort()
        if len(chave):
            manter = np.empty(len(chave), dtype=bool)
            manter[0] = True
            np.not_equal(chave[1:], chave[:-1], out=manter[1:])
            chave = chave[manter]
        indptr = np.zeros(n + 1, dtype=np.int64)
        np.cumsum(np.bincount(chave // n, minlength=n), out=indptr[1:])
        return cls(indptr, (chave % n).astype(np.int32), titulos)

    @classmethod
    def de_dicionario(cls, adj):
        """Atalho para os testes: ``{'A': ['B', 'C'], 'B': ['C']}``."""
        nomes = sorted(set(adj) | {v for vs in adj.values() for v in vs})
        idx = {nome: i for i, nome in enumerate(nomes)}
        orig = [idx[u] for u, vs in adj.items() for _ in vs]
        dest = [idx[v] for vs in adj.values() for v in vs]
        return cls.de_arestas(len(nomes), orig, dest, titulos=nomes)

    # ------------------------------------------------------------- consultas
    @property
    def n(self):
        return len(self.indptr) - 1

    @property
    def m(self):
        return len(self.indices)

    def vizinhos(self, u):
        return self.indices[self.indptr[u]:self.indptr[u + 1]]

    def grau_saida(self):
        return np.diff(self.indptr)

    def grau_entrada(self):
        return np.bincount(self.indices, minlength=self.n)

    def tem_aresta(self, u, v):
        viz = self.vizinhos(u)  # ordenados, então dá pra usar busca binária
        i = np.searchsorted(viz, v)
        return bool(i < len(viz) and viz[i] == v)

    def transposto(self):
        """Grafo com todas as arestas invertidas (``v -> u``). Fica em cache."""
        if self._transposto is None:
            origens = np.repeat(np.arange(self.n, dtype=np.int64), self.grau_saida())
            t = Grafo.de_arestas(self.n, self.indices, origens, self.titulos,
                                 remover_lacos=False)
            t._transposto = self
            self._transposto = t
        return self._transposto

    def sem_vertices(self, removidos):
        """Cópia do grafo sem as arestas que tocam ``removidos``.

        Os vértices continuam existindo (os ids não mudam), só ficam isolados.
        Uso isso na análise de remoção de hubs.
        """
        fora = np.zeros(self.n, dtype=bool)
        fora[np.asarray(removidos, dtype=np.int64)] = True
        origens = np.repeat(np.arange(self.n, dtype=np.int64), self.grau_saida())
        ok = ~fora[origens] & ~fora[self.indices]
        return Grafo.de_arestas(self.n, origens[ok], self.indices[ok], self.titulos,
                                remover_lacos=False)

    # --------------------------------------------------------------- títulos
    def titulo(self, u):
        return self.titulos[u] if self.titulos is not None else str(u)

    def id_de(self, titulo):
        if self._indice_titulos is None:
            self._indice_titulos = {t: i for i, t in enumerate(self.titulos)}
        titulo = titulo.strip().replace(" ", "_")
        if titulo in self._indice_titulos:
            return self._indice_titulos[titulo]
        # a Wikipédia ignora maiúscula/minúscula só na primeira letra
        titulo = titulo[:1].upper() + titulo[1:]
        if titulo in self._indice_titulos:
            return self._indice_titulos[titulo]
        raise KeyError(f"artigo não encontrado: {titulo!r}")

    # ----------------------------------------------------------- persistência
    def salvar(self, caminho_npz, caminho_titulos=None):
        np.savez(caminho_npz, indptr=self.indptr, indices=self.indices)
        if caminho_titulos is not None and self.titulos is not None:
            Path(caminho_titulos).write_text("\n".join(self.titulos) + "\n",
                                             encoding="utf-8")

    @classmethod
    def carregar(cls, caminho_npz, caminho_titulos=None):
        dados = np.load(caminho_npz)
        titulos = None
        if caminho_titulos is not None and Path(caminho_titulos).exists():
            titulos = Path(caminho_titulos).read_text(encoding="utf-8").splitlines()
        return cls(dados["indptr"], dados["indices"], titulos)

    def __repr__(self):
        return f"Grafo(n={self.n}, m={self.m})"
