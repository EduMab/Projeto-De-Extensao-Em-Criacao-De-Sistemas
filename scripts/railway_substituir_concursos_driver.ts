// Acrescente este driver à parte exportada de substituir_concursos.ts,
// substituindo __ACERVO_COMMIT__ pelo commit revisado. Envie o arquivo completo
// à função PreparacaoBanco. Usa as credenciais já configuradas nessa função.
const ACERVO_COMMIT='__ACERVO_COMMIT__';
const env=Bun.env;
if(env.DB_NAME!=='evoluamais'||!env.DB_ROOT_PASSWORD||!/^[a-f0-9]{40}$/.test(ACERVO_COMMIT))throw Error('Configuração ausente');
const url=`https://raw.githubusercontent.com/EduMab/Projeto-De-Extensao-Em-Criacao-De-Sistemas/${ACERVO_COMMIT}/acervo/concursos/questoes-recortadas.json.gz`;
let productionSql: SQL|undefined;
try {
    const response=await fetch(url);
    if(!response.ok)throw Error('Acervo indisponível');
    const bytes=new Uint8Array(await response.arrayBuffer());
    const expected='__ACERVO_SHA256__';
    const hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))).map(v=>v.toString(16).padStart(2,'0')).join('');
    if(hash!==expected)throw Error('Hash do acervo divergente');
    const dataset=JSON.parse(new TextDecoder().decode(Bun.gunzipSync(bytes)));
    validarRecortes(dataset);
    const origin='https://evoluamais-api.onrender.com';
    const script=await fetch(origin+'/simulados.js',{signal:AbortSignal.timeout(60000)});
    if(!script.ok||!(await script.text()).includes('function recortesOriginais'))throw Error('A aplicação ainda não publicou o novo visual');
    const images=[...new Set<string>(dataset.provas.flatMap((p:any)=>p.questoes.flatMap((q:any)=>q.conteudo.recortes.map((r:any)=>r.imagem))))];
    for(let offset=0;offset<images.length;offset+=8) {
        await Promise.all(images.slice(offset,offset+8).map(async path=>{
            const r=await fetch(origin+path,{method:'HEAD',signal:AbortSignal.timeout(30000)});
            if(!r.ok||!r.headers.get('content-type')?.includes('image/webp'))throw Error('Imagem não publicada: '+path);
        }));
    }
    console.log(JSON.stringify({status:'OK',operacao:'ASSETS_PUBLICADOS',imagens:images.length,commit:ACERVO_COMMIT,sha256:hash}));
    productionSql=new SQL({adapter:'mysql',hostname:env.DB_HOST,port:Number(env.DB_PORT||3306),database:env.DB_NAME,username:'root',password:env.DB_ROOT_PASSWORD,tls:'require',max:1,connectionTimeout:15});
    // Uma simulação integral antecede a gravação; ambos validam preservação e totais.
    console.log(JSON.stringify(await substituirConcursos(productionSql,dataset,false)));
    console.log(JSON.stringify(await substituirConcursos(productionSql,dataset,true)));
    // Reexecução confirma idempotência com o estado já gravado.
    const repeat=await substituirConcursos(productionSql,dataset,true);
    if(repeat.audit.some(p=>p.novas!==0))throw Error('Reexecução inseriu duplicatas');
    console.log(JSON.stringify({...repeat,operacao:'REEXECUCAO_CONFIRMADA',commit:ACERVO_COMMIT,sha256:hash}));
} catch(error:any) {
    console.error(JSON.stringify({status:'ERROR',operacao:'SUBSTITUICAO_CONCURSOS',code:error.code||null,etapa:error.code?'Falha SQL; transação revertida':error.message}));
    process.exitCode=1;
} finally {if(productionSql)await productionSql.close();}
