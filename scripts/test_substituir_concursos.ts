import { SQL } from 'bun';
import { strict as assert } from 'node:assert';
import {substituirConcursos,CODIGOS_ANTIGOS} from './substituir_concursos';
const env=Bun.env;
if(env.DB_NAME!=='evolua_concursos_test'||env.DB_HOST!=='127.0.0.1')throw Error('Teste exige banco local isolado');
const sql=new SQL({adapter:'mysql',hostname:env.DB_HOST,port:Number(env.DB_PORT||3306),database:env.DB_NAME,username:'root',password:env.DB_SENHA,tls:false,max:1});
const dataset=JSON.parse(new TextDecoder().decode(Bun.gunzipSync(new Uint8Array(await Bun.file(new URL('../acervo/concursos/questoes-recortadas.json.gz',import.meta.url)).arrayBuffer()))));
const scalar=async(q:string)=>(await sql.unsafe(q))[0].n;
try {
    for(const table of ['simulado_diario_questao','simulado_diario','resposta','desempenho','recomendacao_ia','alternativa','questao','estudante','usuario','prova','disciplina'])await sql.unsafe(`DELETE FROM ${table}`);
    await sql.unsafe("INSERT INTO disciplina(id_disciplina,nome) VALUES (1,'Conhecimentos gerais')");
    await sql.unsafe("INSERT INTO prova(id_prova,nome,tipo,codigo,status_importacao) VALUES (1,'ETEC','ETEC','ETEC-TEST','VALIDADA'),(2,'Antiga vinculada','CONCURSO',?,'VALIDADA'),(3,'Antiga livre','CONCURSO',?,'VALIDADA')",CODIGOS_ANTIGOS.slice(0,2));
    await sql.unsafe("INSERT INTO questao(id_questao,enunciado,id_disciplina,id_prova,numero_original,anulada) VALUES (1,'ETEC mantida',1,1,1,0),(2,'Histórico mantido',1,2,1,0),(3,'Excluir',1,3,1,0)");
    await sql.unsafe("INSERT INTO alternativa(id_alternativa,texto,correta,id_questao,letra) VALUES (1,'A',1,1,'A'),(2,'A',1,2,'A'),(3,'A',1,3,'A')");
    await sql.unsafe("INSERT INTO usuario(id_usuario,nome,email,senha) VALUES (1,'Teste','teste@example.invalid','hash-teste')");
    await sql.unsafe('INSERT INTO estudante(id_estudante,id_usuario,id_prova) VALUES (1,1,2)');
    await sql.unsafe("INSERT INTO simulado_diario(id_simulado,id_estudante,tipo,data_simulado) VALUES (1,1,'CONCURSO','2026-11-23')");
    const frozen=JSON.stringify({enunciado:'Histórico mantido',alternativas:[{id:2,letra:'A'}]});
    await sql.unsafe('INSERT INTO simulado_diario_questao(id_simulado,posicao,id_questao,snapshot_json,id_alternativa,acertou) VALUES (1,1,2,?,2,1)',[frozen]);
    await sql.unsafe('INSERT INTO resposta(id_estudante,id_questao,id_alternativa,acertou) VALUES (1,2,2,1)');
    // Dry run rolls back inserts and removals together.
    assert.equal((await substituirConcursos(sql,dataset,false)).status,'SIMULACAO_REVERTIDA');
    assert.equal(Number(await scalar('SELECT COUNT(*) n FROM prova')),3);
    assert.equal(Number(await scalar('SELECT COUNT(*) n FROM questao')),3);
    // Inject a late SQL error to prove atomic rollback, rather than only input validation.
    const broken=structuredClone(dataset);broken.provas[9].ano='invalido';
    await assert.rejects(()=>substituirConcursos(sql,broken,true));
    assert.equal(Number(await scalar('SELECT COUNT(*) n FROM prova')),3);
    // Apply, preserve FK-linked history, and physically remove unused old content.
    const first=await substituirConcursos(sql,dataset,true);
    assert.equal(first.questoesAntigasExcluidas,1);assert.equal(first.provasAntigasExcluidas,1);
    assert.equal(Number(await scalar('SELECT COUNT(*) n FROM questao WHERE id_questao=2')),1);
    assert.equal(Number(await scalar('SELECT COUNT(*) n FROM questao WHERE id_questao=3')),0);
    assert.equal((await sql.unsafe('SELECT status_importacao FROM prova WHERE id_prova=2'))[0].status_importacao,'RASCUNHO');
    assert.equal(Number(await scalar("SELECT COUNT(*) n FROM questao q JOIN prova p ON p.id_prova=q.id_prova WHERE p.tipo='ETEC'")),1);
    assert.equal(Number(await scalar('SELECT COUNT(*) n FROM resposta')),1);
    const row=(await sql.unsafe('SELECT snapshot_json FROM simulado_diario_questao'))[0].snapshot_json;
    assert.deepEqual(typeof row==='string'?JSON.parse(row):row,JSON.parse(frozen));
    // Repeating the same import leaves IDs, counts and histories intact.
    const ids=await sql.unsafe('SELECT id_questao,hash_fonte FROM questao ORDER BY id_questao');
    const second=await substituirConcursos(sql,dataset,true);
    assert.equal(second.audit.reduce((n,p)=>n+p.novas,0),0);
    assert.deepEqual(await sql.unsafe('SELECT id_questao,hash_fonte FROM questao ORDER BY id_questao'),ids);
    console.log('OK: reversão, falha tardia, substituição, histórico, ETEC e reexecução');
}finally{await sql.close();}
