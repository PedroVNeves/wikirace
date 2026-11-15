"""Baixa os dumps da Wikipédia em português e monta o grafo de artigos.

Uso:
    python scripts/montar_grafo.py            # baixa (se precisar) e monta
    python scripts/montar_grafo.py --sem-baixar

Gera ``grafo.npz`` e ``titulos.txt`` em ``WIKIRACE_DATA`` (ou ./data) e um
resumo em ``resultados/grafo_resumo.json``.
"""

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from wikirace import config, dumps  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sem-baixar", action="store_true")
    args = ap.parse_args()

    if not args.sem_baixar:
        for tabela in config.TABELAS:
            dumps.baixar(tabela)

    inicio = time.time()
    g = dumps.construir_grafo(config.DUMPS, verbose=True)
    config.DADOS.mkdir(parents=True, exist_ok=True)
    g.salvar(config.GRAFO_NPZ, config.TITULOS_TXT)

    gs, ge = g.grau_saida(), g.grau_entrada()
    resumo = {
        "vertices": g.n,
        "arestas": g.m,
        "grau_medio": g.m / g.n,
        "grau_saida_max": int(gs.max()),
        "artigo_grau_saida_max": g.titulo(int(gs.argmax())),
        "grau_entrada_max": int(ge.max()),
        "artigo_grau_entrada_max": g.titulo(int(ge.argmax())),
        "sem_links_de_saida": int((gs == 0).sum()),
        "sem_links_de_entrada": int((ge == 0).sum()),
        "dump": "ptwiki-latest (" + time.strftime(
            "%Y-%m-%d", time.localtime(
                (config.DUMPS / "ptwiki-latest-pagelinks.sql.gz").stat().st_mtime)) + ")",
        "segundos": round(time.time() - inicio),
    }
    config.RESULTADOS.mkdir(exist_ok=True)
    (config.RESULTADOS / "grafo_resumo.json").write_text(
        json.dumps(resumo, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(resumo, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
