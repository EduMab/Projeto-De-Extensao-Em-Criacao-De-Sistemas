package br.com.evoluamais.config;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;

public class ConexaoBanco {

    private static final String URL =
            "jdbc:mysql://localhost:3306/evoluamais";

    private static final String USUARIO =
            System.getenv("DB_USUARIO");

    private static final String SENHA =
            System.getenv("DB_SENHA");

    public static Connection conectar() throws SQLException {

        if (USUARIO == null || SENHA == null) {
            throw new SQLException(
                    "Variáveis DB_USUARIO e DB_SENHA não configuradas."
            );
        }

        return DriverManager.getConnection(
                URL,
                USUARIO,
                SENHA
        );
    }
}