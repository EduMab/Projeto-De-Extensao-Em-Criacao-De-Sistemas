package br.com.evoluamais.repository;

import br.com.evoluamais.config.ConexaoBanco;
import br.com.evoluamais.model.Questao;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;

public class QuestaoRepository {

    public List<Questao> buscarPorProva(int idProva) {

        List<Questao> questoes = new ArrayList<>();

        String sql = """
                SELECT
                    q.id_questao,
                    q.enunciado,
                    q.dificuldade,
                    q.id_disciplina,
                    q.id_prova
                FROM questao q
                WHERE q.id_prova = ?
                ORDER BY q.id_questao
                """;

        try (Connection conexao = ConexaoBanco.conectar();
             PreparedStatement comando = conexao.prepareStatement(sql)) {

            comando.setInt(1, idProva);

            ResultSet resultado = comando.executeQuery();

            while (resultado.next()) {

                Questao questao = new Questao();

                questao.setIdQuestao(
                        resultado.getInt("id_questao")
                );

                questao.setEnunciado(
                        resultado.getString("enunciado")
                );

                questao.setDificuldade(
                        resultado.getString("dificuldade")
                );

                questoes.add(questao);
            }

        } catch (SQLException e) {

            System.out.println("Erro ao buscar questões:");
            e.printStackTrace();
        }

        return questoes;
    }
}