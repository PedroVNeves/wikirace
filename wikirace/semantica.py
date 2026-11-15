"""Similaridade de texto entre artigos, com embeddings dos títulos.

Uso um modelo multilíngue do sentence-transformers que entende português
(``paraphrase-multilingual-MiniLM-L12-v2``, vetores de 384 dimensões). Só o
título entra no modelo: é a informação que o jogador vê no link antes de
clicar, então é uma comparação justa com um humano.

Os vetores são normalizados (norma 1), então similaridade de cosseno vira
produto escalar. Guardo em float16 num arquivo .npy e abro com memmap, pra
não ocupar ~1 GB de RAM à toa.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

MODELO_PADRAO = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def texto_do_titulo(titulo):
    return titulo.replace("_", " ")


def carregar_modelo(nome=MODELO_PADRAO, dispositivo=None):
    from sentence_transformers import SentenceTransformer  # import pesado (torch)
    return SentenceTransformer(nome, device=dispositivo)


def codificar(modelo, titulos, lote=512):
    """Embeddings normalizados (float32) de uma lista de títulos."""
    textos = [texto_do_titulo(t) for t in titulos]
    e = np.asarray(modelo.encode(textos, batch_size=lote, show_progress_bar=False,
                                 convert_to_numpy=True), dtype=np.float32)
    normas = np.linalg.norm(e, axis=1, keepdims=True)
    normas[normas == 0] = 1.0
    return e / normas


def calcular_embeddings(modelo, titulos, caminho, bloco=50_000, lote=512, verbose=False):
    """Calcula e salva os embeddings de todos os títulos, bloco por bloco."""
    n = len(titulos)
    dim = codificar(modelo, titulos[:1]).shape[1]
    saida = np.lib.format.open_memmap(caminho, mode="w+", dtype=np.float16, shape=(n, dim))
    for i in range(0, n, bloco):
        saida[i:i + bloco] = codificar(modelo, titulos[i:i + bloco], lote).astype(np.float16)
        if verbose:
            print(f"  {min(i + bloco, n):,}/{n:,}", flush=True)
    saida.flush()
    del saida
    return carregar_embeddings(caminho)


def carregar_embeddings(caminho):
    return np.load(Path(caminho), mmap_mode="r")


class CodificadorComCache:
    """Para jogar ao vivo: calcula o embedding de um título só na primeira vez."""

    def __init__(self, modelo):
        self.modelo = modelo
        self.cache = {}

    def __call__(self, titulos):
        faltando = [t for t in dict.fromkeys(titulos) if t not in self.cache]
        if faltando:
            for t, e in zip(faltando, codificar(self.modelo, faltando)):
                self.cache[t] = e
        return np.stack([self.cache[t] for t in titulos]) if titulos else np.zeros((0, 1))
