package br.com.evoluamais.repository;

import br.com.evoluamais.config.ConexaoBanco;
import br.com.evoluamais.model.RecomendacaoIA;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.SQLException;

public class RecomendacaoIARepository {

    public void salvar(RecomendacaoIA recomendacao) {

        String sql = """
                INSERT INTO recomendacao_ia
                (id_estudante, analise)
                VALUES (?, ?)
                """;

        try (Connection conexao = ConexaoBanco.conectar();
             PreparedStatement comando = conexao.prepareStatement(sql)) {

            comando.setInt(
                    1,
                    recomendacao.getEstudante().getIdEstudante()
            );

            comando.setString(
                    2,
                    recomendacao.getAnalise()
            );

            comando.executeUpdate();

            System.out.println("Recomendação da IA salva com sucesso!");

        } catch (SQLException e) {

            System.out.println("Erro ao salvar recomendação da IA:");
            e.printStackTrace();
        }
    }
}