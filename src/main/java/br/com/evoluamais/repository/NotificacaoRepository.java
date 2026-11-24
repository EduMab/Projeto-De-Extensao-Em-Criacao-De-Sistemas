package br.com.evoluamais.repository;

import br.com.evoluamais.config.ConexaoBanco;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Repository;
import org.springframework.web.server.ResponseStatusException;

import java.sql.*;
import java.time.LocalDate;
import java.util.*;

@Repository
public class NotificacaoRepository {
    @FunctionalInterface public interface Conexoes { Connection abrir() throws SQLException; }
    private final Conexoes conexoes;

    public NotificacaoRepository() { this(ConexaoBanco::conectar); }
    public NotificacaoRepository(Conexoes conexoes) { this.conexoes = conexoes; }

    /** Cria no maximo uma notificacao por aluno e por ciclo semanal. */
    public int gerarPendentes(LocalDate hoje) {
        String alunos = """
            SELECT e.id_estudante, e.objetivo_prova, s.id_simulado,
                   s.data_simulado, s.concluido_em
            FROM estudante e
            LEFT JOIN simulado_diario s ON s.id_simulado = (
                SELECT s2.id_simulado
                FROM simulado_diario s2
                WHERE s2.id_estudante=e.id_estudante
                  AND s2.tipo=e.objetivo_prova
                ORDER BY s2.data_simulado DESC, s2.id_simulado DESC
                LIMIT 1
            )
            WHERE e.objetivo_prova IN ('ETEC','CONCURSO')
            """;
        String inserir = """
            INSERT IGNORE INTO notificacao
                (id_estudante, chave, tipo, titulo, mensagem, link, criada_em)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """;
        int criadas = 0;
        try (Connection c = conexoes.abrir();
             PreparedStatement consulta = c.prepareStatement(alunos);
             ResultSet r = consulta.executeQuery();
             PreparedStatement insert = c.prepareStatement(inserir)) {
            while (r.next()) {
                int estudante = r.getInt("id_estudante");
                String objetivo = r.getString("objetivo_prova");
                long idSimulado = r.getLong("id_simulado");
                boolean semSimulado = r.wasNull();
                if (semSimulado) {
                    preencher(insert, estudante, "TAREFA_INICIAL_" + objetivo,
                        "TAREFA_SEMANAL", "Sua tarefa da semana está disponível!",
                        "Separe um momento para responder às 40 questões da sua preparação.",
                        "/simulados.html");
                    criadas += insert.executeUpdate();
                    continue;
                }

                LocalDate abertura = r.getDate("data_simulado").toLocalDate();
                Timestamp concluido = r.getTimestamp("concluido_em");
                LocalDate liberacao = abertura.plusDays(7);
                if (!hoje.isBefore(liberacao)) {
                    preencher(insert, estudante, "TAREFA_" + objetivo + "_" + liberacao,
                        "TAREFA_SEMANAL", "Uma nova tarefa semanal está liberada!",
                        "Seu próximo simulado de 40 questões já pode ser iniciado.",
                        "/simulados.html");
                    criadas += insert.executeUpdate();
                } else if (concluido == null && !hoje.isBefore(abertura.plusDays(3))) {
                    preencher(insert, estudante, "LEMBRETE_" + idSimulado,
                        "LEMBRETE_TAREFA", "Não deixe sua tarefa da semana para depois",
                        "Seu simulado continua em andamento. Volte e conclua as 40 questões no seu ritmo.",
                        "/simulados.html");
                    criadas += insert.executeUpdate();
                }
            }
            return criadas;
        } catch (SQLException e) {
            throw new IllegalStateException("Não foi possível gerar as notificações semanais.", e);
        }
    }

    private void preencher(PreparedStatement s, int estudante, String chave, String tipo,
                           String titulo, String mensagem, String link) throws SQLException {
        s.setInt(1, estudante); s.setString(2, chave); s.setString(3, tipo);
        s.setString(4, titulo); s.setString(5, mensagem); s.setString(6, link);
    }

    public Map<String,Object> listar(int estudante) {
        String sql = """
            SELECT id_notificacao, tipo, titulo, mensagem, link, criada_em, lida_em
            FROM notificacao WHERE id_estudante=?
            ORDER BY criada_em DESC, id_notificacao DESC LIMIT 30
            """;
        List<Map<String,Object>> itens = new ArrayList<>();
        int naoLidas = 0;
        try (Connection c = conexoes.abrir();
             PreparedStatement s = c.prepareStatement(sql)) {
            s.setInt(1, estudante);
            try (ResultSet r = s.executeQuery()) {
                while (r.next()) {
                    Timestamp lida = r.getTimestamp("lida_em");
                    if (lida == null) naoLidas++;
                    Map<String,Object> item = new LinkedHashMap<>();
                    item.put("id", r.getLong("id_notificacao"));
                    item.put("tipo", r.getString("tipo"));
                    item.put("titulo", r.getString("titulo"));
                    item.put("mensagem", r.getString("mensagem"));
                    item.put("link", r.getString("link"));
                    item.put("criadaEm", r.getTimestamp("criada_em").toString());
                    item.put("lida", lida != null);
                    itens.add(item);
                }
            }
            return Map.of("naoLidas", naoLidas, "notificacoes", itens);
        } catch (SQLException e) {
            throw new IllegalStateException("Não foi possível carregar suas notificações.", e);
        }
    }

    public void marcarLida(int estudante, long id) {
        String sql = "UPDATE notificacao SET lida_em=CURRENT_TIMESTAMP WHERE id_notificacao=? AND id_estudante=? AND lida_em IS NULL";
        try (Connection c = conexoes.abrir(); PreparedStatement s = c.prepareStatement(sql)) {
            s.setLong(1,id); s.setInt(2,estudante);
            if (s.executeUpdate() == 0) {
                try (PreparedStatement check = c.prepareStatement(
                        "SELECT 1 FROM notificacao WHERE id_notificacao=? AND id_estudante=?")) {
                    check.setLong(1,id); check.setInt(2,estudante);
                    try (ResultSet r = check.executeQuery()) {
                        if (!r.next()) throw new ResponseStatusException(HttpStatus.NOT_FOUND,"Notificação não encontrada.");
                    }
                }
            }
        } catch (ResponseStatusException e) { throw e; }
        catch (SQLException e) { throw new IllegalStateException("Não foi possível atualizar a notificação.", e); }
    }

    public void marcarTodasLidas(int estudante) {
        try (Connection c = conexoes.abrir(); PreparedStatement s = c.prepareStatement(
                "UPDATE notificacao SET lida_em=CURRENT_TIMESTAMP WHERE id_estudante=? AND lida_em IS NULL")) {
            s.setInt(1,estudante); s.executeUpdate();
        } catch (SQLException e) { throw new IllegalStateException("Não foi possível atualizar as notificações.", e); }
    }
}
