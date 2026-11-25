package br.com.evoluamais.repository;

import br.com.evoluamais.config.ConexaoBanco;
import br.com.evoluamais.model.Resposta;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;

public class RespostaRepository {

    // Busca todas as respostas de um estudante
    public List<Resposta> buscarPorEstudante(int idEstudante) {

        List<Resposta> respostas = new ArrayList<>();

        String sql = """
                SELECT
                    id_resposta,
                    id_estudante,
                    id_questao,
                    id_alternativa,
                    acertou,
                    data_resposta
                FROM resposta
                WHERE id_estudante = ?
                """;

        try (Connection conexao = ConexaoBanco.conectar();
             PreparedStatement comando = conexao.prepareStatement(sql)) {

            comando.setInt(1, idEstudante);

            ResultSet resultado = comando.executeQuery();

            while (resultado.next()) {

                Resposta resposta = new Resposta();

                resposta.setIdResposta(
                        resultado.getInt("id_resposta")
                );

                resposta.setAcertou(
                        resultado.getBoolean("acertou")
                );

                resposta.setDataResposta(
                        resultado.getString("data_resposta")
                );

                respostas.add(resposta);
            }

        } catch (SQLException e) {

            System.out.println("Erro ao buscar respostas:");
            e.printStackTrace();
        }

        return respostas;
    }


    // Busca as respostas de um estudante em uma prova específica
    public List<Resposta> buscarPorEstudanteEProva(
            int idEstudante,
            int idProva) {

        List<Resposta> respostas = new ArrayList<>();

        String sql = """
                SELECT
                    r.id_resposta,
                    r.id_estudante,
                    r.id_questao,
                    r.id_alternativa,
                    r.acertou,
                    r.data_resposta
                FROM resposta r
                INNER JOIN questao q
                    ON r.id_questao = q.id_questao
                WHERE r.id_estudante = ?
                  AND q.id_prova = ?
                """;

        try (Connection conexao = ConexaoBanco.conectar();
             PreparedStatement comando = conexao.prepareStatement(sql)) {

            comando.setInt(1, idEstudante);
            comando.setInt(2, idProva);

            ResultSet resultado = comando.executeQuery();

            while (resultado.next()) {

                Resposta resposta = new Resposta();

                resposta.setIdResposta(
                        resultado.getInt("id_resposta")
                );

                resposta.setAcertou(
                        resultado.getBoolean("acertou")
                );

                resposta.setDataResposta(
                        resultado.getString("data_resposta")
                );

                respostas.add(resposta);
            }

        } catch (SQLException e) {

            System.out.println(
                    "Erro ao buscar respostas da prova:"
            );

            e.printStackTrace();
        }

        return respostas;
    }


    // Busca os erros do estudante em uma prova específica
    public List<String> buscarErrosDetalhados(
            int idEstudante,
            int idProva) {

        List<String> erros = new ArrayList<>();

        String sql = """
                SELECT
                    q.id_questao,
                    q.enunciado,
                    q.dificuldade,
                    d.nome AS disciplina
                FROM resposta r
                INNER JOIN questao q
                    ON r.id_questao = q.id_questao
                INNER JOIN disciplina d
                    ON q.id_disciplina = d.id_disciplina
                WHERE r.id_estudante = ?
                  AND q.id_prova = ?
                  AND r.acertou = false
                """;

        try (Connection conexao = ConexaoBanco.conectar();
             PreparedStatement comando = conexao.prepareStatement(sql)) {

            comando.setInt(1, idEstudante);
            comando.setInt(2, idProva);

            ResultSet resultado = comando.executeQuery();

            while (resultado.next()) {

                String erro =
                        "Questão: "
                                + resultado.getInt("id_questao")
                                + " | Disciplina: "
                                + resultado.getString("disciplina")
                                + " | Dificuldade: "
                                + resultado.getString("dificuldade")
                                + " | Enunciado: "
                                + resultado.getString("enunciado");

                erros.add(erro);
            }

        } catch (SQLException e) {

            System.out.println(
                    "Erro ao buscar erros detalhados:"
            );

            e.printStackTrace();
        }

        return erros;
    }


    // Salva ou atualiza a resposta do estudante
    public void salvarResposta(
            int idEstudante,
            int idQuestao,
            int idAlternativa,
            boolean acertou) {

        String sqlVerificar = """
                SELECT id_resposta
                FROM resposta
                WHERE id_estudante = ?
                  AND id_questao = ?
                LIMIT 1
                """;

        String sqlAtualizar = """
                UPDATE resposta
                SET id_alternativa = ?,
                    acertou = ?,
                    data_resposta = NOW()
                WHERE id_estudante = ?
                  AND id_questao = ?
                """;

        String sqlInserir = """
                INSERT INTO resposta
                (
                    id_estudante,
                    id_questao,
                    id_alternativa,
                    acertou,
                    data_resposta
                )
                VALUES (?, ?, ?, ?, NOW())
                """;

        try (Connection conexao = ConexaoBanco.conectar()) {

            boolean respostaExiste = false;

            // Verifica se o estudante já respondeu a questão
            try (PreparedStatement comando =
                         conexao.prepareStatement(sqlVerificar)) {

                comando.setInt(1, idEstudante);
                comando.setInt(2, idQuestao);

                ResultSet resultado = comando.executeQuery();

                if (resultado.next()) {
                    respostaExiste = true;
                }
            }


            // Se já existe, atualiza
            if (respostaExiste) {

                try (PreparedStatement comando =
                             conexao.prepareStatement(sqlAtualizar)) {

                    comando.setInt(1, idAlternativa);
                    comando.setBoolean(2, acertou);
                    comando.setInt(3, idEstudante);
                    comando.setInt(4, idQuestao);

                    comando.executeUpdate();

                    System.out.println(
                            "Resposta atualizada com sucesso!"
                    );
                }

            } else {

                // Se ainda não existe, insere
                try (PreparedStatement comando =
                             conexao.prepareStatement(sqlInserir)) {

                    comando.setInt(1, idEstudante);
                    comando.setInt(2, idQuestao);
                    comando.setInt(3, idAlternativa);
                    comando.setBoolean(4, acertou);

                    comando.executeUpdate();

                    System.out.println(
                            "Resposta salva com sucesso!"
                    );
                }
            }

        } catch (SQLException e) {

            System.out.println(
                    "Erro ao salvar resposta:"
            );

            e.printStackTrace();
        }
    }
}