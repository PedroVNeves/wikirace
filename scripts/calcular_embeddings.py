"""Calcula os embeddings de todos os títulos do grafo (usa GPU se tiver).

Uso:
    python scripts/calcular_embeddings.py
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from wikirace import config, semantica  # noqa: E402


def main():
    titulos = config.TITULOS_TXT.read_text(encoding="utf-8").splitlines()
    print(f"{len(titulos):,} títulos")
    modelo = semantica.carregar_modelo()
    print("dispositivo:", modelo.device)
    inicio = time.time()
    e = semantica.calcular_embeddings(modelo, titulos, config.EMBEDDINGS_NPY, verbose=True)
    print(f"pronto: {e.shape} em {time.time() - inicio:.0f}s -> {config.EMBEDDINGS_NPY}")


if __name__ == "__main__":
    main()
