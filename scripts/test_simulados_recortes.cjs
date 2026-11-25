const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
class Node { constructor(tag){this.tagName=tag;this.children=[];this.style={setProperty(k,v){this[k]=v}};this.classList={toggle(){}};}append(...x){this.children.push(...x)}setAttribute(){}replaceChildren(...x){this.children=[...x]}scrollIntoView(){}querySelector(){return new Node("legend")}}
const ids=new Map(),document={getElementById(id){if(!ids.has(id))ids.set(id,new Node('div'));return ids.get(id)},createElement(tag){return new Node(tag)},querySelectorAll(){return []}};
const ctx=vm.createContext({document,window:{location:{replace(){}}},fetch:async()=>({status:401}),localStorage:{clear(){}},console});
vm.runInContext(fs.readFileSync('src/main/resources/static/simulados.js','utf8'),ctx);
const data=JSON.parse(require('zlib').gunzipSync(fs.readFileSync('acervo/concursos/questoes-recortadas.json.gz')));
const p=data.provas[0],q=p.questoes[6],container=new Node('div');
ctx.q={...q,numeroOriginal:q.numero,prova:p.nome};ctx.container=container;
vm.runInContext('recortesOriginais(q,container)',ctx);
assert.equal(container.children[0].children.length,q.conteudo.recortes.length);
assert.equal(container.children[0].children[0].children[0].textContent,'TEXTO DE APOIO');
assert.equal(container.children[0].children.at(-1).children[0].textContent,'QUESTÃO');
for(const card of container.children[0].children)assert.match(card.children[1].src,/^\/questoes\/concursos\//);
ctx.q.conteudo.recortes=[{tipo:'questao',imagem:'https://example.invalid/x.webp'}];ctx.container=new Node('div');vm.runInContext('recortesOriginais(q,container)',ctx);assert.equal(ctx.container.children[0].children.length,0);
console.log('OK: apoio antes da questão, imagens locais e rejeição de URL externa');
const antigos=JSON.parse(require('zlib').gunzipSync(fs.readFileSync('acervo/concursos/questoes.json.gz')));
const fortaleza=antigos.provas.find(p=>p.codigo.startsWith('FORTALEZA-'));
const legacy=fortaleza.questoes.find(q=>q.numero===68);
ctx.q={...legacy,numeroOriginal:legacy.numero,prova:fortaleza.nome};ctx.container=new Node('div');
vm.runInContext('questaoIndividual(q,container)',ctx);
const nodes=n=>[n,...n.children.flatMap(nodes)];
let rendered=nodes(ctx.container);
assert(!rendered.some(n=>n.tagName==='iframe'));
assert(rendered.some(n=>n.textContent===legacy.enunciado));
for(const a of legacy.alternativas)assert(rendered.some(n=>n.textContent===`${a.letra}) ${a.texto}`));
assert(rendered.some(n=>n.textContent==='QUESTÃO 68'));
ctx.q.conteudo.textoApoio='Texto de apoio <script>sem HTML executável</script>';
ctx.container=new Node('div');vm.runInContext('questaoIndividual(q,container)',ctx);
assert.equal(ctx.container.children[0].children[0].children[0].textContent,'TEXTO DE APOIO');
assert.equal(ctx.container.children[0].children[0].children[1].textContent,ctx.q.conteudo.textoApoio);
assert(!nodes(ctx.container).some(n=>['iframe','script'].includes(n.tagName)));
console.log('OK: Fortaleza 68 e demais snapshots antigos exibem questão, alternativas e apoio sem PDF embutido; textos tratados como texto.');
let totalAntigas=0;
for(const prova of antigos.provas)for(const original of prova.questoes){
 ctx.q={...original,numeroOriginal:original.numero,prova:prova.nome};ctx.container=new Node('div');
 vm.runInContext('questaoIndividual(q,container)',ctx);const rendered=nodes(ctx.container);
 assert(!rendered.some(n=>n.tagName==='iframe'));
 assert(rendered.some(n=>n.textContent===original.enunciado));
 for(const a of original.alternativas)assert(rendered.some(n=>n.textContent===`${a.letra}) ${a.texto}`));
 totalAntigas++;
}
console.log(`OK: ${totalAntigas} questões antigas preservam enunciados e alternativas na apresentação individual.`);
const indiceEtec=JSON.parse(require('zlib').gunzipSync(fs.readFileSync('src/main/resources/etec-recortes.json.gz')));
let exibidas=0;
for(const [key,row] of Object.entries(indiceEtec)){
 ctx.q={numeroOriginal:Number(key.split('/')[1]),prova:'ETEC '+key.split('/')[0],conteudo:{modo:'recorte_original',recortes:row.recortes}};
 ctx.container=new Node('div');vm.runInContext('recortesOriginais(q,container)',ctx);
 const cards=ctx.container.children[0].children;
 assert.equal(cards.length,row.recortes.length,key);
 cards.forEach((card,i)=>{
  const frame=card.children[1],img=frame.children[0],p=row.recortes[i];
  assert.equal(frame.className,'etec-crop-frame');assert.equal(img.src,p.imagem);
  assert.equal(frame.style.aspectRatio,`${p.caixa[2]-p.caixa[0]} / ${p.caixa[3]-p.caixa[1]}`);
  assert.equal(img.style.left,`${-p.caixa[0]/(p.caixa[2]-p.caixa[0])*100}%`);
  assert.equal(img.style.top,`${-p.caixa[1]/(p.caixa[3]-p.caixa[1])*100}%`);
 });exibidas++;
}
ctx.q.conteudo.recortes=[{tipo:'questao',imagem:'/questoes/etec/2026-2/pagina-15.webp',caixa:[0,0,600,100],larguraPagina:581,alturaPagina:751}];
ctx.container=new Node('div');vm.runInContext('recortesOriginais(q,container)',ctx);assert.equal(ctx.container.children[0].children.length,0);
const css=fs.readFileSync('src/main/resources/static/simulados.css','utf8');assert.match(css,/\.etec-crop-frame\{[^}]*overflow:hidden/);
console.log(`OK: ${exibidas} questões ETEC em janelas proporcionais, imagens originais, rejeição de recortes fora da página.`);
