"""Caminhos usados no projeto.

Os arquivos grandes (dumps ~900 MB, grafo, embeddings) não vão pro git.
Eles ficam em ``WIKIRACE_DATA`` se a variável existir, senão em ``./data``.
"""

import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DADOS = Path(os.environ.get("WIKIRACE_DATA", RAIZ / "data"))
DUMPS = DADOS / "raw"
RESULTADOS = RAIZ / "resultados"

DUMP_URL = "https://dumps.wikimedia.org/ptwiki/latest/ptwiki-latest-{tabela}.sql.gz"
TABELAS = ("page", "linktarget", "pagelinks", "redirect")

# arquivos gerados pelo pipeline
GRAFO_NPZ = DADOS / "grafo.npz"
TITULOS_TXT = DADOS / "titulos.txt"
EMBEDDINGS_NPY = DADOS / "embeddings.npy"

USER_AGENT = "wikirace-trabalho-md/0.1 (projeto academico; python-requests)"
