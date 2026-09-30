package br.com.evoluamais.controller;

import br.com.evoluamais.model.Estudante;
import br.com.evoluamais.repository.EstudanteRepository;

import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/login")
public class LoginController {

    private final EstudanteRepository estudanteRepository;

    public LoginController() {
        this.estudanteRepository =
                new EstudanteRepository();
    }

    @PostMapping
    public Map<String, Object> login(
            @RequestParam String email,
            @RequestParam String senha) {

        Estudante estudante =
                estudanteRepository.fazerLogin(
                        email,
                        senha
                );

        Map<String, Object> resposta =
                new HashMap<>();

        if (estudante == null) {

            resposta.put("sucesso", false);
            resposta.put(
                    "mensagem",
                    "E-mail ou senha inválidos."
            );

            return resposta;
        }

        resposta.put("sucesso", true);
        resposta.put(
                "idEstudante",
                estudante.getIdEstudante()
        );

        resposta.put(
                "nome",
                estudante.getUsuario().getNome()
        );

        resposta.put(
                "email",
                estudante.getUsuario().getEmail()
        );

        return resposta;
    }
}