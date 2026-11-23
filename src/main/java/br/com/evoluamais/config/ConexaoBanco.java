package br.com.evoluamais.config;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;

public class ConexaoBanco {

    private static final String USUARIO =
            System.getenv("DB_USUARIO");

    private static final String SENHA =
            System.getenv("DB_SENHA");

    public static Connection conectar() throws SQLException {

        String url = System.getenv("DB_URL");

        if (url == null || url.isBlank()) {
            url = "jdbc:mysql://localhost:3306/evoluamais";
        }

        if (USUARIO == null || USUARIO.isBlank() || SENHA == null) {
            throw new SQLException(
                    "Variáveis DB_USUARIO e DB_SENHA não configuradas."
            );
        }

        return DriverManager.getConnection(
                url,
                USUARIO,
                SENHA
        );
    }
}
