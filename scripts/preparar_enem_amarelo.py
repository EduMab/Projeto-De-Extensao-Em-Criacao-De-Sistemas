#!/usr/bin/env python3
"""Acervo ENEM amarelo 2017–2026. Preparação offline; nunca acessa o banco.

Cada caderno físico é armazenado uma vez. As cinco questões de espanhol têm
chave própria, preservando numeroOriginal e idioma nos metadados. As 85 questões
comuns do primeiro dia não são duplicadas. Estado PREVIA até revisão humana.
"""
from pathlib import Path
from collections import Counter
import argparse, concurrent.futures, gzip, hashlib, json, re, unicodedata, urllib.request, zipfile
import fitz
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ACERVO = ROOT / 'acervo/enem'
WORK = ROOT / 'tmp/pdfs/enem'
OUT = ROOT / 'tmp/enem-assets'

def normalized(text):
    return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode().upper()

def source_path(year, day, kind):
    caderno = 2 if day == 1 else 5
    if year >= 2020:
        return f'enem/provas_e_gabaritos/{year}_{"PV" if kind == "dia" else "GB"}_impresso_D{day}_CD{caderno}.pdf'
    if year == 2019:
        if kind == 'gab': return f'educacao_basica/enem/gabaritos/2019/gabarito_{day}_dia_caderno_{caderno}_amarelo_aplicacao_regular.pdf'
        return ('educacao_basica/enem/provas/2019/caderno_de_questoes_1_dia_caderno_2_amarelo_aplicacao_regular.pdf'
                if day == 1 else 'educacao_basica/enem/provas/2019/2019_PV_impresso_D2_CD5.pdf')
    if year == 2018:
        return (f'educacao_basica/enem/provas/2018/{day}DIA_{caderno:02}_AMARELO_BAIXA.pdf' if kind == 'dia'
                else f'educacao_basica/enem/gabaritos/2018/GAB_ENEM_2018_DIA_{day}_AMARELO.pdf')
    date = '5112017' if day == 1 else '12112017'
    return f'educacao_basica/enem/{"provas" if kind == "dia" else "gabaritos"}/2017/cad_{caderno}_{"prova" if kind == "dia" else "gabarito"}_amarelo_{date}.pdf'

def download():
    WORK.mkdir(parents=True, exist_ok=True)
    def one(task):
        year, day, kind = task
        p = WORK / f'{year}-{kind}{day}.pdf'
        if not p.exists():
            url = 'https://download.inep.gov.br/' + source_path(year, day, kind)
            with urllib.request.urlopen(url, timeout=90) as response: data = response.read()
            if not data.startswith(b'%PDF'): raise ValueError(f'Fonte não é PDF: {url}')
            p.write_bytes(data)
        return p.name
    tasks = [(y,d,k) for y in range(2017,2027) for d in (1,2) for k in ('dia','gab')]
    for name in concurrent.futures.ThreadPoolExecutor(6).map(one,tasks): print(name, flush=True)

def page_lines(page):
    return [( ''.join(s['text'] for s in line['spans']).strip(), fitz.Rect(line['bbox']))
            for block in page.get_text('dict')['blocks'] for line in block.get('lines', [])]

def markers(doc, year, day):
    found=[]
    for page in doc:
        for text,box in page_lines(page):
            m=re.fullmatch(r'QUESTAO(\d{1,3})',re.sub(r'\s+','',normalized(text)))
            if not m: continue
            number=int(m[1]); col=int(box.x0 >= page.rect.width / 2)
            # O PDF oficial 2022 contém este texto invisível atrás da charge da Q5.
            # Conferido visualmente: não é uma questão visível nem deve cortar a charge.
            if (year,day,page.number+1,col,number)==(2022,1,3,0,6): continue
            found.append({'numeroOriginal':number,'pagina':page.number+1,'coluna':col,'caixa':list(box)})
    found.sort(key=lambda m:(m['pagina'],m['coluna'],m['caixa'][1]))
    expected=list(range(1,6))+list(range(1,91)) if day==1 else list(range(91,181))
    actual=[m['numeroOriginal'] for m in found]
    if actual != expected: raise ValueError(f'Marcadores incompletos/fora de ordem {year}/{day}: {actual}')
    for index,m in enumerate(found):
        m['idioma']='INGLES' if day==1 and index<5 else 'ESPANHOL' if day==1 and index<10 else None
        m['chave']=f"{m['numeroOriginal']:03}"+(('-'+m['idioma'].lower()) if m['idioma'] else '')
    return found

def answer_key(doc, day):
    words=[w for p in doc for w in p.get_text('words')]
    result={}
    for w in words:
        numbermatch=re.fullmatch(r'(\d{1,3})(\*)?',w[4])
        if not numbermatch:continue
        n=int(numbermatch[1])
        if not (1<=n<=90 if day==1 else 91<=n<=180):continue
        cy=(w[1]+w[3])/2
        nums=[v for v in words if re.fullmatch(r'\d{1,3}',v[4]) and abs((v[1]+v[3])/2-cy)<4 and v[0]>w[2]+3]
        limit=min([v[0] for v in nums]+[1000])
        columnnums=[a for a in words if re.fullmatch(r'\d{1,3}',a[4]) and abs(a[0]-w[0])<5]
        values=sorted([v for v in words if abs((v[1]+v[3])/2-cy)<9 and w[2]<v[0]<limit
            and re.fullmatch(r'[A-E]|[Aa][Nn][Uu][Ll][Aa][Dd][OoAa]|\*',v[4])
            and (not columnnums or min(columnnums,key=lambda a:abs((a[1]+a[3])/2-(v[1]+v[3])/2))==w)],key=lambda v:v[0])
        answers=[None if v[4].lower() in ('anulado','anulada') or v[4]=='*' else v[4] for v in values]
        if answers and all(a is None for a in answers):answers=[None]
        if not answers:
            if numbermatch[2]:answers=[None]
            else:continue
        if day==1 and n<=5:
            if len(answers)!=2:raise ValueError(f'Idiomas no gabarito {n}: {answers}')
            result[f'{n:03}-ingles'],result[f'{n:03}-espanhol']=answers
        else:
            if len(answers)!=1:raise ValueError(f'Gabarito ambíguo {n}: {answers}')
            result[f'{n:03}']=answers[0]
    expected=95 if day==1 else 90
    if len(result)!=expected:raise ValueError(f'Gabarito incompleto: {len(result)}/{expected}; chaves={sorted(result)}')
    return result

def area(number,day):
    if day==1:return 'Linguagens' if number<=45 else 'Ciências Humanas'
    return 'Ciências da Natureza' if number<=135 else 'Matemática'

def build(render=True):
    ACERVO.mkdir(parents=True,exist_ok=True)
    manifest=[];proofs=[];audit=[]
    for year in range(2017,2027):
      for day in (1,2):
        slug=f'enem-{year}-dia-{day}-amarelo'
        source=WORK/f'{year}-dia{day}.pdf';gab=WORK/f'{year}-gab{day}.pdf'
        doc=fitz.open(source);keydoc=fitz.open(gab)
        cover=normalized(doc[0].get_text())
        # Algumas capas têm o ano em curvas vetoriais. As 20 capas foram
        # conferidas visualmente; cor/ano também são conferidos no gabarito.
        keytitle=normalized(keydoc[0].get_text())
        if 'AMARELO' not in cover+normalized(doc[1].get_text()) or str(year) not in keytitle or 'AMARELO' not in keytitle:
            raise ValueError(f'Capa/gabarito incompatível: {slug}')
        key=answer_key(keydoc,day); positions=markers(doc,year,day)
        keydoc.close()
        # Limites físicos por caderno: preservam a coluna inteira sem rodapés/cabeçalhos.
        left=min(m['caixa'][0] for m in positions if m['coluna']==0)
        right=min(m['caixa'][0] for m in positions if m['coluna']==1)
        margin=left-3
        boundaries=[max(0,margin),right-7,right-2,doc[1].rect.width-margin]
        top=min(m['caixa'][1] for m in positions)-2
        bottom=doc[1].rect.height-(45 if year<=2019 else 35)
        folder=OUT/'questoes/enem'/slug;folder.mkdir(parents=True,exist_ok=True)
        questions=[];flags=[]
        cached={p.number:page_lines(p) for p in doc}
        footer=[b.y0 for p in doc for t,b in cached[p.number]
                if b.y0>p.rect.height*.85 and 'CADERNO' in normalized(t) and 'AMARELO' in normalized(t)]
        if footer:bottom=min(bottom,min(footer)-3)
        # Há páginas inteiras em coluna única (por exemplo, espanhol em 2025).
        # Só usamos largura total quando o texto atravessa o meio da página
        # e não existe questão iniciando na coluna direita.
        columns={}
        page_bounds={}
        shared={}
        editorial_pages=set()
        for p in doc:
            if any(re.match(r'^(INSTRUCOES PARA A REDACAO|PROPOSTA DE REDACAO)',normalized(t)) for t,b in cached[p.number]):
                editorial_pages.add(p.number)
            pm=[m for m in positions if m['pagina']==p.number+1]
            parity=[m for m in positions if m['pagina']%2==(p.number+1)%2]
            lm=[m['caixa'][0] for m in pm if m['coluna']==0] or [m['caixa'][0] for m in parity if m['coluna']==0]
            rm=[m['caixa'][0] for m in pm if m['coluna']==1] or [m['caixa'][0] for m in parity if m['coluna']==1]
            # As páginas pares/ímpares têm deslocamento de impressão diferente.
            lx=min(lm) if lm else left;rx=min(rm) if rm else right
            page_bounds[p.number]=[max(0,lx-3),rx-9,rx-3,p.rect.width-lx+3]
            crossing=[t for t,b in cached[p.number] if 115<b.y0<bottom and 8<b.height<35
                and b.x0<p.rect.width/2-65 and b.x1>p.rect.width/2+65
                and not normalized(t).startswith('ENEM') and 'CADERNO' not in normalized(t)]
            columns[p.number]=1 if crossing and not any(m['coluna']==1 for m in pm) else 2
            for t,b in cached[p.number]:
                match=re.search(r'TEXTO PARA AS QUESTOES DE (\d+) A (\d+)',normalized(t))
                if match:
                    if pm:raise ValueError(f'Apoio misturado a questões exige layout explícito: {slug}/{p.number+1}')
                    shared[p.number]={'questoes':list(range(int(match[1]),int(match[2])+1)),
                        'caixa':[page_bounds[p.number][0],b.y0-2,page_bounds[p.number][3],bottom],
                        'justificativa':t}
        slots=[(p.number,c) for p in doc for c in range(columns[p.number])]
        slot_index={pair:i for i,pair in enumerate(slots)}
        for index,start in enumerate(positions):
            n=start['numeroOriginal'];nxt=positions[index+1] if index+1<len(positions) else None
            first=slot_index[(start['pagina']-1,start['coluna'])]
            last=slot_index[(nxt['pagina']-1,nxt['coluna'])] if nxt else slot_index[(start['pagina']-1,columns[start['pagina']-1]-1)]
            fragments=[];texts=[];letters=[];regions=[]
            for slot in range(first,last+1):
                pnum,col=slots[slot]; page=doc[pnum]
                if pnum in shared or pnum in editorial_pages:continue
                x0,x1=page_bounds[pnum][col*2:col*2+2] if columns[pnum]==2 else [page_bounds[pnum][0],page_bounds[pnum][3]]
                y0=start['caixa'][1]-2 if slot==first else top
                y1=nxt['caixa'][1]-3 if nxt and slot==last else bottom
                if y1<=y0+3:continue
                lines=[(t,b) for t,b in cached[pnum] if x0-2<=b.x0<x1 and y0<=b.y0<y1 and t]
                # Não captura títulos de idioma/área, proposta de redação ou rascunho seguintes.
                for text,box in lines:
                    nt=normalized(text)
                    if (slot!=first or box.y0>y0+20) and (re.match(r'^QUESTOES\s+DE\s+\d',nt) or re.match(r'^LINGUAGENS,? CODIGOS E SUAS TECNOLOGIAS',nt) or nt.startswith('PROPOSTA DE REDACAO') or nt=='RASCUNHO' or nt.startswith('CIENCIAS HUMANAS') or nt.startswith('CIENCIAS DA NATUREZA') or nt.startswith('MATEMATICA E SUAS TECNOLOGIAS')):
                        y1=min(y1,box.y0-3)
                if y1<=y0+3:continue
                lines=[(t,b) for t,b in lines if b.y0<y1]
                # Ignora camadas técnicas de marca d'água e cabeçalho; não redesenha o original.
                lines=[(t,b) for t,b in lines if not t.startswith('*') and not re.match(r'^(ENEM\s*\d{4}){2,}',re.sub(r'\s+','',normalized(t))) and b.width>0]
                if not lines:continue
                # O fim só é aparado depois do conteúdo: figuras e tabelas vetoriais
                # permanecem dentro do retângulo completo até a próxima questão.
                rect=fitz.Rect(x0,y0,x1,y1)
                pix=page.get_pixmap(matrix=fitz.Matrix(2.2,2.2),clip=rect,alpha=False) if render else None
                if render:
                    im=Image.frombytes('RGB',(pix.width,pix.height),pix.samples)
                    # Remove somente branco periférico; nunca remove texto do enunciado.
                    from PIL import ImageChops
                    diff=ImageChops.difference(im,Image.new('RGB',im.size,'white')).convert('L').point(lambda x:255 if x>28 else 0)
                    bbox=diff.getbbox()
                    if bbox:
                        bbox=(max(0,bbox[0]-5),max(0,bbox[1]-5),min(im.width,bbox[2]+5),min(im.height,bbox[3]+5))
                        im=im.crop(bbox)
                    name=f'questao-{start["chave"]}-{len(fragments)+1}.webp'
                    im.save(folder/name,'WEBP',quality=92,method=4)
                else:name=f'questao-{start["chave"]}-{len(fragments)+1}.webp'
                fragments.append({'tipo':'questao','imagem':f'/questoes/enem/{slug}/{name}',
                    'pagina':pnum+1,'caixa':[round(v,3) for v in rect],
                    'larguraOriginal':round(rect.width,3)})
                regions.append([pnum+1,col,round(y0,3),round(y1,3)])
                texts.extend(t for t,b in sorted(lines,key=lambda v:(round(v[1].y0,1),v[1].x0)))
                for t,b in lines:
                    match=re.match(r'^([A-E])(?:\s|$)',t)
                    if match:letters.append(match[1])
            if not fragments:raise ValueError(f'Sem recortes {slug}/{start["chave"]}')
            supports=[]
            for pnum,support in shared.items():
                if n not in support['questoes'] or start['idioma']:continue
                name=f'apoio-pagina-{pnum+1:02}.webp'
                supports.append({'tipo':'apoio','imagem':f'/questoes/enem/{slug}/{name}',
                    'pagina':pnum+1,'caixa':[round(v,3) for v in support['caixa']],
                    'larguraOriginal':round(support['caixa'][2]-support['caixa'][0],3),
                    'necessario':True,'justificativa':support['justificativa']})
            fragments=supports+fragments
            text='\n'.join(texts)
            labelset=''.join(sorted(set(letters)))
            if labelset!='ABCDE':flags.append({'questao':start['chave'],'motivo':'conferir alternativas na imagem','letrasExtraidas':labelset})
            if re.search(r'(?i)texto[s]?\s+(?:a\s+seguir\s+)?para\s+(?:responder\s+)?(?:a[s]?\s+)?quest',text):
                flags.append({'questao':start['chave'],'motivo':'conferir texto compartilhado'})
            content={'modo':'recorte_original','numeroOriginal':n,'idioma':start['idioma'],'area':area(n,day),
                'dia':day,'cor':'AMARELO','urlProva':f'/questoes/enem/{slug}/prova.pdf#page={start["pagina"]}',
                'apoioSeparado':bool(supports),'recortes':fragments}
            # Índice interno único; a numeração impressa fica explícita em numeroOriginal.
            internal=n if start['idioma']!='ESPANHOL' else 90+n
            hashsource=hashlib.sha256((hashlib.sha256(source.read_bytes()).hexdigest()+':'+start['chave']+':'+json.dumps(content,sort_keys=True)).encode()).hexdigest()
            questions.append({'numero':internal,'numeroOriginal':n,'chave':start['chave'],'idioma':start['idioma'],
                'disciplina':area(n,day),'enunciado':text,'anulada':key[start['chave']] is None,'gabarito':key[start['chave']],
                'alternativas':[{'letra':l,'texto':l} for l in 'ABCDE'],'conteudo':content,'hashFonte':hashsource})
        caderno=2 if day==1 else 5
        item={'codigo':slug.upper(),'slug':slug,'nome':f'ENEM {year} · {day}º dia · Amarelo',
            'ano':year,'edicao':str(year),'dia':day,'caderno':f'CADERNO {caderno} AMARELO','banca':'INEP',
            'urlProva':'https://download.inep.gov.br/'+source_path(year,day,'dia'),
            'urlGabarito':'https://download.inep.gov.br/'+source_path(year,day,'gab')}
        manifest.append({**item,'sha256Prova':hashlib.sha256(source.read_bytes()).hexdigest(),
            'sha256Gabarito':hashlib.sha256(gab.read_bytes()).hexdigest(),'paginas':len(doc),
            'limites':boundaries,'topo':top,'rodape':bottom,
            'paginasColunaUnica':[i+1 for i,n in columns.items() if n==1],
            'limitesPorPagina':{str(i+1):[round(v,3) for v in bounds] for i,bounds in page_bounds.items()},
            'apoiosCompartilhados':[{**v,'pagina':i+1} for i,v in shared.items()]})
        proofs.append({**item,'questoes':sorted(questions,key=lambda q:q['numero'])})
        audit.append({'codigo':item['codigo'],'questoes':len(questions),'anuladas':[q['chave'] for q in questions if q['anulada']],
            'recortes':sum(len(q['conteudo']['recortes']) for q in questions),'pendenciasRevisao':flags})
        if render:
            (folder/'prova.pdf').write_bytes(source.read_bytes())
            with zipfile.ZipFile(ACERVO/f'recortes-{year}-dia-{day}.zip','w',compression=zipfile.ZIP_DEFLATED) as z:
                for p in sorted(folder.iterdir()):z.write(p,p.relative_to(OUT))
        print(slug,len(questions),'questões;',len(flags),'revisões',flush=True)
    dataset={'formato':3,'tipo':'ENEM','estado':'PREVIA_NAO_APROVADA','cor':'AMARELO',
        'anos':list(range(2017,2027)),'provas':proofs}
    data=json.dumps(dataset,ensure_ascii=False,separators=(',',':')).encode()
    (ACERVO/'questoes-recortadas.json.gz').write_bytes(gzip.compress(data,mtime=0))
    (ACERVO/'fontes-amarelo.json').write_text(json.dumps({'fonte':'INEP','provas':manifest},ensure_ascii=False,indent=2))
    report={'estado':'PREVIA_NAO_APROVADA','edicoes':10,'cadernosFisicos':20,
        'questoes':sum(len(p['questoes']) for p in proofs),'ativas':sum(not q['anulada'] for p in proofs for q in p['questoes']),
        'alternativas':sum(len(q['alternativas']) for p in proofs for q in p['questoes']),
        'criterioApoio':'Texto-base da própria questão permanece integrado; apoio compartilhado exige revisão explícita.',
        'auditoria':audit}
    (ACERVO/'validacao-previa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k!='auditoria'},ensure_ascii=False),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--baixar',action='store_true');parser.add_argument('--somente-validar',action='store_true');args=parser.parse_args()
    if args.baixar:download()
    build(not args.somente_validar)
