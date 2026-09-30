package br.com.evoluamais;

import br.com.evoluamais.model.Usuario;
import br.com.evoluamais.repository.UsuarioRepository;

public class TesteConexao {

    public static void main(String[] args) {

        Usuario usuario = new Usuario(
                0,
                "Eduardo",
                "eduardo@email.com",
                "123456"
        );

        UsuarioRepository repository = new UsuarioRepository();

        repository.salvar(usuario);
    }
}