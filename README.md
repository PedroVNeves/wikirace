# Wikirace: busca exata contra inteligência artificial na Wikipédia

Trabalho da disciplina de **Matemática Discreta** (teoria dos grafos).

No Wikirace o jogador sai de um artigo da Wikipédia e tenta chegar em outro só
clicando em links. A ideia aqui é medir **quanto se perde, em número de cliques,
quando trocamos a busca exata (BFS) por agentes que escolhem links "por
intuição"** — parecido com o que um humano faz.

> **Pergunta central:** quão perto do caminho ótimo um agente heurístico chega,
> e quanto ele precisa explorar para isso?

A proposta completa está em [`docs/proposta.pdf`](docs/proposta.pdf) e o plano
de execução em [`PLANO.md`](PLANO.md).

## Modelagem

A Wikipédia em português é um grafo dirigido `G = (V, E)`: cada artigo é um
vértice e cada link de `u` para `v` é uma aresta `u → v`. A distância `d(u, v)`
é o menor número de cliques de `u` até `v` (∞ se não existe caminho). Como os
links têm sentido, em geral `d(u, v) ≠ d(v, u)`.

## Como rodar

```bash
pip install -r requirements.txt
pytest
```

*(em construção)*
