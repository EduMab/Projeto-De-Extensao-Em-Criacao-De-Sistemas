package br.com.evoluamais.service;

import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;

public class SenhaService {

    private final BCryptPasswordEncoder encoder;

    public SenhaService() {
        this.encoder = new BCryptPasswordEncoder();
    }

    public String gerarHash(String senha) {
        return encoder.encode(senha);
    }

    public boolean verificar(String senha, String hash) {
        return encoder.matches(senha, hash);
    }
}