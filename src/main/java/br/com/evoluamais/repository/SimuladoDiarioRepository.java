package br.com.evoluamais.repository;

import br.com.evoluamais.config.ConexaoBanco;
import br.com.evoluamais.service.SeletorQuestoesDiarias;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Repository;
import org.springframework.web.server.ResponseStatusException;

import java.sql.*;
import java.time.LocalDate;
import java.util.*;

@Repository
public class SimuladoDiarioRepository {
    private static final int INTERVALO_DIAS = 7;
    @FunctionalInterface public interface Conexoes { Connection abrir() throws SQLException; }
    private final Conexoes conexoes;
    private final ObjectMapper mapper = new ObjectMapper();
    private final SeletorQuestoesDiarias seletor = new SeletorQuestoesDiarias();

    @Autowired public SimuladoDiarioRepository() { this(ConexaoBanco::conectar); }
    public SimuladoDiarioRepository(Conexoes conexoes) { this.conexoes = conexoes; }

    private static ResponseStatusException erro(HttpStatus status, String message) {
        return new ResponseStatusException(status, message);
    }
    private static ResponseStatusException indisponivel(Exception cause) {
        org.slf4j.LoggerFactory.getLogger(SimuladoDiarioRepository.class).error("Falha no banco do simulado semanal: {}", cause.getClass().getSimpleName());
        return new ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE, "Nao foi possivel acessar o simulado. Tente novamente.");
    }
    private JsonNode json(String value) throws SQLException {
        try { return mapper.readTree(value); }
        catch (Exception e) { throw new SQLException("Conteudo de questao invalido", e); }
    }

    public Map<String, Object> acervo() {
        String sql = """
            SELECT COUNT(*) total, COUNT(DISTINCT q.id_prova) edicoes
            FROM questao q JOIN prova p ON p.id_prova=q.id_prova
            WHERE p.tipo='ETEC' AND p.status_importacao='VALIDADA' AND q.anulada=0
              AND q.conteudo_json IS NOT NULL
              AND (SELECT COUNT(*) FROM alternativa a WHERE a.id_questao=q.id_questao)=5
              AND (SELECT COUNT(DISTINCT a.letra) FROM alternativa a WHERE a.id_questao=q.id_questao AND a.letra IN ('A','B','C','D','E'))=5
              AND (SELECT COUNT(*) FROM alternativa a WHERE a.id_questao=q.id_questao AND a.correta=1)=1
            """;
        try (Connection c = conexoes.abrir(); var s = c.prepareStatement(sql); var r = s.executeQuery()) {
            r.next(); int total = r.getInt("total");
            return Map.of("tipo", "ETEC", "questoesAtivas", total, "edicoes", r.getInt("edicoes"),
                    "questoesPorSimulado", 40, "intervaloDias", INTERVALO_DIAS,
                    "semanasCom40Ineditas", total / 40, "ineditasRestantes", total % 40);
        } catch (SQLException e) { throw indisponivel(e); }
    }

    public Map<String, Object> iniciar(int estudante, LocalDate dia) {
        try (Connection c = conexoes.abrir()) {
            c.setAutoCommit(false);
            try {
                // Uma trava por estudante evita duas requisicoes criarem selecoes diferentes.
                try (var s = c.prepareStatement("SELECT id_estudante FROM estudante WHERE id_estudante=? FOR UPDATE")) {
                    s.setInt(1, estudante);
                    try (var r = s.executeQuery()) { if (!r.next()) throw erro(HttpStatus.UNAUTHORIZED, "Entre novamente na sua conta."); }
                }
                Long existente = null;
                // Mantem as tabelas existentes e retoma a selecao mais recente dos ultimos sete dias.
                // A trava do estudante tambem protege requisicoes em datas diferentes na virada do dia.
                try (var s = c.prepareStatement("""
                        SELECT id_simulado FROM simulado_diario
                        WHERE id_estudante=? AND tipo='ETEC' AND data_simulado>=? AND data_simulado<=?
                        ORDER BY data_simulado DESC,id_simulado DESC LIMIT 1
                        """)) {
                    s.setInt(1, estudante);
                    s.setDate(2, java.sql.Date.valueOf(dia.minusDays(INTERVALO_DIAS - 1)));
                    s.setDate(3, java.sql.Date.valueOf(dia));
                    try (var r = s.executeQuery()) { if (r.next()) existente = r.getLong(1); }
                }
                if (existente != null) {
                    var resultado = carregar(c, estudante, existente);
                    c.commit(); return resultado;
                }
                var candidatas = candidatas(c, estudante);
                List<Integer> ids;
                try { ids = seletor.selecionar(candidatas, 40, new Random()); }
                catch (IllegalStateException e) { throw erro(HttpStatus.CONFLICT, e.getMessage()); }
                long simulado;
                try (var s = c.prepareStatement("INSERT INTO simulado_diario(id_estudante,tipo,data_simulado) VALUES (?,'ETEC',?)", Statement.RETURN_GENERATED_KEYS)) {
                    s.setInt(1, estudante); s.setDate(2, java.sql.Date.valueOf(dia)); s.executeUpdate();
                    try (var r = s.getGeneratedKeys()) { if (!r.next()) throw new SQLException("Simulado sem identificador"); simulado = r.getLong(1); }
                }
                try (var s = c.prepareStatement("INSERT INTO simulado_diario_questao(id_simulado,posicao,id_questao,snapshot_json) VALUES (?,?,?,?)")) {
                    for (int i = 0; i < ids.size(); i++) {
                        s.setLong(1, simulado); s.setInt(2, i + 1); s.setInt(3, ids.get(i));
                        s.setString(4, snapshot(c, ids.get(i)).toString()); s.addBatch();
                    }
                    s.executeBatch();
                }
                var resultado = carregar(c, estudante, simulado);
                c.commit(); return resultado;
            } catch (Exception e) { c.rollback(); throw e; }
        } catch (ResponseStatusException e) { throw e; }
        catch (Exception e) { throw indisponivel(e); }
    }

    private List<SeletorQuestoesDiarias.Candidata> candidatas(Connection c, int estudante) throws SQLException {
        String sql = """
            SELECT q.id_questao,p.codigo,
              (SELECT MAX(h.dia) FROM (
                SELECT sq.id_questao,s.id_estudante,s.data_simulado dia
                  FROM simulado_diario_questao sq JOIN simulado_diario s ON s.id_simulado=sq.id_simulado
                UNION ALL SELECT id_questao,id_estudante,CAST(data_resposta AS DATE) dia FROM resposta
              ) h WHERE h.id_questao=q.id_questao AND h.id_estudante=?) ultima
            FROM questao q JOIN prova p ON p.id_prova=q.id_prova
            WHERE p.tipo='ETEC' AND p.status_importacao='VALIDADA' AND q.anulada=0 AND q.conteudo_json IS NOT NULL
              AND (SELECT COUNT(*) FROM alternativa a WHERE a.id_questao=q.id_questao)=5
              AND (SELECT COUNT(DISTINCT a.letra) FROM alternativa a WHERE a.id_questao=q.id_questao AND a.letra IN ('A','B','C','D','E'))=5
              AND (SELECT COUNT(*) FROM alternativa a WHERE a.id_questao=q.id_questao AND a.correta=1)=1
            ORDER BY q.id_questao
            """;
        List<SeletorQuestoesDiarias.Candidata> resultado = new ArrayList<>();
        try (var s = c.prepareStatement(sql)) {
            s.setInt(1, estudante);
            try (var r = s.executeQuery()) {
                while (r.next()) { var data = r.getDate("ultima"); resultado.add(new SeletorQuestoesDiarias.Candidata(r.getInt("id_questao"), r.getString("codigo"), data == null ? null : data.toLocalDate())); }
            }
        }
        return resultado;
    }

    private ObjectNode snapshot(Connection c, int questao) throws SQLException {
        ObjectNode node = mapper.createObjectNode();
        try (var s = c.prepareStatement("SELECT q.*,p.nome prova_nome,p.edicao FROM questao q JOIN prova p ON p.id_prova=q.id_prova WHERE q.id_questao=? AND q.anulada=0 AND p.status_importacao='VALIDADA'")) {
            s.setInt(1, questao);
            try (var r = s.executeQuery()) {
                if (!r.next()) throw new SQLException("Questao indisponivel durante selecao");
                node.put("idQuestao", questao); node.put("numeroOriginal", r.getInt("numero_original"));
                node.put("prova", r.getString("prova_nome")); node.put("edicao", r.getString("edicao"));
                node.put("enunciado", r.getString("enunciado")); node.set("conteudo", json(r.getString("conteudo_json")));
            }
        }
        var alternativas = node.putArray("alternativas"); int corretas = 0;
        try (var s = c.prepareStatement("SELECT id_alternativa,letra,texto,correta FROM alternativa WHERE id_questao=? ORDER BY letra")) {
            s.setInt(1, questao);
            try (var r = s.executeQuery()) {
                while (r.next()) {
                    String letra = r.getString("letra");
                    if (letra == null || !letra.matches("[A-E]")) throw new SQLException("Letra de alternativa invalida");
                    var a = alternativas.addObject(); a.put("id", r.getInt("id_alternativa")); a.put("letra", letra); a.put("texto", r.getString("texto"));
                    if (r.getBoolean("correta")) { node.put("gabarito", letra); corretas++; }
                }
            }
        }
        if (alternativas.size() != 5 || corretas != 1) throw new SQLException("Questao sem cinco alternativas e gabarito unico");
        return node;
    }

    public Map<String, Object> obter(int estudante, long id) {
        try (Connection c = conexoes.abrir()) { return carregar(c, estudante, id); }
        catch (ResponseStatusException e) { throw e; }
        catch (SQLException e) { throw indisponivel(e); }
    }

    private Map<String, Object> carregar(Connection c, int estudante, long id) throws SQLException {
        boolean concluido; String dia;
        try (var s = c.prepareStatement("SELECT data_simulado,concluido_em FROM simulado_diario WHERE id_simulado=? AND id_estudante=?")) {
            s.setLong(1, id); s.setInt(2, estudante);
            try (var r = s.executeQuery()) {
                if (!r.next()) throw erro(HttpStatus.NOT_FOUND, "Simulado nao encontrado.");
                concluido = r.getTimestamp("concluido_em") != null; dia = r.getDate("data_simulado").toString();
            }
        }
        List<JsonNode> questoes = new ArrayList<>(); int respondidas = 0, acertos = 0;
        try (var s = c.prepareStatement("SELECT posicao,snapshot_json,id_alternativa,acertou FROM simulado_diario_questao WHERE id_simulado=? ORDER BY posicao")) {
            s.setLong(1, id);
            try (var r = s.executeQuery()) {
                while (r.next()) {
                    ObjectNode q = (ObjectNode) json(r.getString("snapshot_json"));
                    q.put("posicao", r.getInt("posicao")); int alternativa = r.getInt("id_alternativa");
                    if (r.wasNull()) q.putNull("alternativaSelecionada"); else { q.put("alternativaSelecionada", alternativa); respondidas++; }
                    if (r.getBoolean("acertou")) acertos++;
                    if (!concluido) q.remove("gabarito");
                    else q.put("acertou", r.getBoolean("acertou"));
                    questoes.add(q);
                }
            }
        }
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("id", id); result.put("data", dia); result.put("tipo", "ETEC"); result.put("concluido", concluido);
        result.put("intervaloDias", INTERVALO_DIAS);
        result.put("proximaLiberacao", LocalDate.parse(dia).plusDays(INTERVALO_DIAS).toString());
        result.put("respondidas", respondidas); result.put("total", questoes.size()); result.put("questoes", questoes);
        if (concluido) { result.put("acertos", acertos); result.put("percentual", acertos * 100.0 / 40); }
        return result;
    }

    private boolean travar(Connection c, int estudante, long id) throws SQLException {
        try (var s = c.prepareStatement("SELECT concluido_em FROM simulado_diario WHERE id_simulado=? AND id_estudante=? FOR UPDATE")) {
            s.setLong(1, id); s.setInt(2, estudante);
            try (var r = s.executeQuery()) { if (!r.next()) throw erro(HttpStatus.NOT_FOUND, "Simulado nao encontrado."); return r.getTimestamp(1) != null; }
        }
    }

    public void responder(int estudante, long id, int posicao, int alternativa) {
        if (posicao < 1 || posicao > 40) throw erro(HttpStatus.BAD_REQUEST, "Posicao invalida.");
        try (Connection c = conexoes.abrir()) {
            c.setAutoCommit(false);
            try {
                if (travar(c, estudante, id)) throw erro(HttpStatus.CONFLICT, "O simulado ja foi concluido.");
                JsonNode q;
                try (var s = c.prepareStatement("SELECT snapshot_json FROM simulado_diario_questao WHERE id_simulado=? AND posicao=?")) {
                    s.setLong(1, id); s.setInt(2, posicao);
                    try (var r = s.executeQuery()) { if (!r.next()) throw erro(HttpStatus.NOT_FOUND, "Questao nao encontrada."); q = json(r.getString(1)); }
                }
                String letra = null;
                for (JsonNode a : q.get("alternativas")) if (a.get("id").asInt() == alternativa) letra = a.get("letra").asText();
                if (letra == null) throw erro(HttpStatus.BAD_REQUEST, "A alternativa nao pertence a esta questao.");
                try (var s = c.prepareStatement("UPDATE simulado_diario_questao SET id_alternativa=?,acertou=?,respondida_em=CURRENT_TIMESTAMP WHERE id_simulado=? AND posicao=?")) {
                    s.setInt(1, alternativa); s.setBoolean(2, letra.equals(q.get("gabarito").asText())); s.setLong(3, id); s.setInt(4, posicao); s.executeUpdate();
                }
                c.commit();
            } catch (Exception e) { c.rollback(); throw e; }
        } catch (ResponseStatusException e) { throw e; }
        catch (Exception e) { throw indisponivel(e); }
    }

    public Map<String, Object> finalizar(int estudante, long id) {
        try (Connection c = conexoes.abrir()) {
            c.setAutoCommit(false);
            try {
                if (!travar(c, estudante, id)) {
                    try (var s = c.prepareStatement("SELECT COUNT(*) total,COUNT(id_alternativa) respondidas FROM simulado_diario_questao WHERE id_simulado=?")) {
                        s.setLong(1, id);
                        try (var r = s.executeQuery()) {
                            r.next(); if (r.getInt("total") != 40 || r.getInt("respondidas") != 40) throw erro(HttpStatus.CONFLICT, "Responda as 40 questoes antes de finalizar.");
                        }
                    }
                    try (var s = c.prepareStatement("UPDATE simulado_diario SET concluido_em=CURRENT_TIMESTAMP WHERE id_simulado=?")) { s.setLong(1, id); s.executeUpdate(); }
                }
                var result = carregar(c, estudante, id); c.commit(); return result;
            } catch (Exception e) { c.rollback(); throw e; }
        } catch (ResponseStatusException e) { throw e; }
        catch (Exception e) { throw indisponivel(e); }
    }

    public List<Map<String, Object>> historico(int estudante) {
        String sql = """
            SELECT s.id_simulado,s.data_simulado,s.concluido_em,COUNT(q.id_questao) total,
              COUNT(q.id_alternativa) respondidas,COALESCE(SUM(q.acertou),0) acertos
            FROM simulado_diario s LEFT JOIN simulado_diario_questao q ON q.id_simulado=s.id_simulado
            WHERE s.id_estudante=? GROUP BY s.id_simulado,s.data_simulado,s.concluido_em
            ORDER BY s.data_simulado DESC LIMIT 30
            """;
        try (Connection c = conexoes.abrir(); var s = c.prepareStatement(sql)) {
            s.setInt(1, estudante); List<Map<String, Object>> result = new ArrayList<>();
            try (var r = s.executeQuery()) {
                while (r.next()) {
                    boolean concluido = r.getTimestamp("concluido_em") != null;
                    var linha = new LinkedHashMap<String, Object>(); linha.put("id", r.getLong("id_simulado")); linha.put("data", r.getDate("data_simulado").toString());
                    linha.put("concluido", concluido); linha.put("respondidas", r.getInt("respondidas"));
                    if (concluido) linha.put("acertos", r.getInt("acertos")); result.add(linha);
                }
            }
            return result;
        } catch (SQLException e) { throw indisponivel(e); }
    }
}
