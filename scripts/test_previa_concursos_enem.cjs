const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
class Node{constructor(tag){this.tagName=tag;this.children=[];this.style={setProperty(k,v){this[k]=v}};this.classList={toggle(){},add(){}};this.value='0';}append(...x){this.children.push(...x)}replaceChildren(...x){this.children=[...x]}setAttribute(k,v){this[k]=v}scrollIntoView(){}querySelector(tag){return this.children.find(n=>n.tagName===tag)}}
const html=fs.readFileSync('tmp/previa-concursos-enem/previa-concursos-padrao-enem.html','utf8');
const ids=new Map();function node(id){if(!ids.has(id))ids.set(id,new Node('div'));return ids.get(id)}
const scripts=[...html.matchAll(/<script([^>]*)>([\s\S]*?)<\/script>/g)];
for(const [,attrs,text] of scripts){const id=attrs.match(/id="([^"]+)"/);if(id)node(id[1]).textContent=text}
node('respostas').append(new Node('legend'));node('zoom').value=100;
const context={document:{getElementById:node,createElement:tag=>new Node(tag),querySelectorAll:()=>[],querySelector:()=>null},location:{replace(){}},console,localStorage:{clear(){}}};context.window=context;
const ctx=vm.createContext(context);for(const [,attrs,text] of scripts)if(!attrs.includes('application/json'))vm.runInContext(text,ctx);
const nodes=n=>[n,...n.children.flatMap(nodes)];
async function test(){for(let i=0;i<12;i++)await Promise.resolve();
 let count=0;const proofs=vm.runInContext('PREVIEW_DATA.provas',ctx);
 for(let p=0;p<proofs.length;p++){
  vm.runInContext(`selecionarProva(${p})`,ctx);
  for(let q=0;q<proofs[p].questoes.length;q++){
   vm.runInContext(`indice=${q};mostrar()`,ctx);
   const images=nodes(node('paginas')).filter(n=>n.tagName==='img');
   assert.equal(images.length,proofs[p].questoes[q].conteudo.recortes.length);
   assert(images.every(n=>n.src.startsWith('data:image/webp;base64,')));
   assert(!nodes(node('paginas')).some(n=>n.tagName==='iframe'));
   assert.equal(node('opcoes').children.length,proofs[p].questoes[q].alternativas.length);count++;
  }
 }
 assert.equal(count,364);vm.runInContext('selecionarProva(0);indice=4;mostrar()',ctx);
 assert(!nodes(node('paginas')).some(n=>n.textContent==='TEXTO DE APOIO'));
 const answer=proofs[0].questoes[4].gabarito,index=proofs[0].questoes[4].alternativas.findIndex(a=>a.letra===answer);
 node('opcoes').children[index].children[0].onchange();for(let i=0;i<12;i++)await Promise.resolve();
 node('finalizar').onclick();assert(node('correcao').textContent.startsWith('Você acertou.'));
 node('proxima').onclick();node('anterior').onclick();assert.equal(node('opcoes').children[index].children[0].checked,true);
 vm.runInContext('selecionarProva(7);indice=17;mostrar()',ctx);node('finalizar').onclick();assert(node('correcao').textContent.includes('anulada'));
 assert(!html.includes('<link rel="stylesheet"'));assert(!html.includes('<script src='));
 console.log('OK: 364 questões, imagens embutidas, alternativas ABCD/ABCDE, navegação, correção, respostas em memória, apoio e anulada.');
}
test().catch(e=>{console.error(e);process.exitCode=1});
