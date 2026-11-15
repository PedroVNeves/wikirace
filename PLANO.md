# Plano de trabalho

Trabalho de Matemática Discreta (grafos) — Wikirace na Wikipédia em português.
A proposta original está resumida no [README](README.md). Aqui fica o plano que eu
fui seguindo, dividido em partes pequenas. Cada parte só é marcada como feita
depois de ter teste passando e de eu revisar o código.

## Partes

- [x] **0. Estrutura** — repositório, dependências, configuração de testes.
- [x] **1. Grafo em CSR** — estrutura compacta (`indptr`/`indices`), graus de
      entrada e saída, grafo transposto. Teste do lema do aperto de mãos dirigido.
- [x] **2. BFS e BFS bidirecional** — distâncias, reconstrução de caminho,
      BFS vetorizada em numpy para as análises. Testes contra força bruta.
- [x] **3. Pipeline dos dumps** — download, parser dos `.sql.gz`
      (`page`, `linktarget`, `pagelinks`, `redirect`), resolução de
      redirecionamentos, grafo final salvo em `.npz`.
- [x] **4. API da Wikipédia** — cliente para buscar links ao vivo, com cache.
- [x] **5. Agentes** — passeio aleatório, guloso por grau, guloso semântico,
      A\* semântico (com peso `w`). Interface comum e orçamento de cliques.
- [x] **6. Embeddings** — vetores dos títulos com um modelo multilíngue
      (sentence-transformers), salvos em disco.
- [x] **7. Experimento principal** — 100 pares sorteados, todos os agentes,
      métricas (razão cliques/ótimo, artigos consultados, taxa de sucesso).
- [ ] **8. Análises do grafo** — componentes fortemente conexas, mundo pequeno
      vs. Erdős–Rényi, graus e hubs, assimetria, ciclo do primeiro link.
- [x] **9. Demo** — a turma joga contra os agentes.
- [ ] **10. Relatório** — provas e resultados. (Em Markdown com LaTeX, que o
      GitHub renderiza; fica em `relatorio/relatorio.md`.)
- [ ] **11. Revisão final.**

## Decisões

- O grafo final (dump de 01/11/2026) tem 1.187.101 artigos e 80.389.152 links;
  montar tudo leva ~3 min e a BFS bidirecional responde em milissegundos.
- Heurística do A\*: `h(v) = (1 - cos(v, t)) / 2`. Como fica em [0, 1] e
  `d(v, t) >= 1` para `v != t`, ela é admissível. O peso `w` do A\* ponderado
  controla a troca entre otimalidade (garantia de no máximo `w` vezes o
  ótimo) e exploração. Rodo com `w = 1, 2, 4, 8`.
- Caminhantes (gulosos e aleatório) podem apertar "voltar" quando caem num
  beco; isso conta como clique.
- A parte 8 (análises) foi feita antes da 7, enquanto os embeddings
  calculavam.
- Limites do experimento: 50 cliques para os caminhantes e 20.000 consultas
  para os A\* (~9 s por partida no pior caso; o experimento todo levou 48 min).
- A API da Wikipédia devolve 429 se as requisições forem rápidas demais; o
  script do primeiro link espera 1 s entre requisições.
- A referência humana ainda não foi coletada: a demo grava as partidas da
  turma em `resultados/humanos.csv`.
- Os dados pesados (dumps e grafo) ficam fora do repositório, na pasta
  definida por `WIKIRACE_DATA` (padrão: `./data`).
- Só artigos (namespace 0) entram no grafo. Redirecionamentos viram o artigo
  de destino.
