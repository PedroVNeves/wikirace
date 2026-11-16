# Roteiro da apresentação

Isso aqui é pra quem vai apresentar. Dá pra apresentar só com este arquivo e
os slides, sem ter participado do código. Cada slide também tem nota do
apresentador com o que falar (no modo apresentação aparece pra você e não pra
turma).

* Slides: https://claude.ai/artifact/1nXV2LJTVmTAxgPtoQn3F8 (dá pra baixar em
  PowerPoint ou PDF pelo menu de compartilhar)
* Como instalar e rodar: [`COMO_RODAR.md`](COMO_RODAR.md)
* Os conceitos de grafos explicados com a Wikipédia: [`GRAFOS_NA_WIKIPEDIA.md`](GRAFOS_NA_WIKIPEDIA.md)
* Relatório com as provas: [`../relatorio/relatorio.md`](../relatorio/relatorio.md)

---

## Antes do dia

- [ ] Instalar tudo seguindo o `COMO_RODAR.md` (caminho curto, com a pasta de
      dados que eu te passo).
- [ ] Rodar `pytest` e ver passar.
- [ ] Rodar `python scripts/demo.py --sem-pausa` e ver chegar até o fim. Na
      primeira vez a parte 7 demora uns segundos a mais.
- [ ] Baixar os slides em PDF (se a internet da sala cair, você ainda tem eles).
- [ ] No dia, deixar o terminal **já aberto, com o `.venv` ativado e na pasta
      do projeto**, e com a fonte grande (Ctrl + roda do mouse). Ninguém
      enxerga terminal com fonte 12 no projetor.

## Tempo

Uns 20 minutos de slide + 5 de demo + perguntas. Se precisar cortar, os slides
que dá pra pular sem perder o fio são: **montagem** (6), **condensação** (10),
**asteroides** (12) e **tradeoff** (19).

## As seis perguntas (e a cola das respostas)

A apresentação começa com essas seis perguntas e termina respondendo cada uma.
Vale pedir pra turma chutar a 1 e a 2 no começo.

| # | pergunta | resposta curta |
|---|---|---|
| 1 | A Wikipédia é conexa? | **Não.** Nem fortemente (101.368 componentes fortes; a maior tem 90,9%) nem fracamente (304 componentes; 301 artigos sem link nenhum). |
| 2 | Quantos cliques separam dois artigos? | **4,25 em média**; 98,6% dos pares em até 6. Mundo pequeno. |
| 3 | A volta tem o mesmo tamanho que a ida? | **Só em 38% dos pares.** Por isso a distância é uma quase-métrica. |
| 4 | O que segura a rede junta? | **Os hubs, em conjunto.** Tirando 10 mil (0,84%), a média vai de 4,31 pra 5,32 e os pares sem caminho quase dobram. |
| 5 | A "intuição" joga tão bem quanto a busca exata? | **Não.** O guloso semântico termina 10% e usa 4,8× o ótimo; a BFS bidirecional resolve 100% lendo 20 artigos. |
| 6 | Clicando sempre no primeiro link, onde você para? | **Sempre cai num ciclo** (casa dos pombos). Em 150 artigos sorteados só apareceram 7 ciclos, e 88% caem em dois: Política/Ciência e Animalia/Corpo. Filosofia não é o fim, ela fica no caminho pro ciclo do Corpo. |

## Ordem dos slides

| # | slide | o que fica na cabeça da turma |
|---:|---|---|
| 1 | capa | |
| 2 | o jogo | Pelé → Inglaterra → Mecânica quântica, 2 cliques |
| 3 | seis perguntas | o roteiro da apresentação |
| 4 | modelagem | artigo = vértice, link = aresta dirigida |
| 5 | números | 1,2 milhão de vértices, 80 milhões de arestas, aperto de mãos |
| 6 | montagem | dos dumps até o CSR |
| 7 | forte × fraca | os dois sentidos de "conexo" |
| 8 | **não é conexa** | resposta da pergunta 1 |
| 9 | gravata-borboleta | quem fica de fora é destino difícil (órfão) |
| 10 | condensação | relação de equivalência e grafo das componentes acíclico |
| 11 | mundo pequeno | resposta da pergunta 2 |
| 12 | 207 cliques | a exceção (asteroides) |
| 13 | assimetria | resposta da pergunta 3 |
| 14 | hubs | quem são os hubs |
| 15 | tirando os hubs | resposta da pergunta 4 |
| 16 | os jogadores | BFS, A\*, gulosos, aleatório |
| 17 | BFS bidirecional | por que ela é barata |
| 18 | placar | resposta da pergunta 5 |
| 19 | tradeoff | perder cliques × explorar |
| 20 | onde a intuição se perde | Hallucigenia → Alucinação |
| 21 | primeiro link | a teoria: sempre cai num ciclo (casa dos pombos) |
| 22 | primeiro link na Wikipédia | resposta da pergunta 6: 88% em dois ciclos, Filosofia não é o fim |
| 23 | demo | ao vivo |
| 24 | respostas | as seis perguntas de novo |
| 25 | fim | perguntas |

## A demo

```powershell
python scripts/demo.py
```

A cada Enter aparece uma parte. O que comentar em cada uma:

1. **o grafo:** o lema do aperto de mãos batendo na hora, com 80 milhões de arestas.
2. **um vértice:** Pelé tem 731 links saindo e 1.562 chegando; os vizinhos mais
   linkados dele são hubs (Estados Unidos, Brasil).
3. **caminho mínimo:** sai em milissegundos.
4. **ida e volta:** Capivara → Brasil é 1, Brasil → Capivara é 2.
5. **mundo pequeno:** uma BFS no grafo inteiro em ~2 s. 81% dos artigos estão a
   no máximo 4 cliques de Pelé, e 9,1% não dá pra alcançar.
6. **conexa?:** o órfão (dá pra sair dele mas não chegar) e o ilhado (nem um nem outro).
7. **agentes:** a BFS lê 2 artigos; o A\* lê 293 pra achar o mesmo caminho; o
   guloso chega em 3 cliques passando por "Complexo de vira-lata"; o guloso por
   grau não chega.
8. **primeiro link:** Pelé vai clicando no primeiro link até cair no ciclo da
   Política, e a Filosofia cai no ciclo do Corpo. É a pergunta 6 ao vivo. Usa o
   `cache_api.sqlite` da pasta de dados; se ele não estiver lá e não tiver
   internet, a demo avisa e mostra o resultado salvo, não trava.

Depois, se der tempo, chama alguém pra jogar:

```powershell
python scripts/jogar.py --origem Pelé --destino "Mecânica quântica" --jogador "nome da pessoa"
```

Digita parte do nome do link pra filtrar (tipo `ingl`), o número pra clicar,
`<` pra voltar. No fim aparece o ótimo e o que cada agente fez. **A partida
fica salva em `resultados/humanos.csv`, guarda esse arquivo e me manda.**

Se mais de uma pessoa jogar, fecha com o placar da turma contra os agentes:

```powershell
python scripts/resumo_humanos.py
```

Fala só a linha da turma e a do guloso semântico: "a gente chegou em X%, o
guloso em Y%". É o fechamento perfeito pra pergunta 5.

### Se o computador da sala não rodar

Mostra esta saída (é exatamente o que a demo imprime com o dump que a gente usou):

```
1. O GRAFO
  vértices (artigos):  |V| = 1.187.101
  arestas  (links):    |E| = 80.389.152
  grau médio |E|/|V| = 67,7

  lema do aperto de mãos (versão dirigida):
    soma dos graus de saída   = 80.389.152
    soma dos graus de entrada = 80.389.152
    as duas iguais a |E|?       True

2. UM VÉRTICE: PELÉ
  grau de saída  (links que saem de Pelé): 731
  grau de entrada (artigos que linkam Pelé): 1.562
  alguns vizinhos de saída (os mais linkados):
    → Estados Unidos  (grau de entrada 185.206)
    → Brasil  (grau de entrada 176.369)
    → International Standard Book Number  (grau de entrada 132.770)
    → International Standard Serial Number  (grau de entrada 58.428)
    → Brasileiros  (grau de entrada 35.764)
    → Europa  (grau de entrada 34.753)
    → Rio de Janeiro  (grau de entrada 33.721)
    → Argentina  (grau de entrada 33.463)

  o maior hub do grafo: Estados Unidos, com 185.206 links chegando

3. CAMINHO MÍNIMO (BFS BIDIRECIONAL)
  d(Pelé, Mecânica quântica) = 2   (leu 2 artigos, 0 ms)
     Pelé → Inglaterra → Mecânica quântica

4. IDA E VOLTA: O GRAFO É DIRIGIDO
  d(Capivara, Brasil) = 1   (leu 1 artigo, 0 ms)
     Capivara → Brasil
  d(Brasil, Capivara) = 2   (leu 2 artigos, 0 ms)
     Brasil → Amazonas → Capivara

  e o par do começo, na volta (às vezes dá igual):
  d(Pelé, Mecânica quântica) = 2   (leu 2 artigos, 0 ms)
     Pelé → Inglaterra → Mecânica quântica
  d(Mecânica quântica, Pelé) = 2   (leu 2 artigos, 0 ms)
     Mecânica quântica → Século XX → Pelé

  link tem sentido: ir de A pra B não é o mesmo que voltar de B pra A.

5. MUNDO PEQUENO: QUÃO LONGE FICA TUDO A PARTIR DE PELÉ?
  (uma BFS no grafo inteiro: 2,1 s)
    a 1 clique :        731   (acumulado   0,1%)
    a 2 cliques:     65.922   (acumulado   5,6%)
    a 3 cliques:    489.843   (acumulado  46,9%)
    a 4 cliques:    406.146   (acumulado  81,1%)
    a 5 cliques:     89.283   (acumulado  88,6%)
    a 6 cliques:     19.324   (acumulado  90,2%)
    a 7 cliques:      4.242   (acumulado  90,6%)
    a 8 cliques:        541   (acumulado  90,6%)
    ... o mais longe fica a 207 cliques
  sem caminho nenhum: 107.880 artigos (9,1%)

6. A WIKIPÉDIA É CONEXA?
  Princípio de Premack: grau de entrada 0, grau de saída 1  (órfão)
  d(Pelé, Princípio de Premack) = ∞   (não existe caminho; 0 ms)
  d(Princípio de Premack, Pelé) = 3   (leu 3 artigos, 0 ms)
     Princípio de Premack → Psicologia → Brasil → Pelé

  Igoe: grau de entrada 0, grau de saída 0  (ilhado)
  d(Pelé, Igoe) = ∞   (não existe caminho; 0 ms)
  d(Igoe, Pelé) = ∞   (não existe caminho; 0 ms)

  ou seja: NÃO é fortemente conexa (tem par sem caminho num sentido)
  e NÃO é nem fracamente conexa (tem artigo sem ligação nenhuma).
  os números completos estão em resultados/analises/conexidade.json

7. AGENTES CONTRA A BFS
  Pelé → Mecânica quântica

  agente               cliques  artigos lidos   caminho
  bfs_bidirecional           2              2   Pelé → Inglaterra → Mecânica quântica
  a_estrela_w4               2            293   Pelé → Inglaterra → Mecânica quântica
  guloso_semantico           3              3   Pelé → Complexo de vira-lata → Prêmio Nobel de Física → Mecânica qu...
  guloso_grau         não chegou             50
  aleatorio                 44             44   Pelé → Drible de Pelé → Gol fantasma → Copa do Mundo FIFA de 2010 –...

======================================================================
8. PRIMEIRO LINK: SEMPRE CAI NUM CICLO
======================================================================

  Pelé:
    caminho: Pelé → Futebolista → Trabalhador → Trabalho (economia) → Fatores de produção → Economia
    ciclo:   Ciência → Rigor → Autocracia → Forma de governo → Ciência política → Política → Administração → Ciências sociais → (volta pra Ciência)

  Filosofia:
    caminho: Filosofia → Humano → Primatas → Mamíferos → Vertebrados
    ciclo:   Animalia → Organismo → Corpo → (volta pra Animalia)

  no experimento (150 artigos sorteados), os ciclos mais comuns:
     67 corridas  Administração → Ciências sociais → Ciência → Rigor → Autocracia → Forma de governo → Ciência política → Política
     65 corridas  Animalia → Organismo → Corpo
      7 corridas  Aptidão física → Exercício físico
      5 corridas  Direito → Norma jurídica
```

## Perguntas que podem aparecer

**"Por que dirigido? Não dava pra fazer com grafo normal?"**
Porque link tem sentido. Capivara linka Brasil e Brasil não linka Capivara. Se
tratasse como não dirigido, ia achar caminhos que não dá pra clicar de verdade.
A versão não dirigida aparece só na conexidade fraca.

**"Como vocês sabem que a BFS tá certa?"**
Duas coisas. Tem prova (apêndice A.1 e A.2 do relatório: correção da BFS e da
BFS bidirecional). E tem teste: o código é comparado com Floyd–Warshall e com
força bruta em centenas de grafos aleatórios pequenos. São 125 testes.

**"E as componentes, como calcularam?"**
Componentes fortes com o algoritmo de Kosaraju (duas buscas em profundidade,
uma no grafo e outra no transposto). Fracas com uma BFS que anda pelos links
nos dois sentidos. Os dois deram exatamente a mesma resposta que a biblioteca
scipy.

**"Esses 301 artigos isolados são erro de vocês?"**
Não: são artigos que, no arquivo de 01/11/2026, não linkam nenhum outro artigo
e não são linkados por ninguém. Geralmente esboço muito curto ou artigo novo.
Como a Wikipédia muda todo dia, alguns já podem ter ganhado link hoje.

**"Isso é o 'seis graus de separação'?"**
É a mesma ideia (mundo pequeno). Aqui é ainda menor: média 4,25, e 98,6% dos
pares em até 6.

**"Por que tem artigo a 207 cliques, se a média é 4?"**
Cadeia de asteroides numerados: cada artigo só linka o próximo da série, então
não tem atalho. É a cauda longa.

**"O que é esse modelo de linguagem dos agentes?"**
Um modelo pequeno (`paraphrase-multilingual-MiniLM-L12-v2`) que transforma cada
título num vetor de 384 números. Títulos parecidos viram vetores parecidos, e a
"intuição" é o cosseno entre o vetor do link e o vetor do destino. Só o título
entra, porque é o que o jogador vê antes de clicar.

**"Por que o A\* com w = 1 resolveu só 15%?"**
Com w = 1 a heurística é fraca demais (nunca passa de 1), então ele vira quase
uma BFS de um lado só. Pra distância 4 isso é ler uns 200 mil artigos, e o
limite era 20 mil. Quando aumenta o w ele confia mais na intuição, lê menos, e
a garantia vira "no máximo w vezes o ótimo". Em todas as partidas que ele
terminou, essa garantia valeu.

**"Por que não usar o texto do artigo em vez do título?"**
Provavelmente ajudaria os agentes. A gente usou só o título pra ser justo com
um humano, que vê só o nome do link antes de clicar. Tá nas limitações do
relatório.

**"Se eu rodar hoje dá o mesmo resultado?"**
Quase. O script baixa a Wikipédia mais recente, então os números mudam um
pouco. Os resultados do trabalho são todos do dump de 01/11/2026 e estão
salvos em `resultados/`.

**"Quanto tempo leva pra rodar tudo?"**
Montar o grafo: uns 3 minutos depois de baixar. Uma BFS no grafo inteiro: ~2
segundos. O caminho mínimo entre dois artigos: milissegundos. O experimento
com 100 pares e 8 agentes: 48 minutos.

**"Mas na Wikipédia tudo não leva pra Filosofia?"**
Na em inglês, sim (é famoso). Na em português, não: Filosofia → Humano →
Primatas → Mamíferos → Vertebrados → Animalia, e aí fica girando em Animalia →
Organismo → Corpo. A Filosofia tá no caminho de 34% das corridas, mas no ciclo
mesmo, não. O outro ciclo grande é o da Política (Política → Administração →
Ciências sociais → Ciência → Rigor → …). Pelé cai nesse.

**"E os 3 artigos que não caíram em ciclo nenhum?"**
São artigos que são só uma tabela (quadro de medalhas, resultado de eleição),
sem nenhum link no texto. Aí o primeiro link não existe, f não tá definida
nesse artigo, e o teorema não se aplica. Não é contraexemplo, é fora da
hipótese.
