import { SQL } from "bun";
const env=Bun.env;
if(env.DB_NAME!=="evoluamais"||!env.DB_ROOT_PASSWORD||!env.APP_PASSWORD||!env.CONCURSO_PASSWORD)throw new Error("Configuracao ausente");
const common={adapter:"mysql",hostname:env.DB_HOST,port:Number(env.DB_PORT||3306),database:env.DB_NAME,tls:"require",max:1,connectionTimeout:15};
const root=new SQL({...common,username:"root",password:env.DB_ROOT_PASSWORD});
const app=new SQL({...common,username:"evolua_app",password:env.APP_PASSWORD});
try {
 const columns=await root.unsafe("SELECT COLUMN_NAME,DATA_TYPE,IS_NULLABLE FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='estudante' AND COLUMN_NAME='objetivo_prova'");
 if(!columns.length) await root.unsafe("ALTER TABLE estudante ADD COLUMN objetivo_prova VARCHAR(20) DEFAULT NULL, ALGORITHM=INSTANT");
 const schema=await root.unsafe("SELECT COLUMN_NAME,DATA_TYPE,IS_NULLABLE FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='estudante' AND COLUMN_NAME='objetivo_prova'");
 if(schema.length!==1||schema[0].DATA_TYPE!=="varchar"||schema[0].IS_NULLABLE!=="YES")throw new Error("Esquema inesperado");
 const verify=await app.unsafe("SELECT COUNT(*) estudantes,COUNT(objetivo_prova) com_objetivo FROM estudante");
 const archive=await app.unsafe("SELECT COUNT(*) questoes,SUM(q.anulada=0) ativas FROM questao q JOIN prova p ON p.id_prova=q.id_prova WHERE p.tipo='ETEC'");
 console.log(JSON.stringify({status:"OK",migracao:"05_objetivo_estudante",adicionada:!columns.length,contaAplicacaoLeitura:true,schema,verify,archive}));
 await importarConcursos();
 await executarAcervoCompleto();
} catch(error) {
 console.error(JSON.stringify({status:"ERROR",migracao:"05_objetivo_estudante",code:error.code||null}));process.exitCode=1;
} finally {await app.close();await root.close();}

async function importarConcursos() {
 const carga=[{"nome":"INSS - Tecnico do Seguro Social (2022)","descricao":"Nivel medio. Prova objetiva. Caderno e gabarito para consulta externa.","tipo":"CONCURSO","codigo":"INSS-2022-TECNICO-SEGURO-SOCIAL","edicao":"INSS-2022","ano":2022,"etapa":"OBJETIVA","caderno":"CADERNO OBJETIVO","orgao":"Instituto Nacional do Seguro Social (INSS)","cargo":"Tecnico do Seguro Social","banca":"CEBRASPE","url_prova":"https://arquivos.qconcursos.com/prova/arquivo_prova/89730/cespe-cebraspe-2022-inss-tecnico-do-seguro-social-prova.pdf","url_gabarito":"https://arquivos.qconcursos.com/prova/arquivo_gabarito/89730/cespe-cebraspe-2022-inss-tecnico-do-seguro-social-gabarito.pdf","status_importacao":"RASCUNHO"},{"nome":"TJ-SP - Escrevente Tecnico Judiciario (2023)","descricao":"Nivel medio. Prova objetiva aplicada em 28/05/2023. Caderno e gabarito para consulta externa.","tipo":"CONCURSO","codigo":"TJSP-2023-ESCREVENTE-TECNICO","edicao":"TJSP-2023","ano":2023,"etapa":"OBJETIVA","caderno":"VERSAO 3","orgao":"Tribunal de Justica do Estado de Sao Paulo (TJ-SP)","cargo":"Escrevente Tecnico Judiciario","banca":"VUNESP","url_prova":"https://arquivos.qconcursos.com/prova/arquivo_prova/94462/vunesp-2023-tj-sp-escrevente-tecnico-judiciario-prova.pdf","url_gabarito":"https://arquivos.qconcursos.com/prova/arquivo_gabarito/94462/vunesp-2023-tj-sp-escrevente-tecnico-judiciario-gabarito.pdf","status_importacao":"RASCUNHO"},{"nome":"Policia Federal - Agente Administrativo (2014)","descricao":"Nivel intermediario. Prova objetiva do Plano Especial de Cargos. PDF e gabarito oficial da PF.","tipo":"CONCURSO","codigo":"PF-2014-AGENTE-ADMINISTRATIVO","edicao":"PF-2014","ano":2014,"etapa":"OBJETIVA","caderno":"CARGO 9 - AGENTE ADMINISTRATIVO","orgao":"Departamento de Policia Federal","cargo":"Agente Administrativo","banca":"CESPE/CEBRASPE","url_prova":"https://www.gov.br/pf/pt-br/acesso-a-informacao/servidores/concursos/provas-e-gabaritos-de-concursos-anteriores/Concurso%20Plano%20Especial%20de%20Cargos%20-%202013/Prova%20de%20Agente%20Administrativo.pdf/@@download/file","url_gabarito":"https://www.gov.br/pf/pt-br/acesso-a-informacao/servidores/concursos/provas-e-gabaritos-de-concursos-anteriores/Concurso%20Plano%20Especial%20de%20Cargos%20-%202013/Gabarito%20Agente%20Administrativo.PDF/@@download/file","status_importacao":"RASCUNHO"},{"nome":"Fortaleza - Guarda Municipal (2023)","descricao":"Nivel medio. Concurso da Prefeitura de Fortaleza. Caderno tipo A e gabarito para consulta externa.","tipo":"CONCURSO","codigo":"FORTALEZA-2023-GUARDA-MUNICIPAL","edicao":"FORTALEZA-2023","ano":2023,"etapa":"OBJETIVA","caderno":"TIPO A","orgao":"Prefeitura Municipal de Fortaleza (CE)","cargo":"Guarda Municipal","banca":"IDECAN","url_prova":"https://arquivos.qconcursos.com/prova/arquivo_prova/95032/idecan-2023-prefeitura-de-fortaleza-ce-guarda-municipal-prova.pdf","url_gabarito":"https://arquivos.qconcursos.com/prova/arquivo_gabarito/95032/idecan-2023-prefeitura-de-fortaleza-ce-guarda-municipal-gabarito.pdf","status_importacao":"RASCUNHO"},{"nome":"TJ-RN - Tecnico Judiciario - Area Judiciaria (2023)","descricao":"Nivel medio. Prova objetiva tipo 1 - branca. Gabarito definitivo.","tipo":"CONCURSO","codigo":"TJRN-2023-TECNICO-JUDICIARIO-JUDICIARIA","edicao":"TJRN-2023","ano":2023,"etapa":"OBJETIVA","caderno":"TIPO 1 - BRANCA","orgao":"Tribunal de Justica do Estado do Rio Grande do Norte (TJ-RN)","cargo":"Tecnico Judiciario - Area Judiciaria","banca":"FGV","url_prova":"https://arquivos.qconcursos.com/prova/arquivo_prova/94852/fgv-2023-tj-rn-tecnico-judiciario-area-judiciaria-prova.pdf","url_gabarito":"https://arquivos.qconcursos.com/prova/arquivo_gabarito/94852/fgv-2023-tj-rn-tecnico-judiciario-area-judiciaria-gabarito.pdf","status_importacao":"RASCUNHO"},{"nome":"Campinas - Agente Administrativo (2019)","descricao":"Nivel medio. Concurso publico - edital 09/2019. Prova objetiva e gabarito para consulta externa.","tipo":"CONCURSO","codigo":"CAMPINAS-2019-AGENTE-ADMINISTRATIVO","edicao":"CAMPINAS-2019","ano":2019,"etapa":"OBJETIVA","caderno":"CODIGO 002","orgao":"Prefeitura Municipal de Campinas (SP)","cargo":"Agente Administrativo","banca":"VUNESP","url_prova":"https://arquivos.qconcursos.com/prova/arquivo_prova/65678/vunesp-2019-prefeitura-de-campinas-sp-agente-administrativo-prova.pdf","url_gabarito":"https://arquivos.qconcursos.com/prova/arquivo_gabarito/65678/vunesp-2019-prefeitura-de-campinas-sp-agente-administrativo-gabarito.pdf","status_importacao":"RASCUNHO"},{"nome":"DPE-RS - Tecnico - Area Administrativa (2023)","descricao":"Nivel medio. Prova objetiva tipo 4 - azul. Gabarito definitivo.","tipo":"CONCURSO","codigo":"DPE-RS-2023-TECNICO-ADMINISTRATIVA","edicao":"DPE-RS-2023","ano":2023,"etapa":"OBJETIVA","caderno":"TIPO 4 - AZUL","orgao":"Defensoria Publica do Estado do Rio Grande do Sul (DPE-RS)","cargo":"Tecnico - Area Administrativa","banca":"FGV","url_prova":"https://arquivos.qconcursos.com/prova/arquivo_prova/95770/fgv-2023-dpe-rs-tecnico-area-administrativa-prova.pdf","url_gabarito":"https://arquivos.qconcursos.com/prova/arquivo_gabarito/95770/fgv-2023-dpe-rs-tecnico-area-administrativa-gabarito.pdf","status_importacao":"RASCUNHO"},{"nome":"UFRJ - Assistente em Administracao (2017)","descricao":"Nivel medio. Edital 455/2017. Caderno assistente em administracao e gabarito A.","tipo":"CONCURSO","codigo":"UFRJ-2017-ASSISTENTE-ADMINISTRACAO-B206","edicao":"UFRJ-2017","ano":2017,"etapa":"OBJETIVA","caderno":"B-206 - GABARITO A","orgao":"Universidade Federal do Rio de Janeiro (UFRJ)","cargo":"Assistente em Administracao - Geral","banca":"PR-4 UFRJ","url_prova":"https://arquivos.qconcursos.com/prova/arquivo_prova/56189/pr-4-ufrj-2017-ufrj-assistente-em-administracao-prova.pdf","url_gabarito":"https://arquivos.qconcursos.com/prova/arquivo_gabarito/56189/pr-4-ufrj-2017-ufrj-assistente-em-administracao-gabarito.pdf","status_importacao":"RASCUNHO"},{"nome":"BNB - Analista Bancario 1 (2018)","descricao":"Nivel medio. Caderno de prova CEBRASPE. Gabarito definitivo publicado pelo Banco do Nordeste.","tipo":"CONCURSO","codigo":"BNB-2018-ANALISTA-BANCARIO-1","edicao":"BNB-2018","ano":2018,"etapa":"OBJETIVA","caderno":"CADERNO OBJETIVO","orgao":"Banco do Nordeste do Brasil (BNB)","cargo":"Analista Bancario 1","banca":"CESPE/CEBRASPE","url_prova":"https://arquivos.qconcursos.com/prova/arquivo_prova/59579/cespe-2018-bnb-analista-bancario-prova.pdf","url_gabarito":"https://www.bnb.gov.br/documents/45807/73822/Gabarito%2BAnalista%2BBanc%C3%A1rio%2B1%2B2018.pdf/e7b0486b-d482-3af9-f36f-6695b0d4534a?t=1642167566229&version=1.0","status_importacao":"RASCUNHO"},{"nome":"Caixa - Tecnico Bancario Novo (2024)","descricao":"Nivel medio. Edital 01/2024/NM. Caderno objetivo e gabarito 3.","tipo":"CONCURSO","codigo":"CAIXA-2024-TECNICO-BANCARIO-NOVO","edicao":"CAIXA-2024","ano":2024,"etapa":"OBJETIVA","caderno":"PROVA 1 - GABARITO 3","orgao":"Caixa Economica Federal","cargo":"Tecnico Bancario Novo","banca":"Fundacao Cesgranrio","url_prova":"https://arquivos.qconcursos.com/prova/arquivo_prova/109980/cesgranrio-2024-caixa-tecnico-bancario-novo-prova.pdf","url_gabarito":"https://arquivos.qconcursos.com/prova/arquivo_gabarito/109980/cesgranrio-2024-caixa-tecnico-bancario-novo-gabarito.pdf","status_importacao":"RASCUNHO"}];
 const campos=["nome","descricao","tipo","codigo","edicao","ano","etapa","caderno","orgao","cargo","banca","url_prova","url_gabarito","status_importacao"];
 const sql=new SQL({...common,username:"editor_concurso",password:env.CONCURSO_PASSWORD});
 let locked=false, committed=false;
 try {
  const lock=await sql.unsafe("SELECT GET_LOCK('evolua_concursos_importacao',15) adquirido");
  locked=Number(lock[0].adquirido)===1;
  if(!locked)throw new Error("IMPORTACAO_OCUPADA");
  const table=await sql.unsafe("SELECT ENGINE FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='prova'");
  const unique=await sql.unsafe("SELECT INDEX_NAME FROM information_schema.STATISTICS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='prova' AND NON_UNIQUE=0 GROUP BY INDEX_NAME HAVING COUNT(*)=1 AND MIN(COLUMN_NAME)='codigo' AND MAX(COALESCE(SUB_PART,0))=0");
  if(table[0]?.ENGINE!=="InnoDB"||!unique.length)throw new Error("SCHEMA_INESPERADO");
  await sql.unsafe("SET SESSION sql_mode=CONCAT_WS(',',@@SESSION.sql_mode,'STRICT_ALL_TABLES')");
  await sql.unsafe("START TRANSACTION");
  const preservacao="SELECT (SELECT COUNT(*) FROM questao) questoes,(SELECT COUNT(*) FROM alternativa) alternativas,(SELECT COUNT(*) FROM prova WHERE tipo='ETEC') provas_etec,(SELECT COUNT(*) FROM questao q JOIN prova p ON p.id_prova=q.id_prova WHERE p.tipo='ETEC') questoes_etec";
  const before=await sql.unsafe(preservacao);
  const codes=carga.map(r=>r.codigo);
  const query="SELECT id_prova,codigo,tipo,status_importacao,url_prova,url_gabarito FROM prova WHERE codigo IN ("+codes.map(()=>"?").join(",")+") ORDER BY codigo FOR UPDATE";
  const existing=await sql.unsafe(query,codes);
  if(existing.some(r=>r.tipo!=="CONCURSO"))throw new Error("CONFLITO_CATEGORIA");
  const seen=new Set(existing.map(r=>r.codigo));
  let novas=0;
  for(const row of carga) {
   if(seen.has(row.codigo))continue;
   await sql.unsafe("INSERT INTO prova("+campos.join(",")+") VALUES ("+campos.map(()=>"?").join(",")+")",campos.map(c=>row[c]));
   novas++;
  }
  const result=await sql.unsafe(query,codes);
  if(result.length!==10||result.some(r=>r.tipo!=="CONCURSO"||!r.url_prova||!r.url_gabarito||!["RASCUNHO","VALIDADA"].includes(r.status_importacao)))throw new Error("CONFERENCIA_FALHOU");
  const after=await sql.unsafe(preservacao);
  if(JSON.stringify(before)!==JSON.stringify(after))throw new Error("CONTAGENS_DIVERGENTES");
  await sql.unsafe("COMMIT"); committed=true;
  const confirm=await sql.unsafe(query,codes);
  console.log(JSON.stringify({status:"OK",operacao:"06_importacao_10_concursos",conta:"editor_concurso",banco:env.DB_NAME,total:confirm.length,novas,existentes:existing.length,questoes_importadas:0,preservado:before,provas:confirm.map(r=>({id_prova:r.id_prova,codigo:r.codigo,status:r.status_importacao,link_prova:!!r.url_prova,link_gabarito:!!r.url_gabarito}))}));
  const repeat=await sql.unsafe(query,codes);
  if(repeat.length!==10)throw new Error("RELEITURA_FALHOU");
 } catch(error) {
  if(!committed)await sql.unsafe("ROLLBACK");
  console.error(JSON.stringify({status:"ERROR",operacao:"06_importacao_10_concursos",confirmado:committed,code:error.code||null,etapa:error.code?null:error.message}));
  process.exitCode=1;
 } finally {
  if(locked)await sql.unsafe("SELECT RELEASE_LOCK('evolua_concursos_importacao')");
  await sql.close();
 }
}


async function importarQuestoesConcursos(sql: SQL, dataset: any) {
    if (dataset.formato !== 1 || dataset.tipo !== "CONCURSO" || dataset.provas.length !== 10)
        throw new Error("Acervo de concursos inválido");
    const lock = await sql.unsafe("SELECT GET_LOCK('evolua_concursos_questoes',15) adquirido");
    if (Number(lock[0].adquirido) !== 1) throw new Error("Importação em andamento");
    const audit = [];
    try {
        await sql.unsafe("SET SESSION sql_mode=CONCAT_WS(',',@@SESSION.sql_mode,'STRICT_ALL_TABLES')");
        const disciplinas = await sql.unsafe("SELECT id_disciplina FROM disciplina WHERE nome='Conhecimentos gerais' ORDER BY id_disciplina LIMIT 1");
        if (disciplinas.length !== 1) throw new Error("Disciplina de conteúdo não localizada");
        const disciplina = disciplinas[0].id_disciplina;
        for (const prova of dataset.provas) {
            const seen = new Set();
            for (const q of prova.questoes) {
                const letras = q.alternativas.map((a: any) => a.letra).join("");
                if (!Number.isInteger(q.numero) || q.numero < 1 || seen.has(q.numero)
                    || !["CE", "ABCD", "ABCDE"].includes(letras)
                    || !q.enunciado?.trim() || q.alternativas.some((a: any) => !a.texto?.trim())
                    || (q.anulada ? q.gabarito !== null : !q.alternativas.some((a: any) => a.letra === q.gabarito))
                    || !/^[a-f0-9]{64}$/.test(q.hashFonte) || q.conteudo?.modo !== "pdf_original")
                    throw new Error(`Questão inválida: ${prova.codigo}/${q.numero}`);
                seen.add(q.numero);
            }
            if (seen.size !== prova.questoes.length || !seen.has(prova.questoes.length)) throw new Error("Numeração incompleta");
            await sql.unsafe("START TRANSACTION");
            try {
                const found = await sql.unsafe("SELECT id_prova,tipo FROM prova WHERE codigo=? FOR UPDATE", [prova.codigo]);
                if (found.length !== 1 || found[0].tipo !== "CONCURSO") throw new Error("Prova ausente ou categoria divergente");
                const id = found[0].id_prova;
                let novas = 0;
                for (const q of prova.questoes) {
                    const old = await sql.unsafe("SELECT id_questao,hash_fonte,enunciado,anulada FROM questao WHERE id_prova=? AND numero_original=?", [id, q.numero]);
                    let questao;
                    if (old.length) {
                        if (old[0].hash_fonte !== q.hashFonte || old[0].enunciado !== q.enunciado || Number(old[0].anulada) !== Number(q.anulada))
                            throw new Error(`Conteúdo existente diverge: ${prova.codigo}/${q.numero}`);
                        questao = old[0].id_questao;
                    } else {
                        await sql.unsafe("INSERT INTO questao(enunciado,dificuldade,id_disciplina,id_prova,numero_original,anulada,conteudo_json,hash_fonte) VALUES (?,NULL,?,?,?,?,?,?)",
                            [q.enunciado, disciplina, id, q.numero, q.anulada ? 1 : 0, JSON.stringify(q.conteudo), q.hashFonte]);
                        questao = (await sql.unsafe("SELECT LAST_INSERT_ID() id"))[0].id;
                        for (const a of q.alternativas)
                            await sql.unsafe("INSERT INTO alternativa(texto,correta,id_questao,letra) VALUES (?,?,?,?)", [a.texto, a.letra === q.gabarito ? 1 : 0, questao, a.letra]);
                        novas++;
                    }
                    const alternatives = await sql.unsafe("SELECT letra,texto,correta FROM alternativa WHERE id_questao=? ORDER BY letra", [questao]);
                    if (alternatives.length !== q.alternativas.length || alternatives.some((a: any, i: number) =>
                        a.letra !== q.alternativas[i].letra || a.texto !== q.alternativas[i].texto || Number(a.correta) !== Number(a.letra === q.gabarito)))
                        throw new Error(`Alternativas divergentes: ${prova.codigo}/${q.numero}`);
                }
                const count = (await sql.unsafe("SELECT COUNT(*) total FROM questao WHERE id_prova=?", [id]))[0].total;
                if (Number(count) !== prova.questoes.length) throw new Error("Contagem final divergente");
                await sql.unsafe("UPDATE prova SET caderno=?,url_gabarito=?,status_importacao='VALIDADA' WHERE id_prova=?", [prova.caderno, prova.urlGabarito, id]);
                await sql.unsafe("COMMIT");
                const item = {codigo: prova.codigo, total: Number(count), novas, anuladas: prova.questoes.filter((q: any) => q.anulada).length};
                audit.push(item);
                console.log(JSON.stringify({status: "OK", operacao: "questoes_concurso", ...item}));
            } catch (error) { await sql.unsafe("ROLLBACK"); throw error; }
        }
        return audit;
    } finally { await sql.unsafe("SELECT RELEASE_LOCK('evolua_concursos_questoes')"); }
}

async function executarAcervoCompleto() {
 const response=await fetch("https://raw.githubusercontent.com/EduMab/Projeto-De-Extensao-Em-Criacao-De-Sistemas/34fdcd3aa2f5ce6185184dab05e69b4da2c3da7c/acervo/concursos/questoes.json.gz");
 if(!response.ok)throw new Error("Fonte indisponível");
 const bytes=new Uint8Array(await response.arrayBuffer());
 const actual=Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256",bytes))).map(v=>v.toString(16).padStart(2,"0")).join("");
 if(actual!=="6e57b2d1fe9e2f82d9397d973f1d43dd64e5427e7f01696acc9c1880c67534c1")throw new Error("Hash do acervo divergente");
 const dataset=JSON.parse(new TextDecoder().decode(Bun.gunzipSync(bytes)));
 const baseline=await root.unsafe("SELECT COUNT(DISTINCT p.id_prova) provas,COUNT(q.id_questao) questoes FROM prova p JOIN questao q ON q.id_prova=p.id_prova WHERE p.tipo='ETEC'");
 const old=await root.unsafe("SELECT DISTINCT INDEX_NAME FROM information_schema.STATISTICS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='simulado_diario' AND INDEX_NAME='uq_simulado_estudante_dia'");
 const newer=await root.unsafe("SELECT DISTINCT INDEX_NAME FROM information_schema.STATISTICS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='simulado_diario' AND INDEX_NAME='uq_simulado_estudante_tipo_dia'");
 if(!newer.length) {
  if(old.length!==1)throw new Error("Índice de simulados inesperado");
  await root.unsafe("ALTER TABLE simulado_diario DROP INDEX uq_simulado_estudante_dia, ADD UNIQUE KEY uq_simulado_estudante_tipo_dia(id_estudante,tipo,data_simulado)");
 }
 const conteudo=new SQL({...common,username:"editor_concurso",password:env.CONCURSO_PASSWORD});
 try {
  const auditoria=await importarQuestoesConcursos(conteudo,dataset);
  const totals=await conteudo.unsafe("SELECT COUNT(DISTINCT p.id_prova) provas,COUNT(q.id_questao) questoes,SUM(q.anulada) anuladas,SUM(q.anulada=0) ativas FROM prova p JOIN questao q ON p.id_prova=q.id_prova WHERE p.tipo='CONCURSO' AND p.codigo IN ("+dataset.provas.map(()=>"?").join(",")+")",dataset.provas.map(p=>p.codigo));
  const alt=await conteudo.unsafe("SELECT COUNT(*) alternativas FROM alternativa a JOIN questao q ON q.id_questao=a.id_questao JOIN prova p ON p.id_prova=q.id_prova WHERE p.tipo='CONCURSO' AND p.codigo IN ("+dataset.provas.map(()=>"?").join(",")+")",dataset.provas.map(p=>p.codigo));
  const after=await root.unsafe("SELECT COUNT(DISTINCT p.id_prova) provas,COUNT(q.id_questao) questoes FROM prova p JOIN questao q ON q.id_prova=p.id_prova WHERE p.tipo='ETEC'");
  if(JSON.stringify(baseline)!==JSON.stringify(after))throw new Error("Contagens ETEC divergentes");
  if(Number(totals[0].questoes)!==830||Number(totals[0].ativas)!==800||Number(alt[0].alternativas)!==2990)throw new Error("Total do acervo divergente");
  console.log(JSON.stringify({status:"OK",operacao:"ACERVO_COMPLETO_CONCURSOS",commit:"34fdcd3aa2f5ce6185184dab05e69b4da2c3da7c",sha256:actual,auditoria,totais:totals,alternativas:alt,etec_preservado:after}));
 } finally {await conteudo.close();}
}
