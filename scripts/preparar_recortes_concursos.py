#!/usr/bin/env python3
"""Recorta o caderno original; coordenadas e vínculos de apoio ficam auditáveis."""
from pathlib import Path
import hashlib
import json
import re
import gzip
import zipfile
import fitz
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / 'tmp/pdfs/concursos-recortes'
SOURCES = ROOT / 'acervo/concursos/fontes-recortes.json'

def lines(page):
    return [("".join(s['text'] for s in l['spans']).strip(), fitz.Rect(l['bbox']))
            for b in page.get_text('dict')['blocks'] for l in b.get('lines', [])]

def body_lines(page, source, col):
    left, right = source['limites'][col * 2:col * 2 + 2]
    return sorted([(t, b) for t, b in lines(page)
                   if left - 2 <= b.x0 < right and source['topo'] - 2 <= b.y0 < source['rodape']
                   and t and 'pciconcursos' not in t.lower() and not t.startswith('pcimarkpci')], key=lambda v: (round(v[1].y0, 1), v[1].x0))

def markers(doc, source):
    result = []
    expected = 1
    for p in doc:
        for col in range(source['colunas']):
            for t, b in body_lines(p, source, col):
                normalized = t.upper().replace('QUESTA0', 'QUESTÃO')
                m = re.match(r'^QUEST[ÃA]O\s*(\d{1,2})\b', normalized)
                if not m and not source['slug'] in ['olegario-2011', 'montes-claros-2010', 'papagaios-2009']:
                    m = re.match(r'^(\d{1,2})\s*[.\-–](?:\s|$)', normalized)
                if m and int(m[1]) == expected and abs(b.x0 - source['limites'][col * 2]) < 6:
                    # Equações alinhadas à primeira linha podem subir acima do número.
                    box = list(b)
                    peers = [r for text, r in body_lines(p, source, col) if text]
                    while True:
                        top = min([box[1]] + [r.y0 for r in peers if r.y0 < box[1] < r.y1])
                        if top == box[1]: break
                        box[1] = top
                    result.append({'numero': expected, 'pagina': p.number + 1, 'coluna': col, 'caixa': box})
                    expected += 1
    if expected - 1 != source['total']:
        raise ValueError(f"Numeração incompleta: {source['slug']}: {expected-1}/{source['total']}")
    return result

def preparar_fontes():
    allowed={p['slug']+'/'+name for p in json.loads(SOURCES.read_text())['provas'] for name in ['prova.pdf','gabarito.pdf']}
    with zipfile.ZipFile(ROOT/'acervo/concursos/fontes-recortes.zip') as archive:
        if set(archive.namelist()) != allowed: raise ValueError('Arquivo de fontes inesperado')
        for name in sorted(allowed):
            target=WORK/name
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(archive.read(name))

def index_sources():
    report = {}
    for source in json.loads(SOURCES.read_text())['provas']:
        doc = fitz.open(WORK/source['slug']/'prova.pdf')
        found = markers(doc, source)
        report[source['slug']] = found
        print(source['slug'], len(found), 'questões; início', found[0], flush=True)
    target = WORK/'marcadores.json'
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    return report

def regions_between(source, start, end):
    slots = source['colunas']
    first = (start['pagina']-1)*slots+start['coluna']
    last = (end['pagina']-1)*slots+end['coluna']
    for slot in range(first,last+1):
        page,col=divmod(slot,slots)
        y0=start['caixa'][1]-2 if slot==first else source['topo']
        y1=end['caixa'][1]-3 if slot==last else source['rodape']
        if y1>y0+2:yield [page+1,col,y0,y1]

def build():
    layout=json.loads((ROOT/'acervo/concursos/layout-recortes.json').read_text())
    keys=json.loads((ROOT/'acervo/concursos/gabaritos-recortes.json').read_text())
    exams=[];audit=[]
    for source in json.loads(SOURCES.read_text())['provas']:
        code=source['slug']; doc=fitz.open(WORK/code/'prova.pdf')
        positions=markers(doc,source)
        settings=layout.get(code,{})
        contexts=settings.get('apoios',[])
        folder=ROOT/'src/main/resources/static/questoes/concursos'/('pci-'+code)
        folder.mkdir(parents=True,exist_ok=True)
        # Oculta apenas o cabeçalho de acesso no caderno completo. Redaction
        # reescreve glifos matemáticos sem Unicode e pode corromper as fórmulas.
        pdf=fitz.open(WORK/code/'prova.pdf')
        for p in pdf:
            if p.search_for('pcimarkpci'):
                box=p.cropbox
                p.set_cropbox(fitz.Rect(box.x0,max(box.y0,11),box.x1,box.y1))
        pdf.save(folder/'prova.pdf',garbage=4,deflate=True,no_new_id=True)
        pdf.close()
        def render(region,name,kind,trim=True):
            pnum,col,y0,y1=region;p=doc[pnum-1]
            left,right=source['limites'][col*2:col*2+2]
            rect=fitz.Rect(left,y0,right,y1)
            if trim:
                ls=[b for t,b in body_lines(p,source,col) if y0<=b.y0<y1 and t]
                images=[fitz.Rect(b['bbox']) for b in p.get_text('dict')['blocks'] if b['type']==1 and fitz.Rect(b['bbox']).intersects(rect) and fitz.Rect(b['bbox']).get_area() < p.rect.get_area()*.8]
                if not ls and not images:return None
                if not images:rect.y1=min(y1,max(b.y1 for b in ls)+3)
            pix=p.get_pixmap(matrix=fitz.Matrix(2.5,2.5),clip=rect,alpha=False)
            path=folder/(name+'.webp')
            Image.frombytes('RGB',(pix.width,pix.height),pix.samples).save(path,'WEBP',quality=92,method=4)
            return {'tipo':kind,'imagem':f'/questoes/concursos/pci-{code}/{name}.webp',
                    'pagina':pnum,'caixa':[round(v,3) for v in rect],
                    'larguraOriginal':round(rect.width,3),'largura':pix.width,'altura':pix.height}
        support_map={};all_contexts=[]
        for i,context in enumerate(contexts):
            rendered=[render(reg,f'apoio-{i+1:02}-{j+1}','apoio') for j,reg in enumerate(context['regioes'])]
            rendered=[x for x in rendered if x]
            if len(rendered)!=len(context['regioes']):raise ValueError(f'Apoio vazio: {code}/{i}')
            for n in context['questoes']:support_map.setdefault(n,[]).extend(rendered)
            all_contexts.extend(context['regioes'])
        questions=[]
        for i,pos in enumerate(positions):
            number=pos['numero'];start={**pos,'caixa':list(pos['caixa'])}
            adjustment=settings.get('ajustes',{}).get(str(number),{})
            start['caixa'][1]=adjustment.get('inicioY',start['caixa'][1])
            end=positions[i+1] if i+1<len(positions) else {'pagina':len(doc),'coluna':source['colunas']-1,'caixa':[0,source['rodape']+3,0,0]}
            ranges=list(regions_between(source,start,end))
            cropped=[];text=[]
            for j,reg in enumerate(ranges):
                for context in all_contexts:
                    if reg[:2]==context[:2]:
                        if context[2]<=reg[2]<context[3]:reg[2]=context[3]+1
                        if reg[2]<context[2]<reg[3]:reg[3]=context[2]-3
                # Não inclui títulos da seção seguinte nem instruções finais.
                for t,b in body_lines(doc[reg[0]-1],source,reg[1]):
                    if reg[2]+10 < b.y0 < reg[3] and re.search(r'\d[ªa]\s*Parte|^PARTE\s+[IVX]+|^PROVA DE|^QUESTÃO DISCURSIVA|^ATENÇÃO$|^MATEMÁTICA$',t,re.I):
                        reg[3]=b.y0-4
                if 'fimY' in adjustment and j==len(ranges)-1:reg[3]=min(reg[3],adjustment['fimY'])
                if reg[3]<=reg[2]+2:continue
                fragment=render(reg,f'questao-{number:02}-{j+1}','questao')
                if fragment:
                    cropped.append(fragment)
                    pnum,col,y0,y1=reg
                    text.extend(t for t,b in body_lines(doc[pnum-1],source,col) if y0<=b.y0<y1)
            if not cropped:raise ValueError(f'Questão sem recorte: {code}/{number}')
            statement='\n'.join(text).strip()
            labels=sorted(set(re.findall(r'\b([A-Ea-e])\)',statement)))
            letters=''.join(sorted(set(x.upper() for x in labels)))
            if letters not in ['ABCD','ABCDE']:raise ValueError(f'Alternativas incompletas: {code}/{number}: {letters}')
            answer=keys[code][str(number)]
            if answer and answer not in letters:raise ValueError('Gabarito incompatível')
            content={'modo':'recorte_original','pagina':pos['pagina'],'numeroOriginal':number,'gabaritoPreliminar':source['gabaritoPreliminar'],
                     'urlProva':f'/questoes/concursos/pci-{code}/prova.pdf#page={pos["pagina"]}',
                     'recortes':support_map.get(number,[])+cropped}
            questions.append({'numero':number,'anulada':answer is None,'gabarito':answer,'enunciado':statement,
                'alternativas':[{'letra':a,'texto':a} for a in letters], 'conteudo':content,
                'hashFonte':hashlib.sha256((source['codigo']+':'+str(number)+':'+json.dumps(content,sort_keys=True)).encode()).hexdigest()})
        exams.append({**source,'edicao':str(source['ano']),'caderno':'CADERNO ORIGINAL PCI','questoes':questions})
        published={r['imagem'].lstrip('/') for q in questions for r in q['conteudo']['recortes']}
        published.add(f'questoes/concursos/pci-{code}/prova.pdf')
        with zipfile.ZipFile(ROOT/'acervo/concursos'/f'recortes-{code}.zip','w') as archive:
            for name in sorted(published):
                info=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0))
                info.external_attr=0o644 << 16
                archive.writestr(info,(ROOT/'src/main/resources/static'/name).read_bytes())
        audit.append({'codigo':source['codigo'],'questoes':len(questions),'anuladas':[q['numero'] for q in questions if q['anulada']],
            'provaSha256':hashlib.sha256((folder/'prova.pdf').read_bytes()).hexdigest(),
            'gabaritoSha256':hashlib.sha256((WORK/code/'gabarito.pdf').read_bytes()).hexdigest()})
        print(code,len(questions),'recortadas',flush=True)
    dataset={'formato':2,'tipo':'CONCURSO','provas':exams}
    raw=json.dumps(dataset,ensure_ascii=False,separators=(',',':')).encode()
    (ROOT/'acervo/concursos/questoes-recortadas.json.gz').write_bytes(gzip.compress(raw,mtime=0))
    (ROOT/'acervo/concursos/validacao-recortes.json').write_text(json.dumps({'status':'PREPARADO','provas':audit},ensure_ascii=False,indent=2))
    return dataset

if __name__ == '__main__':
    import sys
    preparar_fontes()
    build() if '--build' in sys.argv else index_sources()
