"""Análises estruturais do grafo da Wikipédia.

* componentes fortemente conexas (Kosaraju) e o grafo de componentes;
* distâncias numa amostra de pares (mundo pequeno) e comparação com
  Erdős–Rényi com os mesmos |V| e |E|;
* graus e remoção de hubs;
* assimetria d(u, v) ≠ d(v, u);
* grafos funcionais (o "primeiro link" de cada artigo).
"""

from __future__ import annotations

from collections import Counter

import numpy as np

from .busca import INF, bfs_niveis
from .grafo import Grafo


# ------------------------------------------------- componentes fortes
def componentes_fortes(g):
    """Kosaraju iterativo. Devolve ``rotulos`` (componente de cada vértice).

    1ª passada: DFS no grafo e guarda a ordem de término.
    2ª passada: DFS no grafo transposto, pegando os vértices na ordem
    inversa de término; cada árvore dessa DFS é uma componente.

    Uso ``memoryview`` em vez de indexar o numpy direto porque acessar um
    elemento de memoryview devolve um int do Python bem mais rápido (são
    ~10^8 acessos no grafo inteiro).
    """
    n = g.n
    ordem = _ordem_de_termino(n, g.indptr, g.indices)
    gt = g.transposto()
    ip, ix = memoryview(gt.indptr), memoryview(gt.indices)
    rotulo = np.full(n, -1, dtype=np.int32)
    rot = memoryview(rotulo)
    c = 0
    for r in reversed(ordem.tolist()):
        if rot[r] != -1:
            continue
        rot[r] = c
        pilha = [r]
        while pilha:
            u = pilha.pop()
            for p in range(ip[u], ip[u + 1]):
                v = ix[p]
                if rot[v] == -1:
                    rot[v] = c
                    pilha.append(v)
        c += 1
    return rotulo


def _ordem_de_termino(n, indptr, indices):
    ip, ix = memoryview(indptr), memoryview(indices)
    prox = np.array(indptr[:-1], dtype=np.int64)  # próximo vizinho a olhar de cada u
    pr = memoryview(prox)
    vis = bytearray(n)
    ordem = np.empty(n, dtype=np.int32)
    k = 0
    for r in range(n):
        if vis[r]:
            continue
        vis[r] = 1
        pilha = [r]
        while pilha:
            u = pilha[-1]
            p, fim = pr[u], ip[u + 1]
            while p < fim and vis[ix[p]]:
                p += 1
            if p < fim:
                v = ix[p]
                pr[u] = p + 1
                vis[v] = 1
                pilha.append(v)
            else:
                pr[u] = p
                pilha.pop()
                ordem[k] = u
                k += 1
    return ordem


def condensacao(g, rotulos):
    """Grafo das componentes: uma aresta C -> D se algum u ∈ C linka v ∈ D."""
    k = int(rotulos.max()) + 1
    origens = np.repeat(rotulos, g.grau_saida())
    destinos = rotulos[g.indices]
    fora = origens != destinos
    return Grafo.de_arestas(k, origens[fora], destinos[fora])


def eh_aciclico(g):
    """Algoritmo de Kahn: tira fontes até acabar; sobrou vértice => tem ciclo."""
    grau_ent = g.grau_entrada().copy()
    fila = list(np.flatnonzero(grau_ent == 0))
    removidos = 0
    while fila:
        u = fila.pop()
        removidos += 1
        for v in g.vizinhos(u).tolist():
            grau_ent[v] -= 1
            if grau_ent[v] == 0:
                fila.append(v)
    return removidos == g.n


def gravata_borboleta(g, rotulos):
    """Classifica os vértices em relação à maior componente forte (SCC):
    SCC, IN (chega na SCC), OUT (é alcançado pela SCC) e OUTROS."""
    gigante = np.bincount(rotulos).argmax()
    raiz = int(np.flatnonzero(rotulos == gigante)[0])
    sai = bfs_niveis(g, raiz) >= 0
    chega = bfs_niveis(g.transposto(), raiz) >= 0
    scc = sai & chega
    return {"SCC": int(scc.sum()), "IN": int((chega & ~scc).sum()),
            "OUT": int((sai & ~scc).sum()), "OUTROS": int((~sai & ~chega).sum())}


# --------------------------------------------------- distâncias / BFS
def histograma_distancias(g, fontes, bloqueados=None):
    """Conta, para cada distância d, quantos pares (fonte, v) têm d(fonte, v) = d.

    Devolve ``(contagem, sem_caminho, total_de_pares)``; pares (s, s) não contam.
    Com bloqueados, os vértices removidos não entram como destino.
    """
    contagem = Counter()
    sem_caminho = 0
    validos = g.n if bloqueados is None else g.n - int(bloqueados.sum())
    for s in fontes:
        d = bfs_niveis(g, int(s), bloqueados=bloqueados)
        alcancados = d[d > 0]
        valores, quantos = np.unique(alcancados, return_counts=True)
        contagem.update(dict(zip(valores.tolist(), quantos.tolist())))
        sem_caminho += validos - 1 - len(alcancados)
    total = len(fontes) * (validos - 1)
    return {int(k): int(v) for k, v in sorted(contagem.items())}, int(sem_caminho), int(total)


def resumo_distancias(hist, sem_caminho, total):
    ds = np.array(list(hist.keys()), dtype=float)
    cs = np.array(list(hist.values()), dtype=float)
    media = float((ds * cs).sum() / cs.sum()) if cs.sum() else float("nan")
    acum = np.cumsum(cs) / cs.sum() if cs.sum() else cs
    mediana = int(ds[np.searchsorted(acum, 0.5)]) if cs.sum() else None
    efetivo = int(ds[np.searchsorted(acum, 0.9)]) if cs.sum() else None
    return {"media": media, "mediana": mediana, "diametro_efetivo_90": efetivo,
            "maior_vista": int(ds.max()) if len(ds) else None,
            "fracao_sem_caminho": sem_caminho / total if total else float("nan")}


def erdos_renyi_dirigido(n, m, semente=0):
    """G(n, m) dirigido gerado direto em CSR.

    Sorteia m origens e m destinos uniformes. Repetições e laços são tão
    raros (~m²/2n² ≈ 2 mil em 80 milhões) que não vale a pena tirar, e assim
    não preciso ordenar 80 milhões de chaves.
    """
    rng = np.random.default_rng(semente)
    cont = rng.multinomial(m, np.full(n, 1.0 / n))
    indptr = np.zeros(n + 1, dtype=np.int64)
    np.cumsum(cont, out=indptr[1:])
    indices = rng.integers(0, n, size=m, dtype=np.int32)
    return Grafo(indptr, indices)


# ------------------------------------------------------------ assimetria
def assimetria(g, fontes):
    """Para pares (s, v) com s nas fontes: compara d(s, v) com d(v, s).

    Uma BFS no grafo dá d(s, ·) e uma no transposto dá d(·, s).
    """
    gt = g.transposto()
    iguais = diferentes = so_ida = 0
    diferencas = Counter()
    for s in fontes:
        ida = bfs_niveis(g, int(s))
        volta = bfs_niveis(gt, int(s))
        ida[s] = volta[s] = INF  # tira o par (s, s)
        ambos = (ida >= 0) & (volta >= 0)
        um = (ida >= 0) ^ (volta >= 0)
        iguais += int((ambos & (ida == volta)).sum())
        diferentes += int((ambos & (ida != volta)).sum())
        so_ida += int(um.sum())
        valores, quantos = np.unique(np.abs(ida[ambos] - volta[ambos]), return_counts=True)
        diferencas.update(dict(zip(valores.tolist(), quantos.tolist())))
    total = iguais + diferentes + so_ida
    return {"pares_com_algum_caminho": total,
            "fracao_simetrica": iguais / total if total else float("nan"),
            "fracao_diferente_ambos_finitos": diferentes / total if total else float("nan"),
            "fracao_so_um_sentido": so_ida / total if total else float("nan"),
            "hist_diferenca_absoluta": {int(k): int(v) for k, v in sorted(diferencas.items())}}


# ------------------------------------------------------ grafos funcionais
def segue_ate_ciclo(f, inicio, max_passos=10_000):
    """Aplica f (o "primeiro link") até repetir um artigo.

    Pela casa dos pombos, num conjunto finito isso sempre acontece. Devolve
    ``(cauda, ciclo)``; se f(v) não existe (artigo sem link), ciclo = [].
    """
    visto = {}
    seq = []
    v = inicio
    while v is not None and v not in visto and len(seq) < max_passos:
        visto[v] = len(seq)
        seq.append(v)
        v = f(v)
    if v is None or v not in visto:
        return seq, []
    i = visto[v]
    return seq[:i], seq[i:]


def ciclo_canonico(ciclo):
    """Escreve o ciclo começando pelo menor elemento (pra comparar ciclos)."""
    if not ciclo:
        return ()
    i = min(range(len(ciclo)), key=lambda j: ciclo[j])
    return tuple(ciclo[i:] + ciclo[:i])


def componentes_funcionais(f_dict):
    """Para um grafo funcional dado como dicionário v -> f(v), devolve a lista
    de componentes (fracamente conexas) e os ciclos de cada uma.

    Serve pra checar o resultado do relatório: cada componente tem exatamente
    um ciclo (desde que todo vértice tenha f(v) definido dentro do conjunto).
    """
    pai = {v: v for v in f_dict}

    def acha(x):
        while pai[x] != x:
            pai[x] = pai[pai[x]]
            x = pai[x]
        return x

    for v, w in f_dict.items():
        a, b = acha(v), acha(w)
        if a != b:
            pai[a] = b
    comps = {}
    for v in f_dict:
        comps.setdefault(acha(v), set()).add(v)
    ciclos = {}
    for v in f_dict:
        _, ciclo = segue_ate_ciclo(f_dict.get, v)
        ciclos.setdefault(acha(v), set()).add(ciclo_canonico(ciclo))
    return [(comps[r], ciclos[r]) for r in comps]
