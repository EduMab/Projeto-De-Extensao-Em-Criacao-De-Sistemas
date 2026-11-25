#!/usr/bin/env python3
"""Prévia isolada: mesmos PDFs/gabaritos; nunca conecta ao banco nem publica."""
from pathlib import Path
import base64,copy,gzip,hashlib,io,json,re,zipfile
import fitz
from PIL import Image,ImageChops,ImageOps
ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'tmp/previa-concursos-enem'; DEST.mkdir(parents=True,exist_ok=True)
OUT=DEST/'imagens';OUT.mkdir(exist_ok=True)
DATA=ROOT/'acervo/concursos/questoes-recortadas.json.gz'
# Revisão editorial por pergunta: os trechos/expressões já estão completos na questão.
DISPENSAR={
 'aedecca-2010':{4:'Trecho citado integralmente; análise gramatical local.',5:'Período e afirmações completos no enunciado.',6:'Frase completa para substituição de Há.',8:'Concordância examinada nas próprias alternativas.'},
 'olegario-2011':{5:'Fragmento completo e comando preservados nas duas colunas.',6:'Regra de acentuação do vocábulo fornecido.',7:'Circunstâncias analisadas nos excertos das alternativas.',8:'Expressão destacada está na citação do enunciado.',9:'Orações com que estão nas alternativas.'},
 'montes-claros-2010':{8:'Período e oração necessários citados no enunciado.',10:'Trecho com os verbos a transformar já está completo.'},
 'primavera-2009':{3:'Som da letra na palavra fornecida.',4:'Classe gramatical da palavra no trecho fornecido.',5:'Oração completa para transformação de voz.',6:'Colocação pronominal examinada nas alternativas.',7:'Análise sintática da frase citada integralmente.',9:'Período completo para análise das conjunções.',29:'Texto da Coreia do Norte não se relaciona à questão sobre H1N1.'},
 'papagaios-2009':{6:'Pronomes nas frases completas das alternativas.',7:'Trecho e termos da análise sintática estão na pergunta.',8:'Formas verbais contidas nas alternativas.',9:'Infinitivos e sujeitos nas próprias alternativas.',10:'Cinco frases completas fornecidas no enunciado.',11:'Classificações verbais nas alternativas.',12:'Pontuação examinada em frases completas nas alternativas.'},
 'casserengue-2009':{3:'Oração completa fornecida para identificação do sujeito.',5:'Oração completa fornecida para ordenação sintática.',6:'Forma verbal grifada está na expressão citada.',9:'Classificação tônica da palavra fornecida.'}}
SECTION=re.compile(r'^(?:PARTE\s+[IVX]+\s*[–-].*|CONHECIMENTOS\s+(?:GERAIS|ESPEC[ÍI]FICOS).*|ATUALIDADES|MATEM[ÁA]TICA|INFORM[ÁA]TICA|L[ÍI]NGUA\s+PORTUGUESA|AGENTE ADMINISTRATIVO, ATENDENTE ADMINISTRATIVO, AUXILIAR DE.*)$',re.I)
def canon(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def trim(im):
 mask=ImageChops.difference(im,Image.new('RGB',im.size,'white')).convert('L').point(lambda v:255 if v>25 else 0)
 box=mask.getbbox()
 if not box:return None
 # Somente margem externa branca; não apaga conteúdo/fórmulas/marcas da fonte.
 x,y,x2,y2=box;box=(max(0,x-9),max(0,y-9),min(im.width,x2+9),min(im.height,y2+9))
 return im.crop(box)
def main():
 old=json.loads(gzip.decompress(DATA.read_bytes()));data=copy.deepcopy(old)
 srczip=zipfile.ZipFile(ROOT/'acervo/concursos/fontes-recortes.zip')
 audit=[];imgs={};removed=[];joined=[];cleaned=[]
 for proof in data['provas']:
  slug=proof['slug'];doc=fitz.open(stream=srczip.read(slug+'/prova.pdf'),filetype='pdf')
  usage={}
  for q in proof['questoes']:
   for r in q['conteudo']['recortes']:
    if r['tipo']=='apoio':usage.setdefault(r['imagem'],set()).add(q['numero'])
  cache={}
  def render(r):
   key=(r['pagina'],tuple(r['caixa']))
   if key in cache:return cache[key]
   page=doc[r['pagina']-1];box=fitz.Rect(r['caixa']);texts=[]
   for b in page.get_text('dict')['blocks']:
    for line in b.get('lines',[]):
     text=''.join(s['text'] for s in line['spans']).strip();rect=fitz.Rect(line['bbox'])
     if box.contains(rect.tl) and SECTION.fullmatch(text):texts.append((text,rect))
   all_lines=[(''.join(s['text'] for s in l['spans']).strip(),fitz.Rect(l['bbox'])) for b in page.get_text('dict')['blocks'] for l in b.get('lines',[])]
   only_heading=bool(texts) and not any(t and not SECTION.fullmatch(t) and box.contains(b.tl) and b.y0<min(r.y0 for _,r in texts) for t,b in all_lines)
   for text,rect in texts:
    cleaned.append({'prova':slug,'pagina':r['pagina'],'texto':text})
    box.y1=min(box.y1,rect.y0-4)
   if box.height<=3 or only_heading:cache[key]=None;return None
   pix=page.get_pixmap(matrix=fitz.Matrix(2.5,2.5),clip=box,alpha=False)
   im=trim(Image.frombytes('RGB',(pix.width,pix.height),pix.samples))
   cache[key]=im;return im
  def save(im,name,kind,regions,reason=None):
   path=f'/questoes/concursos/pci-{slug}-previa-enem/{name}.webp';f=OUT/(slug+'-'+name+'.webp');im.save(f,'WEBP',quality=92,method=4)
   imgs[path]=f
   meta={'tipo':kind,'imagem':path,'pagina':regions[0]['pagina'],'larguraOriginal':round(im.width/2.5,3),'regioesFonte':[{'pagina':r['pagina'],'caixa':r['caixa']} for r in regions]}
   if kind=='apoio':meta.update(necessario=True,justificativa=reason)
   return meta
  for q in proof['questoes']:
   rs=q['conteudo']['recortes'];support=[r for r in rs if r['tipo']=='apoio'];questions=[r for r in rs if r['tipo']=='questao'];n=q['numero']
   if n in DISPENSAR.get(slug,{}):
    removed.append({'prova':slug,'questao':n,'motivo':DISPENSAR[slug][n]});support=[]
   rendered=[]
   if support and all(len(usage[r['imagem']])==1 for r in support):
    parts=[(r,render(r)) for r in support+questions];parts=[(r,im) for r,im in parts if im is not None]
    width=max(im.width for _,im in parts);height=sum(im.height for _,im in parts)+18*(len(parts)-1)
    im=Image.new('RGB',(width,height),'white');y=0
    for _,part in parts:im.paste(part,(0,y));y+=part.height+18
    rendered=[save(im,f'questao-{n:02}-integrada','questao',[r for r,_ in parts])];joined.append({'prova':slug,'questao':n})
   else:
    for i,r in enumerate(support):
     im=render(r)
     if im is not None:rendered.append(save(im,'apoio-'+hashlib.sha256(canon(r).encode()).hexdigest()[:12],'apoio',[r],'A pergunta depende do texto, da charge ou das referências deste trecho.'))
    for i,r in enumerate(questions):
     im=render(r)
     if im is not None:rendered.append(save(im,f'questao-{n:02}-{i+1}','questao',[r]))
   assert any(r['tipo']=='questao' for r in rendered),(slug,n)
   q['conteudo']['recortes']=rendered
   q['conteudo']['apoioRevisado']=True
   q['hashFonte']=hashlib.sha256(canon(q['conteudo']).encode()).hexdigest()
  audit.append({'prova':slug,'questoes':len(proof['questoes'])})
 qs=[q for p in data['provas'] for q in p['questoes']]
 assert (len(data['provas']),len(qs),sum(not q['anulada'] for q in qs),sum(len(q['alternativas']) for q in qs))==(10,364,363,1616)
 for a,b in zip(old['provas'],data['provas']):
  for x,y in zip(a['questoes'],b['questoes']):
   for k in ['numero','anulada','gabarito','enunciado','alternativas']:assert x[k]==y[k],(a['slug'],x['numero'],k)
 data['estado']='PREVIA_AGUARDANDO_APROVACAO'
 report={'estado':data['estado'],'baseGitHub':'48a57f12455ab1f0a083835e521217bcb43dacbc','sha256Original':hashlib.sha256(DATA.read_bytes()).hexdigest(),'provas':10,'questoes':364,'ativas':363,'alternativas':1616,'imagens':len(imgs),'apoiosDispensados':removed,'apoiosIntegrados':joined,'cabecalhosRemovidos':cleaned,'auditoria':audit}
 meta=ROOT/'acervo/concursos-previa-enem';meta.mkdir(exist_ok=True)
 (meta/'revisao.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
 (DEST/'questoes-previa.json.gz').write_bytes(gzip.compress(canon(data).encode(),mtime=0))
 (DEST/'imagens.json').write_text(json.dumps({p:str(f) for p,f in imgs.items()}))
 (DEST/'dados.json').write_text(json.dumps(data,ensure_ascii=False))
 print(json.dumps({k:v for k,v in report.items() if k not in ['auditoria','apoiosDispensados','apoiosIntegrados','cabecalhosRemovidos']},ensure_ascii=False))
 print('Dispensados',len(removed),'integrados',len(joined),'cabeçalhos',len(cleaned))
if __name__=='__main__':main()
