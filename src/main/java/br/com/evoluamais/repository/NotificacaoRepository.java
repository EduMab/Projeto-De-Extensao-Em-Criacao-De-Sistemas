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
    public record EntregaPush(long idNotificacao, String endpoint, String p256dh, String auth,
                              String titulo, String mensagem, String link) {}
    private final Conexoes conexoes;

    public NotificacaoRepository() { this(ConexaoBanco::conectar); }
    public NotificacaoRepository(Conexoes conexoes) { this.conexoes = conexoes; }

    /**
     * Gera avisos coerentes com o ciclo semanal do simulado:
     * primeira tarefa, lembrete apos 3 dias e nova tarefa apos 7 dias.
     * A chave unica impede duplicidade mesmo com mais de uma instancia da aplicacao.
     */
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
                        "Seu plano de estudos tem uma nova etapa. Reserve um momento para responder às 40 questões.",
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
                        "Continue sua preparação: um novo simulado de 40 questões está disponível.",
                        "/simulados.html");
                    criadas += insert.executeUpdate();
                } else if (concluido == null && !hoje.isBefore(abertura.plusDays(3))) {
                    preencher(insert, estudante, "LEMBRETE_" + idSimulado,
                        "LEMBRETE_TAREFA", "Que tal retomar seus estudos?",
                        "Seu simulado semanal ainda está em andamento. Volte de onde parou e avance no seu ritmo.",
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
                    Timestamp criada = r.getTimestamp("criada_em");
                    item.put("criadaEm", criada == null ? null : criada.toString());
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

    public List<EntregaPush> buscarEntregasPushPendentes() {
        String sql = """
            SELECT n.id_notificacao, p.endpoint, p.p256dh, p.auth,
                   n.titulo, n.mensagem, n.link
            FROM notificacao n
            JOIN push_subscription p ON p.id_estudante=n.id_estudante
            WHERE n.push_enviada_em IS NULL
              AND n.criada_em >= p.criada_em
              AND n.criada_em >= DATE_SUB(CURRENT_TIMESTAMP, INTERVAL 7 DAY)
            ORDER BY n.id_notificacao, p.id_assinatura
            LIMIT 500
            """;
        List<EntregaPush> entregas = new ArrayList<>();
        try (Connection c=conexoes.abrir(); PreparedStatement s=c.prepareStatement(sql);
             ResultSet r=s.executeQuery()) {
            while(r.next()) entregas.add(new EntregaPush(r.getLong("id_notificacao"),
                r.getString("endpoint"),r.getString("p256dh"),r.getString("auth"),
                r.getString("titulo"),r.getString("mensagem"),r.getString("link")));
            return entregas;
        } catch(SQLException e) { throw new IllegalStateException("Não foi possível consultar a fila de notificações push.",e); }
    }

    public void marcarPushEnviado(long idNotificacao) {
        try(Connection c=conexoes.abrir(); PreparedStatement s=c.prepareStatement(
            "UPDATE notificacao SET push_enviada_em=CURRENT_TIMESTAMP, push_ultimo_erro=NULL WHERE id_notificacao=? AND push_enviada_em IS NULL")) {
            s.setLong(1,idNotificacao); s.executeUpdate();
        } catch(SQLException e) { throw new IllegalStateException("Não foi possível confirmar o envio push.",e); }
    }

    public void registrarFalhaPush(long idNotificacao, String motivo) {
        try(Connection c=conexoes.abrir(); PreparedStatement s=c.prepareStatement(
            "UPDATE notificacao SET push_tentativas=push_tentativas+1, push_ultimo_erro=? WHERE id_notificacao=? AND push_enviada_em IS NULL")) {
            s.setString(1,motivo == null ? "Falha de entrega" : motivo.substring(0,Math.min(240,motivo.length())));
            s.setLong(2,idNotificacao); s.executeUpdate();
        } catch(SQLException e) { throw new IllegalStateException("Não foi possível registrar falha de push.",e); }
    }
}
