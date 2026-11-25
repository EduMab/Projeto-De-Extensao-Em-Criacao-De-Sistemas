package br.com.evoluamais.repository;

import br.com.evoluamais.config.ConexaoBanco;
import org.springframework.stereotype.Repository;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.sql.*;
import java.util.HexFormat;

@Repository
public class PushSubscriptionRepository {
    @FunctionalInterface public interface Conexoes { Connection abrir() throws SQLException; }
    private final Conexoes conexoes;
    public PushSubscriptionRepository() { this(ConexaoBanco::conectar); }
    public PushSubscriptionRepository(Conexoes conexoes) { this.conexoes=conexoes; }

    public void salvar(int estudante, String endpoint, String p256dh, String auth) {
        String sql="""
            INSERT INTO push_subscription
                (id_estudante, endpoint, endpoint_hash, p256dh, auth, criada_em, atualizada_em)
            VALUES (?,?,?,?,?,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)
            ON DUPLICATE KEY UPDATE id_estudante=VALUES(id_estudante),
                endpoint=VALUES(endpoint), p256dh=VALUES(p256dh), auth=VALUES(auth),
                atualizada_em=CURRENT_TIMESTAMP
            """;
        try(Connection c=conexoes.abrir(); PreparedStatement s=c.prepareStatement(sql)) {
            s.setInt(1,estudante); s.setString(2,endpoint); s.setString(3,hash(endpoint));
            s.setString(4,p256dh); s.setString(5,auth); s.executeUpdate();
        } catch(SQLException e) { throw new IllegalStateException("Não foi possível ativar os avisos neste dispositivo.",e); }
    }

    public void remover(int estudante, String endpoint) {
        try(Connection c=conexoes.abrir(); PreparedStatement s=c.prepareStatement(
            "DELETE FROM push_subscription WHERE id_estudante=? AND endpoint_hash=?")) {
            s.setInt(1,estudante); s.setString(2,hash(endpoint)); s.executeUpdate();
        } catch(SQLException e) { throw new IllegalStateException("Não foi possível desativar os avisos neste dispositivo.",e); }
    }

    public void removerEndpoint(String endpoint) {
        try(Connection c=conexoes.abrir(); PreparedStatement s=c.prepareStatement(
            "DELETE FROM push_subscription WHERE endpoint_hash=?")) {
            s.setString(1,hash(endpoint)); s.executeUpdate();
        } catch(SQLException e) { throw new IllegalStateException("Não foi possível remover uma assinatura expirada.",e); }
    }

    private String hash(String endpoint) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(endpoint.getBytes(StandardCharsets.UTF_8))); }
        catch(Exception e) { throw new IllegalStateException("Falha ao identificar dispositivo.",e); }
    }
}
