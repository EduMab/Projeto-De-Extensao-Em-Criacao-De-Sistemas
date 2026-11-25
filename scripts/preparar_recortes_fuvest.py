#!/usr/bin/env python3
"""Gera uma imagem por questão FUVEST, incluindo apoio e continuações do original."""
from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path
import re
import unicodedata

import fitz
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
INDICE = ROOT / "src/main/resources/fuvest-recortes.json.gz"
PADRAO_APOIO = re.compile(r"questoes\s+(?:de\s+)?(\d{1,2})\s+(?:a|e)\s+(\d{1,2})\b")
# Esses cabeçalhos não têm Unicode no PDF de 2021. Coordenadas conferidas no caderno V.
APOIOS_2021 = [(17, 1, 56, 58), (18, 0, 59, 60), (19, 0, 63, 65),
               (20, 0, 68, 69), (21, 0, 72, 74), (22, 1, 78, 80), (24, 0, 83, 84)]
SEPARADORES = {"154aad3306e7ab3c0a99860a0e75509b", "e92031ec5dde29b90d56405daae2205f"}


def normalizar(texto):
    return "".join(c for c in unicodedata.normalize("NFD", texto.lower())
                   if unicodedata.category(c) != "Mn")


def linhas(pagina):
    return [("".join(s["text"] for s in l["spans"]), fitz.Rect(l["bbox"]))
            for b in pagina.get_text("dict", flags=fitz.TEXTFLAGS_TEXT)["blocks"]
            for l in b.get("lines", [])]


def regioes_edicao(documento, edicao):
    """Particiona na ordem física, inclusive quando a numeração troca de coluna."""
    questoes = {q["numero"]: q for q in edicao["questoes"]}
    ultima = max(q["conteudo"]["pagina"] for q in questoes.values())
    imagens_paginas = {p: documento[p - 1].get_image_info(hashes=True) for p in range(2, ultima + 1)}
    eventos = {}
    apoios = {}
    partes = {n: [] for n in questoes}
    for n, q in questoes.items():
        c = q["conteudo"]
        caixa = c["caixaTitulo"]
        eventos.setdefault(c["pagina"], []).append({
            "tipo": "questao", "numero": n, "x": caixa[0], "y": caixa[1],
            "inicio": caixa[1],
        })

    def apoio(pagina, coluna, a, b, topo, inicio):
        chave = f"{a}-{b}"
        if chave in apoios:
            raise ValueError(f"Apoio repetido em {edicao['ano']}: {chave}")
        apoios[chave] = {"numeros": list(range(a, b + 1)), "regioes": []}
        eventos.setdefault(pagina, []).append({"tipo": "apoio", "chave": chave,
            "x": 310 if coluna else 34, "y": topo, "inicio": inicio})

    if edicao["ano"] == 2021:
        for p, col, a, b in APOIOS_2021:
            apoio(p, col, a, b, 39, 55.5)
    else:
        for p in range(2, ultima + 1):
            ls = linhas(documento[p - 1])
            for texto, caixa in ls:
                m = PADRAO_APOIO.search(normalizar(texto))
                if not m:
                    continue
                a, b = map(int, m.groups())
                if not 1 <= a < b <= len(questoes):
                    continue
                c = questoes[a]["conteudo"]
                if (p, caixa.x0 > 298, caixa.y0) >= (c["pagina"], c["caixaTitulo"][0] > 298,
                                                        c["caixaTitulo"][1]):
                    continue
                topo = caixa.y0 - 3
                # O cabeçalho de 2022/20 ocupa duas linhas de instrução.
                anteriores = [(t, r) for t, r in ls if (r.x0 > 298) == (caixa.x0 > 298)
                              and 0 <= caixa.y0 - r.y1 < 6 and r.y0 < caixa.y0]
                for t, r in anteriores:
                    if re.search(r"leia|responder|texto.*para", normalizar(t)):
                        topo = min(topo, r.y0 - 3)
                apoio(p, caixa.x0 > 298, a, b, topo, caixa.y1 + 2)

    dono = None

    def adicionar(evento, pagina, caixa):
        if evento is None or caixa[3] - caixa[1] < 2:
            return
        x0, y0, x1, y1 = caixa
        for imagem in imagens_paginas[pagina]:
            r = fitz.Rect(imagem["bbox"])
            if (imagem["digest"].hex() in SEPARADORES and x0 <= r.x0 < x1
                    and y0 < r.y0 and 0 <= y1 - r.y0 < 50):
                y1 = min(y1, r.y0 - .5)
        caixa = (x0, y0, x1, y1)
        regiao = {"pagina": pagina, "caixa": [round(v, 3) for v in caixa],
                  "tipo": evento["tipo"]}
        if evento["tipo"] == "questao":
            partes[evento["numero"]].append(regiao)
        else:
            apoios[evento["chave"]]["regioes"].append(regiao)

    for p in range(2, ultima + 1):
        pagina = documento[p - 1]
        # O traço vertical identifica as páginas em duas colunas. Há também
        # páginas largas com mapas, tabelas e alternativas em várias colunas.
        divisorias = [d["rect"] for d in pagina.get_drawings()
                      if 290 < d["rect"].x0 < 302 and d["rect"].width < 3
                      and d["rect"].height > 500]
        meio = pagina.rect.width / 2
        caixas = [(10, 36, meio - .7, 802), (meio + 3, 36, pagina.rect.width - 10, 802)] \
            if divisorias else [(10, 36, pagina.rect.width - 10, 795)]
        if divisorias and max(r.y1 for r in divisorias) < 790:
            # Em 2021/26, 88 e 89 ficam lado a lado. A questão 90 ocupa
            # a faixa inferior inteira, com enunciado à esquerda e opções à direita.
            fim = max(r.y1 for r in divisorias)
            inicio = min(e["y"] for e in eventos[p] if e["y"] >= fim)
            caixas = [(10, 36, meio - .7, fim), (meio + 3, 36, pagina.rect.width - 10, fim),
                      (10, inicio, pagina.rect.width - 10, 795)]
        for x0, y0, x1, y1 in caixas:
            es = sorted((e for e in eventos.get(p, []) if x0 <= e["x"] < x1 and y0 <= e["y"] < y1),
                        key=lambda e: e["y"])
            cursor = y0
            for e in es:
                adicionar(dono, p, (x0, cursor, x1, min(e["y"], y1)))
                dono = e
                cursor = max(y0, e["inicio"])
            adicionar(dono, p, (x0, cursor, x1, y1))

    for n in questoes:
        suporte = [r for a in apoios.values() if n in a["numeros"] for r in a["regioes"]]
        partes[n] = suporte + partes[n]
        # Nenhum recorte pode conter o título de outra questão.
        for r in partes[n]:
            rect = fitz.Rect(r["caixa"])
            for outro, q in questoes.items():
                c = q["conteudo"]
                titulo = fitz.Rect(c["caixaTitulo"])
                centro = (titulo.tl + titulo.br) / 2
                if c["pagina"] == r["pagina"] and centro in rect:
                    if outro != n or r["tipo"] != "questao":
                        raise ValueError(f"Questão vizinha no recorte {edicao['ano']}/{n}: {outro}")
    return partes, apoios


def renderizar(documento, regioes, destino):
    imagens = []
    usadas = []
    for r in regioes:
        pix = documento[r["pagina"] - 1].get_pixmap(matrix=fitz.Matrix(2.5, 2.5),
                                                    clip=fitz.Rect(r["caixa"]), alpha=False)
        im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        # A letra do caderno, no centro do rodapé, pode tocar a margem da coluna.
        # Não é parte do enunciado e não deve alongar um recorte com espaço vazio.
        if r["caixa"][3] > 798:
            draw = ImageDraw.Draw(im)
            draw.rectangle((294 * 2.5 - pix.x, 798 * 2.5 - pix.y,
                            301 * 2.5 - pix.x, im.height), fill="white")
        tinta = im.convert("L").point(lambda p: 255 if p < 235 else 0)
        bbox = tinta.getbbox()
        if bbox is None:
            continue
        # Remove apenas margens vazias, mantendo a escala e a largura do original.
        im = im.crop((0, max(0, bbox[1] - 8), im.width, min(im.height, bbox[3] + 8)))
        imagens.append(im)
        usadas.append(r)
    if not imagens:
        raise ValueError(f"Questão sem imagem: {destino}")
    largura = max(im.width for im in imagens)
    final = Image.new("RGB", (largura + 32, sum(im.height for im in imagens) + 24 * (len(imagens) + 1)), "white")
    y = 24
    for im in imagens:
        final.paste(im, ((final.width - im.width) // 2, y))
        y += im.height + 24
    final.save(destino, "WEBP", quality=92, method=4)
    return usadas, round(final.width / 2.5, 3)


def preparar(edicoes):
    indice, relatorios = {}, []
    for edicao in edicoes:
        ano = edicao["ano"]
        pdf = ROOT / f"tmp/pdfs/fuvest/{ano}/prova.pdf"
        if hashlib.sha256(pdf.read_bytes()).hexdigest() != edicao["sha256Prova"]:
            raise ValueError(f"PDF divergente para recorte: {ano}")
        # A versão no caminho evita que navegador/CDN reutilizem as páginas antigas.
        prefixo = f"/questoes/fuvest/{ano}-{edicao['sha256Prova'][:12]}-individual-v1"
        destino = ROOT / "src/main/resources/static" / prefixo.lstrip("/")
        destino.mkdir(parents=True, exist_ok=True)
        with fitz.open(pdf) as doc:
            regioes, apoios = regioes_edicao(doc, edicao)
            for q in edicao["questoes"]:
                n, c = q["numero"], q["conteudo"]
                nome = f"questao-{n:02}.webp"
                usadas, largura = renderizar(doc, regioes[n], destino / nome)
                indice[f"{ano}/{n}"] = {"pagina": c["pagina"], "caixaTitulo": c["caixaTitulo"],
                    "urlProva": c["urlProva"], "regioesFonte": usadas,
                    "recortes": [{"tipo": "questao", "imagem": f"{prefixo}/{nome}",
                                  "larguraOriginal": largura}]}
        relatorios.append({"ano": ano, "questoes": len(edicao["questoes"]),
                           "apoiosCompartilhados": len(apoios), "sha256Prova": edicao["sha256Prova"]})
        print(f"FUVEST {ano}: {len(edicao['questoes'])} recortes individuais, {len(apoios)} apoios", flush=True)
    INDICE.write_bytes(gzip.compress(json.dumps(indice, ensure_ascii=False, separators=(",", ":")).encode(), mtime=0))
    (ROOT / "acervo/fuvest/validacao-recortes.json").write_text(
        json.dumps({"total": len(indice), "edicoes": relatorios}, ensure_ascii=False, indent=2) + "\n")
    return indice


if __name__ == "__main__":
    preparar(json.loads(gzip.decompress((ROOT / "acervo/fuvest/questoes.json.gz").read_bytes()))["edicoes"])
