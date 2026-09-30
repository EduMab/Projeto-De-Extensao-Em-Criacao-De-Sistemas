package br.com.evoluamais.repository;

import br.com.evoluamais.config.ConexaoBanco;
import br.com.evoluamais.model.Alternativa;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;

public class AlternativaRepository {

    public List<Alternativa> buscarPorQuestao(int idQuestao) {

        List<Alternativa> alternativas = new ArrayList<>();

        String sql = """
                SELECT
                    id_alternativa,
                    texto,
                    correta,
                    id_questao
                FROM alternativa
                WHERE id_questao = ?
                ORDER BY id_alternativa
                """;

        try (Connection conexao = ConexaoBanco.conectar();
             PreparedStatement comando = conexao.prepareStatement(sql)) {

            comando.setInt(1, idQuestao);

            ResultSet resultado = comando.executeQuery();

            while (resultado.next()) {

                Alternativa alternativa = new Alternativa();

                alternativa.setIdAlternativa(
                        resultado.getInt("id_alternativa")
                );

                alternativa.setTexto(
                        resultado.getString("texto")
                );

                alternativa.setCorreta(
                        resultado.getBoolean("correta")
                );

                alternativas.add(alternativa);
            }

        } catch (SQLException e) {

            System.out.println("Erro ao buscar alternativas:");
            e.printStackTrace();
        }

        return alternativas;
    }
    public Alternativa buscarPorId(int idAlternativa) {

        String sql = """
            SELECT
                id_alternativa,
                texto,
                correta,
                id_questao
            FROM alternativa
            WHERE id_alternativa = ?
            """;

        try (Connection conexao = ConexaoBanco.conectar();
             PreparedStatement comando = conexao.prepareStatement(sql)) {

            comando.setInt(1, idAlternativa);

            ResultSet resultado = comando.executeQuery();

            if (resultado.next()) {

                Alternativa alternativa = new Alternativa();

                alternativa.setIdAlternativa(
                        resultado.getInt("id_alternativa")
                );

                alternativa.setTexto(
                        resultado.getString("texto")
                );

                alternativa.setCorreta(
                        resultado.getBoolean("correta")
                );

                return alternativa;
            }

        } catch (SQLException e) {

            System.out.println(
                    "Erro ao buscar alternativa:"
            );

            e.printStackTrace();
        }

        return null;
    }
}