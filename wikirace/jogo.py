"""Lógica da demo: um humano joga Wikirace e depois compara com os agentes.

A parte de terminal (input/print) fica em ``scripts/jogar.py``; aqui fica só o
estado da partida, pra dar pra testar.
"""

from __future__ import annotations

import csv
import time
import unicodedata
from datetime import datetime
from pathlib import Path


def sem_acento(s):
    s = unicodedata.normalize("NFD", s.lower().replace("_", " "))
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


class PartidaHumana:
    """Partida no ambiente ``amb`` (offline ou ao vivo).

    ``caminho`` guarda a caminhada inteira; "voltar" também conta como clique,
    igual aos agentes caminhantes.
    """

    def __init__(self, amb, origem, destino, jogador="anonimo"):
        self.amb, self.origem, self.destino = amb, origem, destino
        self.jogador = jogador
        self.caminho = [origem]
        self.pilha = [origem]
        self.lidos = set()
        self.inicio = time.time()

    @property
    def atual(self):
        return self.pilha[-1]

    @property
    def terminou(self):
        return self.atual == self.destino

    @property
    def cliques(self):
        return len(self.caminho) - 1

    def links(self):
        self.lidos.add(self.atual)
        return list(self.amb.vizinhos(self.atual))

    def opcoes(self, filtro="", limite=30):
        """Links do artigo atual cujo nome contém ``filtro`` (sem ligar pra acento)."""
        f = sem_acento(filtro)
        nomes = [(self.amb.nome(v), v) for v in self.links()]
        achados = [(n, v) for n, v in nomes if f in sem_acento(n)]
        achados.sort(key=lambda nv: (not sem_acento(nv[0]).startswith(f), nv[0]))
        return achados[:limite]

    def clicar(self, v):
        if v not in set(self.links()):
            raise ValueError("esse link não existe no artigo atual")
        self.caminho.append(v)
        self.pilha.append(v)

    def voltar(self):
        if len(self.pilha) == 1:
            raise ValueError("já está no artigo de origem")
        self.pilha.pop()
        self.caminho.append(self.pilha[-1])

    def registro(self, otimo=None):
        return {"quando": datetime.now().isoformat(timespec="seconds"),
                "jogador": self.jogador,
                "origem": self.amb.nome(self.origem), "destino": self.amb.nome(self.destino),
                "sucesso": self.terminou, "cliques": self.cliques, "otimo": otimo,
                "consultados": len(self.lidos),
                "segundos": round(time.time() - self.inicio, 1),
                "caminho": " → ".join(self.amb.nome(v) for v in self.caminho)}


def salvar_registro(caminho_csv, registro):
    caminho_csv = Path(caminho_csv)
    novo = not caminho_csv.exists()
    caminho_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho_csv, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(registro))
        if novo:
            w.writeheader()
        w.writerow(registro)


def resumir_humanos(humanos, pares, partidas):
    """Junta as partidas da turma (``humanos.csv``) com o experimento.

    Recebe três DataFrames: as partidas humanas, ``pares.csv`` e
    ``partidas.csv`` do experimento. Devolve um dicionário com o resumo dos
    humanos e, nos pares do experimento que a turma jogou, o que cada agente
    fez nesses mesmos pares (pra comparar maçã com maçã).
    """
    import pandas as pd

    def chave(s):
        return s.astype(str).str.replace(" ", "_")

    h = humanos.copy()
    h["sucesso"] = h["sucesso"].astype(str).str.lower() == "true"
    h["_o"], h["_d"] = chave(h["origem"]), chave(h["destino"])
    p = pares.assign(_o=chave(pares["titulo_origem"]), _d=chave(pares["titulo_destino"]))
    h = h.merge(p[["_o", "_d", "par", "otimo"]].rename(columns={"otimo": "otimo_exp"}),
                on=["_o", "_d"], how="left")
    h["otimo"] = pd.to_numeric(h["otimo"], errors="coerce").fillna(h["otimo_exp"])

    def resumo(df, cliques="cliques", consultados="consultados"):
        ok = df[df["sucesso"]]
        razao = ok[cliques] / ok["otimo"]
        return {"partidas": int(len(df)),
                "taxa_sucesso": float(df["sucesso"].mean()) if len(df) else None,
                "razao_media": float(razao.mean()) if len(ok) else None,
                "fracao_otima": float((razao == 1).mean()) if len(ok) else None,
                "consultados_mediana": float(df[consultados].median()) if len(df) else None}

    geral = resumo(h)
    geral["segundos_medio"] = float(h["segundos"].mean()) if len(h) else None
    jogadores = {j: resumo(df) for j, df in h.groupby("jogador")}

    pares_jogados = sorted(int(x) for x in h["par"].dropna().unique())
    agentes = {}
    if pares_jogados:
        pa = partidas[partidas["par"].isin(pares_jogados)].copy()
        pa["sucesso"] = pa["sucesso"].astype(str).str.lower() == "true"
        agentes = {a: resumo(df) for a, df in pa.groupby("agente")}
    nos_pares = h[h["par"].notna()]
    return {"humanos": geral,
            "humanos_nos_pares_do_experimento": resumo(nos_pares),
            "por_jogador": jogadores,
            "pares_do_experimento_jogados": pares_jogados,
            "agentes_nos_mesmos_pares": agentes,
            "partidas_fora_do_experimento": int(h["par"].isna().sum())}
