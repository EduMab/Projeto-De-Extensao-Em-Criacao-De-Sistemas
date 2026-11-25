const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
const file=process.argv[2]||'tmp/previa-enem/previa-enem-amarelo.html';
const html=fs.readFileSync(file,'utf8');const data=JSON.parse(html.match(/<script id="dados" type="application\/json">([\s\S]*?)<\/script>/)[1]);
class Node{constructor(tag){this.tagName=tag;this.children=[];this.style={setProperty(k,v){this[k]=v}};this.value='';this.hidden=false;}append(...n){this.children.push(...n)}replaceChildren(...n){this.children=[...n]}}
const ids=new Map();const document={getElementById(id){if(!ids.has(id))ids.set(id,new Node('div'));return ids.get(id)},createElement(tag){return new Node(tag)}};
document.getElementById('dados').textContent=JSON.stringify(data);document.getElementById('idioma').value='TODOS';
const ctx=vm.createContext({document,console});const script=html.match(/<script>\n([\s\S]*?)<\/script>/)[1];vm.runInContext(script,ctx);
assert.equal(vm.runInContext('EXEMPLOS.length',ctx),30);
for(let i=0;i<data.length;i++){vm.runInContext(`indice=${i};mostrar()`,ctx);assert(ids.get('recortes').children.length>0);assert.equal(ids.get('opcoes').children.length,5);for(const card of ids.get('recortes').children){const im=card.children.at(-1);assert.match(im.src,/^data:image\/webp;base64,/);assert(im.src.length>1000);}}
vm.runInContext('indice=0;mostrar()',ctx);ids.get('opcoes').children[0].children[0].onchange();ids.get('conferir').onclick();assert.match(ids.get('resultado').textContent,/Gabarito oficial: alternativa/);
for(const idioma of ['INGLES','ESPANHOL']){ids.get('idioma').value=idioma;ids.get('idioma').onchange();assert(vm.runInContext('lista.every(e=>!e.idioma||e.idioma==="'+idioma+'")',ctx));}
ids.get('zoom').oninput({target:{value:'150'}});assert.equal(ids.get('estudo').style['--crop-scale'],1.5);
assert(!/<iframe|fetch\(/.test(html));console.log('OK: 30 exemplos, imagens incorporadas, idioma, navegação, marcação, gabarito e zoom; sem requisições ao banco.');
