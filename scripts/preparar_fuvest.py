#!/usr/bin/env python3
"""Baixa os PDFs oficiais, valida numeração/gabarito e prepara a carga FUVEST."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import gzip
import hashlib
import json
from pathlib import Path
import re
import subprocess
from urllib.request import urlopen

import fitz
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ACERVO = ROOT / "acervo/fuvest"
CACHE = ROOT / "tmp/pdfs/fuvest"
STATIC = ROOT / "src/main/resources/static"
DIGITOS_2018 = (
    "0c6d748bbb6a18de0de47f22ad7ae192", "500483bd743aaa3d6dae1e5788482934",
    "770b909578c43bbb38da3648e95d2905", "47573bed0da89f6d76a7d32423dce5c5",
    "6851845be9b14231a8fcd9977666387d", "1656e6faaff6a0a1861faaf9c3bb8ac4",
    "90ff53433b79d37d91f0f8e7bf2f5654", "829f10e1c30d97d1a43aca29efbc31ee",
    "b6cd548cb4be8c4d61c7c3c450cb857c", "b11ecbfea3e079fdc68d5e34c460592e",
)
FONTES_TITULO = {
    2019: "BrandonGrotesque-Black", 2020: "BrandonGrotesque-Black",
    2021: "SegoeUIBlack", 2022: "Arial", 2023: "Gadugi,Bold", 2024: "Gadugi,Bold",
    2025: "Gadugi-Bold", 2026: "Baloo2ExtraBold", 2027: "Baloo2-ExtraBold",
}


def baixar(fonte, usar_cache):
    pasta = CACHE / str(fonte["ano"])
    pasta.mkdir(parents=True, exist_ok=True)
    for tipo in ("prova", "gabarito"):
        destino = pasta / f"{tipo}.pdf"
        if usar_cache and destino.is_file():
            continue
        with urlopen(fonte[tipo], timeout=90) as resposta:
            dados = resposta.read()
        if not dados.startswith(b"%PDF") or b"%%EOF" not in dados[-1024:]:
            raise ValueError(f"PDF inválido: {fonte['ano']} / {tipo}")
        temporario = destino.with_suffix(".part")
        temporario.write_bytes(dados)
        temporario.replace(destino)
    return pasta


def gabarito(path, fonte):
    # A primeira página contém a tabela por caderno, com V/V1 nas duas primeiras
    # colunas de respostas. As páginas de correspondência usam outra ordem.
    texto = subprocess.check_output(["pdftotext", "-f", "1", "-l", "1", "-layout", str(path), "-"],
                                    encoding="utf-8")
    cabecalho = re.search(r"(?im)^\s*prova\s+(V1?)\s+prova\s+(?:K|V2)\b", texto)
    if not cabecalho or cabecalho[1].upper() != fonte["caderno"]:
        raise ValueError(f"Caderno ausente no cabeçalho do gabarito: {fonte['ano']}")
    metade = fonte["total"] // 2
    respostas = {}
    for linha in texto[cabecalho.end():].splitlines():
        campos = re.split(r"\s*[‐–-]\s*|\s+", linha.strip())
        if not campos[0].isdigit():
            continue
        numeros = [i for i, campo in enumerate(campos) if campo.isdigit()]
        if len(numeros) < 3:
            raise ValueError(f"Linha incompleta no gabarito de {fonte['ano']}: {linha}")
        i, j, k = numeros[:3]
        n = int(campos[i])
        if n != 1 + len(respostas) // 2 or int(campos[j]) != n + metade or int(campos[k]) != n:
            raise ValueError(f"Colunas inesperadas no gabarito de {fonte['ano']}: {linha}")
        for indice, limite in ((i, j), (j, k)):
            resposta = "".join(campos[indice + 1:limite])
            if not re.fullmatch(r"(?:[A-E]{1,2}|\*)", resposta) or len(set(resposta)) != len(resposta):
                raise ValueError(f"Resposta inválida no gabarito de {fonte['ano']}: {linha}")
            respostas[int(campos[indice])] = [] if resposta == "*" else list(resposta)
    if set(respostas) != set(range(1, fonte["total"] + 1)):
        raise ValueError(f"Gabarito incompleto: {fonte['ano']}")
    return respostas


def titulos_2018(pagina):
    digitos = []
    for item in pagina.get_image_info(hashes=True):
        chave = item["digest"].hex()
        if chave not in DIGITOS_2018:
            continue
        caixa = fitz.Rect(item["bbox"])
        digitos.append((caixa.x0 > 200, caixa, str(DIGITOS_2018.index(chave))))
    digitos.sort(key=lambda d: (d[0], round(d[1].y0 / 3), d[1].x0))
    # As duas imagens de cada número compartilham a mesma linha.
    resultado = []
    while digitos:
        coluna, caixa, primeiro = digitos.pop(0)
        pares = [d for d in digitos if d[0] == coluna and abs(d[1].y0 - caixa.y0) < 1
                 and abs(d[1].x0 - caixa.x0) < 12]
        if len(pares) != 1:
            raise ValueError(f"Número gráfico incompleto na página {pagina.number + 1}")
        segundo = pares[0]
        digitos.remove(segundo)
        if caixa.x0 > segundo[1].x0:
            resultado.append((int(segundo[2] + primeiro), caixa | segundo[1]))
        else:
            resultado.append((int(primeiro + segundo[2]), caixa | segundo[1]))
    return resultado


def titulos_texto(pagina, ano):
    for bloco in pagina.get_text("dict", flags=fitz.TEXTFLAGS_TEXT)["blocks"]:
        for linha in bloco.get("lines", []):
            for trecho in linha["spans"]:
                texto = trecho["text"].strip()
                caixa = fitz.Rect(trecho["bbox"])
                if (trecho["font"] == FONTES_TITULO[ano] and 11.9 <= trecho["size"] <= 14.2
                        and (28 <= caixa.x0 <= 39 or 300 <= caixa.x0 <= 317)
                        and re.fullmatch(r"\d{2}", texto)):
                    yield int(texto), caixa


def mapear_questoes(documento, fonte):
    ano = fonte["ano"]
    localizacoes = []
    for pagina in list(documento)[1:]:
        titulos = titulos_2018(pagina) if ano == 2018 else list(titulos_texto(pagina, ano))
        for numero, caixa in sorted(titulos, key=lambda t: (t[1].x0 > 200, t[1].y0)):
            localizacoes.append((numero, pagina.number + 1, [round(v, 3) for v in caixa]))
    if sorted(n for n, _, _ in localizacoes) != list(range(1, fonte["total"] + 1)):
        encontrados = [n for n, _, _ in localizacoes]
        raise ValueError(f"Numeração incompleta ou duplicada: {ano}: {encontrados}")
    return sorted(localizacoes)


def textos_de_apoio(path, total):
    # Leitura com layout mantém os títulos em uma linha e as páginas separadas.
    texto = subprocess.check_output(["pdftotext", "-layout", str(path), "-"], encoding="utf-8")
    padrao = re.compile(r"textos?\s+para\s+as\s+quest(?:ões|oes)\s+(?:de\s+)?(\d{1,2})"
                        r"\s+(?:a|e)\s+(\d{1,2})\b", re.IGNORECASE)
    apoios = {}
    for pagina, texto_pagina in enumerate(texto.split("\f"), 1):
        for inicio, fim in padrao.findall(texto_pagina):
            inicio, fim = int(inicio), int(fim)
            if 1 <= inicio < fim <= total:
                for numero in range(inicio, fim + 1):
                    apoios.setdefault(numero, pagina)
    return apoios


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def preparar_edicao(fonte, pasta):
    ano = fonte["ano"]
    prova = pasta / "prova.pdf"
    chave = pasta / "gabarito.pdf"
    respostas = gabarito(chave, fonte)
    hash_prova, hash_gabarito = sha256(prova), sha256(chave)
    if (hash_prova, hash_gabarito) != (fonte["sha256Prova"], fonte["sha256Gabarito"]):
        raise ValueError(f"PDF diferente da versão conferida: {ano}. Revise as fontes antes de atualizar.")
    prefixo = f"/questoes/fuvest/{ano}-{hash_prova[:12]}"
    destino = STATIC / prefixo.lstrip("/")
    destino.mkdir(parents=True, exist_ok=True)
    questoes = []
    apoios = textos_de_apoio(prova, fonte["total"])
    if ano == 2021:
        # O PDF de 2021 não possui mapeamento Unicode para esses cabeçalhos.
        # Páginas e intervalos conferidos nas imagens do caderno V.
        for pagina, inicio, fim in [(17, 56, 58), (18, 59, 60), (19, 63, 65),
                                    (20, 68, 69), (21, 72, 74), (22, 78, 80), (24, 83, 84)]:
            apoios.update(dict.fromkeys(range(inicio, fim + 1), pagina))
    with fitz.open(prova) as documento:
        titulos = mapear_questoes(documento, fonte)
        ultima = max(pagina for _, pagina, _ in titulos)
        for pagina in range(2, ultima + 1):
            if (destino / f"pagina-{pagina:02}.webp").is_file():
                continue  # O caminho identifica o PDF pelo SHA-256.
            pix = documento[pagina - 1].get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            imagem = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            imagem.save(destino / f"pagina-{pagina:02}.webp", "WEBP", quality=88, method=4)

        def imagem_pagina(pagina):
            return {"numero": pagina, "imagem": f"{prefixo}/pagina-{pagina:02}.webp"}

        for indice, (numero, pagina, caixa) in enumerate(titulos):
            rect = documento[pagina - 1].rect
            # A página seguinte está disponível quando a questão pode continuar.
            # As anteriores atendem textos de apoio que começam em outra página.
            proxima = titulos[indice + 1][1] if indice + 1 < len(titulos) else pagina
            inicio = min(pagina, max(2, apoios.get(numero, pagina)))
            paginas = [imagem_pagina(p) for p in range(inicio, pagina + 1)]
            if proxima > pagina:
                paginas.append(imagem_pagina(pagina + 1))
            conteudo = {
                "modo": "pagina_original", "pagina": pagina, "paginas": paginas,
                "apoioAnterior": [imagem_pagina(p) for p in range(max(2, inicio - 2), inicio)],
                "numeroOriginal": numero, "caixaTitulo": caixa, "larguraPagina": rect.width,
                "alturaPagina": rect.height, "urlProva": f"{fonte['prova']}#page={pagina}",
            }
            questoes.append({
                "numero": numero, "anulada": not respostas[numero], "gabarito": respostas[numero],
                "enunciado": f"FUVEST {ano}, questão {numero:02}. Consulte o caderno original na página {pagina}.",
                "imagem": imagem_pagina(pagina)["imagem"], "conteudo": conteudo,
                "hashFonte": hashlib.sha256(f"{hash_prova}:{numero}".encode()).hexdigest(),
            })
    return {**fonte, "codigo": f"FUVEST-{ano}-FASE1-{fonte['caderno']}", "questoes": questoes,
            "sha256Prova": hash_prova, "sha256Gabarito": hash_gabarito}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--usar-cache", action="store_true", help="Usar os PDFs já baixados em tmp/pdfs/fuvest.")
    args = parser.parse_args()
    fontes = json.loads((ACERVO / "fontes.json").read_text(encoding="utf-8"))
    with ThreadPoolExecutor(max_workers=5) as pool:
        pastas = list(pool.map(lambda fonte: baixar(fonte, args.usar_cache), fontes))
    edicoes = [preparar_edicao(fonte, pasta) for fonte, pasta in zip(fontes, pastas, strict=True)]
    acervo = {"formato": 1, "tipo": "FUVEST", "edicoes": edicoes}
    pacote = gzip.compress(json.dumps(acervo, ensure_ascii=False, separators=(",", ":")).encode(), mtime=0)
    (ACERVO / "questoes.json.gz").write_bytes(pacote)
    from preparar_recortes_fuvest import preparar
    preparar(edicoes)
    for edicao in edicoes:
        anuladas = [q["numero"] for q in edicao["questoes"] if q["anulada"]]
        multiplas = [q["numero"] for q in edicao["questoes"] if len(q["gabarito"]) > 1]
        print(f"{edicao['codigo']}: {edicao['total']} questões, anuladas {anuladas}, gabarito múltiplo {multiplas}")


if __name__ == "__main__":
    main()
