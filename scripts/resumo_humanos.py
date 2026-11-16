"""Resume as partidas da turma e compara com os agentes nos mesmos pares.

Lê ``resultados/humanos.csv`` (gravado pelo ``jogar.py``), junta com o
experimento e:

* imprime uma tabela pronta pra colar na seção 4.4 do relatório;
* salva ``resultados/humanos_resumo.json``.

Dá pra rodar no fim da apresentação, ao vivo, pra mostrar como a turma foi.

Uso:
    python scripts/resumo_humanos.py [--entrada resultados/humanos.csv]
"""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from wikirace import config  # noqa: E402
from wikirace.jogo import resumir_humanos  # noqa: E402

NOMES = {"bfs_bidirecional": "BFS bidirecional", "a_estrela_w1": "A* (w = 1)",
         "a_estrela_w2": "A* (w = 2)", "a_estrela_w4": "A* (w = 4)",
         "a_estrela_w8": "A* (w = 8)", "guloso_semantico": "guloso semântico",
         "guloso_grau": "guloso por grau", "aleatorio": "aleatório"}


def pct(x):
    return "-" if x is None else f"{100 * x:.0f}%".replace(".", ",")


def razao(x):
    return "-" if x is None else f"{x:.2f}×".replace(".", ",")


def lidos(x):
    return "-" if x is None else f"{x:,.0f}".replace(",", ".")


def linha(nome, r):
    return (f"| {nome} | {r['partidas']} | {pct(r['taxa_sucesso'])} | "
            f"{razao(r['razao_media'])} | {lidos(r['consultados_mediana'])} |")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--entrada", default=str(config.RESULTADOS / "humanos.csv"))
    args = ap.parse_args()

    entrada = Path(args.entrada)
    if not entrada.exists():
        sys.exit(f"Não achei {entrada}. Ninguém jogou ainda? (python scripts/jogar.py)")
    humanos = pd.read_csv(entrada)
    exp = config.RESULTADOS / "experimento"
    r = resumir_humanos(humanos, pd.read_csv(exp / "pares.csv"),
                        pd.read_csv(exp / "partidas.csv"))

    h = r["humanos"]
    print(f"\n{h['partidas']} partidas de {len(r['por_jogador'])} jogadores, "
          f"{pct(h['taxa_sucesso'])} chegaram, {h['segundos_medio']:.0f} s em média.\n")
    print("Razão = cliques / ótimo, só nas partidas que chegaram.\n")
    print("| jogador | partidas | chegaram | razão média | artigos lidos (mediana) |")
    print("|---|---:|---:|---:|---:|")
    print(linha("**turma (todas)**", h))
    if r["pares_do_experimento_jogados"]:
        print(linha("turma, nos pares do experimento", r["humanos_nos_pares_do_experimento"]))
        for ag, ra in sorted(r["agentes_nos_mesmos_pares"].items(),
                             key=lambda kv: -(kv[1]["taxa_sucesso"] or 0)):
            print(linha(NOMES.get(ag, ag), ra))
        print(f"\nPares do experimento jogados: {len(r['pares_do_experimento_jogados'])}"
              f" (os agentes acima são só nesses pares).")
    if r["partidas_fora_do_experimento"]:
        print(f"Partidas em pares escolhidos na hora (fora do experimento): "
              f"{r['partidas_fora_do_experimento']} (entram só na linha da turma).")

    print("\nPor jogador:")
    for j, rj in sorted(r["por_jogador"].items()):
        print(f"  {j}: {rj['partidas']} partidas, {pct(rj['taxa_sucesso'])} chegaram, "
              f"razão {razao(rj['razao_media'])}")

    destino = config.RESULTADOS / "humanos_resumo.json"
    destino.write_text(json.dumps(r, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
                       newline="\n")
    print(f"\nSalvo em {destino}")


if __name__ == "__main__":
    main()
