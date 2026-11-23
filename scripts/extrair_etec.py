#!/usr/bin/env python3
"""Extrai numeracao/gabarito e preserva as paginas originais, sem OCR inventado."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import unicodedata

import fitz

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "tmp/pdfs/etec"
ASSETS = ROOT / "src/main/resources/static/questoes/etec"


def plain(value):
    return "".join(c for c in unicodedata.normalize("NFD", value) if not unicodedata.combining(c)).lower()


def lines(page):
    return [("".join(s["text"] for s in line["spans"]).strip(), tuple(line["bbox"]))
            for block in page.get_text("dict")["blocks"] for line in block.get("lines", [])]


def key_for(path, edition):
    text = "\n".join(p.get_text(sort=True) for p in fitz.open(path))
    if edition == "2025-2":
        # Este PDF tambem contem outros cargos/modulos, com numeracao reiniciada.
        text = re.split(r"M[ÓO]DULO\s+02", text)[0]
    pairs = re.findall(r"(?<!\d)(\d{1,3})\s*:?\s+(ANULADA|[A-E])\b", text)
    result = {}
    for number, answer in pairs:
        number = int(number)
        if not 1 <= number <= 50:
            continue
        if number in result and result[number] != answer:
            raise ValueError(f"Gabaritos conflitantes: {edition}, questao {number}")
        result[number] = answer
    expected = 40 if edition == "2023-1" else 50
    if set(result) != set(range(1, expected + 1)):
        raise ValueError(f"Gabarito incompleto: {edition}, {len(result)} entradas")
    return result


def markers(document, edition, expected):
    result = {}
    for page in list(document)[1:]:
        page_lines = lines(page)
        for text, box in page_lines:
            # Alguns PDFs possuem sobreimpressao duplicada (QuestaoQuestao 0019).
            normalized = re.sub(r"(?:Quest[ãa]o\s*)+", "Questao ", text, flags=re.I)
            match = re.fullmatch(r"Questao\s*0*(\d{1,2})", normalized, re.I)
            if edition == "2025-2":
                match = re.match(r"^(\d{1,2})\.\s+", text)
            if edition == "2026-2" and text == "Questão":
                candidates = [(t, b) for t, b in page_lines if re.fullmatch(r"\d{2}", t) and int(t) > 0
                              and abs(b[1] - box[1]) < 6 and 0 < b[0] - box[0] < 100]
                if len(candidates) != 1:
                    raise ValueError("Numero separado do titulo sem correspondencia unica")
                match = re.fullmatch(r"(\d{2})", candidates[0][0])
            if not match:
                continue
            number = int(match[1])
            if not 1 <= number <= expected:
                continue
            marker = {"pagina": page.number + 1, "caixa": [round(v, 3) for v in box]}
            if number in result and result[number] != marker:
                raise ValueError(f"Marcador duplicado: {edition}/{number}")
            result[number] = marker
    if set(result) != set(range(1, expected + 1)):
        raise ValueError(f"Numeracao incompleta: {edition}; faltam {set(range(1, expected + 1))-set(result)}")
    return result


def shared_context(document):
    contexts = {}
    pattern = re.compile(r"questoes\s*(?:de\s*)?(?:numeros?\s*)?(\d{1,2})\s*(a|e|ate\s*a?)\s*(\d{1,2})")
    for page in list(document)[1:]:
        text = plain(page.get_text(sort=True))
        for m in pattern.finditer(text):
            start, end = int(m[1]), int(m[3])
            if 1 <= start < end <= 50:
                for number in range(start, end + 1):
                    contexts[number] = min(contexts.get(number, page.number + 1), page.number + 1)
    return contexts


def extract(manifest):
    exams = []
    audit = []
    for source in manifest["edicoes"]:
        edition = source["edicao"]
        pdf_path = WORK / edition / "prova.pdf"
        source_hash = hashlib.sha256(pdf_path.read_bytes()).hexdigest()
        with fitz.open(pdf_path) as document:
            answers = key_for(WORK / edition / "gabarito.pdf", edition)
            positions = markers(document, edition, len(answers))
            contexts = shared_context(document)
            assets = ASSETS / edition
            assets.mkdir(parents=True, exist_ok=True)
            stamp = assets / "fonte.sha256"
            changed = not stamp.exists() or stamp.read_text().strip() != source_hash
            # Uma imagem por pagina, compartilhada entre as questoes. Mantem graficos,
            # formulas, alternativas e textos vinculados que a extracao linear perde.
            last_page = max(v["pagina"] for v in positions.values())
            page_text = {}
            for page_number in range(2, last_page + 1):
                page = document[page_number - 1]
                target = assets / f"pagina-{page_number:02}.webp"
                if changed or not target.exists():
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                    from PIL import Image
                    im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
                    im.save(target, "WEBP", quality=88, method=4)
                page_text[page_number] = page.get_text(sort=True).strip()
            stamp.write_text(source_hash + "\n")
            questions = []
            for number, answer in sorted(answers.items()):
                pos = positions[number]
                page_number = pos["pagina"]
                start_page = min(contexts.get(number, page_number), page_number)
                # O caderno integral tambem fica acessivel para referencias nao padronizadas.
                pages = list(range(start_page, page_number + 1))
                image = f"/questoes/etec/{edition}/pagina-{page_number:02}.webp"
                content = {"modo": "pagina_original", "pagina": page_number,
                           "paginas": [{"numero": p, "imagem": f"/questoes/etec/{edition}/pagina-{p:02}.webp"} for p in pages],
                           "apoioAnterior": [{"numero": p, "imagem": f"/questoes/etec/{edition}/pagina-{p:02}.webp"}
                                              for p in range(max(2, start_page - 2), start_page)],
                           "numeroOriginal": number, "caixaTitulo": pos["caixa"],
                           "larguraPagina": float(document[page_number - 1].rect.width),
                           "alturaPagina": float(document[page_number - 1].rect.height),
                           "urlProva": source["prova"] + f"#page={page_number}"}
                # A pagina original e a referencia visual, nao se atribui materia/dificuldade
                # por suposicao. O texto extraido serve para pesquisa, com escopo explicito.
                question = {"numero": number, "anulada": answer == "ANULADA", "gabarito": None if answer == "ANULADA" else answer,
                            "enunciado": f"ETEC {edition}, questao {number:02}. Consulte a pagina original {page_number}.\n\n"
                                         + page_text[page_number],
                            "imagem": image, "conteudo": content,
                            "hashFonte": hashlib.sha256((source_hash + f":{number}").encode()).hexdigest()}
                questions.append(question)
            exams.append({**source, "codigo": f"ETEC-{source['ano']}-S{source['semestre']}-REGULAR", "questoes": questions})
            audit.append({"edicao": edition, "questoes": len(questions), "anuladas": [q["numero"] for q in questions if q["anulada"]],
                          "paginas": last_page - 1, "numeracaoConferida": True, "gabaritoConferido": True})
            print(f"{edition}: {len(questions)} questoes; anuladas: {audit[-1]['anuladas']}", flush=True)
    result = {"formato": 1, "tipo": "ETEC", "inicio": manifest["inicio"], "fim": manifest["fim"], "edicoes": exams}
    output = ROOT / "acervo/etec/questoes.json"
    output.write_text(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    total = sum(x["questoes"] for x in audit)
    cancelled = sum(len(x["anuladas"]) for x in audit)
    summary = {"edicoes": audit, "total": total, "anuladas": cancelled, "ativas": total - cancelled,
               "diasCom40Ineditas": (total - cancelled) // 40, "ineditasRestantes": (total - cancelled) % 40,
               "apresentacao": "Paginas originais; a interface identifica a questao a responder. Podem aparecer questoes vizinhas.",
               "limiteValidacao": "Conferencia automatica de numeracao e gabarito; sem classificacao pedagogica individual."}
    (output.parent / "relatorio.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    return summary


if __name__ == "__main__":
    print(json.dumps(extract(json.loads((ROOT / "acervo/etec/manifesto.json").read_text())), ensure_ascii=False, indent=2))
