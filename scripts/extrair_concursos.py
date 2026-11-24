"""Extrai os dez cadernos, mantendo PDF, numeração e gabarito rastreáveis."""
import hashlib
import gzip
import json
from pathlib import Path
import re
import shutil
import sys
import fitz

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "tmp/pdfs/concursos"
EXPECTED = {"INSS":120,"TJSP":100,"PF":120,"FORTALEZA":80,"TJRN":60,
            "CAMPINAS":50,"DPE-RS":70,"UFRJ":50,"BNB":120,"CAIXA":60}


def lines(page):
    return [{"text":"".join(s["text"] for s in l["spans"]).strip(),
             "box":list(l["bbox"]),"size":max(s["size"] for s in l["spans"]),
             "font":l["spans"][0]["font"],"page":page.number+1}
            for b in page.get_text("dict")["blocks"] for l in b.get("lines",[]) if l["spans"]]


def key_table(text):
    out={}; previous=[]
    for line in text.splitlines():
        t=line.strip().split()
        if t and t[0] in ("Item","Gabarito"): t=t[1:]
        if t and all(re.fullmatch(r"\d+",v) for v in t): previous=[int(v) for v in t]
        elif t and all(re.fullmatch(r"[A-EX*0]",v) for v in t) and previous:
            if len(t)!=len(previous): raise ValueError(("Linha de gabarito incompleta",previous,t))
            for n,a in zip(previous,t):
                if n: out[n]=a if a not in ("X","*") else None
            previous=[]
    return out


def key_pairs(text):
    return {int(n):None if a in ("N","ANULADA") else a
            for n,a in re.findall(r"(?<!\d)(\d{1,3})\s*-?\s+(ANULADA|[A-EN])\b",text)}


def load_key(code):
    folder=WORK/code
    text=(folder/"gabarito.txt").read_text()
    if code.startswith("PF-"):
        result=key_table((folder/"gabarito-basicos.txt").read_text()); result.update(key_table(text)); return result
    if code.startswith(("INSS-","BNB-")):return key_table(text)
    if code.startswith("DPE-"):return key_table(text.split("TIPO 4",1)[1].split("(*)",1)[0])
    if code.startswith("TJRN-"):return key_table(text.split("TIPO 1",1)[1].split("(*)",1)[0])
    if code.startswith("FORTALEZA-"):return key_table(text)
    if code.startswith("TJSP-"):
        text=(folder/"gabarito-final.txt").read_text();return key_pairs(text.split("VERSÃO 3",1)[1].split("VERSÃO 4",1)[0])
    if code.startswith("CAMPINAS-"):
        result=key_pairs(text.split("Versão 1",1)[1].split("Versão 2",1)[0])
        # Publicação de resultados após recursos, 11/10/2019, seção 3, página 8.
        result[47]=None
        return result
    if code.startswith("CAIXA-"):return key_pairs(text.split("GABARITO 1",1)[1].split("GABARITO 2",1)[0])
    return key_pairs(text)


def extract_exam(meta):
    code=meta["codigo"]; kind=next(k for k in EXPECTED if code.startswith(k+"-"));expected=EXPECTED[kind]
    key=load_key(code)
    if set(key)!=set(range(1,expected+1)):raise ValueError((code,"gabarito",len(key),set(range(1,expected+1))-set(key)))
    doc=fitz.open(WORK/code/"prova.pdf")
    all_lines=[]; marks=[]
    for page in doc:
        if page.number==0 and kind not in ("INSS","BNB"):continue
        page_lines=lines(page)
        for line in page_lines:
            x,y,x2,y2=line["box"];text=line["text"]
            if re.match(r"^(?:Técnico Judiciário - Área|Técnico - Área Administrativa|Tipo [1-4].*Página|PMCP\d|TJSP\d|CARGO 9:|Confidencial até)",text):continue
            if text in ("\uf044\uf020","\uf044","\uf020"):continue
            if text.isdigit() and page.rect.width*.45<x<page.rect.width*.55 and y>page.rect.height-65:continue
            col=0 if x<page.rect.width/2 else 1
            # Margens excluem cabeçalhos/rodapés; a ordem preserva as duas colunas.
            top=20 if kind in ("TJSP","CAMPINAS") else 45 if kind in ("INSS","BNB","PF") else 50
            bottom=page.rect.height-(44 if kind in ("DPE-RS","TJRN") else 35)
            if not top<=y<bottom:continue
            line["col"]=col;line["order"]=(page.number,col,round(y,1),x)
            match=None
            if kind in ("TJSP","CAMPINAS","FORTALEZA","UFRJ"):
                match=re.match(r"^(\d{1,3})\.\s+",text)
                if not ((col==0 and x<50) or (col==1 and x<320)):match=None
            elif kind=="INSS":
                match=re.match(r"^(\d{1,3})(?:\s+|$)",text)
                if not ((col==0 and x<30) or (col==1 and x<305)):match=None
            else:
                match=re.match(r"^(\d{1,3})(?:\s+|$)",text) if kind in ("BNB","PF") else re.fullmatch(r"(\d{1,3})",text)
                if kind in ("DPE-RS","TJRN"):
                    if not ("Bold" in line["font"] and (abs(x-42.6)<1 or abs(x-311.7)<1)):match=None
                elif kind=="CAIXA":
                    if not (abs(line["size"]-11)<.2 and (abs(x-28.3)<1 or abs(x-311.8)<1 or abs(x-311.1)<1)):match=None
                else:
                    valid_size=(8<=line["size"]<8.3) or (bool(re.match(r"^1\d\d\s",text)) and 9.8<line["size"]<10.1)
                    if not (valid_size and (abs(x-28.3)<1 or abs(x-304.4)<1)):match=None
            if match and 1<=int(match[1])<=expected:
                line["number"]=int(match[1]);marks.append(line)
            all_lines.append(line)
    for mark in marks:
        if re.fullmatch(r"\d{1,3}",mark["text"]):
            nearby=[l["box"][1] for l in all_lines if l["page"]==mark["page"] and l["col"]==mark["col"] and abs(l["box"][1]-mark["box"][1])<2]
            mark["order"]=(mark["page"]-1,mark["col"],min(nearby)-.1,mark["box"][0])
    all_lines.sort(key=lambda l:l["order"]);marks.sort(key=lambda l:l["order"])
    nums=[l["number"] for l in marks]
    if nums!=list(range(1,expected+1)):raise ValueError((code,"marcadores",len(nums),"faltam",set(range(1,expected+1))-set(nums),"duplicados",[n for n in set(nums) if nums.count(n)>1]))
    questions=[]
    for i,start in enumerate(marks):
        end=marks[i+1]["order"] if i+1<len(marks) else (999,0,0,0)
        chunk=[l for l in all_lines if start["order"]<=l["order"]<end]
        # Uma redação e páginas de rascunho não fazem parte da última questão.
        if i==len(marks)-1:
            chunk=[l for l in chunk if l["page"]==start["page"]]
        text="\n".join(l["text"] for l in chunk)
        text=re.sub(r"^\d{1,3}\.?\s*", "", text).strip()
        if kind=="PF":text=text.split("JUSTIFICATIVA",1)[0].strip()
        if kind in ("INSS","BNB","PF"):
            alternatives=[{"letra":"C","texto":"Certo"},{"letra":"E","texto":"Errado"}]
            statement=text
        else:
            pattern=r"(?m)^\(?([A-E])\)\s*"
            options=list(re.finditer(pattern,text))
            labels=[m[1] for m in options]
            expected_labels=list("ABCD" if kind=="FORTALEZA" else "ABCDE")
            if labels!=expected_labels:raise ValueError((code,start["number"],"alternativas",labels,text[:400]))
            statement=text[:options[0].start()].strip()
            alternatives=[{"letra":m[1],"texto":text[m.end():(options[j+1].start() if j+1<len(options) else len(text))].strip()}
                          for j,m in enumerate(options)]
        if not statement or any(not a["texto"] for a in alternatives):raise ValueError((code,start["number"],"texto vazio"))
        q={"numero":start["number"],"enunciado":statement,"alternativas":alternatives,
           "gabarito":key[start["number"]],"anulada":key[start["number"]] is None,
           "conteudo":{"modo":"pdf_original","numeroOriginal":start["number"],"pagina":start["page"],
                       "urlProva":meta["url_prova"]+"#page="+str(start["page"]),
                       "pdf":"/questoes/concursos/"+code.lower()+"/prova.pdf#page="+str(start["page"]),
                       "formato":"CERTO_ERRADO" if kind in ("INSS","BNB","PF") else "MULTIPLA_ESCOLHA"}}
        q["hashFonte"]=hashlib.sha256(json.dumps(q,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
        questions.append(q)
    apoio=""
    for q in questions:
        if apoio:q["conteudo"]["textoApoio"]=apoio
        if len(q["alternativas"])<4:continue
        last=q["alternativas"][-1]
        match=re.search(r"(?im)^(?:texto\s+\d|leia(?:\s|-)|conhecimentos\s|raciocínio\s+lógico|r\s*a\s*s\s*c\s*u\s*n\s*h\s*o)",last["texto"])
        if match and match.start()>0:
            apoio=last["texto"][match.start():].strip()
            last["texto"]=last["texto"][:match.start()].strip()
    # O hash cobre o registro final, incluindo a separação de textos de apoio.
    for q in questions:
        del q["hashFonte"]
        q["hashFonte"]=hashlib.sha256(json.dumps(q,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
    key_url=meta["url_gabarito"]
    if kind=="TJSP":key_url="https://www.novaconcursos.com.br/laravel/blog/pdf/portal/stream/2025/05/gabarito-tj-sp-2023-1.pdf?download=1"
    return {"codigo":code,"nome":meta["nome"],"urlGabarito":key_url,"caderno":("PROVA 1 - GABARITO 1" if kind=="CAIXA" else "VERSAO 1" if kind=="CAMPINAS" else meta["caderno"]),"provaSha256":hashlib.sha256((WORK/code/"prova.pdf").read_bytes()).hexdigest(),"questoes":questions}


def preparar_pdf(code):
    source=WORK/code/"prova.pdf"
    target=ROOT/"src/main/resources/static/questoes/concursos"/code.lower()/"prova.pdf"
    target.parent.mkdir(parents=True,exist_ok=True)
    if not code.startswith("PF-"):
        shutil.copyfile(source,target)
        return
    # A cópia oficial da PF tem justificativas. Removemos apenas essas partes
    # dos blocos, preservando integralmente textos de apoio e assertivas.
    doc=fitz.open(source)
    removed=0
    for page in doc:
        for block in page.get_text("dict")["blocks"]:
            text="\n".join("".join(s["text"] for s in l["spans"]) for l in block.get("lines",[]))
            if "JUSTIFICATIVA" not in text:continue
            for rect in page.search_for("JUSTIFICATIVA",clip=fitz.Rect(block["bbox"])):
                page.add_redact_annot(fitz.Rect(rect.x0-.2,rect.y0,block["bbox"][2]+.2,rect.y1),fill=(1,1,1))
                if block["bbox"][3]>rect.y1:
                    page.add_redact_annot(fitz.Rect(block["bbox"][0]-.2,rect.y1,block["bbox"][2]+.2,block["bbox"][3]+.2),fill=(1,1,1))
                removed+=1
        page.apply_redactions(images=0,graphics=0)
    if removed!=120:raise ValueError("Quantidade inesperada de justificativas PF")
    doc.save(target,garbage=4,deflate=True)
    if any("JUSTIFICATIVA" in p.get_text() for p in fitz.open(target)):raise ValueError("Resposta residual no caderno PF")


def main():
    rows=json.loads((WORK/"fontes.json").read_text());result=[]
    for row in rows:
        exam=extract_exam(row);result.append(exam)
        if "--somente-dados" not in sys.argv:preparar_pdf(row["codigo"])
        print(exam["codigo"],len(exam["questoes"]),"anuladas",[q["numero"] for q in exam["questoes"] if q["anulada"]],flush=True)
    out=ROOT/"acervo/concursos/questoes.json";out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps({"formato":1,"tipo":"CONCURSO","provas":result},ensure_ascii=False,separators=(",",":")))
    out.with_suffix(".json.gz").write_bytes(gzip.compress(out.read_bytes(),mtime=0))


if __name__=="__main__":main()
