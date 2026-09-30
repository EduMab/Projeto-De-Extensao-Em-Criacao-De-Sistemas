package br.com.evoluamais.service;

import br.com.evoluamais.model.Usuario;
import br.com.evoluamais.repository.UsuarioRepository;

public class UsuarioService {

    private UsuarioRepository usuarioRepository;

    public UsuarioService() {
        this.usuarioRepository = new UsuarioRepository();
    }

    public void cadastrarUsuario(Usuario usuario) {
        usuarioRepository.salvar(usuario);
    }
}