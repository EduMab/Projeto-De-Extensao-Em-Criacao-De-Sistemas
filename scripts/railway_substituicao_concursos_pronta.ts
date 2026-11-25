import { SQL } from 'bun';

export const CODIGOS_ANTIGOS = ['INSS-2022-TECNICO-SEGURO-SOCIAL','TJSP-2023-ESCREVENTE-TECNICO','PF-2014-AGENTE-ADMINISTRATIVO','FORTALEZA-2023-GUARDA-MUNICIPAL','TJRN-2023-TECNICO-JUDICIARIO-JUDICIARIA','CAMPINAS-2019-AGENTE-ADMINISTRATIVO','DPE-RS-2023-TECNICO-ADMINISTRATIVA','UFRJ-2017-ASSISTENTE-ADMINISTRACAO-B206','BNB-2018-ANALISTA-BANCARIO-1','CAIXA-2024-TECNICO-BANCARIO-NOVO'];
const ETEC = "SELECT COUNT(DISTINCT p.id_prova) provas,COUNT(q.id_questao) questoes,SUM(q.anulada=0) ativas FROM prova p LEFT JOIN questao q ON q.id_prova=p.id_prova WHERE p.tipo='ETEC'";
const HISTORY = 'SELECT (SELECT COUNT(*) FROM simulado_diario) simulados,(SELECT COUNT(*) FROM simulado_diario_questao) itens,(SELECT COUNT(*) FROM resposta) respostas,(SELECT COUNT(*) FROM estudante) estudantes';
const slots = (xs: any[]) => xs.map(()=>'?').join(',');
export function validarRecortes(dataset: any) {
    if(dataset.formato!==2 || dataset.tipo!=='CONCURSO' || dataset.provas?.length!==10) throw Error('Acervo inválido');
    const codes=new Set(); let total=0;
    for(const p of dataset.provas) {
        if(!/^PCI-[A-Z0-9-]+$/.test(p.codigo)||codes.has(p.codigo)||!p.nome||p.nome.length>100||!p.questoes.length)throw Error('Prova inválida');
        codes.add(p.codigo);
        for(const [i,q] of p.questoes.entries()) {
            const letters=q.alternativas.map((a:any)=>a.letra).join('');
            if(q.numero!==i+1 || !['ABCD','ABCDE'].includes(letters)||!q.enunciado?.trim()||q.conteudo?.modo!=='recorte_original'
                || !q.conteudo.recortes?.some((r:any)=>r.tipo==='questao') || !/^[a-f0-9]{64}$/.test(q.hashFonte)
                || (q.anulada?q.gabarito!==null:!letters.includes(q.gabarito))
                || q.conteudo.recortes.some((r:any)=>!['questao','apoio'].includes(r.tipo)||!/^\/questoes\/concursos\/pci-[a-z0-9-]+\/[a-z0-9-]+\.webp$/.test(r.imagem)))throw Error(`Questão inválida: ${p.codigo}/${i+1}`);
            total++;
        }
    }
    if(total!==364)throw Error('Total de questões divergente');
}

// A conta deve ter DELETE somente nas tabelas de conteúdo; nunca há DELETE de usuários ou histórico.
export async function substituirConcursos(sql: SQL, dataset: any, aplicar=true) {
    validarRecortes(dataset);
    const locks=['evolua_concursos_importacao','evolua_concursos_questoes']; const acquired=[];
    let transaction=false;
    try {
        for(const name of locks) {
            if(Number((await sql.unsafe('SELECT GET_LOCK(?,15) adquirido',[name]))[0].adquirido)!==1)throw Error('Importação concorrente');
            acquired.push(name);
        }
        await sql.unsafe("SET SESSION sql_mode=CONCAT_WS(',',@@SESSION.sql_mode,'STRICT_ALL_TABLES')");
        await sql.unsafe('START TRANSACTION'); transaction=true;
        const before={etec:await sql.unsafe(ETEC),historico:await sql.unsafe(HISTORY)};
        const discipline=await sql.unsafe("SELECT id_disciplina FROM disciplina WHERE nome='Conhecimentos gerais' ORDER BY id_disciplina LIMIT 1");
        if(discipline.length!==1)throw Error('Disciplina ausente');
        const audit=[];
        for(const p of dataset.provas) {
            let found=await sql.unsafe('SELECT id_prova,tipo FROM prova WHERE codigo=? FOR UPDATE',[p.codigo]);
            if(found.length&&found[0].tipo!=='CONCURSO')throw Error('Categoria divergente');
            if(!found.length) {
                await sql.unsafe("INSERT INTO prova(nome,descricao,tipo,codigo,edicao,ano,etapa,caderno,banca,url_prova,url_gabarito,status_importacao) VALUES (?,?,'CONCURSO',?,?,?,'OBJETIVA',?,?,?,?,'RASCUNHO')",[p.nome,`Ensino médio. Caderno original recortado por questão.${p.gabaritoPreliminar?' Gabarito preliminar da fonte.':''}`,p.codigo,p.edicao,p.ano,p.caderno,p.banca,p.urlProva,p.urlGabarito]);
                found=await sql.unsafe('SELECT id_prova,tipo FROM prova WHERE codigo=?',[p.codigo]);
            }
            const id=found[0].id_prova;let novas=0;
            for(const q of p.questoes) {
                const old=await sql.unsafe('SELECT id_questao,hash_fonte,enunciado,anulada,conteudo_json FROM questao WHERE id_prova=? AND numero_original=?',[id,q.numero]);
                let qid;
                if(old.length) {
                    if(old[0].hash_fonte!==q.hashFonte||old[0].enunciado!==q.enunciado||Number(old[0].anulada)!==Number(q.anulada))throw Error('Questão existente divergente');
                    const content=typeof old[0].conteudo_json==='string'?JSON.parse(old[0].conteudo_json):old[0].conteudo_json;
                    const canonical=(v:any):string=>JSON.stringify(v&&typeof v==='object'&&!Array.isArray(v)?Object.fromEntries(Object.keys(v).sort().map(k=>[k,JSON.parse(canonical(v[k]))])):Array.isArray(v)?v.map(x=>JSON.parse(canonical(x))):v);
                    if(canonical(content)!==canonical(q.conteudo))throw Error('Recortes existentes divergentes');
                    qid=old[0].id_questao;
                } else {
                    await sql.unsafe('INSERT INTO questao(enunciado,id_disciplina,id_prova,numero_original,anulada,conteudo_json,hash_fonte) VALUES (?,?,?,?,?,?,?)',[q.enunciado,discipline[0].id_disciplina,id,q.numero,Number(q.anulada),JSON.stringify(q.conteudo),q.hashFonte]);
                    qid=(await sql.unsafe('SELECT LAST_INSERT_ID() id'))[0].id;
                    for(const a of q.alternativas)await sql.unsafe('INSERT INTO alternativa(texto,correta,id_questao,letra) VALUES (?,?,?,?)',[a.texto,Number(a.letra===q.gabarito),qid,a.letra]);
                    novas++;
                }
                const alternatives=await sql.unsafe('SELECT letra,texto,correta FROM alternativa WHERE id_questao=? ORDER BY letra',[qid]);
                if(alternatives.length!==q.alternativas.length||alternatives.some((a:any,i:number)=>a.letra!==q.alternativas[i].letra||a.texto!==q.alternativas[i].texto||Number(a.correta)!==Number(a.letra===q.gabarito)))throw Error('Alternativas divergentes');
            }
            if(Number((await sql.unsafe('SELECT COUNT(*) n FROM questao WHERE id_prova=?',[id]))[0].n)!==p.questoes.length)throw Error('Contagem divergente');
            await sql.unsafe("UPDATE prova SET status_importacao='VALIDADA' WHERE id_prova=?",[id]);
            audit.push({codigo:p.codigo,questoes:p.questoes.length,novas});
        }
        const old=await sql.unsafe(`SELECT id_prova,tipo FROM prova WHERE codigo IN (${slots(CODIGOS_ANTIGOS)}) FOR UPDATE`,CODIGOS_ANTIGOS);
        if(old.some((p:any)=>p.tipo!=='CONCURSO'))throw Error('Acervo antigo em categoria divergente');
        let removidas=0,provasRemovidas=0;
        for(const p of old) {
            await sql.unsafe("UPDATE prova SET status_importacao='RASCUNHO' WHERE id_prova=?",[p.id_prova]);
            // Bloqueia as linhas candidatas, mantendo todos os vínculos históricos.
            const disposable=await sql.unsafe(`SELECT q.id_questao FROM questao q WHERE q.id_prova=?
                AND NOT EXISTS(SELECT 1 FROM simulado_diario_questao s WHERE s.id_questao=q.id_questao)
                AND NOT EXISTS(SELECT 1 FROM resposta r WHERE r.id_questao=q.id_questao)
                AND NOT EXISTS(SELECT 1 FROM resposta r JOIN alternativa a ON a.id_alternativa=r.id_alternativa WHERE a.id_questao=q.id_questao)
                AND NOT EXISTS(SELECT 1 FROM simulado_diario_questao s JOIN alternativa a ON a.id_alternativa=s.id_alternativa WHERE a.id_questao=q.id_questao) FOR UPDATE`,[p.id_prova]);
            for(const q of disposable) {
                await sql.unsafe('DELETE FROM alternativa WHERE id_questao=?',[q.id_questao]);
                await sql.unsafe('DELETE FROM questao WHERE id_questao=?',[q.id_questao]);removidas++;
            }
            const refs=await sql.unsafe('SELECT (SELECT COUNT(*) FROM questao WHERE id_prova=?)+(SELECT COUNT(*) FROM estudante WHERE id_prova=?) n',[p.id_prova,p.id_prova]);
            if(Number(refs[0].n)===0){await sql.unsafe('DELETE FROM prova WHERE id_prova=?',[p.id_prova]);provasRemovidas++;}
        }
        const after={etec:await sql.unsafe(ETEC),historico:await sql.unsafe(HISTORY)};
        if(JSON.stringify(before)!==JSON.stringify(after))throw Error('Preservação divergente');
        const codes=dataset.provas.map((p:any)=>p.codigo);
        const totals=await sql.unsafe(`SELECT COUNT(DISTINCT p.id_prova) provas,COUNT(q.id_questao) questoes,SUM(q.anulada=0) ativas FROM prova p JOIN questao q ON q.id_prova=p.id_prova WHERE p.status_importacao='VALIDADA' AND p.codigo IN (${slots(codes)})`,codes);
        const alternatives=await sql.unsafe(`SELECT COUNT(*) alternativas FROM alternativa a JOIN questao q ON q.id_questao=a.id_questao JOIN prova p ON p.id_prova=q.id_prova WHERE p.codigo IN (${slots(codes)})`,codes);
        const expectedAlternatives=dataset.provas.reduce((n:number,p:any)=>n+p.questoes.reduce((n:number,q:any)=>n+q.alternativas.length,0),0);
        if(Number(totals[0].provas)!==10||Number(totals[0].questoes)!==364||Number(totals[0].ativas)!==363||Number(alternatives[0].alternativas)!==expectedAlternatives)throw Error('Totais finais divergentes');
        await sql.unsafe(aplicar?'COMMIT':'ROLLBACK');transaction=false;
        return {status:aplicar?'OK':'SIMULACAO_REVERTIDA',operacao:'SUBSTITUICAO_CONCURSOS_RECORTADOS',audit,totals,alternatives,questoesAntigasExcluidas:removidas,provasAntigasExcluidas:provasRemovidas,provasAntigasSomenteHistorico:old.length-provasRemovidas,preservado:after};
    } catch(e) {if(transaction)await sql.unsafe('ROLLBACK');throw e;}
    finally {for(const name of acquired.reverse())await sql.unsafe('SELECT RELEASE_LOCK(?)',[name]);}
}


// Acrescente este driver à parte exportada de substituir_concursos.ts,
// substituindo a7b4ede0c087abfcabc18b951884d1252a535027 pelo commit revisado. Envie o arquivo completo
// à função PreparacaoBanco. Usa as credenciais já configuradas nessa função.
const ACERVO_COMMIT='a7b4ede0c087abfcabc18b951884d1252a535027';
const env=Bun.env;
if(env.DB_NAME!=='evoluamais'||!env.DB_ROOT_PASSWORD||!/^[a-f0-9]{40}$/.test(ACERVO_COMMIT))throw Error('Configuração ausente');
const url=`https://raw.githubusercontent.com/EduMab/Projeto-De-Extensao-Em-Criacao-De-Sistemas/${ACERVO_COMMIT}/acervo/concursos/questoes-recortadas.json.gz`;
let productionSql: SQL|undefined;
try {
    const response=await fetch(url);
    if(!response.ok)throw Error('Acervo indisponível');
    const bytes=new Uint8Array(await response.arrayBuffer());
    const expected='ffba2ee124765ceab6fc166b9547047a6383a75355999b90261e85df30806372';
    const hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))).map(v=>v.toString(16).padStart(2,'0')).join('');
    if(hash!==expected)throw Error('Hash do acervo divergente');
    const dataset=JSON.parse(new TextDecoder().decode(Bun.gunzipSync(bytes)));
    validarRecortes(dataset);
    const origin='https://evoluamais-api.onrender.com';
    const script=await fetch(origin+'/simulados.js',{signal:AbortSignal.timeout(60000)});
    const scriptText=await script.text();
    const visualPublicado=script.ok&&scriptText.includes('function recortesOriginais');
    console.log(JSON.stringify({status:'VERIFICACAO_PUBLICACAO',httpStatus:script.status,tipo:script.headers.get('content-type'),url:script.url,novoVisual:visualPublicado,carregando:scriptText.toLowerCase().includes('application loading')}));
    if(!visualPublicado)throw Error('A aplicação ainda não publicou o novo visual');
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
    process.exitCode=error.message==='A aplicação ainda não publicou o novo visual'?0:1;
} finally {if(productionSql)await productionSql.close();}
