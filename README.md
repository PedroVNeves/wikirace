# Wikirace: busca exata contra inteligência artificial na Wikipédia

Trabalho da disciplina de **Matemática Discreta** (teoria dos grafos).

No Wikirace o jogador sai de um artigo da Wikipédia e tenta chegar em outro só
clicando em links. A ideia aqui é medir **quanto se perde, em número de cliques,
quando trocamos a busca exata (BFS) por agentes que escolhem links "por
intuição"** — parecido com o que um humano faz.

> **Pergunta central:** quão perto do caminho ótimo um agente heurístico chega,
> e quanto ele precisa explorar para isso?

* Proposta: [`docs/proposta.pdf`](docs/proposta.pdf)
* Relatório (provas e resultados): [`relatorio/relatorio.md`](relatorio/relatorio.md)
* Plano de execução: [`PLANO.md`](PLANO.md)

## Modelagem

A Wikipédia em português é um grafo dirigido `G = (V, E)`: cada artigo é um
vértice e cada link de `u` para `v` é uma aresta `u → v`. A distância `d(u, v)`
é o menor número de cliques de `u` até `v` (∞ se não existe caminho). Como os
links têm sentido, em geral `d(u, v) ≠ d(v, u)`.

Com o dump de 01/11/2026: **1.187.101 artigos e 80.389.152 links**
(redirecionamentos resolvidos, só artigos do domínio principal).

## Agentes

| Agente | Estratégia | Garantia |
|---|---|---|
| BFS bidirecional | camadas a partir da origem e do destino | ótimo |
| A\* semântico (`w`) | `g + w·h`, com `h = (1 − cos)/2` dos embeddings dos títulos | ≤ `w` × ótimo |
| Guloso semântico | clica no link de título mais parecido com o destino | nenhuma |
| Guloso por grau | clica no artigo com mais links (hubs) | nenhuma |
| Passeio aleatório | clica num link qualquer (linha de base) | nenhuma |

## Estrutura

```
wikirace/
  grafo.py        grafo dirigido em CSR (indptr/indices), graus, transposto
  busca.py        BFS com fila, BFS em níveis (numpy) e BFS bidirecional
  dumps.py        parser dos dumps SQL + resolução de redirecionamentos
  api.py          cliente da API do MediaWiki (links, afluentes, 1º link) com cache
  semantica.py    embeddings dos títulos (sentence-transformers)
  agentes.py      os agentes e o ambiente offline
  ao_vivo.py      ambiente que joga direto na Wikipédia pela API
  experimento.py  sorteio de pares, partidas e métricas
  analises.py     CFCs (Kosaraju), distâncias, hubs, assimetria, grafos funcionais
  jogo.py         estado da partida humana (demo)
scripts/          montar_grafo, calcular_embeddings, analisar_grafo,
                  rodar_experimento, primeiro_link, figuras, jogar
tests/            pytest (grafos pequenos, força bruta, dumps falsos, API falsa)
resultados/       números gerados (JSON/CSV)
relatorio/        relatório e figuras
```

## Como rodar

```bash
pip install -r requirements.txt
pytest                      # testes offline (rápidos)
pytest -m rede              # testes que usam a internet / o modelo de verdade

# os arquivos grandes (~2 GB) ficam fora do repositório:
export WIKIRACE_DATA=/caminho/para/dados     # padrão: ./data

python scripts/montar_grafo.py          # baixa os dumps (~900 MB) e monta o grafo (~3 min)
python scripts/calcular_embeddings.py   # embeddings dos 1,2 mi de títulos (~5 min na GPU)
python scripts/analisar_grafo.py        # CFCs, distâncias, hubs, assimetria
python scripts/rodar_experimento.py     # 100 pares x 8 agentes
python scripts/primeiro_link.py         # bônus: ciclo do primeiro link (usa a API)
python scripts/figuras.py               # figuras do relatório
```

## Demo: jogue contra os agentes

```bash
python scripts/jogar.py --jogador "seu nome"           # um dos 100 pares do experimento
python scripts/jogar.py --origem Pelé --destino "Mecânica quântica"
python scripts/jogar.py --ao-vivo                      # links direto da Wikipédia
```

Digite parte do nome de um link para filtrar, o número para clicar e `<` para
voltar. No fim aparecem o caminho ótimo e o que cada agente fez no mesmo par;
a partida vai para `resultados/humanos.csv` (é a referência humana do relatório).
