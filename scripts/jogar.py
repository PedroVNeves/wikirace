"""Demo: jogue Wikirace contra os agentes no terminal.

Uso:
    python scripts/jogar.py                         # par sorteado do experimento
    python scripts/jogar.py --origem Pelé --destino "Mecânica quântica"
    python scripts/jogar.py --jogador Ana --par 17
    python scripts/jogar.py --ao-vivo               # links direto da Wikipédia (API)

Comandos durante o jogo:
    <texto>   filtra os links do artigo atual
    <número>  clica no link com esse número na última lista
    <         volta para o artigo anterior (conta como clique)
    desisto   encerra a partida

No fim aparecem o caminho ótimo (BFS) e o que cada agente fez no mesmo par.
A partida é salva em resultados/humanos.csv.
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from wikirace import config, semantica  # noqa: E402
from wikirace.agentes import AEstrela, AmbienteGrafo, todos_os_agentes  # noqa: E402
from wikirace.busca import bfs_bidirecional_grafo  # noqa: E402
from wikirace.grafo import Grafo  # noqa: E402
from wikirace.jogo import PartidaHumana, salvar_registro  # noqa: E402

LIMITE_CLIQUES = 50


def bonito(titulo):
    return titulo.replace("_", " ")


def escolher_par(g, args):
    if args.origem and args.destino:
        return g.id_de(args.origem), g.id_de(args.destino)
    arq = config.RESULTADOS / "experimento" / "pares.csv"
    if arq.exists():
        pares = pd.read_csv(arq)
        i = args.par if args.par is not None else int(np.random.default_rng().integers(len(pares)))
        linha = pares.iloc[i]
        return int(linha.origem), int(linha.destino)
    rng = np.random.default_rng()
    while True:
        s, t = (int(x) for x in rng.integers(0, g.n, 2))
        if s != t and bfs_bidirecional_grafo(g, s, t).caminho is not None:
            return s, t


def jogar(partida, amb):
    ultima = []
    while not partida.terminou:
        if partida.cliques >= LIMITE_CLIQUES:
            print(f"\nLimite de {LIMITE_CLIQUES} cliques.")
            return
        links = partida.links()
        print(f"\n[{partida.cliques} cliques] Você está em: {bonito(amb.nome(partida.atual))}"
              f"  ({len(links)} links)   destino: {bonito(amb.nome(partida.destino))}")
        cmd = input("filtro / número / < / desisto > ").strip()
        if cmd == "desisto":
            return
        if cmd == "<":
            try:
                partida.voltar()
            except ValueError as e:
                print(e)
            continue
        if cmd.isdigit() and ultima:
            i = int(cmd)
            if 0 <= i < len(ultima):
                partida.clicar(ultima[i][1])
                ultima = []
            else:
                print("número fora da lista")
            continue
        ultima = partida.opcoes(cmd)
        if not ultima:
            print("nenhum link com esse texto")
        for i, (nome, _) in enumerate(ultima):
            print(f"  {i:2d}. {nome.replace('_', ' ')}")


def comparar(amb, g, s, t, registro):
    otimo = bfs_bidirecional_grafo(g, s, t)
    print("\n=========== resultado ===========")
    print("caminho ótimo:", " → ".join(bonito(g.titulo(v)) for v in otimo.caminho),
          f"({otimo.cliques} cliques)")
    linhas = [("você", registro["cliques"] if registro["sucesso"] else "-",
               registro["consultados"])]
    for ag in todos_os_agentes(pesos_a_estrela=(4,)):
        if isinstance(ag, AEstrela) or ag.nome == "bfs_bidirecional":
            continue
        p = ag.jogar(amb, s, t, max_cliques=LIMITE_CLIQUES, max_consultas=20_000)
        linhas.append((ag.nome, p.cliques if p.sucesso else "-", p.consultados))
    p = AEstrela(4).jogar(amb, s, t, max_consultas=20_000)
    linhas.append((p.agente, p.cliques if p.sucesso else "-", p.consultados))
    print(f"\n{'jogador':<20}{'cliques':>8}{'artigos lidos':>15}")
    for nome, c, q in linhas:
        print(f"{nome:<20}{str(c):>8}{q:>15}")
    return otimo.cliques


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--origem")
    ap.add_argument("--destino")
    ap.add_argument("--par", type=int)
    ap.add_argument("--jogador", default="anonimo")
    ap.add_argument("--ao-vivo", action="store_true")
    ap.add_argument("--saida", default=str(config.RESULTADOS / "humanos.csv"),
                    help="onde salvar a partida (CSV)")
    args = ap.parse_args()

    print("carregando o grafo...")
    g = Grafo.carregar(config.GRAFO_NPZ, config.TITULOS_TXT)
    emb = semantica.carregar_embeddings(config.EMBEDDINGS_NPY)
    amb = AmbienteGrafo(g, emb)
    s, t = escolher_par(g, args)
    print(f"\nWIKIRACE: de {bonito(g.titulo(s))} até {bonito(g.titulo(t))}")

    if args.ao_vivo:
        from wikirace.api import Cache, WikipediaAPI
        from wikirace.ao_vivo import AmbienteAPI
        amb_jogo = AmbienteAPI(WikipediaAPI(cache=Cache(config.DADOS / "cache_api.sqlite")))
        partida = PartidaHumana(amb_jogo, g.titulo(s), g.titulo(t), args.jogador)
    else:
        partida = PartidaHumana(amb, s, t, args.jogador)
    jogar(partida, partida.amb)

    registro = partida.registro()
    print("\nVocê chegou!" if partida.terminou else "\nNão foi dessa vez.")
    registro["otimo"] = comparar(amb, g, s, t, registro)
    registro["modo"] = "ao_vivo" if args.ao_vivo else "offline"
    salvar_registro(args.saida, registro)


if __name__ == "__main__":
    main()
