#!/usr/bin/env python3
"""Conferência por posição das tabelas; imagens marcadas exigem dupla conferência."""
from pathlib import Path
import json,re
import fitz
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'tmp/pdfs/concursos-recortes'

def grid_key(image, columns, ys, expected):
    kind=str(image)
    image=Image.open(image).convert('RGB')
    result=[]
    for xs,y0,dy in zip(columns,ys,[28.8,28.8] if 'mato' in kind else [28.1,28.1]):
        for i in range(16):
            y=round(y0+dy*i)
            scores=[]
            for x in xs:
                pixels=list(image.crop((x-5,y-4,x+5,y+4)).getdata())
                scores.append(sum(max(c)<90 for c in pixels)/len(pixels))
            best=max(range(4),key=lambda j:scores[j])
            if scores[best]<.65 or sum(v>.5 for v in scores)!=1:
                raise ValueError(f'Marcação ambígua na questão {len(result)+1}: {scores}')
            result.append('ABCD'[best])
    if ''.join(result)!=expected:
        raise ValueError(f'Dupla conferência divergente: {"".join(result)} / {expected}')
    return {i+1:a for i,a in enumerate(result)}

def key(source):
    code=source['slug']; page=fitz.open(WORK/code/'gabarito.pdf')[source['paginaGabarito']-1]
    if code in ['mato-grosso-2010','sao-francisco-2010']:
        page.get_pixmap(matrix=fitz.Matrix(2,2)).save(WORK/code/f'key-{source["paginaGabarito"]}.png')
    if code=='mato-grosso-2010':
        return grid_key(WORK/code/'key-6.png',[[430,468,504,541],[653,690,727,764]],[825,825], 'CDABADBDCBDADAACACABDCAAACDDACCA')
    if code=='sao-francisco-2010':
        return grid_key(WORK/code/'key-3.png',[[442,477,511,547],[655,690,725,760]],[679,679], 'DDDBCADBDDCADBCC AADDDBDCDCCBBACB'.replace(' ',''))
    t=page.get_text()
    if code in ['aedecca-2010','primavera-2009','santa-cruz-2010']:
        pairs=re.findall(r'\b(\d{2})\s*[–-]?\s*([A-E*])\b' if code=='santa-cruz-2010' else r'\b(\d{2})\s*[–-]\s*([A-E*])',t)
        result={int(n):None if a=='*' else a for n,a in pairs}
    else:
        words=page.get_text('words')
        if code=='rio-serra-2010':
            top=page.search_for('AGENTE CULTURAL')[0].y1
            words=[w for w in words if w[1]>top]
        elif code=='casserengue-2009':
            top=page.search_for('AGENTE ADMINISTRATIVO')[0].y1
            bottom=page.search_for('AGENTE COMUNITARIO')[0].y0
            words=[w for w in words if top<w[1]<bottom]
        else:
            words=[w for w in words if w[1]>290 and (code!='montes-claros-2010' or w[1]<375)]
        letters=[w for w in words if re.fullmatch('[A-E*]',w[4])]
        result={}
        for w in words:
            if not re.fullmatch(r'\d{2}',w[4]): continue
            n=int(w[4])
            if not 1<=n<=source['total']:continue
            x,y=(w[0]+w[2])/2,(w[1]+w[3])/2
            candidates=[]
            for a in letters:
                ax,ay=(a[0]+a[2])/2,(a[1]+a[3])/2
                if code in ['papagaios-2009','casserengue-2009']:
                    if abs(ay-y)<3 and 0<ax-x<100:candidates.append((ax-x+abs(ay-y)*10,a[4]))
                elif abs(ax-x)<4 and 0<ay-y<30:candidates.append((ay-y+abs(ax-x)*10,a[4]))
            if not candidates: raise ValueError(f'Sem alternativa: {code}/{n}')
            answer=min(candidates)[1]
            if n in result and result[n]!=answer:raise ValueError('Número duplicado divergente')
            result[n]=None if answer=='*' else answer
    if set(result)!=set(range(1,source['total']+1)):raise ValueError(f'Gabarito incompleto: {code}: {len(result)}')
    return result

if __name__=='__main__':
    result={}
    for source in json.loads((ROOT/'acervo/concursos/fontes-recortes.json').read_text())['provas']:
        result[source['slug']]=key(source)
        print(source['slug'],len(result[source['slug']]),''.join(a or '*' for a in result[source['slug']].values()))
    (ROOT/'acervo/concursos/gabaritos-recortes.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
