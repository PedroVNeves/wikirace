"""Gera as figuras do relatório a partir de resultados/ (JSON e CSV).

Uso:
    python scripts/figuras.py

Salva os PNG em relatorio/figuras/.
"""

import json
import sys
from pathlib import Path

import matplotlib
import matplotlib.ticker

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from wikirace import config  # noqa: E402

FIG = config.RAIZ / "relatorio" / "figuras"
ANALISES = config.RESULTADOS / "analises"
EXPERIMENTO = config.RESULTADOS / "experimento"

# paleta (ordem fixa) e tons de texto
AZUL, LARANJA, AQUA, VIOLETA = "#2a78d6", "#eb6834", "#1baf7a", "#6250d6"
TEXTO, TEXTO_2, GRADE, FUNDO = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
# A* com pesos diferentes: uma rampa só de azul (mais escuro = mais exato)
RAMPA_AZUL = {1: "#104281", 2: "#1c5cab", 4: "#2a78d6", 8: "#6da7ec"}

NOMES = {"bfs_bidirecional": "BFS bidirecional", "guloso_semantico": "Guloso semântico",
         "guloso_grau": "Guloso por grau", "aleatorio": "Passeio aleatório"}


def nome_agente(a):
    if a.startswith("a_estrela_w"):
        return f"A* (w = {a[len('a_estrela_w'):]})"
    return NOMES.get(a, a)


def cor_agente(a):
    if a.startswith("a_estrela_w"):
        return RAMPA_AZUL.get(int(float(a[len("a_estrela_w"):])), AZUL)
    return {"bfs_bidirecional": TEXTO_2, "guloso_semantico": LARANJA,
            "guloso_grau": AQUA, "aleatorio": VIOLETA}.get(a, TEXTO_2)


def br(x, casas=2, pct=False):
    """Número no formato brasileiro: vírgula decimal, ponto no milhar."""
    texto = f"{100 * x:,.{casas}f}%" if pct else f"{x:,.{casas}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def eixo_br(ax, casas=1, pct=False):
    from matplotlib.ticker import FuncFormatter
    ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: br(y, casas, pct)))


def estilo():
    plt.rcParams.update({
        "figure.facecolor": FUNDO, "axes.facecolor": FUNDO, "savefig.facecolor": FUNDO,
        "axes.edgecolor": GRADE, "axes.labelcolor": TEXTO_2, "axes.titlecolor": TEXTO,
        "xtick.color": TEXTO_2, "ytick.color": TEXTO_2, "axes.grid": True,
        "grid.color": GRADE, "grid.linewidth": 0.6, "axes.axisbelow": True,
        "axes.spines.top": False, "axes.spines.right": False, "font.size": 10,
        "axes.titlesize": 11, "axes.titleweight": "bold", "legend.frameon": False,
        "lines.linewidth": 2, "lines.markersize": 6, "figure.dpi": 150,
    })


def ler(nome):
    return json.loads((ANALISES / f"{nome}.json").read_text(encoding="utf-8"))


def salvar(fig, nome):
    FIG.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(FIG / f"{nome}.png", bbox_inches="tight")
    plt.close(fig)
    print("  ", nome)


def frac(hist, total):
    d = np.array([int(k) for k in hist])
    c = np.array(list(hist.values()), dtype=float)
    return d, c / total


# ------------------------------------------------------------ figuras
def fig_distancias():
    dados = ler("distancias")
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    largura = 0.4
    for i, (chave, rotulo, cor) in enumerate([("wikipedia", "Wikipédia", AZUL),
                                               ("erdos_renyi", "Erdős–Rényi", LARANJA)]):
        h = dados[chave]["hist"]
        total = sum(h.values())
        d, f = frac(h, total)
        ok = d <= 10
        ax.bar(d[ok] + (i - 0.5) * largura, f[ok], width=largura - 0.03, color=cor,
               label=f"{rotulo} (média {br(dados[chave]['media'])})")
    ax.set_xticks(range(1, 11))
    ax.set_xlabel("d(u, v)  (cliques)")
    ax.set_ylabel("pares com caminho")
    eixo_br(ax, 0, pct=True)
    ax.set_title("Distâncias entre artigos: Wikipédia vs. grafo aleatório")
    ax.legend()
    salvar(fig, "distancias")


def fig_graus():
    dados = ler("hubs")
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    for chave, rotulo, cor in [("grau_entrada", "grau de entrada", AZUL),
                               ("grau_saida", "grau de saída", LARANJA)]:
        k = np.array([int(x) for x in dados[chave]])
        c = np.array(list(dados[chave].values()), dtype=float)
        ccdf = c[::-1].cumsum()[::-1] / c.sum()  # P(grau >= k)
        ok = k > 0
        ax.loglog(k[ok], ccdf[ok], color=cor, label=rotulo)
    ax.set_xlabel("k")
    ax.set_ylabel("P(grau ≥ k)")
    ax.set_title("Distribuição dos graus (cauda complementar)")
    ax.legend()  # os maiores hubs ficam numa tabela do relatório
    salvar(fig, "graus")


def fig_hubs():
    dados = ler("hubs")["remocao"]
    k = [r["removidos"] for r in dados]
    rot = [f"{x:,}".replace(",", ".") for x in k]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.6, 3.2))
    a1.plot(rot, [r["media"] for r in dados], marker="o", color=AZUL)
    a1.set_title("Distância média")
    a1.set_ylabel("cliques")
    a2.plot(rot, [r["fracao_sem_caminho"] for r in dados], marker="o", color=AZUL)
    a2.set_title("Pares sem caminho")
    a2.set_ylabel("pares")
    eixo_br(a1, 1)
    eixo_br(a2, 0, pct=True)
    for a in (a1, a2):
        a.set_xlabel("hubs removidos (maior grau de entrada)")
    # rótulos embaixo-à-direita na curva que sobe, em cima na curva quase reta
    for a, campo, pct, desloc, ha in [(a1, "media", False, (6, -12), "left"),
                                      (a2, "fracao_sem_caminho", True, (0, 8), "center")]:
        for x, r in zip(rot, dados):
            a.annotate(br(r[campo], 1 if pct else 2, pct), (x, r[campo]),
                       textcoords="offset points", xytext=desloc, ha=ha,
                       fontsize=8, color=TEXTO_2)
    salvar(fig, "hubs")


def fig_assimetria():
    dados = ler("assimetria")
    h = dados["hist_diferenca_absoluta"]
    d = np.array([int(x) for x in h])
    c = np.array(list(h.values()), dtype=float)
    c = c / c.sum()
    barras = list(c[d <= 4]) + [c[d >= 5].sum()]
    rotulos = [str(x) for x in d[d <= 4]] + ["≥ 5"]
    fig, ax = plt.subplots(figsize=(5.4, 3.0))
    ax.bar(rotulos, barras, color=AZUL, width=0.7)
    for x, y in zip(rotulos, barras):
        ax.annotate(br(y, 1, pct=True), (x, y), textcoords="offset points", xytext=(0, 3),
                    ha="center", fontsize=8, color=TEXTO_2)
    ax.set_xlabel("|d(u, v) − d(v, u)|")
    ax.set_ylabel("pares")
    eixo_br(ax, 0, pct=True)
    ax.set_title("Assimetria (pares com caminho nos dois sentidos)")
    salvar(fig, "assimetria")


def fig_curva_sucesso():
    curva = pd.read_csv(EXPERIMENTO / "curva.csv")
    ordem = (curva.groupby("agente")["taxa"].max().sort_values(ascending=False).index)
    fig, ax = plt.subplots(figsize=(7.0, 4.0))
    for a in ordem:
        c = curva[curva.agente == a]
        estilo_linha = "--" if a == "bfs_bidirecional" else "-"
        ax.plot(c.limite, 100 * c.taxa, estilo_linha, color=cor_agente(a),
                label=nome_agente(a), linewidth=1.6 if a.startswith("a_") else 2)
    ax.set_xlabel("limite de cliques L")
    ax.set_ylabel("pares resolvidos com ≤ L cliques")
    ax.set_title("Taxa de sucesso por limite de cliques")
    ax.set_ylim(0, 102)
    eixo_br(ax, 0)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda y, _: f"{y:.0f}%"))
    ax.legend(loc="center left", bbox_to_anchor=(1.0, 0.5))
    salvar(fig, "curva_sucesso")


def fig_tradeoff():
    """A figura que responde a pergunta: quão perto do ótimo x quanto explora.

    Só partidas concluídas (as que bateram no teto de consultas ou de cliques
    distorceriam a mediana) e só agentes com pelo menos 5 sucessos; o resto
    fica na tabela do relatório. A* com w = 1 e w = 2 resolvem exatamente os
    mesmos pares com os mesmos números, então viram um ponto só.
    """
    df = pd.read_csv(EXPERIMENTO / "partidas.csv")
    ok = df[df.sucesso]
    tab = ok.groupby("agente").agg(n=("par", "size"), consultados=("consultados", "median"),
                                   razao=("razao", "mean"))
    tab["taxa"] = tab["n"] / df.groupby("agente").size()
    tab = tab[tab.n >= 5].drop(index="a_estrela_w2", errors="ignore")
    rotulo = {"a_estrela_w1": "A* (w = 1 e 2)"}
    # deslocamento (pontos) de cada rótulo, escolhido olhando a figura
    desloc = {"bfs_bidirecional": (10, 0, "left"), "guloso_semantico": (10, 0, "left"),
              "a_estrela_w8": (0, 22, "center"), "a_estrela_w4": (0, -26, "center"),
              "a_estrela_w1": (12, 10, "left")}
    fig, ax = plt.subplots(figsize=(6.8, 4.0))
    ax.axhline(1, color=GRADE, linewidth=1, zorder=1)
    for a, r in tab.iterrows():
        ax.scatter(r.consultados, r.razao, s=50, color=cor_agente(a), edgecolor=FUNDO,
                   linewidth=2, zorder=3)
        dx, dy, ha = desloc.get(a, (10, 0, "left"))
        ax.annotate(f"{rotulo.get(a, nome_agente(a))}\n{br(r.razao, 2)}× o ótimo, "
                    f"{br(r.taxa, 0, True)} resolvidos",
                    (r.consultados, r.razao), textcoords="offset points", xytext=(dx, dy),
                    ha=ha, va="center", fontsize=8, color=TEXTO)
    ax.set_xscale("log")
    ax.set_xlim(5, 4e4)
    ax.set_ylim(0, 5.6)
    ax.set_xlabel("artigos consultados até chegar (mediana, escala log)")
    ax.set_ylabel("cliques usados / ótimo (média)")
    eixo_br(ax, 1)
    ax.set_title("Quanto se perde vs. quanto se explora")
    salvar(fig, "tradeoff")


def main():
    estilo()
    for f in (fig_distancias, fig_graus, fig_hubs, fig_assimetria, fig_curva_sucesso,
              fig_tradeoff):
        try:
            f()
        except FileNotFoundError as e:
            print(f"  (pulando {f.__name__}: falta {Path(e.filename).name})")


if __name__ == "__main__":
    main()
