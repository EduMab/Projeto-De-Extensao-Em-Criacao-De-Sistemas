#!/usr/bin/env python3
"""Coleta os cadernos oficiais ENEM (azul, aplicacao regular) e seus gabaritos.

Esta etapa baixa e registra as fontes. Ela NAO publica questoes no banco:
a extracao/validacao do conteudo e uma etapa separada e obrigatoria.
"""
from __future__ import annotations

import argparse
from bs4 import BeautifulSoup
import hashlib
import json
from pathlib import Path
import re
import time
from urllib.parse import urljoin
from urllib.request import Request, urlopen

BASE = "https://www.gov.br/inep/pt-br/areas-de-atuacao/avaliacao-e-exames-educacionais/enem/provas-e-gabaritos"
ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "tmp/pdfs/enem"
OUTPUT = ROOT / "acervo/enem/manifesto.json"
UA = "EvoluaMais/1.0 (educational archive; contact repository maintainers)"


def fetch(url: str) -> bytes:
    req = Request(url, headers={"User-Agent": UA})
    with urlopen(req, timeout=60) as response:
        return response.read()


def norm(value: str) -> str:
    value = value.casefold().replace("º", "o").replace("°", "o")
    return re.sub(r"\\s+", " ", value).strip()


def page_links(year: int) -> dict:
    url = f"{BASE}/{year}"
    soup = BeautifulSoup(fetch(url), "html.parser")
    selected = {}
    for anchor in soup.find_all("a", href=True):
        label = norm(anchor.get_text(" ", strip=True))
        if label not in {"prova", "gabarito"}:
            continue
        context = ""
        for parent in anchor.parents:
            text = norm(parent.get_text(" ", strip=True))
            if len(text) > 1600:
                continue
            day = re.search(r"([12])o?\\s*dia", text)
            if day and "azul" in text and "aplica" in text:
                context = text
                break
        if not context or "reaplica" in context or "ppl" in context:
            continue
        day_match = re.search(r"([12])o?\\s*dia", context)
        day = int(day_match.group(1))
        # Na aplicacao regular, o caderno azul e o 1 no primeiro dia
        # e o 7 no segundo. A descricao do bloco tambem precisa confirmar azul.
        caderno = 1 if day == 1 else 7
        key = (day, label)
        href = urljoin(url, anchor["href"])
        previous = selected.get(key)
        if previous and previous["url"] != href:
            raise RuntimeError(f"Mais de um link {label} para dia {day} em {year}; revise a pagina oficial")
        selected[key] = {"url": href, "contexto": context, "rotulo": label, "caderno": caderno}
    result = {}
    for day in (1, 2):
        prova = selected.get((day, "prova"))
        gabarito = selected.get((day, "gabarito"))
        if not prova or not gabarito:
            raise RuntimeError(f"Pagina oficial {year}: nao localizei prova e gabarito azul do dia {day}")
        result[str(day)] = {
            "dia": day, "caderno": "AZUL", "numeroCaderno": 1 if day == 1 else 7,
            "prova": prova["url"], "gabarito": gabarito["url"],
            "contextoPagina": prova["contexto"]
        }
    return {"ano": year, "paginaOficial": url, "dias": result}


def download(url: str, target: Path, use_cache: bool) -> dict:
    target.parent.mkdir(parents=True, exist_ok=True)
    if not (use_cache and target.exists()):
        payload = fetch(url)
        if not payload.startswith(b"%PDF"):
            raise RuntimeError(f"A URL oficial nao retornou PDF: {url}")
        target.write_bytes(payload)
    payload = target.read_bytes()
    if not payload.startswith(b"%PDF"):
        raise RuntimeError(f"Arquivo local nao e PDF: {target}")
    return {"arquivo": str(target.relative_to(ROOT)), "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(), "url": url}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inicio", type=int, default=2017)
    parser.add_argument("--fim", type=int, default=2026)
    parser.add_argument("--usar-cache", action="store_true",
                        help="Reutiliza PDFs locais. Sem esta opcao, baixa novamente para captar retificacoes.")
    parser.add_argument("--somente-manifesto", action="store_true",
                        help="Localiza os links oficiais e gera o manifesto sem baixar os PDFs.")
    args = parser.parse_args()
    if args.inicio < 2000 or args.fim < args.inicio or args.fim > 2100:
        parser.error("Intervalo de anos invalido")
    editions = []
    for year in range(args.inicio, args.fim + 1):
        edition = page_links(year)
        for day in (1, 2):
            item = edition["dias"][str(day)]
            if not args.somente_manifesto:
                folder = WORK / str(year) / f"dia{day}"
                item["arquivos"] = {
                    "prova": download(item["prova"], folder / "prova.pdf", args.usar_cache),
                    "gabarito": download(item["gabarito"], folder / "gabarito.pdf", args.usar_cache)
                }
            print(f"{year} dia {day}: links oficiais identificados" +
                  ("; PDFs baixados e conferidos" if not args.somente_manifesto else ""), flush=True)
        editions.append(edition)
        time.sleep(0.15)
    manifest = {
        "formato": 1, "tipo": "ENEM", "fonte": BASE,
        "inicio": args.inicio, "fim": args.fim,
        "criterios": {"aplicacao": "regular", "caderno": "azul",
                      "linguaEstrangeira": "ingles"},
        "edicoes": editions
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Manifesto criado: {OUTPUT.relative_to(ROOT)}", flush=True)
    print("ATENCAO: manifesto e PDFs nao significam que as questoes foram extraidas ou validadas.", flush=True)


if __name__ == "__main__":
    main()
