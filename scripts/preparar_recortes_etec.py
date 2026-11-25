#!/usr/bin/env python3
"""Indexa recortes das imagens originais ETEC, sem reimportar questões ou respostas."""
from pathlib import Path
import json,re,hashlib,gzip
import fitz
from extrair_etec import lines,plain,markers
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'acervo/etec/questoes.json'
OUT=ROOT/'src/main/resources/etec-recortes.json.gz'
PATTERN=re.compile(r'questoes\s*(?:de\s*)?(?:numeros?\s*)?0*(\d{1,2})\s*(?:a|e|ate\s*a?)\s*0*(\d{1,2})')

def prepare():
 result={};reports=[]
 for edition in json.loads(DATA.read_text())['edicoes']:
  code=edition['edicao'];doc=fitz.open(ROOT/'tmp/pdfs/etec'/code/'prova.pdf')
  source_hash=hashlib.sha256((ROOT/'tmp/pdfs/etec'/code/'prova.pdf').read_bytes()).hexdigest()
  expected=(ROOT/'src/main/resources/static/questoes/etec'/code/'fonte.sha256').read_text().strip()
  if source_hash!=expected:raise ValueError('PDF difere das imagens publicadas: '+code)
  qs=edition['questoes'];ms=markers(doc,code,len(qs));last=max(m['pagina'] for m in ms.values())
  question_parts={q['numero']:[] for q in qs};support_parts={};events_by_page={};contexts={}
  for n,m in ms.items():events_by_page.setdefault(m['pagina'],[]).append({'kind':'questao','numbers':[n],'y':m['caixa'][1]-4,'x':m['caixa'][0],'key':n})
  for pi in range(2,last+1):
   page=doc[pi-1];ls=lines(page)
   for block in page.get_text('dict')['blocks']:
    bl=block.get('lines',[])
    if not bl:continue
    text=' '.join(''.join(s['text'] for s in l['spans']) for l in bl)
    m=PATTERN.search(plain(text))
    if not m:continue
    a,b=map(int,m.groups())
    if not 1<=a<b<=len(qs):continue
    # Só instruções anteriores à primeira questão indicada são apoio compartilhado.
    if pi>ms[a]['pagina'] or (pi==ms[a]['pagina'] and block['bbox'][1]>ms[a]['caixa'][1]):continue
    key=f'{a}-{b}'
    if key in contexts:continue
    contexts[key]=list(range(a,b+1));support_parts[key]=[]
    events_by_page.setdefault(pi,[]).append({'kind':'apoio','numbers':list(range(a,b+1)),'y':max(20,block['bbox'][1]-5),'x':block['bbox'][0],'key':a-.5,'support':key})
  carry=None
  def add(owner,pi,box):
   if owner is None or box[3]-box[1]<7:return
   page=doc[pi-1];rect=fitz.Rect(box)
   # Não produz cartões de espaços em branco.
   if not page.get_text(clip=rect).strip() and not any(rect.intersects(fitz.Rect(b['bbox'])) for b in page.get_text('dict')['blocks'] if b.get('type')==1):return
   part={'tipo':owner['kind'],'imagem':f'/questoes/etec/{code}/pagina-{pi:02}.webp','pagina':pi,'caixa':[round(float(x),3) for x in box],'larguraPagina':round(page.rect.width,3),'alturaPagina':round(page.rect.height,3),'larguraOriginal':round(rect.width,3)}
   if owner['kind']=='questao':question_parts[owner['numbers'][0]].append(part)
   else:support_parts[owner['support']].append(part)
  for pi in range(2,last+1):
   page=doc[pi-1];w,h=page.rect.width,page.rect.height;events=events_by_page.get(pi,[])
   right=[e for e in events if e['x']>w/2]
   top=max(0,min([24]+[b[1]-2 for t,b in lines(page) if t and b[1]<h-40]));bottom=h-28
   # Na edição IDECAN, cabeçalho e rodapé não fazem parte da questão.
   if code=='2025-2':top=min([75]+[e['y'] for e in events]);bottom=h-32
   top=min([top]+[e['y'] for e in events])
   if right:
    split=min(e['y'] for e in right)
    peers=[e['y'] for e in events if e['x']<w/2 and abs(e['y']-split)<22]
    if peers:split=min([split]+peers)
    wide=[b for t,b in lines(page) if t and b[1]<split and b[2]-b[0]>w*.55]
    wide_images=[b['bbox'] for b in page.get_text('dict')['blocks'] if b.get('type')==1 and b['bbox'][1]<split and b['bbox'][2]-b['bbox'][0]>w*.55]
    if wide or wide_images:
     last_wide=max([b[3] for b in wide]+[b[3] for b in wide_images])
     starts=[b[1]-3 for t,b in lines(page) if t and b[0]>w/2+5 and b[1]>=last_wide-1 and b[1]<split]
     if starts:split=min(split,min(starts))
     split=max(top,split)
    else:split=top
    regions=[]
    if split>top+7:regions.append((20,top,w-20,split))
    regions.extend([(20,split,w/2-1,bottom),(w/2+1,split,w-20,bottom)])
   else:
    regions=[(20,top,w-20,bottom)]
   page_owners=[];owner=carry
   for box in regions:
    x0,y0,x1,y1=box
    es=[e for e in events if y0-.1<=e['y']<y1 and (x1-x0>w*.7 or x0<=e['x']<x1)]
    es.sort(key=lambda e:(e['y'],e['key']))
    if es and owner and es[0]['key']<=owner['key']:owner=None
    cursor=y0
    for e in es:
     add(owner,pi,(x0,cursor,x1,min(e['y'],y1)))
     owner=e;page_owners.append(e);cursor=max(y0,e['y'])
    add(owner,pi,(x0,cursor,x1,y1))
   if page_owners:carry=max(page_owners,key=lambda e:e['key'])
  errors=[]
  for q in qs:
   n=q['numero'];parts=question_parts[n]
   texts='\n'.join(doc[p['pagina']-1].get_text(clip=fitz.Rect(p['caixa'])) for p in parts)
   alternatives=set(re.findall(r'\(\s*([A-E])\s*\)',texts))
   if alternatives!=set('ABCDE'):errors.append((n,''.join(sorted(alternatives))))
   supports=[p for key,nums in contexts.items() if n in nums for p in support_parts[key]]
   result[f'{code}/{n}']={'pagina':q['conteudo']['pagina'],'caixaTitulo':q['conteudo']['caixaTitulo'],'recortes':supports+parts}
  reports.append({'edicao':code,'questoes':len(qs),'apoios':len(contexts),'sha256Prova':source_hash,'alternativasPendentes':errors})
  print(code,len(qs),'pendentes',errors,flush=True)
 if any(r['alternativasPendentes'] for r in reports):raise ValueError('Existem alternativas não conferidas')
 OUT.write_bytes(gzip.compress((json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\n').encode(),mtime=0))
 (ROOT/'acervo/etec/validacao-recortes.json').write_text(json.dumps({'total':len(result),'edicoes':reports,'origem':'Imagens originais; coordenadas em pontos do PDF; sem alteração do banco.'},ensure_ascii=False,indent=2)+'\n')
 return reports
if __name__=='__main__':prepare()
