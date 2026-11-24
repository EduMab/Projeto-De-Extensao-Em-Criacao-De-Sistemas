import { SQL } from "bun";

export async function importarQuestoesConcursos(sql: SQL, dataset: any) {
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

if (import.meta.main) {
    const env = Bun.env;
    if (env.DB_NAME !== "evoluamais" || !env.DB_HOST || !env.CONCURSO_PASSWORD) throw new Error("Configuração ausente");
    const sql = new SQL({adapter: "mysql", hostname: env.DB_HOST, port: Number(env.DB_PORT || 3306), database: env.DB_NAME,
        username: "editor_concurso", password: env.CONCURSO_PASSWORD, tls: "require", max: 1});
    try {
        const bytes = await Bun.file(new URL("../acervo/concursos/questoes.json.gz", import.meta.url)).arrayBuffer();
        const dataset = JSON.parse(new TextDecoder().decode(Bun.gunzipSync(new Uint8Array(bytes))));
        await importarQuestoesConcursos(sql, dataset);
    } finally { await sql.close(); }
}
