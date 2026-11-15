# Plano de trabalho

Trabalho de Matemática Discreta (grafos) — Wikirace na Wikipédia em português.
A proposta original está resumida no [README](README.md). Aqui fica o plano que eu
fui seguindo, dividido em partes pequenas. Cada parte só é marcada como feita
depois de ter teste passando e de eu revisar o código.

## Partes

- [ ] **0. Estrutura** — repositório, dependências, configuração de testes.
- [ ] **1. Grafo em CSR** — estrutura compacta (`indptr`/`indices`), graus de
      entrada e saída, grafo transposto. Teste do lema do aperto de mãos dirigido.
- [ ] **2. BFS e BFS bidirecional** — distâncias, reconstrução de caminho,
      BFS vetorizada em numpy para as análises. Testes contra força bruta.
- [ ] **3. Pipeline dos dumps** — download, parser dos `.sql.gz`
      (`page`, `linktarget`, `pagelinks`, `redirect`), resolução de
      redirecionamentos, grafo final salvo em `.npz`.
- [ ] **4. API da Wikipédia** — cliente para buscar links ao vivo, com cache.
- [ ] **5. Agentes** — passeio aleatório, guloso por grau, guloso semântico,
      A\* semântico (com peso `w`). Interface comum e orçamento de cliques.
- [ ] **6. Embeddings** — vetores dos títulos com um modelo multilíngue
      (sentence-transformers), salvos em disco.
- [ ] **7. Experimento principal** — 100 pares sorteados, todos os agentes,
      métricas (razão cliques/ótimo, artigos consultados, taxa de sucesso).
- [ ] **8. Análises do grafo** — componentes fortemente conexas, mundo pequeno
      vs. Erdős–Rényi, graus e hubs, assimetria, ciclo do primeiro link.
- [ ] **9. Demo** — a turma joga contra os agentes.
- [ ] **10. Relatório** — provas e resultados.
- [ ] **11. Revisão final.**

## Decisões

- Os dados pesados (dumps e grafo) ficam fora do repositório, na pasta
  definida por `WIKIRACE_DATA` (padrão: `./data`).
- Só artigos (namespace 0) entram no grafo. Redirecionamentos viram o artigo
  de destino.
