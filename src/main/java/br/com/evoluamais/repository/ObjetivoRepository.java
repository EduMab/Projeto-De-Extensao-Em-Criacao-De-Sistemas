package br.com.evoluamais.repository;

import br.com.evoluamais.config.ConexaoBanco;
import br.com.evoluamais.model.ObjetivoProva;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Repository;
import org.springframework.web.server.ResponseStatusException;

import java.sql.*;
import java.util.*;

@Repository
public class ObjetivoRepository {
    @FunctionalInterface public interface Conexoes { Connection abrir() throws SQLException; }
    private final Conexoes conexoes;

    @Autowired public ObjetivoRepository() { this(ConexaoBanco::conectar); }
    public ObjetivoRepository(Conexoes conexoes) { this.conexoes = conexoes; }

    public Map<String, Object> perfil(int estudante) {
        try (var c = conexoes.abrir()) { return carregar(c, estudante); }
        catch (SQLException e) { throw indisponivel(e); }
    }

    public Map<String, Object> salvar(int estudante, ObjetivoProva objetivo) {
        try (var c = conexoes.abrir()) {
            c.setAutoCommit(false);
            try {
                // A mesma trava usada para abrir simulados serializa a troca do objetivo.
                try (var s = c.prepareStatement("SELECT id_estudante FROM estudante WHERE id_estudante=? FOR UPDATE")) {
                    s.setInt(1, estudante);
                    try (var r = s.executeQuery()) { if (!r.next()) throw semConta(); }
                }
                try (var s = c.prepareStatement("UPDATE estudante SET objetivo_prova=? WHERE id_estudante=?")) {
                    s.setString(1, objetivo.name()); s.setInt(2, estudante); s.executeUpdate();
                }
                var perfil = carregar(c, estudante);
                c.commit(); return perfil;
            } catch (Exception e) { c.rollback(); throw e; }
        } catch (SQLException e) { throw indisponivel(e); }
    }

    private Map<String, Object> carregar(Connection c, int estudante) throws SQLException {
        try (var s = c.prepareStatement("""
                SELECT e.id_estudante,e.id_prova,e.objetivo_prova,u.nome FROM estudante e
                JOIN usuario u ON u.id_usuario=e.id_usuario WHERE e.id_estudante=?
                """)) {
            s.setInt(1, estudante);
            try (var r = s.executeQuery()) {
                if (!r.next()) throw semConta();
                boolean enemPronto;
                try(var preparo=c.prepareStatement("SELECT COUNT(*) n FROM prova WHERE tipo='ENEM' AND status_importacao='VALIDADA' AND ano BETWEEN 2017 AND 2026 AND codigo LIKE 'ENEM-%-DIA-%-AMARELO'");var catalogo=preparo.executeQuery()){
                    catalogo.next();enemPronto=catalogo.getInt("n")==20;
                }
                var perfil = new LinkedHashMap<String, Object>();
                perfil.put("idEstudante", r.getInt("id_estudante"));
                perfil.put("idProva", r.getInt("id_prova"));
                perfil.put("nome", r.getString("nome"));
                perfil.put("objetivo", r.getString("objetivo_prova"));
                perfil.put("objetivos", Arrays.stream(ObjetivoProva.values()).map(o -> Map.of(
                        "codigo", o.name(), "nome", o.nome(), "descricao", o.descricao(),
                        "simuladoDisponivel", o.simuladoDisponivel() && (o!=ObjetivoProva.ENEM || enemPronto))).toList());
                String chave = System.getenv("OPENROUTER_API_KEY");
                perfil.put("iaDisponivel", chave != null && !chave.isBlank());
                return perfil;
            }
        }
    }

    private ResponseStatusException semConta() {
        return new ResponseStatusException(HttpStatus.UNAUTHORIZED, "Entre novamente na sua conta.");
    }
    private ResponseStatusException indisponivel(SQLException e) {
        org.slf4j.LoggerFactory.getLogger(ObjetivoRepository.class).error("Falha ao acessar objetivo: {}", e.getSQLState());
        return new ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE,
                "Não foi possível carregar seu objetivo. Tente novamente.");
    }
}
