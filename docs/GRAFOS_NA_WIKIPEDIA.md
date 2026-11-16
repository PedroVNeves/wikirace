# A Wikipédia como grafo: cada conceito da matéria, com o exemplo real

A ideia desse arquivo é simples: pegar os conceitos de grafos que a gente viu
em Matemática Discreta e mostrar onde cada um aparece na Wikipédia de verdade,
com número tirado dos dados. Tudo aqui é do dump da Wikipédia em português de
01/11/2026 e sai dos scripts do projeto (o arquivo de onde veio cada número tá
indicado).

Se você só tem cinco minutos, lê a seção 5 (conexidade), que é a pergunta que
mais aparece.

---

## 1. Vértice, aresta, grafo dirigido

Um **grafo** é um par `G = (V, E)`: um conjunto de vértices e um conjunto de
arestas ligando esses vértices.

Na Wikipédia:

* **vértice = artigo.** Pelé, Capivara, Mecânica quântica, cada um é um vértice.
* **aresta = link.** Se o texto do artigo `u` tem um link pro artigo `v`, tem
  uma aresta `u → v`.

E aqui já aparece a primeira coisa importante: link **tem sentido**. O artigo
Capivara linka Brasil, mas o artigo Brasil não linka Capivara. Então a aresta é
uma seta, não um tracinho. Isso é um **grafo dirigido** (ou digrafo).

| | |
|---|---|
| vértices `\|V\|` | 1.187.101 artigos |
| arestas `\|E\|` | 80.389.152 links |

Algumas decisões que a gente tomou pra o grafo ficar "limpo" (é o que se
chama de **grafo simples**):

* **sem laços:** um artigo que linka ele mesmo não conta (`u → u` não ajuda
  ninguém a chegar em lugar nenhum);
* **sem arestas repetidas:** se Pelé linka Brasil dez vezes no texto, é uma
  aresta só;
* **redirecionamentos não são vértices:** "Edson Arantes do Nascimento" é só um
  redirecionamento pra "Pelé", então um link pra ele vira link pra Pelé.

(fonte: `resultados/grafo_resumo.json`)

## 2. Grau de entrada e grau de saída

Num grafo dirigido cada vértice tem dois graus:

* **grau de saída** `deg⁺(v)`: quantos links saem do artigo;
* **grau de entrada** `deg⁻(v)`: quantos artigos linkam pra ele.

Exemplo, Pelé: grau de saída 731, grau de entrada 1.562.

O **lema do aperto de mãos** da versão não dirigida (`soma dos graus = 2|E|`)
vira, no dirigido:

```
soma dos graus de saída = soma dos graus de entrada = |E|
```

porque cada link sai de exatamente um artigo e chega em exatamente um. Na
Wikipédia: as duas somas dão 80.389.152, igual a `|E|`. A demo confere isso
ao vivo (`python scripts/demo.py`, parte 1).

Casos especiais:

| | quantos | exemplo |
|---|---:|---|
| grau de entrada 0 (ninguém linka: **órfão**) | 91.644 | Princípio de Premack |
| grau de saída 0 (não linka ninguém: **sumidouro**) | 611 | Julius Obsequens |
| grau 0 dos dois lados (**vértice isolado**) | 301 | Igoe, Hino de Brasilia |

**Grau médio** `|E| / |V|` = 67,7 links por artigo. Mas a mediana do grau de
entrada é só 10: a maioria dos artigos é pouco linkada e uns poucos são
linkados por todo mundo (os hubs, seção 8).

(fonte: `resultados/analises/hubs.json`, `resultados/analises/conexidade.json`)

## 3. Passeio, caminho e distância

* **passeio:** sequência de vértices onde cada um tem aresta pro próximo. É
  exatamente uma partida de Wikirace: cada clique é uma aresta.
* **caminho:** passeio sem repetir vértice.
* **distância** `d(u, v)`: o menor número de arestas de um caminho de `u` até
  `v`. Se não existe caminho, `d(u, v) = ∞`.

No Wikirace, `d(u, v)` é o **menor número de cliques possível**. Exemplo:

```
Pelé → Inglaterra → Mecânica quântica          d = 2
```

## 4. Distância num grafo dirigido não é simétrica

Num grafo não dirigido `d(u, v) = d(v, u)` sempre. Num dirigido, não:

```
Capivara → Brasil                       d(Capivara, Brasil) = 1
Brasil → Amazonas → Capivara            d(Brasil, Capivara) = 2
```

Medindo em 47 milhões de pares:

| | |
|---:|---|
| 37,8% | ida e volta do mesmo tamanho |
| 48,9% | tem caminho nos dois sentidos, mas de tamanhos diferentes |
| 13,2% | só tem caminho num sentido (do outro lado é ∞) |

Então `d` não é uma métrica: falta a simetria. Ela é uma **quase-métrica**:

1. `d(u, v) ≥ 0` e `d(u, v) = 0` só quando `u = v`;
2. vale a **desigualdade triangular** `d(u, x) ≤ d(u, v) + d(v, x)` (se dá pra
   ir de `u` a `v` e de `v` a `x`, juntando os dois dá um jeito de ir de `u`
   a `x`);
3. mas a simetria falha.

(fonte: `resultados/analises/assimetria.json`, prova no Apêndice A.4 do relatório)

## 5. Conexidade: a Wikipédia é conexa?

**Resposta curta: não. Nem no sentido forte, nem no fraco.**

Num grafo dirigido "conexo" tem dois significados:

* **fortemente conexo:** de qualquer vértice dá pra chegar em qualquer outro
  seguindo as setas. No Wikirace: qualquer partida tem solução.
* **fracamente conexo:** se você esquecer o sentido das setas (tratar link
  como via de mão dupla), o grafo fica numa peça só.

Forte implica fraco. O contrário não: `a → b → c` é fracamente conexo mas não
dá pra voltar de `c` pra `a`.

### Fortemente conexa? Não.

Basta um exemplo: o artigo "Princípio de Premack" tem grau de entrada 0 (é
órfão). Então:

```
d(Princípio de Premack, Pelé) = 3     (Princípio de Premack → Psicologia → Brasil → Pelé)
d(Pelé, Princípio de Premack) = ∞     (ninguém linka pra ele, não tem como chegar)
```

Os vértices se dividem em **componentes fortemente conexas** (CFCs): grupos
onde todo mundo alcança todo mundo. "Alcançar e ser alcançado" é uma
**relação de equivalência** (reflexiva, simétrica e transitiva), e as CFCs são
as classes de equivalência dela.

| | |
|---|---:|
| número de CFCs | 101.368 |
| tamanho da maior | 1.078.919 artigos (90,9%) |
| tamanho da segunda maior | 167 |
| CFCs de um artigo só | 98.893 |

Ou seja: tem uma componente gigante com 91% dos artigos e um monte de
artigos soltos em volta dela. Dentro da gigante, qualquer partida tem solução.

**Gravata-borboleta.** Olhando quem fica fora da gigante:

| parte | artigos | o que é |
|---|---:|---|
| CFC gigante | 1.078.919 | ida e volta pra qualquer um dela |
| IN | 107.564 | consegue chegar na gigante, mas ninguém da gigante chega neles (os órfãos tão aqui) |
| OUT | 302 | a gigante chega neles, mas eles não voltam |
| resto | 316 | nem uma coisa nem outra |

Quase tudo que tá fora é IN: o problema quase sempre é o **destino** ser
difícil de alcançar, não a origem. Por isso 9,1% dos pares `(u, v)` não têm
caminho.

### Fracamente conexa? Também não.

Mesmo esquecendo o sentido dos links, o grafo se quebra em **304 componentes
fracas**:

| | |
|---|---:|
| maior componente fraca | 1.186.796 artigos (99,97%) |
| artigos fora dela | 305 |
| artigos **isolados** (nenhum link entrando nem saindo) | 301 |
| componentes de 2 artigos | 2 (ex.: Família Grando, Mahjong Quest) |

Os 301 isolados (Igoe, Hino de Brasilia, Bagre-mandim, Rima leonina...) são
artigos que, no dump, não linkam nenhum outro artigo e não são linkados por
ninguém. São ilhas: `d(Igoe, qualquer um) = d(qualquer um, Igoe) = ∞`.

### O grafo das componentes é acíclico

Se você "espreme" cada CFC num vértice só, sobra um grafo com 101.368 vértices
e 109.339 arestas que **não tem ciclo nenhum** (é um DAG). Isso não é
coincidência, é teorema: se tivesse um ciclo entre duas componentes, dava pra
ir e voltar entre elas, então elas seriam a mesma componente. A gente conferiu
nos dados com o algoritmo de Kahn.

(fonte: `resultados/analises/scc.json`, `resultados/analises/conexidade.json`;
código em `wikirace/analises.py`: `componentes_fortes` é o algoritmo de
Kosaraju, `componentes_fracas` é uma BFS que anda pros dois lados; os dois
foram conferidos contra o `scipy`)

## 6. Busca em largura (BFS)

A **BFS** acha `d(s, v)` pra todo `v`: começa em `s`, visita todos os vizinhos
(distância 1), depois os vizinhos dos vizinhos (distância 2), e assim por
diante. Roda em tempo `O(|V| + |E|)`. No grafo inteiro, uma BFS leva uns 2
segundos.

A **BFS bidirecional** faz uma busca a partir da origem (seguindo os links) e
outra a partir do destino (andando nos links ao contrário, no **grafo
transposto** `Gᵀ`, que é o mesmo grafo com todas as setas invertidas). Quando
as duas se encontram, achou o caminho mínimo. Como cada lado só precisa andar
metade da distância, ela lê uns 20 artigos em vez de milhares.

As provas de que as duas funcionam tão no Apêndice A do relatório.

## 7. Mundo pequeno

Pegando 60 artigos aleatórios e rodando BFS a partir de cada um (71 milhões de
pares):

| | Wikipédia | grafo aleatório (Erdős–Rényi) com mesmo `\|V\|` e `\|E\|` |
|---|---:|---:|
| distância média | 4,25 | 3,76 |
| 90% dos pares em até | 5 cliques | 4 cliques |
| maior distância vista | 208 | 5 |

98,6% dos pares (com caminho) estão a no máximo 6 cliques. É o "seis graus de
separação" da Wikipédia.

Dá pra ter uma ideia disso com o **limite de Moore**: se cada artigo tem uns
100 links, em `k` cliques você alcança no máximo `100^k` artigos. Pra chegar em
1,2 milhão precisa de `k ≈ log₁₀₀(1,2 milhão) ≈ 3`. A conta é otimista (supõe
que nunca repete artigo), mas acerta a ordem de grandeza.

E os 208 cliques? É uma cadeia de asteroides numerados em que cada artigo só
linka o próximo da série. O artigo mais longe de Pelé tá a 207 cliques.

(fonte: `resultados/analises/distancias.json`)

## 8. Hubs

**Hubs** são vértices com grau muito alto. Os maiores graus de entrada:

| artigo | links chegando |
|---|---:|
| Estados Unidos | 185.206 |
| Brasil | 176.369 |
| Densidade populacional | 141.746 |
| International Standard Book Number | 132.770 |

A distribuição dos graus de entrada tem **cauda pesada**: na escala log-log
fica quase uma reta.

O que acontece se a gente tira os hubs (remove os vértices e as arestas deles)?

| hubs removidos | distância média | pares sem caminho |
|---:|---:|---:|
| 0 | 4,31 | 9,1% |
| 100 | 4,44 | 9,1% |
| 10.000 (0,84% dos artigos) | 5,32 | 16,9% |

Nenhum hub sozinho é essencial, mas o conjunto deles é o que segura o mundo
pequeno.

(fonte: `resultados/analises/hubs.json`)

## 9. Grafo funcional: o primeiro link

Se em todo artigo você clicar sempre no **primeiro link** do texto, cada
artigo aponta pra exatamente um outro. Isso é uma **função** `f : V → V`, e o
grafo dela (cada vértice com grau de saída 1) se chama **grafo funcional**.

Teorema: partindo de qualquer artigo, a sequência `v, f(v), f(f(v)), ...`
**sempre** cai num ciclo. Prova pela **casa dos pombos**: o conjunto de
artigos é finito, então em algum momento a sequência repete um artigo, e
dali pra frente ela fica rodando em volta. E mais: cada componente do grafo
funcional tem **exatamente um** ciclo (uma componente com `c` vértices tem `c`
arestas; uma árvore com `c` vértices tem `c − 1`; a aresta que sobra fecha
exatamente um ciclo).

Na Wikipédia em português (150 artigos sorteados, `scripts/primeiro_link.py`):

* 147 caíram num ciclo; os outros 3 são artigos que são só tabela e não têm
  link no texto (aí `f` nem tá definida, é a exceção do teorema);
* só apareceram **7 ciclos**, e quase tudo cai em dois deles:
  * **Política** → Administração → Ciências sociais → Ciência → Rigor →
    Autocracia → Forma de governo → Ciência política → Política (67 corridas);
  * **Animalia** → Organismo → Corpo → Animalia (65 corridas);
* exemplos: Pelé → Futebolista → Trabalhador → … → Economia → Ciência (cai no
  da política); Capivara → Mamíferos → Vertebrados → Animalia (cai no do corpo);
* na Wikipédia em inglês é famoso que "tudo leva à Filosofia". Aqui não:
  Filosofia → Humano → Primatas → Mamíferos → Vertebrados → Animalia, ou seja,
  ela tá na **cauda**, não no ciclo;
* leva em média 10,6 cliques pra entrar no ciclo (no máximo 23);
* e o teorema confere: no pedaço do grafo que as corridas descobriram, as 7
  componentes têm exatamente um ciclo cada.

(fonte: `resultados/analises/primeiro_link.json`)

## 10. Heurística e A\*

O **A\*** é uma busca que, em vez de expandir por camadas como a BFS, vai
primeiro pelos vértices que "parecem" mais perto do destino. Esse "parecer" é
a **heurística** `h(v)`. Aqui ela vem de um modelo de linguagem que compara o
título do artigo com o título do destino.

Se a heurística nunca superestima a distância real (`h(v) ≤ d(v, t)`, ela é
**admissível**), o A\* acha o caminho mínimo. Se multiplica ela por `w`, ele
fica mais rápido mas só garante um caminho até `w` vezes o mínimo. Prova no
Apêndice A.3 do relatório, e o experimento confirmou: todas as partidas que o
A\* terminou respeitaram esse limite.

---

## Resumo numa tabela

| conceito | na Wikipédia |
|---|---|
| vértice | artigo |
| aresta dirigida `u → v` | link de `u` pra `v` |
| grafo simples | sem link pra si mesmo, sem link repetido |
| grau de saída / entrada | links que saem / artigos que linkam |
| aperto de mãos | soma dos graus de saída = soma dos de entrada = 80.389.152 |
| vértice isolado | 301 artigos sem link nenhum |
| passeio | uma partida de Wikirace |
| distância `d(u, v)` | menor número de cliques |
| quase-métrica | `d(Capivara, Brasil) = 1`, `d(Brasil, Capivara) = 2` |
| fortemente conexo? | não: 101.368 CFCs, a maior com 90,9% |
| fracamente conexo? | não: 304 componentes, a maior com 99,97% |
| condensação (DAG) | o grafo das CFCs não tem ciclo |
| grafo transposto | os links ao contrário (usado na BFS bidirecional) |
| BFS | acha o menor número de cliques em ~2 s pro grafo todo |
| mundo pequeno | distância média 4,25 |
| hubs | Estados Unidos, Brasil, ... |
| grafo funcional | "clicar sempre no primeiro link" |
| casa dos pombos | por que o primeiro link sempre cai num ciclo |
