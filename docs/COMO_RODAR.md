# Como rodar o projeto (passo a passo)

Isso aqui é pra quem nunca mexeu no projeto e precisa deixar tudo funcionando,
de preferência sem me ligar. Tá escrito pensando em Windows, que é o que a
maioria usa, mas tem os comandos de Linux/Mac do lado quando muda alguma coisa.

Tem dois caminhos:

* **Caminho curto (recomendado pra apresentação):** pega a pasta de dados
  pronta comigo (pendrive ou Drive) e só instala o Python. Uns 15 minutos.
* **Caminho longo:** baixa os dumps da Wikipédia e monta tudo do zero. Uma
  hora, mais ou menos, e precisa de internet boa.

Os dois começam igual.

---

## 1. O que precisa ter no computador

| coisa | versão | pra quê |
|---|---|---|
| Python | 3.10 ou mais novo (eu usei o 3.12) | tudo |
| Git | qualquer | baixar o repositório |
| RAM | 4 GB livres pra demo, 16 GB pra montar o grafo do zero | o grafo ocupa uns 3 GB carregado |
| Disco | 1,3 GB (caminho curto) ou 3 GB (caminho longo) | dados |

Pra saber se já tem Python, abre o PowerShell e digita:

```powershell
python --version
```

Se aparecer `Python 3.10` ou maior, beleza. Se não aparecer nada ou abrir a
Microsoft Store, instala pelo site https://www.python.org/downloads/ e **marca
a caixinha "Add python.exe to PATH"** na primeira tela do instalador. Esquecer
isso é o erro mais comum. Depois fecha e abre o PowerShell de novo.

Git: https://git-scm.com/download/win (só ir dando "Next").

## 2. Baixar o projeto

```powershell
cd $HOME\Desktop
git clone https://github.com/PedroVNeves/wikirace.git
cd wikirace
```

(Sem Git dá pra baixar o ZIP pelo GitHub, botão verde "Code" → "Download ZIP",
e descompactar.)

## 3. Criar o ambiente virtual e instalar as bibliotecas

O ambiente virtual (`.venv`) é uma pasta com um Python só do projeto, pra não
bagunçar o Python do computador.

**Windows (PowerShell):**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Se o PowerShell reclamar de "execução de scripts desabilitada", roda isso uma
vez e tenta ativar de novo:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

**Linux / Mac:**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Quando o ambiente tá ativo aparece `(.venv)` no começo da linha. **Toda vez que
abrir um terminal novo, tem que ativar de novo** (só a linha do `Activate`).

A instalação demora uns minutos porque o `sentence-transformers` puxa o
PyTorch, que é grande. É normal.

## 4. Conferir se instalou direito

```powershell
pytest
```

Tem que terminar com algo tipo `125 passed`. Esses testes não precisam de
internet nem dos dados grandes: rodam em grafos pequenos que dá pra conferir
na mão. Se passou, o código tá funcionando.

## 5. Os dados

O grafo da Wikipédia inteira não cabe no GitHub, então fica numa pasta
separada. Por padrão o projeto procura numa pasta `data` dentro do próprio
projeto (`wikirace\data`).

### Caminho curto: copiar a pasta pronta

Pega comigo a pasta `wikirace-data` e copia **o conteúdo dela** pra
`wikirace\data`. Precisa destes quatro arquivos:

```
wikirace\
  data\
    grafo.npz        (330 MB)  o grafo
    titulos.txt      (25 MB)   o nome de cada artigo
    embeddings.npy   (900 MB)  os vetores dos títulos (só pros agentes "inteligentes")
    cache_api.sqlite (150 KB)  o primeiro link já baixado (parte 8 da demo roda sem internet)
```

A pasta `raw` (os dumps originais) não precisa.

Se preferir deixar a pasta em outro lugar, avisa o projeto onde ela tá:

```powershell
$env:WIKIRACE_DATA = "D:\onde\ficou\wikirace-data"     # Windows, vale só pra esse terminal
```
```bash
export WIKIRACE_DATA=/onde/ficou/wikirace-data          # Linux / Mac
```

### Caminho longo: montar do zero

```powershell
python scripts/montar_grafo.py            # baixa ~900 MB de dumps e monta o grafo (~3 min depois de baixar)
python scripts/calcular_embeddings.py     # ~5 min com placa de vídeo NVIDIA; sem ela pode passar de meia hora
```

Atenção: o script baixa o dump **mais recente** da Wikipédia, não o de
01/11/2026 que a gente usou. Os números vão sair um pouquinho diferentes dos
do relatório (a Wikipédia muda todo dia), e os exemplos da demo podem mudar
também. Pra apresentação, o caminho curto é mais seguro.

## 6. Rodar a demo da apresentação

```powershell
python scripts/demo.py
```

Ela carrega o grafo (uns segundos) e vai mostrando as partes uma por uma: a
cada Enter aparece a próxima. A ordem é a mesma dos slides. Pra testar antes
sem ficar apertando Enter:

```powershell
python scripts/demo.py --sem-pausa
```

Dá pra trocar o par de artigos:

```powershell
python scripts/demo.py --origem "Capivara" --destino "Albert Einstein"
```

(O nome tem que ser igual ao título do artigo na Wikipédia, com acento e
maiúscula na primeira letra. Se não achar, ele avisa.)

## 7. Deixar a turma jogar

```powershell
python scripts/jogar.py --jogador "Fulano"
python scripts/jogar.py --origem Pelé --destino "Mecânica quântica" --jogador "Fulano"
```

Como joga:

* digita um pedaço do nome do link (tipo `ingl`) → aparece a lista dos links
  que batem, numerada;
* digita o número → clica naquele link;
* `<` → volta pro artigo anterior (conta como clique);
* `desisto` → encerra.

No fim aparece o caminho ótimo e o que cada agente fez no mesmo par. A partida
fica salva em `resultados/humanos.csv`. **Guarda esse arquivo**: é a referência
humana do relatório.

Depois que todo mundo jogou:

```powershell
python scripts/resumo_humanos.py
```

Ele junta as partidas, mostra quantos chegaram, a razão cliques/ótimo e o que
os agentes fizeram **nos mesmos pares** que a turma jogou. A tabela já sai no
formato de colar no relatório (seção 4.4).

## 8. Rodar tudo de novo (opcional, só se quiser refazer os números)

Cada número do relatório sai de um desses scripts. Ninguém precisa rodar pra
apresentar, os resultados já estão em `resultados/`.

| comando | o que faz | tempo |
|---|---|---|
| `python scripts/analisar_grafo.py` | componentes, conexidade, distâncias, hubs, assimetria | ~17 min |
| `python scripts/analisar_grafo.py conexidade` | só a parte "a Wikipédia é conexa?" | ~15 s |
| `python scripts/rodar_experimento.py` | 100 pares × 8 agentes | ~48 min |
| `python scripts/primeiro_link.py` | ciclo do primeiro link (usa a internet, 1 requisição/s) | de 20 min a mais de 1 h: a Wikipédia limita as requisições. O que já baixou fica em cache, então se parar no meio é só rodar de novo |
| `python scripts/figuras.py` | refaz as figuras do relatório | segundos |

## Deu ruim? Os erros mais comuns

| erro | o que fazer |
|---|---|
| `python` não é reconhecido | Python não tá no PATH. Reinstala marcando "Add python.exe to PATH". |
| `No module named 'numpy'` (ou outro) | O ambiente virtual não tá ativo. Roda o `Activate` de novo. |
| `FileNotFoundError: ... grafo.npz` | A pasta de dados não tá em `wikirace\data` nem no `WIKIRACE_DATA`. Confere o passo 5. |
| `KeyError: artigo não encontrado` | O título tá escrito diferente. Confere na Wikipédia (acento, maiúscula). |
| caracteres estranhos tipo `â†'` no lugar de `→` | Terminal antigo. Roda `$env:PYTHONUTF8 = "1"` antes, ou usa o Windows Terminal. |
| `MemoryError` | Falta RAM. Fecha o navegador e o que mais tiver aberto. |
| `pip` muito lento / travado no torch | É o download do PyTorch (centenas de MB). Espera. |
