/** Executar: bun scripts/importar_banco_etec.ts (credenciais somente no ambiente).
 * Requer o schema 01 + migracao 04 previamente aplicados por um administrador.
 * O editor_etec pode importar os dados; este script nunca concede privilegios.
 */
import { SQL } from "bun";

export async function importarETEC(sql: SQL, dataset: any) {
    if (dataset.formato !== 1 || dataset.tipo !== "ETEC" || !Array.isArray(dataset.edicoes)) throw new Error("Formato de acervo invalido");
    const lock = await sql.unsafe("SELECT GET_LOCK('evolua_etec_importacao',15) AS adquirido");
    if (Number(lock[0].adquirido) !== 1) throw new Error("Ja existe uma importacao em andamento");
    const audit = [];
    try {
        const disciplinas = await sql.unsafe("SELECT id_disciplina FROM disciplina WHERE nome='Conhecimentos gerais' ORDER BY id_disciplina LIMIT 1");
        let disciplina = disciplinas[0]?.id_disciplina;
        if (!disciplina) {
            await sql.unsafe("INSERT INTO disciplina(nome) VALUES ('Conhecimentos gerais')");
            disciplina = (await sql.unsafe("SELECT LAST_INSERT_ID() AS id"))[0].id;
        }
        for (const edicao of dataset.edicoes) {
            const expected = edicao.edicao === "2023-1" ? 40 : 50;
            if (!/^ETEC-20\d{2}-S[12]-REGULAR$/.test(edicao.codigo) || edicao.questoes.length !== expected) throw new Error("Edicao invalida");
            const numeros = new Set();
            for (const q of edicao.questoes) {
                if (!Number.isInteger(q.numero) || q.numero < 1 || q.numero > expected || numeros.has(q.numero)
                    || (!q.anulada && !/^[A-E]$/.test(q.gabarito)) || (q.anulada && q.gabarito !== null)
                    || !/^[a-f0-9]{64}$/.test(q.hashFonte) || q.conteudo?.modo !== "pagina_original") throw new Error("Questao/gabarito invalido");
                numeros.add(q.numero);
            }
            await sql.unsafe("START TRANSACTION");
            try {
                let existing = await sql.unsafe("SELECT id_prova,tipo FROM prova WHERE codigo=? FOR UPDATE", [edicao.codigo]);
                let prova = existing[0]?.id_prova;
                if (existing.length && existing[0].tipo !== "ETEC") throw new Error("Codigo ocupado por outra categoria");
                if (!prova) {
                    await sql.unsafe("INSERT INTO prova(nome,descricao,tipo,codigo,edicao,ano,semestre,etapa,caderno,banca,url_prova,url_gabarito,status_importacao) VALUES (?,?,'ETEC',?,?,?,?,'Ingresso','Regular',?,?,?,'RASCUNHO')",
                        [`ETEC ${edicao.ano} - ${edicao.semestre}o semestre`, "Vestibulinho regular; fonte oficial CPS; paginas originais.",
                         edicao.codigo, edicao.edicao, edicao.ano, edicao.semestre, edicao.edicao === "2025-2" ? "IDECAN" : "CPS/FAT", edicao.prova, edicao.gabarito]);
                    prova = (await sql.unsafe("SELECT LAST_INSERT_ID() AS id"))[0].id;
                }
                let novas = 0;
                for (const q of edicao.questoes) {
                    const anteriores = await sql.unsafe("SELECT id_questao,hash_fonte,anulada FROM questao WHERE id_prova=? AND numero_original=?", [prova, q.numero]);
                    let questao = anteriores[0]?.id_questao;
                    if (questao && (anteriores[0].hash_fonte !== q.hashFonte || Number(anteriores[0].anulada) !== Number(q.anulada))) {
                        throw new Error(`Fonte alterada: ${edicao.edicao}/${q.numero}; revisao manual necessaria`);
                    }
                    if (!questao) {
                        await sql.unsafe("INSERT INTO questao(enunciado,dificuldade,id_disciplina,id_prova,numero_original,imagem_url,anulada,conteudo_json,hash_fonte) VALUES (?,NULL,?,?,?,?,?,?,?)",
                            [q.enunciado, disciplina, prova, q.numero, q.imagem, q.anulada ? 1 : 0, JSON.stringify(q.conteudo), q.hashFonte]);
                        questao = (await sql.unsafe("SELECT LAST_INSERT_ID() AS id"))[0].id;
                        for (const letra of ["A", "B", "C", "D", "E"]) {
                            await sql.unsafe("INSERT INTO alternativa(texto,correta,id_questao,letra) VALUES (?,?,?,?)",
                                [`Alternativa ${letra} da pagina original.`, q.gabarito === letra ? 1 : 0, questao, letra]);
                        }
                        novas++;
                    }
                    const alternativas = await sql.unsafe("SELECT letra,correta FROM alternativa WHERE id_questao=? ORDER BY letra", [questao]);
                    if (alternativas.length !== 5 || alternativas.map(a => a.letra).join("") !== "ABCDE"
                        || alternativas.filter(a => Number(a.correta) === 1).map(a => a.letra).join("") !== (q.gabarito || "")) {
                        throw new Error(`Gabarito existente diverge da fonte: ${edicao.edicao}/${q.numero}; dados preservados`);
                    }
                }
                const count = await sql.unsafe("SELECT COUNT(*) total FROM questao WHERE id_prova=?", [prova]);
                if (Number(count[0].total) !== expected) throw new Error("Quantidade existente diverge da edicao oficial");
                await sql.unsafe("UPDATE prova SET status_importacao='VALIDADA' WHERE id_prova=?", [prova]);
                await sql.unsafe("COMMIT");
                audit.push({ edicao: edicao.edicao, total: expected, novas, anuladas: edicao.questoes.filter(q => q.anulada).length });
            } catch (error) { await sql.unsafe("ROLLBACK"); throw error; }
        }
        return audit;
    } finally { await sql.unsafe("SELECT RELEASE_LOCK('evolua_etec_importacao')"); }
}

if (import.meta.main) {
    const env = Bun.env;
    if (!env.DB_HOST || !env.DB_USUARIO || !env.DB_SENHA || env.DB_NAME !== "evoluamais") throw new Error("Configure DB_HOST, DB_PORT, DB_NAME=evoluamais, DB_USUARIO e DB_SENHA no ambiente");
    const sql = new SQL({ adapter: "mysql", hostname: env.DB_HOST, port: Number(env.DB_PORT || 3306), database: env.DB_NAME,
        username: env.DB_USUARIO, password: env.DB_SENHA, tls: "require", max: 1, connectionTimeout: 15 });
    try {
        const dataset = await Bun.file(new URL("../acervo/etec/questoes.json", import.meta.url)).json();
        console.log(JSON.stringify({ status: "OK", edicoes: await importarETEC(sql, dataset) }));
    } catch (error) {
        console.error("Importacao interrompida; nenhuma edicao incompleta foi confirmada. Verifique o schema e o relatorio local.");
        process.exitCode = 1;
    } finally { await sql.close(); }
}
