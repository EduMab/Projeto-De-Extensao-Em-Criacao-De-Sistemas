#!/usr/bin/env python3
"""Prévia autocontida do ENEM. Não envia respostas nem escreve no banco."""
from pathlib import Path
import base64,gzip,json,html
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image
from preparar_enem_amarelo import ROOT,ACERVO,OUT

DEST=ROOT/'tmp/previa-enem';DEST.mkdir(parents=True,exist_ok=True)
data=json.loads(gzip.decompress((ACERVO/'questoes-recortadas.json.gz').read_bytes()))
examples=[]
def add(year,day,key,title):
    proof=next(p for p in data['provas'] if p['ano']==year and p['dia']==day)
    q=next(q for q in proof['questoes'] if q['chave']==key)
    if any(e['id']==proof['codigo']+key for e in examples):return
    examples.append({'id':proof['codigo']+key,'ano':year,'dia':day,'numero':q['numeroOriginal'],
        'idioma':q['idioma'],'area':q['disciplina'],'titulo':title,'gabarito':q['gabarito'],
        'anulada':q['anulada'],'urlProva':proof['urlProva'],'recortes':q['conteudo']['recortes']})
add(2026,2,'098','Questão direta · sem bloco extra')
add(2026,2,'095','Circuito elétrico · figura preservada')
add(2026,2,'161','Dados e cálculo · proporção original')
add(2026,1,'001-ingles','Inglês · texto integrado à questão')
add(2026,1,'001-espanhol','Espanhol · texto integrado à questão')
add(2025,1,'005-espanhol','Charge · somente a questão atual')
add(2022,1,'005-ingles','Charge longa · sem corte no meio')
add(2025,1,'006','Texto-base necessário · Linguagens')
add(2026,1,'046','Texto-base necessário · Ciências Humanas')
add(2023,2,'153','Gráficos · continuação da questão')
add(2026,2,'153','Questão anulada · fora do sorteio final')
for year in range(2026,2016,-1):
    add(year,1,'011',f'ENEM {year} · 1º dia')
    add(year,2,'098',f'ENEM {year} · 2º dia')
disk_examples=json.loads(json.dumps(examples))
for e in examples:
    for r in e['recortes']:
        path=OUT/r['imagem'].lstrip('/')
        r['src']='data:image/webp;base64,'+base64.b64encode(path.read_bytes()).decode()
css=(ROOT/'src/main/resources/static/simulados.css').read_text()
page='''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Prévia ENEM Amarelo | Evolua+</title><style>'''+css+'''
select{font:inherit;max-width:100%;border:1px solid var(--line);background:#fff;border-radius:9px;padding:10px;color:var(--ink)}
.preview-banner{padding:10px 20px;text-align:center;background:#f5f1fc;color:#59427c;font-size:12px;border-bottom:1px solid var(--line)}
main{padding-top:30px}.preview-controls{display:grid;gap:12px}.preview-controls label{display:grid;gap:5px;font-size:12px}.example-caption{font-size:12px;color:var(--muted)}
.question-crop-card{--crop-width:440px}.question-crop-card.support-card{--crop-width:560px}.crop-scroll{overflow-x:auto}
.viewer-tools input{max-width:140px}.question-actions{gap:12px}.question-actions button{flex:1}.preview-intro{font-size:13px;color:var(--muted)}
.preview-result{padding:14px;background:var(--soft);border-radius:9px;margin-top:16px}.support-reason{font-size:12px;color:var(--muted);margin:0 0 10px}
.stats{grid-template-columns:repeat(3,1fr)}.preview-tabs{display:flex;gap:8px;flex-wrap:wrap}.preview-tabs span{padding:5px 10px;border:1px solid var(--line);border-radius:8px;font-size:12px;color:var(--muted)}.preview-tabs .selected{color:var(--purple);background:var(--soft);font-weight:bold}
@media(max-width:520px){.stats{grid-template-columns:1fr 1fr}.stats>div:last-child{grid-column:1/-1}.preview-tabs{display:none}}
</style><body><div class="preview-banner"><b>PRÉVIA PARA REVISÃO</b> · Provas oficiais do INEP · Respostas apenas nesta página, sem envio ao sistema</div>
<header class="topbar"><span class="brand">evolua<span>+</span></span><div class="preview-tabs"><span>ETEC</span><span class="selected">ENEM</span><span>Concurso</span><span>FUVEST</span></div></header>
<main><section class="hero"><div><p class="eyebrow">ENEM · CADERNO AMARELO</p><h1>Seu próximo passo<br><span>começa aqui.</span></h1><p class="intro">Uma questão por tela, com o conteúdo necessário para resolver. Textos, figuras e fórmulas do caderno original.</p></div><div class="weekly-badge"><strong>40</strong><span>questões por semana</span></div></section>
<div class="stats"><div><strong>2017–2026</strong><span>10 edições · 20 cadernos</span></div><div><strong>Inglês ou Espanhol</strong><span>Questões comuns sem duplicação</span></div><div><strong>Recortes originais</strong><span>11 anuladas fora da seleção final</span></div></div>
<p class="preview-intro">Explore os exemplos abaixo. Os exemplos cobrem os dez anos e incluem casos com e sem apoio, figuras, gráficos e mudanças de página. A correção da prévia usa o gabarito oficial; o resultado é percentual de acertos, sem cálculo de TRI.</p>
<div class="study-grid"><aside class="card navigation"><p class="eyebrow">REVISAR A PRÉVIA</p><div class="preview-controls"><label for="idioma">Idioma dos exemplos<select id="idioma"><option value="TODOS">Todos os exemplos</option><option value="INGLES">Inglês + questões comuns</option><option value="ESPANHOL">Espanhol + questões comuns</option></select></label><label for="exemplo">Escolha um exemplo<select id="exemplo"></select></label></div><p id="contador" class="example-caption"></p><p class="muted">No sistema, serão 40 questões por semana, com retomada e histórico. Esta prévia permite conferir a leitura antes da publicação.</p><p class="save-status" id="salvamento" role="status"></p></aside>
<section class="card question-card cropped-question" id="estudo"><div class="question-heading"><div><p class="eyebrow" id="fonte"></p><h2 id="titulo">Questão</h2></div><span class="pill">PRÉVIA</span></div><div class="original-note"><strong id="referencia"></strong><span id="criterio"></span></div><div class="viewer-tools"><a id="oficial" target="_blank" rel="noopener noreferrer">Abrir caderno oficial ↗</a><label for="zoom">Ampliar <input id="zoom" type="range" min="100" max="180" value="100"></label></div><div id="recortes"></div><fieldset id="respostas"><legend>Qual alternativa você escolhe?</legend><div class="options" id="opcoes"></div></fieldset><div class="question-actions"><button id="anterior" class="secondary" type="button">← Anterior</button><button id="proxima" class="primary" type="button">Próxima →</button></div><button id="conferir" class="secondary" type="button" style="margin-top:14px;width:100%">Conferir exemplo</button><p id="resultado" class="preview-result" role="status" hidden></p></section></div>
<footer>Prévia ENEM Amarelo · Fontes: INEP · Sem alteração no site ou no banco de dados.</footer></main>
<script id="dados" type="application/json">'''+json.dumps(examples,ensure_ascii=False).replace('<','\\u003c')+'''</script>
<script>
"use strict";const EXEMPLOS=JSON.parse(document.getElementById('dados').textContent),$=id=>document.getElementById(id);let lista=EXEMPLOS,indice=0;const respostas={};
function el(tag,text,cls){const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;}
function filtrarIdioma(idioma){return EXEMPLOS.filter(e=>idioma==='TODOS'||!e.idioma||e.idioma===idioma);}
function mostrar(){const e=lista[indice];$('exemplo').value=String(indice);$('contador').textContent=`Exemplo ${indice+1} de ${lista.length}`;
$('fonte').textContent=`ENEM ${e.ano} · ${e.dia}º dia · Amarelo · ${e.area}`;$('titulo').textContent=e.titulo;$('referencia').textContent=`Questão original ${e.numero}${e.idioma?' · '+(e.idioma==='INGLES'?'Inglês':'Espanhol'):''}.`;
const apoio=e.recortes.some(r=>r.tipo==='apoio');$('criterio').textContent=apoio?'Esta questão depende do texto-base abaixo. Ele foi preservado porque a pergunta faz referência ao seu conteúdo.':'Enunciado, texto-base e alternativas reunidos. Cabeçalhos de matéria, rascunho e identificação de gabarito não entram como apoio.';
$('oficial').href=e.urlProva;$('recortes').replaceChildren();for(const r of e.recortes){if(r.tipo==='apoio'&&!r.necessario)continue;const card=el('section',undefined,'question-crop-card'+(r.tipo==='apoio'?' support-card':''));card.append(el('p',r.tipo==='apoio'?'TEXTO-BASE NECESSÁRIO':`QUESTÃO ${e.numero} · ${r.pagina}ª página do caderno`,'crop-heading'));if(r.tipo==='apoio')card.append(el('p',r.justificativa,'support-reason'));const im=el('img');im.src=r.src;im.alt=r.tipo==='apoio'?`Texto-base oficial necessário à questão ${e.numero}`:`Recorte original da questão ${e.numero}, ENEM ${e.ano}`;card.append(im);$('recortes').append(card);}
$('opcoes').replaceChildren();for(const letra of 'ABCDE'){const label=el('label',undefined,'option'),input=el('input');input.type='radio';input.name='alternativa';input.value=letra;input.checked=respostas[e.id]===letra;input.disabled=e.anulada;input.onchange=()=>{respostas[e.id]=letra;$('salvamento').textContent='Alternativa '+letra+' marcada somente na prévia.';$('resultado').hidden=true;};label.append(input,el('span',letra));$('opcoes').append(label);}
$('resultado').hidden=true;$('anterior').disabled=indice===0;$('proxima').disabled=indice===lista.length-1;$('conferir').textContent=e.anulada?'Ver situação da questão':'Conferir exemplo';$('salvamento').textContent=e.anulada?'Exemplo de questão anulada: não entrará no sorteio.':respostas[e.id]?'Resposta marcada na prévia.':'';}
function montar(){lista=filtrarIdioma($('idioma').value);indice=0;$('exemplo').replaceChildren();lista.forEach((e,i)=>{const op=el('option',`${e.ano} · D${e.dia} · Q${e.numero}${e.idioma?' · '+e.idioma:''} · ${e.titulo}`);op.value=String(i);$('exemplo').append(op);});mostrar();}
$('idioma').onchange=montar;$('exemplo').onchange=e=>{indice=Number(e.target.value);mostrar();};$('anterior').onclick=()=>{if(indice>0){indice--;mostrar();}};$('proxima').onclick=()=>{if(indice<lista.length-1){indice++;mostrar();}};
$('zoom').oninput=e=>$('estudo').style.setProperty('--crop-scale',Number(e.target.value)/100);
$('conferir').onclick=()=>{const e=lista[indice],r=respostas[e.id];$('resultado').hidden=false;$('resultado').textContent=e.anulada?'Questão anulada no gabarito oficial. Ficará fora dos simulados.':!r?'Marque uma alternativa para conferir o exemplo.':`${r===e.gabarito?'Você acertou.':'Você errou.'} Gabarito oficial: alternativa ${e.gabarito}. Conferência demonstrativa, sem registro de nota no sistema.`;};montar();
</script></body></html>'''
(DEST/'previa-enem-amarelo.html').write_text(page)

# Versão de leitura em PDF: os mesmos recortes, sem reescrita das questões.
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
bold='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
pdfmetrics.registerFont(TTFont('DejaVu',font));pdfmetrics.registerFont(TTFont('DejaVu-Bold',bold))
pdf=canvas.Canvas(str(DEST/'previa-enem-amarelo.pdf'),pagesize=(595.28,841.89))
pdf.setTitle('Prévia ENEM Amarelo — Evolua+')
count=0
def newpage(e,part):
    global count
    count+=1;pdf.setFillColor(HexColor('#faf9fc'));pdf.rect(0,0,596,842,fill=1,stroke=0)
    pdf.setFillColor(HexColor('#252238'));pdf.setFont('DejaVu-Bold',19);pdf.drawString(32,804,'evolua+')
    pdf.setFillColor(HexColor('#6d28d9'));pdf.setFont('DejaVu-Bold',9);pdf.drawRightString(563,807,'ENEM · PRÉVIA PARA REVISÃO')
    pdf.setFillColor(HexColor('#746f85'));pdf.setFont('DejaVu',9);pdf.drawString(32,776,f"ENEM {e['ano']} · {e['dia']}º dia · Amarelo · {e['area']}")
    pdf.setFillColor(HexColor('#252238'));pdf.setFont('DejaVu-Bold',14);pdf.drawString(32,751,f"Questão {e['numero']}"+(' · '+e['idioma'].title() if e['idioma'] else '')+(' · continuação' if part else ''))
    pdf.setFont('DejaVu',8);pdf.setFillColor(HexColor('#746f85'));pdf.drawString(32,731,e['titulo'])
    pdf.setFont('DejaVu',7);pdf.drawString(32,23,'Recortes do PDF oficial do INEP · Prévia sem publicação ou gravação no banco')
    pdf.drawRightString(563,23,str(count))
    pdf.linkURL(e['urlProva'],(32,10,480,32),relative=0)
for e in disk_examples[:10]:
    for j,r in enumerate(e['recortes']):
        newpage(e,j)
        image=Image.open(OUT/r['imagem'].lstrip('/'));iw,ih=image.size
        w=min(500,iw);h=ih*w/iw
        if h>615:w*=615/h;h=615
        x=(595.28-w)/2;y=92+(615-h)
        pdf.setFillColor(HexColor('#ffffff'));pdf.roundRect(x-9,y-8,w+18,h+16,9,fill=1,stroke=0)
        pdf.drawImage(ImageReader(image),x,y,width=w,height=h)
        pdf.setFont('DejaVu-Bold',8);pdf.setFillColor(HexColor('#6d28d9'))
        pdf.drawString(32,66,'TEXTO-BASE NECESSÁRIO' if r['tipo']=='apoio' else 'A     B     C     D     E')
        pdf.setFont('DejaVu',7);pdf.setFillColor(HexColor('#746f85'))
        pdf.drawString(32,48,'Apoio vinculado à pergunta; nenhum cabeçalho dispensável.' if r['tipo']=='apoio' else 'Use a prévia HTML para ampliar, navegar e marcar alternativas.')
        pdf.showPage()
pdf.save()
print(json.dumps({'exemplos':len(examples),'paginasPDF':count,'html':str(DEST/'previa-enem-amarelo.html'),'pdf':str(DEST/'previa-enem-amarelo.pdf')},ensure_ascii=False))
