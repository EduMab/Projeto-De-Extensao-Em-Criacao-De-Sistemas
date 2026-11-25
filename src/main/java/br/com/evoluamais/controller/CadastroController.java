package br.com.evoluamais.controller;

import br.com.evoluamais.model.Estudante;
import br.com.evoluamais.repository.EstudanteRepository;

import org.springframework.web.bind.annotation.*;
import jakarta.servlet.http.HttpServletRequest;

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
            @RequestParam String senha,
            HttpServletRequest request) {

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

        // A prova inicial atende a FK legada; a selecao semanal mistura o acervo ETEC.
        Integer idProva = estudanteRepository.provaInicial();
        if (idProva == null) {
            resposta.put("sucesso", false);
            resposta.put("mensagem", "O acervo ainda nao esta disponivel. Tente novamente mais tarde.");
            return resposta;
        }

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

        var session = request.getSession();
        request.changeSessionId();
        session.setAttribute("idEstudante", estudante.getIdEstudante());
        session.setAttribute("nomeEstudante", estudante.getUsuario().getNome());
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
