package br.com.evoluamais.repository;

import br.com.evoluamais.config.ConexaoBanco;
import br.com.evoluamais.model.Desempenho;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;

public class DesempenhoRepository {

    // Busca o desempenho do estudante
    public Desempenho buscarPorEstudante(int idEstudante) {

        String sql = """
                SELECT
                    id_desempenho,
                    id_estudante,
                    id_disciplina,
                    percentual_acerto
                FROM desempenho
                WHERE id_estudante = ?
                LIMIT 1
                """;

        try (Connection conexao = ConexaoBanco.conectar();
             PreparedStatement comando =
                     conexao.prepareStatement(sql)) {

            comando.setInt(1, idEstudante);

            ResultSet resultado =
                    comando.executeQuery();

            if (resultado.next()) {

                Desempenho desempenho =
                        new Desempenho();

                desempenho.setIdDesempenho(
                        resultado.getInt(
                                "id_desempenho"
                        )
                );

                desempenho.setPercentualAcerto(
                        resultado.getDouble(
                                "percentual_acerto"
                        )
                );

                return desempenho;
            }

        } catch (SQLException e) {

            System.out.println(
                    "Erro ao buscar desempenho:"
            );

            e.printStackTrace();
        }

        return null;
    }


    // Atualiza ou cria o desempenho do estudante
    public void atualizarPercentual(
            int idEstudante,
            double percentual) {

        String sqlVerificar = """
                SELECT id_desempenho
                FROM desempenho
                WHERE id_estudante = ?
                LIMIT 1
                """;

        String sqlAtualizar = """
                UPDATE desempenho
                SET percentual_acerto = ?
                WHERE id_estudante = ?
                """;

        String sqlInserir = """
                INSERT INTO desempenho
                (
                    id_estudante,
                    id_disciplina,
                    percentual_acerto
                )
                VALUES (?, ?, ?)
                """;

        try (Connection conexao =
                     ConexaoBanco.conectar()) {

            boolean desempenhoExiste = false;

            // Verifica se o estudante já possui desempenho
            try (PreparedStatement comando =
                         conexao.prepareStatement(
                                 sqlVerificar
                         )) {

                comando.setInt(
                        1,
                        idEstudante
                );

                ResultSet resultado =
                        comando.executeQuery();

                if (resultado.next()) {
                    desempenhoExiste = true;
                }
            }


            if (desempenhoExiste) {

                // Atualiza o desempenho existente
                try (PreparedStatement comando =
                             conexao.prepareStatement(
                                     sqlAtualizar
                             )) {

                    comando.setDouble(
                            1,
                            percentual
                    );

                    comando.setInt(
                            2,
                            idEstudante
                    );

                    comando.executeUpdate();

                    System.out.println(
                            "Percentual de desempenho atualizado para "
                                    + percentual
                                    + "%"
                    );
                }

            } else {

                // Matemática = id_disciplina 1
                int idDisciplina = 1;

                // Cria o primeiro desempenho do estudante
                try (PreparedStatement comando =
                             conexao.prepareStatement(
                                     sqlInserir
                             )) {

                    comando.setInt(
                            1,
                            idEstudante
                    );

                    comando.setInt(
                            2,
                            idDisciplina
                    );

                    comando.setDouble(
                            3,
                            percentual
                    );

                    comando.executeUpdate();

                    System.out.println(
                            "Desempenho criado com "
                                    + percentual
                                    + "%"
                    );
                }
            }

        } catch (SQLException e) {

            System.out.println(
                    "Erro ao atualizar desempenho:"
            );

            e.printStackTrace();
        }
    }
}