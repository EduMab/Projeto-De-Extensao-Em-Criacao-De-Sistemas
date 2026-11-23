#!/usr/bin/env python3
"""Coleta e prepara o acervo oficial ETEC; a gravacao no banco e uma etapa explicita."""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import urllib.request

ARCHIVE = "https://www.cps.sp.gov.br/etec/vestibulinho/"
ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "tmp/pdfs/etec"


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.capture = None
        self.text = []
        self.href = None
        self.events = []

    def handle_starttag(self, tag, attrs):
        if tag in ("h3", "a"):
            self.capture = tag
            self.text = []
            self.href = dict(attrs).get("href")

    def handle_data(self, data):
        if self.capture:
            self.text.append(data)

    def handle_endtag(self, tag):
        if self.capture == tag:
            self.events.append((tag, " ".join(" ".join(self.text).split()), self.href))
            self.capture = None


def collect(start=2017, end=2026):
    WORK.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(ARCHIVE, headers={"User-Agent": "EvoluaMais/1.0 (educational archive)"})
    with urllib.request.urlopen(request, timeout=45) as response:
        source = response.read().decode("utf-8")
    (WORK / "fonte.html").write_text(source)
    pattern = re.compile(r'<div[^>]*class="[^"]*elementor-tab-mobile-title[^"]*"[^>]*>\s*(20\d\d)\s*</div>')
    panels = list(pattern.finditer(source))
    exams = []
    for index, panel in enumerate(panels):
        year = int(panel.group(1))
        if not start <= year <= end:
            continue
        parser = Links()
        parser.feed(source[panel.end():panels[index + 1].start() if index + 1 < len(panels) else len(source)])
        current = None
        for tag, label, href in parser.events:
            if tag == "h3" and re.search(r"[12].*Semestre", label, re.I):
                if current and current.get("prova") and current.get("gabarito"):
                    exams.append(current)
                semester = int(re.search(r"[12]", label).group())
                current = {"ano": year, "semestre": semester, "edicao": f"{year}-{semester}"}
            elif current and tag == "a" and href:
                if label == "Prova":
                    current["prova"] = html.unescape(href)
                elif label.lower().startswith("gabarito"):
                    current["gabarito"] = html.unescape(href)
                    current["retificado"] = "retificado" in label.lower()
        if current and current.get("prova") and current.get("gabarito"):
            exams.append(current)
    if len({e["edicao"] for e in exams}) != len(exams):
        raise ValueError("Edicoes duplicadas no arquivo oficial")
    return sorted(exams, key=lambda e: (e["ano"], e["semestre"]))


def download(item):
    exam, kind, use_cache = item
    target = WORK / exam["edicao"] / f"{kind}.pdf"
    target.parent.mkdir(exist_ok=True)
    if not use_cache or not target.exists():
        with urllib.request.urlopen(exam[kind], timeout=60) as response:
            payload = response.read()
        if not payload.startswith(b"%PDF"):
            raise ValueError(f"A fonte nao retornou PDF: {exam['edicao']} / {kind}")
        target.write_bytes(payload)
    return {"edicao": exam["edicao"], "tipo": kind,
            "bytes": target.stat().st_size,
            "sha256": hashlib.sha256(target.read_bytes()).hexdigest()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--inicio", type=int, default=2017)
    parser.add_argument("--fim", type=int, default=2026)
    parser.add_argument("--somente-download", action="store_true")
    parser.add_argument("--usar-cache", action="store_true", help="Reutiliza PDFs locais; omita para buscar retificacoes na fonte")
    args = parser.parse_args()
    exams = collect(args.inicio, args.fim)
    print(f"Edicoes oficiais encontradas: {len(exams)}", flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        downloads = list(pool.map(download, [(e, k, args.usar_cache) for e in exams for k in ("prova", "gabarito")]))
    manifest = {"fonte": ARCHIVE, "inicio": args.inicio, "fim": args.fim, "edicoes": exams, "arquivos": downloads}
    path = ROOT / "acervo/etec/manifesto.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    print(f"PDFs coletados: {len(downloads)}; manifesto: {path.relative_to(ROOT)}", flush=True)
    if not args.somente_download:
        from extrair_etec import extract
        result = extract(manifest)
        print(f"Questoes: {result['total']}; ativas: {result['ativas']}; anuladas: {result['anuladas']}", flush=True)


if __name__ == "__main__":
    main()
