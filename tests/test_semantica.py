import numpy as np
import pytest

from wikirace import semantica


class ModeloFalso:
    """Imita o SentenceTransformer: vetor = contagem de letras (a..e) do texto."""

    def __init__(self):
        self.chamadas = 0

    def encode(self, textos, **kwargs):
        self.chamadas += 1
        return np.array([[t.lower().count(c) for c in "abcde"] for t in textos], dtype=float)


def test_texto_do_titulo():
    assert semantica.texto_do_titulo("Mecânica_quântica") == "Mecânica quântica"


def test_codificar_normaliza():
    e = semantica.codificar(ModeloFalso(), ["abc", "aab", "xyz"])
    np.testing.assert_allclose(np.linalg.norm(e[:2], axis=1), 1.0, rtol=1e-6)
    assert np.all(e[2] == 0)  # vetor nulo não vira NaN


def test_calcular_em_blocos_igual_de_uma_vez(tmp_path):
    titulos = ["abacate", "banana", "cebola", "dado", "eca", "aaa", "bcd"]
    m = ModeloFalso()
    e = semantica.calcular_embeddings(m, titulos, tmp_path / "e.npy", bloco=3)
    assert e.shape == (7, 5) and e.dtype == np.float16
    direto = semantica.codificar(ModeloFalso(), titulos)
    np.testing.assert_allclose(np.asarray(e, dtype=np.float32), direto, atol=1e-3)
    assert m.chamadas == 1 + 3  # 1 pra descobrir a dimensão + 3 blocos


def test_codificador_com_cache():
    m = ModeloFalso()
    cod = semantica.CodificadorComCache(m)
    a = cod(["abc", "bcd"])
    b = cod(["bcd", "abc", "abc"])
    assert m.chamadas == 1
    np.testing.assert_array_equal(a[0], b[1])


@pytest.mark.rede
def test_modelo_de_verdade_entende_portugues():
    m = semantica.carregar_modelo()
    e = semantica.codificar(m, ["Futebol", "Pelé", "Mecânica_quântica", "Física"])
    assert e[0] @ e[1] > e[0] @ e[2]   # futebol ~ Pelé
    assert e[2] @ e[3] > e[1] @ e[3]   # mecânica quântica ~ física
