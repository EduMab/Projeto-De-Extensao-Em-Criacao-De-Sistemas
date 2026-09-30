package br.com.evoluamais.repository;

import br.com.evoluamais.config.ConexaoBanco;
import br.com.evoluamais.model.Estudante;
import br.com.evoluamais.model.Usuario;
import br.com.evoluamais.service.SenhaService;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;

public class EstudanteRepository {

    private final SenhaService senhaService;

    public EstudanteRepository() {
        this.senhaService = new SenhaService();
    }


    // LOGIN
    public Estudante fazerLogin(String email, String senhaDigitada) {

        String sql = """
                SELECT
                    e.id_estudante,
                    u.id_usuario,
                    u.nome,
                    u.email,
                    u.senha
                FROM estudante e
                INNER JOIN usuario u
                    ON e.id_usuario = u.id_usuario
                WHERE u.email = ?
                LIMIT 1
                """;

        try (Connection conexao = ConexaoBanco.conectar();
             PreparedStatement comando =
                     conexao.prepareStatement(sql)) {

            comando.setString(1, email);

            ResultSet resultado =
                    comando.executeQuery();

            if (resultado.next()) {

                int idUsuario =
                        resultado.getInt("id_usuario");

                String senhaBanco =
                        resultado.getString("senha");

                boolean senhaCorreta;

                // Senha já utiliza BCrypt
                if (senhaBanco != null &&
                        senhaBanco.startsWith("$2")) {

                    senhaCorreta =
                            senhaService.verificar(
                                    senhaDigitada,
                                    senhaBanco
                            );

                } else {

                    // Compatibilidade temporária
                    // com usuários antigos
                    senhaCorreta =
                            senhaBanco != null &&
                                    senhaBanco.equals(senhaDigitada);

                    // Se o login antigo estiver correto,
                    // converte automaticamente para BCrypt
                    if (senhaCorreta) {

                        atualizarSenhaParaHash(
                                idUsuario,
                                senhaDigitada
                        );
                    }
                }

                if (!senhaCorreta) {
                    return null;
                }

                Usuario usuario =
                        new Usuario();

                usuario.setIdUsuario(idUsuario);

                usuario.setNome(
                        resultado.getString("nome")
                );

                usuario.setEmail(
                        resultado.getString("email")
                );


                Estudante estudante =
                        new Estudante();

                estudante.setIdEstudante(
                        resultado.getInt(
                                "id_estudante"
                        )
                );

                estudante.setUsuario(usuario);

                return estudante;
            }

        } catch (SQLException e) {

            System.out.println(
                    "Erro ao realizar login:"
            );

            e.printStackTrace();
        }

        return null;
    }


    // CONVERTE SENHA ANTIGA PARA BCRYPT
    private void atualizarSenhaParaHash(
            int idUsuario,
            String senha) {

        String sql = """
                UPDATE usuario
                SET senha = ?
                WHERE id_usuario = ?
                """;

        String hash =
                senhaService.gerarHash(senha);

        try (Connection conexao =
                     ConexaoBanco.conectar();

             PreparedStatement comando =
                     conexao.prepareStatement(sql)) {

            comando.setString(1, hash);
            comando.setInt(2, idUsuario);

            comando.executeUpdate();

            System.out.println(
                    "Senha antiga convertida para BCrypt."
            );

        } catch (SQLException e) {

            System.out.println(
                    "Erro ao atualizar senha:"
            );

            e.printStackTrace();
        }
    }


    // VERIFICA SE O EMAIL JÁ EXISTE
    public boolean emailExiste(String email) {

        String sql = """
                SELECT id_usuario
                FROM usuario
                WHERE email = ?
                LIMIT 1
                """;

        try (Connection conexao =
                     ConexaoBanco.conectar();

             PreparedStatement comando =
                     conexao.prepareStatement(sql)) {

            comando.setString(1, email);

            ResultSet resultado =
                    comando.executeQuery();

            return resultado.next();

        } catch (SQLException e) {

            System.out.println(
                    "Erro ao verificar e-mail:"
            );

            e.printStackTrace();

            return true;
        }
    }


    // CADASTRO
    public Estudante cadastrar(
            String nome,
            String email,
            String senha,
            int idProva) {

        String sqlUsuario = """
                INSERT INTO usuario
                    (nome, email, senha)
                VALUES (?, ?, ?)
                """;

        String sqlEstudante = """
                INSERT INTO estudante
                    (id_usuario, id_prova)
                VALUES (?, ?)
                """;

        Connection conexao = null;

        try {

            conexao =
                    ConexaoBanco.conectar();

            conexao.setAutoCommit(false);

            int idUsuario;

            // Gera o hash ANTES de salvar
            String senhaHash =
                    senhaService.gerarHash(senha);


            try (PreparedStatement comandoUsuario =
                         conexao.prepareStatement(
                                 sqlUsuario,
                                 Statement.RETURN_GENERATED_KEYS
                         )) {

                comandoUsuario.setString(
                        1,
                        nome
                );

                comandoUsuario.setString(
                        2,
                        email
                );

                comandoUsuario.setString(
                        3,
                        senhaHash
                );

                comandoUsuario.executeUpdate();


                ResultSet chaves =
                        comandoUsuario.getGeneratedKeys();

                if (!chaves.next()) {

                    conexao.rollback();

                    return null;
                }

                idUsuario =
                        chaves.getInt(1);
            }


            int idEstudante;


            try (PreparedStatement comandoEstudante =
                         conexao.prepareStatement(
                                 sqlEstudante,
                                 Statement.RETURN_GENERATED_KEYS
                         )) {

                comandoEstudante.setInt(
                        1,
                        idUsuario
                );

                comandoEstudante.setInt(
                        2,
                        idProva
                );

                comandoEstudante.executeUpdate();


                ResultSet chaves =
                        comandoEstudante.getGeneratedKeys();

                if (!chaves.next()) {

                    conexao.rollback();

                    return null;
                }

                idEstudante =
                        chaves.getInt(1);
            }


            conexao.commit();


            Usuario usuario =
                    new Usuario();

            usuario.setIdUsuario(
                    idUsuario
            );

            usuario.setNome(
                    nome
            );

            usuario.setEmail(
                    email
            );


            Estudante estudante =
                    new Estudante();

            estudante.setIdEstudante(
                    idEstudante
            );

            estudante.setUsuario(
                    usuario
            );


            System.out.println(
                    "Estudante cadastrado com sucesso!"
            );

            return estudante;


        } catch (SQLException e) {

            if (conexao != null) {

                try {

                    conexao.rollback();

                } catch (SQLException erroRollback) {

                    erroRollback.printStackTrace();
                }
            }


            System.out.println(
                    "Erro ao cadastrar estudante:"
            );

            e.printStackTrace();

            return null;


        } finally {

            if (conexao != null) {

                try {

                    conexao.setAutoCommit(true);
                    conexao.close();

                } catch (SQLException e) {

                    e.printStackTrace();
                }
            }
        }
    }
}