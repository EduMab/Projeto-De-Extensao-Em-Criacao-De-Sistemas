const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
class Node {
  constructor(tag){this.tagName=tag;this.children=[];this.style={setProperty(k,v){this[k]=v}};this.classList={toggle(){},add(){}};this.value=100;}
  append(...x){this.children.push(...x)}
  replaceChildren(...x){this.children=[...x]}
  setAttribute(k,v){this[k]=v}
  querySelector(tag){return this.children.find(n=>n.tagName===tag)||null}
  scrollIntoView(){}
}
const ids=new Map(),document={getElementById(id){if(!ids.has(id))ids.set(id,new Node('div'));return ids.get(id)},createElement(tag){return new Node(tag)},querySelectorAll(){return []},querySelector(){return null}};
document.getElementById('respostas').append(new Node('legend'));
const ctx=vm.createContext({document,window:{location:{replace(){}}},fetch:async()=>({status:401}),localStorage:{clear(){}},console});
vm.runInContext(fs.readFileSync('src/main/resources/static/simulados.js','utf8'),ctx);
const data=JSON.parse(require('zlib').gunzipSync(fs.readFileSync('acervo/enem/questoes-recortadas.json.gz')));
const approved=JSON.parse(fs.readFileSync('acervo/enem/imagens-aprovadas.json'));
const nodes=n=>[n,...n.children.flatMap(nodes)];
let count=0;
for(const p of data.provas)for(const original of p.questoes){
  ctx.q={...original,numeroOriginal:original.numeroOriginal,prova:p.nome};ctx.container=new Node('div');
  vm.runInContext('recortesOriginais(q,container)',ctx);
  const rendered=nodes(ctx.container),images=rendered.filter(n=>n.tagName==='img');
  assert.deepEqual(images.map(n=>n.src),original.conteudo.recortes.map(r=>r.imagem));
  for(const img of images){assert(approved[img.src]);assert(img.alt.includes(String(original.numeroOriginal)))}
  assert(!rendered.some(n=>['iframe','script'].includes(n.tagName)));
  assert.equal(rendered.filter(n=>n.textContent==='TEXTO DE APOIO').length,original.conteudo.recortes.filter(r=>r.tipo==='apoio'&&r.necessario===true).length);
  count++;
}
ctx.q={numeroOriginal:1,prova:'ENEM',conteudo:{recortes:[{tipo:'questao',imagem:'/questoes/enem/enem-2026-dia-1-amarelo/q-1.webp'},{tipo:'apoio',imagem:'/questoes/enem/enem-2026-dia-1-amarelo/apoio.webp'},{tipo:'questao',imagem:'https://example.invalid/injetado.webp'}]}};
ctx.container=new Node('div');vm.runInContext('recortesOriginais(q,container)',ctx);
assert.equal(nodes(ctx.container).filter(n=>n.tagName==='img').length,1);
async function main(){
  const previous=document.getElementById('proxima').onclick;
  const choice=vm.runInContext('escolherIdiomaEnem()',ctx);
  assert.equal(document.getElementById('proxima').disabled,true);
  assert.equal(document.getElementById('opcoes').children.length,2);
  const spanish=document.getElementById('opcoes').children[1].children[0];
  spanish.onchange();assert.equal(document.getElementById('proxima').disabled,false);
  document.getElementById('proxima').onclick();assert.equal(await choice,'ESPANHOL');
  assert.equal(document.getElementById('proxima').onclick,previous);
  const p=data.provas[0],q=p.questoes.find(q=>q.idioma==='ESPANHOL');
  ctx.attempt={id:1,tipo:'ENEM',idioma:'ESPANHOL',data:'2026-11-25',proximaLiberacao:'2026-12-02',concluido:false,questoes:[{...q,prova:p.nome,numeroOriginal:q.numeroOriginal,alternativaSelecionada:null}]};
  vm.runInContext('simulado=attempt; indice=0; mostrar()',ctx);
  assert(document.getElementById('periodo').textContent.includes('Espanhol'));
  assert.equal(document.getElementById('respostas').querySelector('legend').textContent,'Qual alternativa você escolhe?');
  assert.equal(document.getElementById('opcoes').children.length,5);
  assert(document.getElementById('fonte').textContent.endsWith('Espanhol'));
  assert(document.getElementById('questaoOriginal').textContent.includes(String(q.numeroOriginal).padStart(2,'0')));
  console.log(`OK: ${count} questões exibem exatamente os recortes aprovados; apoio necessário, URLs seguras, escolha de idioma e controles existentes.`);
}
main().catch(e=>{console.error(e);process.exitCode=1});
