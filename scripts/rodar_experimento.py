"""Experimento principal: 100 pares sorteados, todos os agentes, BFS de gabarito.

Uso:
    python scripts/rodar_experimento.py [--pares 100] [--semente 2026]

Salva em resultados/experimento/:
    pares.csv      os pares sorteados e o caminho ótimo de cada um
    partidas.csv   uma linha por (par, agente)
    resumo.csv     tabela por agente
    curva.csv      taxa de sucesso por limite de cliques
    info.json      parâmetros e pares descartados (sem caminho)
"""

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from wikirace import config, experimento, semantica  # noqa: E402
from wikirace.agentes import AmbienteGrafo, todos_os_agentes  # noqa: E402
from wikirace.grafo import Grafo  # noqa: E402

SAIDA = config.RESULTADOS / "experimento"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pares", type=int, default=100)
    ap.add_argument("--semente", type=int, default=2026)
    ap.add_argument("--max-cliques", type=int, default=50)
    ap.add_argument("--max-consultas", type=int, default=20_000)
    args = ap.parse_args()

    g = Grafo.carregar(config.GRAFO_NPZ, config.TITULOS_TXT)
    emb = semantica.carregar_embeddings(config.EMBEDDINGS_NPY)
    amb = AmbienteGrafo(g, emb)
    SAIDA.mkdir(parents=True, exist_ok=True)

    print("sorteando pares...", flush=True)
    pares, descartados = experimento.sortear_pares(g, args.pares, args.semente)
    pares.to_csv(SAIDA / "pares.csv", index=False)
    print(f"  {len(pares)} pares, {descartados} descartados sem caminho", flush=True)

    agentes = todos_os_agentes(pesos_a_estrela=(1, 2, 4, 8))
    inicio = time.time()
    partidas = experimento.rodar(amb, pares, agentes, args.max_cliques,
                                 args.max_consultas, args.semente, verbose=True)
    partidas.to_csv(SAIDA / "partidas.csv", index=False)

    tab = experimento.resumo(partidas)
    tab.to_csv(SAIDA / "resumo.csv")
    experimento.curva_sucesso(partidas, range(1, args.max_cliques + 1)).to_csv(
        SAIDA / "curva.csv", index=False)
    (SAIDA / "info.json").write_text(json.dumps({
        "pares": len(pares), "semente": args.semente,
        "descartados_sem_caminho": descartados,
        "fracao_sem_caminho_estimada": descartados / (descartados + len(pares)),
        "max_cliques": args.max_cliques, "max_consultas": args.max_consultas,
        "agentes": [a.nome for a in agentes],
        "modelo_embeddings": semantica.MODELO_PADRAO,
        "segundos": round(time.time() - inicio),
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(tab.round(3).to_string())


if __name__ == "__main__":
    main()
