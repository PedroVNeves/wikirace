"""Demo da apresentação: mostra o grafo da Wikipédia funcionando, ao vivo.

É pra rodar na frente da turma. Cada parte espera um Enter antes de começar,
assim dá pra ir falando entre uma e outra (os slides seguem a mesma ordem).

Uso:
    python scripts/demo.py
    python scripts/demo.py --origem "Pelé" --destino "Mecânica quântica"
    python scripts/demo.py --sem-pausa          # roda tudo direto (pra testar antes)

Partes:
    1. o grafo: |V|, |E| e o lema do aperto de mãos conferido na hora
    2. um vértice: graus de entrada e saída, alguns vizinhos
    3. caminho mínimo com BFS bidirecional (e quanto tempo levou)
    4. ida e volta: d(u, v) vs d(v, u)
    5. mundo pequeno: BFS completa a partir da origem
    6. a Wikipédia é conexa? (artigo órfão e artigo ilhado)
    7. agentes contra a BFS no mesmo par (precisa dos embeddings)
    8. primeiro link: seguir sempre o primeiro link cai num ciclo
       (usa o cache_api.sqlite; sem ele, precisa de internet)
"""

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from wikirace import config  # noqa: E402
from wikirace.busca import bfs_bidirecional_grafo, bfs_niveis  # noqa: E402
from wikirace.grafo import Grafo  # noqa: E402

# exemplos que a gente já conferiu no dump de 01/11/2026
ORFAO = "Princípio de Premack"     # ninguém linka pra ele, mas ele linka pros outros
ILHADO = "Igoe"                    # nem entra nem sai link nenhum
ASSIMETRIA = ("Capivara", "Brasil")  # Capivara linka Brasil, mas Brasil não linka Capivara

PAUSA = True


def bonito(t):
    return t.replace("_", " ")


def num(x):
    return f"{x:,}".replace(",", ".")


def dec(x, casas=1):
    """Decimal com vírgula, do jeito brasileiro."""
    return f"{x:.{casas}f}".replace(".", ",")


def parte(titulo):
    if PAUSA:
        input(f"\n[Enter] → {titulo}")
    print("\n" + "=" * 70)
    print(titulo.upper())
    print("=" * 70)


def caminho_txt(g, r):
    return " → ".join(bonito(g.titulo(v)) for v in r.caminho)


def mostra_caminho(g, s, t):
    t0 = time.perf_counter()
    r = bfs_bidirecional_grafo(g, s, t)
    ms = (time.perf_counter() - t0) * 1000
    de, ate = bonito(g.titulo(s)), bonito(g.titulo(t))
    if r.caminho is None:
        print(f"  d({de}, {ate}) = ∞   (não existe caminho; {ms:.0f} ms)")
    else:
        lidos = f"{r.consultados} artigo" + ("s" if r.consultados != 1 else "")
        print(f"  d({de}, {ate}) = {r.cliques}   (leu {lidos}, {ms:.0f} ms)")
        print(f"     {caminho_txt(g, r)}")
    return r


def main():
    global PAUSA
    ap = argparse.ArgumentParser()
    ap.add_argument("--origem", default="Pelé")
    ap.add_argument("--destino", default="Mecânica quântica")
    ap.add_argument("--sem-pausa", action="store_true")
    args = ap.parse_args()
    PAUSA = not args.sem_pausa

    print("carregando o grafo...")
    t0 = time.time()
    g = Grafo.carregar(config.GRAFO_NPZ, config.TITULOS_TXT)
    g.transposto()  # monta já o grafo invertido (a BFS de trás usa ele)
    print(f"pronto em {time.time() - t0:.0f} s")
    s, t = g.id_de(args.origem), g.id_de(args.destino)
    gs, ge = g.grau_saida(), g.grau_entrada()

    # 1 ------------------------------------------------------------------
    parte("1. o grafo")
    print(f"  vértices (artigos):  |V| = {num(g.n)}")
    print(f"  arestas  (links):    |E| = {num(g.m)}")
    print(f"  grau médio |E|/|V| = {dec(g.m / g.n)}")
    print("\n  lema do aperto de mãos (versão dirigida):")
    print(f"    soma dos graus de saída   = {num(int(gs.sum()))}")
    print(f"    soma dos graus de entrada = {num(int(ge.sum()))}")
    print(f"    as duas iguais a |E|?       {int(gs.sum()) == int(ge.sum()) == g.m}")

    # 2 ------------------------------------------------------------------
    parte(f"2. um vértice: {bonito(g.titulo(s))}")
    print(f"  grau de saída  (links que saem de {bonito(g.titulo(s))}): {num(int(gs[s]))}")
    print(f"  grau de entrada (artigos que linkam {bonito(g.titulo(s))}): {num(int(ge[s]))}")
    viz = g.vizinhos(s)
    amostra = sorted(viz, key=lambda v: -ge[v])[:8]
    print("  alguns vizinhos de saída (os mais linkados):")
    for v in amostra:
        print(f"    → {bonito(g.titulo(int(v)))}  (grau de entrada {num(int(ge[v]))})")
    top = int(ge.argmax())
    print(f"\n  o maior hub do grafo: {bonito(g.titulo(top))}, com {num(int(ge[top]))} "
          "links chegando")

    # 3 ------------------------------------------------------------------
    parte("3. caminho mínimo (BFS bidirecional)")
    mostra_caminho(g, s, t)

    # 4 ------------------------------------------------------------------
    parte("4. ida e volta: o grafo é dirigido")
    a, b = (g.id_de(x) for x in ASSIMETRIA)
    mostra_caminho(g, a, b)
    mostra_caminho(g, b, a)
    print("\n  e o par do começo, na volta (às vezes dá igual):")
    mostra_caminho(g, s, t)
    mostra_caminho(g, t, s)
    print("\n  link tem sentido: ir de A pra B não é o mesmo que voltar de B pra A.")

    # 5 ------------------------------------------------------------------
    parte(f"5. mundo pequeno: quão longe fica tudo a partir de {bonito(g.titulo(s))}?")
    t0 = time.time()
    d = bfs_niveis(g, s)
    print(f"  (uma BFS no grafo inteiro: {dec(time.time() - t0)} s)")
    alcancados = d[d >= 0]
    valores, quantos = np.unique(alcancados, return_counts=True)
    acum = 0
    for k, c in zip(valores.tolist(), quantos.tolist()):
        acum += c
        if 1 <= k <= 8:
            nome = "clique " if k == 1 else "cliques"
            print(f"    a {k} {nome}: {num(c):>10}   (acumulado {dec(100 * acum / g.n):>5}%)")
    print(f"    ... o mais longe fica a {int(valores.max())} cliques")
    sem = g.n - len(alcancados)
    print(f"  sem caminho nenhum: {num(sem)} artigos ({dec(100 * sem / g.n)}%)")

    # 6 ------------------------------------------------------------------
    parte("6. a Wikipédia é conexa?")
    try:
        o, i = g.id_de(ORFAO), g.id_de(ILHADO)
    except KeyError as e:  # se alguém montar o grafo com outro dump
        print(f"  exemplo não está nesse dump ({e}); pulando")
    else:
        print(f"  {ORFAO}: grau de entrada {ge[o]}, grau de saída {gs[o]}  (órfão)")
        mostra_caminho(g, s, o)
        mostra_caminho(g, o, s)
        print(f"\n  {ILHADO}: grau de entrada {ge[i]}, grau de saída {gs[i]}  (ilhado)")
        mostra_caminho(g, s, i)
        mostra_caminho(g, i, s)
    print("\n  ou seja: NÃO é fortemente conexa (tem par sem caminho num sentido)")
    print("  e NÃO é nem fracamente conexa (tem artigo sem ligação nenhuma).")
    print("  os números completos estão em resultados/analises/conexidade.json")

    # 7 ------------------------------------------------------------------
    parte("7. agentes contra a BFS")
    if config.EMBEDDINGS_NPY.exists():
        mostra_agentes(g, s, t)
    else:
        print("  sem embeddings.npy, pulando (rode scripts/calcular_embeddings.py)")

    # 8 ------------------------------------------------------------------
    parte("8. primeiro link: sempre cai num ciclo")
    mostra_primeiro_link([bonito(g.titulo(s)), "Filosofia"])


def mostra_agentes(g, s, t):
    from wikirace import semantica
    from wikirace.agentes import AEstrela, AmbienteGrafo, BFSBidirecional, GulosoGrau, \
        GulosoSemantico, PasseioAleatorio
    amb = AmbienteGrafo(g, semantica.carregar_embeddings(config.EMBEDDINGS_NPY))
    print(f"  {bonito(g.titulo(s))} → {bonito(g.titulo(t))}\n")
    print(f"  {'agente':<20}{'cliques':>8}{'artigos lidos':>15}   caminho")
    for ag in (BFSBidirecional(), AEstrela(4), GulosoSemantico(), GulosoGrau(),
               PasseioAleatorio()):
        p = ag.jogar(amb, s, t, max_cliques=50, max_consultas=20_000)
        cam = " → ".join(bonito(g.titulo(int(v))) for v in p.caminho) if p.sucesso else ""
        if len(cam) > 70:
            cam = cam[:67] + "..."
        cliques = p.cliques if p.sucesso else "não chegou"
        print(f"  {p.agente:<20}{str(cliques):>8}{p.consultados:>15}   {cam}")


def mostra_primeiro_link(inicios):
    """Segue o primeiro link até repetir (casa dos pombos).

    Os links vêm do cache da API (``cache_api.sqlite`` na pasta de dados); o
    que não estiver lá é buscado na Wikipédia. Sem internet, mostra o
    resultado salvo do experimento.
    """
    from wikirace import analises
    from wikirace.api import Cache, WikipediaAPI
    api = WikipediaAPI(cache=Cache(config.DADOS / "cache_api.sqlite"), pausa=0.5)
    try:
        for t in inicios:
            cauda, ciclo = analises.segue_ate_ciclo(api.primeiro_link, t.replace(" ", "_"),
                                                    max_passos=100)
            print(f"\n  {t}:")
            print("    caminho: " + " → ".join(bonito(x) for x in cauda))
            if ciclo:
                print("    ciclo:   " + " → ".join(bonito(x) for x in ciclo)
                      + f" → (volta pra {bonito(ciclo[0])})")
            else:
                print("    parou: artigo sem link no texto")
    except Exception as e:  # sem internet e sem cache
        print(f"  não deu pra consultar a Wikipédia ({type(e).__name__}).")
    arq = config.RESULTADOS / "analises" / "primeiro_link.json"
    if arq.exists():
        r = json.loads(arq.read_text(encoding="utf-8"))
        print(f"\n  no experimento ({r['inicios']} artigos sorteados), os ciclos mais comuns:")
        for c in r["ciclos"][:4]:
            if c["ciclo"]:
                print(f"    {c['quantos_chegam']:3d} corridas  "
                      + " → ".join(bonito(x) for x in c["ciclo"]))


if __name__ == "__main__":
    main()
