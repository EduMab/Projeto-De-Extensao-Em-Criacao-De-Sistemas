#!/usr/bin/env python3
"""Gera HTML offline no HTML/CSS reais do site, com respostas somente em memória."""
from pathlib import Path
import base64,json,re,html,zipfile,hashlib
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from PIL import Image
from preparar_previa_concursos_enem import ROOT,DEST

def main():
 data=json.loads((DEST/'dados.json').read_text());files=json.loads((DEST/'imagens.json').read_text())
 images={k:'data:image/webp;base64,'+base64.b64encode(Path(v).read_bytes()).decode() for k,v in files.items()}
 css=(ROOT/'src/main/resources/static/simulados.css').read_text();original=(ROOT/'src/main/resources/static/simulados.html').read_text();site=(ROOT/'src/main/resources/static/simulados.js').read_text()
 # Apenas adaptador da prévia: os arquivos de produção permanecem intactos.
 script=site.replace('img.src = fragment.imagem;', 'img.src = PREVIEW_IMAGES[fragment.imagem];')
 script=script.replace('indice === 39','indice === simulado.questoes.length - 1').replace('indice < 39','indice < simulado.questoes.length - 1')
 script=script.replace('${indice + 1} / 40','${indice + 1} / ${simulado.questoes.length}').replace('${count} de 40','${count} de ${simulado.questoes.length}')
 script=script.replace('inicializar();','inicializar().then(()=>selecionarProva(0));')
 adapter='''
const PREVIEW_DATA=JSON.parse(document.getElementById('preview-data').textContent),PREVIEW_IMAGES=JSON.parse(document.getElementById('preview-images').textContent);
function previewAttempt(index){const p=PREVIEW_DATA.provas[index];return {id:index+1,tipo:'CONCURSO',data:'2026-11-25',proximaLiberacao:'2026-12-02',concluido:false,questoes:p.questoes.map((q,i)=>({...q,numeroOriginal:q.numero,prova:p.nome,edicao:p.edicao,posicao:i+1,alternativaSelecionada:null,conteudo:{...q.conteudo,urlProva:p.urlProva+'#page='+q.conteudo.pagina},alternativas:q.alternativas.map((a,j)=>({...a,id:j+1}))}))};}
window.fetch=async(url,opts={})=>({ok:true,status:200,json:async()=>url==='/api/perfil'?{objetivo:'CONCURSO'}:url.includes('/acervo')?{questoesAtivas:363,edicoes:10}:url.includes('/historico')?[]:url.includes('/atual')?previewAttempt(Number(document.getElementById('preview-prova').value)):{} });
function selecionarProva(index){simulado=previewAttempt(index);indice=0;ocupado=false;document.getElementById('progresso').max=simulado.questoes.length;mostrar();document.getElementById('periodo').textContent='PRÉVIA DO ACERVO · Questões deste caderno para revisão; no sistema o simulado continua com 40 questões por semana.';document.getElementById('inicio').hidden=true;}
'''
 post='''
const seletor=document.getElementById('preview-prova');PREVIEW_DATA.provas.forEach((p,i)=>{const o=document.createElement('option');o.value=i;o.textContent=p.nome+' ('+p.ano+')';seletor.append(o);});seletor.onchange=()=>selecionarProva(Number(seletor.value));
document.getElementById('finalizar').textContent='Conferir questão';document.getElementById('finalizar').onclick=()=>{const q=simulado.questoes[indice],node=document.getElementById('correcao');node.hidden=false;node.textContent=q.anulada?'Questão anulada: permanece no acervo para revisão e fica fora do sorteio.':q.alternativaSelecionada===null?'Escolha uma alternativa para conferir.':(q.alternativas.find(a=>a.id===q.alternativaSelecionada).letra===q.gabarito?'Você acertou. ':'Você errou. ')+(q.conteudo.gabaritoPreliminar?'Gabarito preliminar da fonte: ':'Gabarito da fonte: ')+q.gabarito+'. Resposta somente nesta prévia.';};
document.getElementById('sair').onclick=()=>{document.getElementById('mensagem').hidden=false;document.getElementById('mensagem').textContent='Prévia offline: nenhuma sessão ou conta foi alterada.';};document.querySelectorAll('.topbar a').forEach(a=>{a.href='#';a.onclick=e=>e.preventDefault();});
'''
 # Preserva exatamente o CSS e a estrutura do entorno do site. A faixa é só de revisão.
 page=re.sub(r'<link rel="stylesheet"[^>]+>',lambda m:'<style>'+css+'</style>',original)
 banner='<section class="message" aria-label="Controles exclusivos da prévia"><strong>PRÉVIA PARA SUA APROVAÇÃO — sem publicação ou gravação no banco.</strong> <label for="preview-prova">Revisar prova: </label><select id="preview-prova" aria-label="Escolher prova para revisar"></select><p>Use os números para navegar, marque uma alternativa e clique em Conferir questão. As respostas duram apenas nesta página. A faixa de revisão não será adicionada ao site.</p></section>'
 page=page.replace('<main>','<main>'+banner)
 page=page.replace('Questões e gabaritos: acervo oficial do Centro Paula Souza.','Questões e gabaritos: cadernos originais disponibilizados no PCI Concursos.')
 js='<script id="preview-data" type="application/json">'+json.dumps(data,ensure_ascii=False).replace('<','\\u003c')+'</script><script id="preview-images" type="application/json">'+json.dumps(images)+'</script><script>'+adapter+script+post+'</script>'
 page=re.sub(r'<script src="/simulados.js[^>]+></script>',lambda m:js,page)
 (DEST/'previa-concursos-padrao-enem.html').write_text(page)
 # Amostras em PDF: mesma imagem da prévia HTML, sem reescrever os enunciados.
 pdfmetrics.registerFont(TTFont('DV','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'));pdfmetrics.registerFont(TTFont('DVB','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
 samples=[('aedecca-2010',5),('aedecca-2010',1),('aedecca-2010',31),('olegario-2011',5),('rio-serra-2010',22),('mato-grosso-2010',20),('montes-claros-2010',8),('santa-cruz-2010',20),('sao-francisco-2010',20),('primavera-2009',29),('primavera-2009',8),('papagaios-2009',6),('casserengue-2009',39),('primavera-2009',18)]
 pdf=canvas.Canvas(str(DEST/'previa-concursos-padrao-enem.pdf'),pagesize=(595.28,841.89));pdf.setTitle('Concursos no padrão ENEM - prévia para revisão')
 for slug,n in samples:
  p=next(p for p in data['provas'] if p['slug']==slug);q=next(q for q in p['questoes'] if q['numero']==n)
  parts=[Image.open(files[r['imagem']]).convert('RGB') for r in q['conteudo']['recortes']];width=max(im.width for im in parts);height=sum(im.height for im in parts)+20*(len(parts)-1);im=Image.new('RGB',(width,height),'white');y=0
  for part in parts:im.paste(part,(0,y));y+=part.height+20
  scale=min(510/width,600/height);w,h=width*scale,height*scale
  pdf.setFillColor(HexColor('#faf9fc'));pdf.rect(0,0,596,842,fill=1,stroke=0)
  pdf.setFont('DVB',18);pdf.setFillColor(HexColor('#6d28d9'));pdf.drawString(32,802,'EVOLUA+ · CONCURSOS')
  pdf.setFont('DV',8);pdf.setFillColor(HexColor('#746f85'));pdf.drawString(32,780,'PRÉVIA PARA APROVAÇÃO · Mesmos recortes da versão HTML')
  pdf.setFont('DV',10);pdf.setFillColor(HexColor('#252238'));pdf.drawString(32,752,p['nome'][:84]);pdf.setFont('DVB',13);pdf.drawString(32,731,f'Questão {n} · {p["ano"]}')
  pdf.drawImage(ImageReader(im),(595.28-w)/2,110+(600-h),width=w,height=h)
  pdf.setFont('DV',9);pdf.setFillColor(HexColor('#6d28d9'));pdf.drawString(32,72,'ANULADA · Fora do sorteio' if q['anulada'] else '     '.join(a['letra'] for a in q['alternativas']))
  pdf.setFont('DV',7);pdf.setFillColor(HexColor('#746f85'));pdf.drawString(32,47,'Enunciado, figuras, fórmulas e alternativas preservados. Apoio somente quando necessário.')
  pdf.drawString(32,30,'Use o HTML para navegar pelas 364 questões, ampliar, responder e conferir.');pdf.showPage()
 pdf.save()
 doc=__import__('fitz').open(DEST/'previa-concursos-padrao-enem.pdf');doc[0].get_pixmap(matrix=__import__('fitz').Matrix(1.5,1.5)).save(DEST/'previa-concursos-padrao-enem.png')
 with zipfile.ZipFile(DEST/'previa-concursos-padrao-enem.zip','w',zipfile.ZIP_DEFLATED) as z:
  for name in ['previa-concursos-padrao-enem.html','previa-concursos-padrao-enem.pdf','previa-concursos-padrao-enem.png']:z.write(DEST/name,name)
 print(json.dumps({'htmlBytes':(DEST/'previa-concursos-padrao-enem.html').stat().st_size,'pdfPaginas':len(doc),'questoes':sum(len(p['questoes']) for p in data['provas'])}))
if __name__=='__main__':main()
