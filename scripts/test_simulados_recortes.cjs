const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
class Node { constructor(tag){this.tagName=tag;this.children=[];this.style={setProperty(k,v){this[k]=v}};this.classList={toggle(){}};}append(...x){this.children.push(...x)}setAttribute(){}replaceChildren(...x){this.children=[...x]}scrollIntoView(){}}
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
