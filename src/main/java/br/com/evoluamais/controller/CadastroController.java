package br.com.evoluamais.controller;

import br.com.evoluamais.model.Estudante;
import br.com.evoluamais.repository.EstudanteRepository;

import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/cadastro")
public class CadastroController {

    private final EstudanteRepository estudanteRepository;

    public CadastroController() {
        this.estudanteRepository = new EstudanteRepository();
    }

    @PostMapping
    public Map<String, Object> cadastrar(
            @RequestParam String nome,
            @RequestParam String email,
            @RequestParam String senha) {

        Map<String, Object> resposta = new HashMap<>();

        // Verifica se o e-mail já está cadastrado
        if (estudanteRepository.emailExiste(email)) {

            resposta.put("sucesso", false);
            resposta.put(
                    "mensagem",
                    "Este e-mail já está cadastrado."
            );

            return resposta;
        }

        // Por enquanto novos estudantes utilizam a Prova 1
        int idProva = 1;

        Estudante estudante =
                estudanteRepository.cadastrar(
                        nome,
                        email,
                        senha,
                        idProva
                );

        if (estudante == null) {

            resposta.put("sucesso", false);
            resposta.put(
                    "mensagem",
                    "Não foi possível realizar o cadastro."
            );

            return resposta;
        }

        resposta.put("sucesso", true);
        resposta.put(
                "mensagem",
                "Cadastro realizado com sucesso!"
        );

        resposta.put(
                "idEstudante",
                estudante.getIdEstudante()
        );

        resposta.put(
                "nome",
                estudante.getUsuario().getNome()
        );

        return resposta;
    }
}